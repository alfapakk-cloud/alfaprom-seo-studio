# -*- coding: utf-8 -*-
"""Bounded public-source retrieval. No credentials, proxies, local URLs or paid services."""
import concurrent.futures
import hashlib
import http.client
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
import time
import zlib
from urllib.parse import urljoin, urlsplit, unquote

CACHE_ROOT = Path.home() / 'Library/Application Support/ALFAPROM SEO Studio/source-cache'
MAX_DOWNLOAD = 10_000_000
FACTORY_DOMAINS = ('henkelman.com', 'hualianmachinery.com', 'hualian.biz')


def normalized(text):
    return re.sub(r'\s+', ' ', str(text).replace('\u00ad', '')).strip().casefold()


def public_source_link(url):
    try:
        p = urlsplit(url)
        host = (p.hostname or '').lower().removeprefix('www.')
        path = unquote(p.path).lower()
        return (p.scheme == 'https' and p.port in (None, 443) and not p.username and not p.password
                and host in FACTORY_DOMAINS and len(path) > 4
                and not re.search(r'cart|checkout|order|quote|dealers?|contact|login|/products?/|/catalog|\-pd\d', path + '?' + p.query.lower())
                and bool(re.search(r'\.pdf$|manual|download|support|technical|knowledge|guide|maintenance|faq|vacuum.pack|packaging.*princip', path)))
    except (ValueError, TypeError):
        return False


def checked_url(url):
    if not isinstance(url, str) or len(url) > 2000 or re.search(r'[\x00-\x20\x7f]', url):
        raise ValueError('Некорректный адрес источника.')
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Источники должны открываться по обычному HTTPS.')
    host = p.hostname.encode('idna').decode('ascii')
    addresses = {row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError('Локальные и служебные адреса не подходят для источника.')
    return p, host, sorted(addresses)


class PublicConnection(http.client.HTTPSConnection):
    def __init__(self, host, addresses):
        super().__init__(host, timeout=12, context=ssl.create_default_context())
        self.addresses = addresses

    def connect(self):
        last = None
        for ip in self.addresses:
            try:
                raw = socket.create_connection((ip, 443), self.timeout)
                self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
                return
            except OSError as exc:
                last = exc
        raise last or ValueError('Источник недоступен.')


class TextPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.title = False
        self.title_parts, self.parts = [], []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg'):
            self.skip += 1
        if tag == 'title':
            self.title = True
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'tr', 'td', 'br', 'div'):
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg'):
            self.skip = max(0, self.skip - 1)
        if tag == 'title':
            self.title = False
        self.parts.append(' ')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.title:
                self.title_parts.append(data)


def pdf_text(data):
    # Isolate the document parser: a remote PDF cannot exhaust the helper process.
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('PDF больше 10 МБ.')
    script = '''import io,itertools,logging,resource,sys
logging.disable(logging.CRITICAL)
for kind,desired in [(resource.RLIMIT_AS,512*1024*1024),(resource.RLIMIT_CPU,10)]:
 try:
  soft,hard=resource.getrlimit(kind)
  limit=desired if hard==resource.RLIM_INFINITY else min(desired,hard)
  resource.setrlimit(kind,(limit,hard))
 except (ValueError,OSError): pass # macOS does not implement RLIMIT_AS; parent monitors RSS.
sys.path.insert(0,sys.argv[1])
from pypdf import PdfReader,overwrite_configuration
overwrite_configuration(maximum_declared_stream_length=10000000,
 array_based_stream_maximum_output_length=10000000,zlib_maximum_output_length=10000000,
 lzw_maximum_output_length=10000000,run_length_maximum_output_length=10000000,
 brotli_maximum_output_length=10000000,jbig2_maximum_output_length=10000000,
 image_maximum_buffer_size=10000000,stream_decoding_work_maximum_length=40000000,
 stream_parsing_work_maximum_count=250000,page_tree_maximum_entries=500,
 page_tree_maximum_page_entries=50000,array_maximum_element_count=10000,
 dictionary_maximum_element_count=10000,xform_maximum_invocations_per_extraction=100,
 jbig2dec_binary=None)
r=PdfReader(io.BytesIO(sys.stdin.buffer.read()),strict=False)
if r.is_encrypted: raise ValueError('Encrypted PDF')
out=[];size=0
for page in itertools.islice(r.pages,100):
 t=page.extract_text() or '';out.append(t);size+=len(t)
 if size>800000:break
sys.stdout.write(' '.join(out)[:800000])
'''
    process = subprocess.Popen([sys.executable, '-B', '-c', script, str(Path(__file__).with_name('vendor'))],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    started, pending = time.monotonic(), data
    try:
        while True:
            try:
                output, _ = process.communicate(input=pending, timeout=0.25)
                break
            except subprocess.TimeoutExpired:
                pending = None
                if time.monotonic() - started > 16:
                    raise ValueError('Превышено время чтения PDF.')
                # Query only our own parser PID. Works on macOS where RLIMIT_AS is unsupported.
                usage = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(process.pid)],
                                       capture_output=True, timeout=1)
                if usage.returncode == 0 and usage.stdout.strip():
                    if int(usage.stdout.strip()) > 512 * 1024:
                        raise ValueError('PDF требует слишком много памяти.')
                elif process.poll() is None:
                    raise ValueError('Не удалось проверить ресурсы PDF.')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate()
    if process.returncode or not output.strip():
        raise ValueError('PDF не содержит доступного для проверки текста.')
    return output.decode('utf-8', errors='replace'), ''


def fetch_document(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    cache = CACHE_ROOT / (key + '.json')
    try:
        if cache.stat().st_size <= 2_000_000 and time.time() - cache.stat().st_mtime < 12 * 3600:
            saved = json.loads(cache.read_text(encoding='utf-8'))
            if saved.get('url') == url and saved.get('text'):
                return saved
    except (OSError, ValueError):
        pass
    current = url
    for _ in range(5):
        parsed, host, addresses = checked_url(current)
        connection = PublicConnection(host, addresses)
        try:
            path = parsed.path or '/'
            if parsed.query:
                path += '?' + parsed.query
            connection.request('GET', path, headers={'User-Agent': 'ALFAPROM-Source-Checker/1.8', 'Accept-Encoding': 'gzip, deflate'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                if not location:
                    raise ValueError('Источник не сообщил новый адрес.')
                current = urljoin(current, location)
                continue
            if response.status != 200:
                raise ValueError('Источник недоступен: HTTP ' + str(response.status))
            data = response.read(MAX_DOWNLOAD + 1)
            if len(data) > MAX_DOWNLOAD:
                raise ValueError('Документ больше 10 МБ.')
            encoding = response.getheader('Content-Encoding', 'identity').strip().lower()
            if encoding in ('gzip', 'deflate'):
                decoder = zlib.decompressobj(31 if encoding == 'gzip' else 15)
                data = decoder.decompress(data, MAX_DOWNLOAD + 1)
                if len(data) > MAX_DOWNLOAD or decoder.unconsumed_tail or not decoder.eof:
                    raise ValueError('Сжатый документ превышает допустимый размер или повреждён.')
            elif encoding not in ('identity', ''):
                raise ValueError('Источник вернул неподдерживаемое сжатие: ' + encoding)
            mime = response.getheader('Content-Type', '').lower()
            if data.startswith(b'%PDF-'):
                text, title = pdf_text(data)
            elif 'html' in mime:
                charset = response.headers.get_content_charset() or 'utf-8'
                page = TextPage()
                page.feed(data.decode(charset, errors='replace'))
                text, title = ' '.join(page.parts), ' '.join(page.title_parts)
            elif mime.startswith('text/plain'):
                text, title = data.decode('utf-8', errors='replace'), ''
            else:
                raise ValueError('Нужен HTML, текстовый документ или PDF.')
            text = re.sub(r'\s+', ' ', text).strip()[:800000]
            if len(text) < 100:
                raise ValueError('В источнике недостаточно доступного текста.')
            saved = {'url': url, 'finalUrl': current, 'title': title[:500], 'text': text,
                     'sha256': hashlib.sha256(data).hexdigest(), 'checkedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                     'publicAllowed': public_source_link(url) and public_source_link(current)}
            try:
                CACHE_ROOT.mkdir(parents=True, exist_ok=True)
                temporary = cache.with_suffix('.tmp')
                temporary.write_text(json.dumps(saved, ensure_ascii=False), encoding='utf-8')
                temporary.replace(cache)
            except OSError:
                pass
            return saved
        finally:
            connection.close()
    raise ValueError('Слишком много перенаправлений источника.')


def verify_sources(data):
    """Verify retrieval and literal quotations. Relevance remains a separate model audit."""
    facts = data.get('facts', [])
    sources = data.get('sources', [])
    urls = list(dict.fromkeys([f.get('sourceUrl') for f in facts] + [s.get('url') for s in sources]))
    urls = [u for u in urls if isinstance(u, str) and u][:12]

    def retrieve(url):
        try:
            return url, fetch_with_retry(url)
        except Exception as exc:
            return url, {'error': str(exc)[:300]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        documents = dict(pool.map(retrieve, urls))
    verified = []
    for source in sources[:12]:
        doc = documents.get(source.get('url'), {})
        quote = source.get('quote', '')
        title = source.get('title', '')
        title_present = len(title) >= 5 and normalized(title) in normalized(doc.get('title', '') + ' ' + doc.get('text', ''))
        ok = not doc.get('error') and title_present and 30 <= len(quote) <= 6000 and normalized(quote) in normalized(doc.get('text', ''))
        source['verification'] = {'verified': bool(ok), 'checkedAt': doc.get('checkedAt'),
                                  'sha256': doc.get('sha256'), 'publicAllowed': bool(ok and doc.get('publicAllowed')),
                                  'reason': doc.get('error', '' if ok else 'Точная выдержка не найдена в документе.')}
        if ok:
            verified.append(source['url'])
    for fact in facts:
        doc = documents.get(fact.get('sourceUrl'), {})
        quote = fact.get('sourceQuote', '')
        ok = fact.get('sourceUrl') in verified and not doc.get('error') and 30 <= len(quote) <= 6000 and normalized(quote) in normalized(doc.get('text', ''))
        fact['verification'] = {'verified': bool(ok), 'checkedAt': doc.get('checkedAt'), 'sha256': doc.get('sha256'),
                                'reason': doc.get('error', '' if ok else 'Точная выдержка не найдена в документе.')}
    data['sourceChecks'] = {'version': 1, 'verifiedUrls': list(dict.fromkeys(verified)), 'checkedUrls': len(documents)}
    # A positive fact verdict needs both the independent relevance judgement and real evidence.
    unsupported = [f for f in facts if not f['verification']['verified']]
    for criterion in data.get('criteria', []):
        if criterion['id'] in (3, 4) and criterion['status'] == 'pass' and (unsupported or not verified):
            criterion['status'] = 'unverified'
            criterion['reason'] = ('Нужно найти доступный первоисточник и точные выдержки либо исправить неподтверждённые утверждения. '
                                   'Проверенных документов: %d; фактов без подтверждения: %d.' % (len(verified), len(unsupported)))
    return data


def fetch_with_retry(url):
    for attempt in range(2):
        try:
            return fetch_document(url)
        except (OSError, http.client.HTTPException):
            if attempt:
                raise


def verify_links(urls):
    if not isinstance(urls, list) or len(urls) > 40 or any(not isinstance(u, str) for u in urls):
        raise ValueError('Некорректный список ссылок статьи.')
    def check(url):
        try:
            doc = fetch_with_retry(url)
            if public_source_link(url) and not doc.get('publicAllowed'):
                raise ValueError('Техническая ссылка перенаправляет за пределы разрешённых материалов завода.')
            original_host = (urlsplit(url).hostname or '').lower().removeprefix('www.')
            final_host = (urlsplit(doc.get('finalUrl', url)).hostname or '').lower().removeprefix('www.')
            if original_host == 'alfaprom.org' and final_host != original_host:
                raise ValueError('Внутренняя ссылка перенаправляет на другой сайт.')
            return {'url': url, 'ok': True, 'checkedAt': doc['checkedAt'], 'finalUrl': doc.get('finalUrl', url)}
        except Exception as exc:
            return {'url': url, 'ok': False, 'kind': 'unavailable' if isinstance(exc, (OSError, http.client.HTTPException)) else 'invalid', 'reason': str(exc)[:300]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(check, list(dict.fromkeys(urls))))
