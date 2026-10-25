#!/usr/bin/env python3
"""Loopback-only revision bridge. Uses official Codex ChatGPT login; accepts no API keys."""
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8766
MAX_BODY = 2_000_000
HOST = f'127.0.0.1:{PORT}'
ORIGIN = f'http://{HOST}'
PARENT_ORIGINS = ['https://alfapakk-cloud.github.io', 'http://127.0.0.1:8765', ORIGIN]
SESSION = secrets.token_urlsafe(32)
LOCK = threading.Lock()
ACTIVE = {}
CANCELLED = set()
PROGRESS = {}


def studio_page(project=None):
    source = Path(__file__).with_name('studio.html')
    if not source.is_file():
        source = Path(__file__).parent.parent / 'index.html'
    page = source.read_text(encoding='utf-8')
    if project is not None:
        if not isinstance(project, dict) or not isinstance(project.get('articles'), list):
            raise ValueError('Нужен проект с очередью статей.')
        payload = json.dumps(project, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        tag = '<script type="application/json" id="alfapromTransfer">' + payload + '</script>'
        page = page.replace('<body>', '<body>' + tag, 1)
    return page


def set_progress(job_id, stage):
    with LOCK:
        now = time.monotonic()
        state = PROGRESS.setdefault(job_id, {'started': now})
        order = ['connecting', 'authenticating', 'starting', 'generating', 'validating', 'complete']
        if state.get('stage') in order and order.index(stage) < order.index(state['stage']):
            return
        state.update(stage=stage, updated=now)
        # No article, prompt, model output or account data is kept in progress records.
        for old_id in list(PROGRESS):
            if old_id != job_id and old_id not in ACTIVE and now - PROGRESS[old_id]['updated'] > 1800:
                del PROGRESS[old_id]


def progress_snapshot(job_id):
    with LOCK:
        state = PROGRESS.get(job_id)
        if not state:
            return {'stage': 'connecting', 'elapsed': 0}
        return {'stage': state['stage'], 'elapsed': round(time.monotonic() - state['started'])}


def watch_events(path, job_id, stop):
    # Read only documented event types. Never forward model text or raw stderr to the page.
    with path.open(encoding='utf-8') as stream:
        while not stop.is_set():
            line = stream.readline()
            if not line:
                stop.wait(.25)
                continue
            try:
                event = json.loads(line)
                if event.get('type') == 'turn.started':
                    set_progress(job_id, 'generating')
                elif event.get('type') == 'turn.completed':
                    set_progress(job_id, 'validating')
            except (ValueError, AttributeError):
                pass


def codex_binary():
    binary = shutil.which('codex')
    if not binary:
        candidate = Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
        if candidate.is_file():
            binary = str(candidate)
    if not binary:
        raise ValueError('Не найден официальный Codex CLI. Установите Codex из официального источника и выполните codex login с аккаунтом ChatGPT.')
    return binary


def clean_environment():
    result = os.environ.copy()
    for key in ['OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'AZURE_OPENAI_API_KEY']:
        result.pop(key, None)
    return result


def chatgpt_status(binary, env):
    status = subprocess.run([binary, 'login', 'status'], capture_output=True, text=True, timeout=15, env=env)
    output = ' '.join((status.stdout + status.stderr).lower().split())
    if not status.returncode and 'logged in using chatgpt' in output:
        return {'state': 'chatgpt', 'exitCode': 0}
    reason = 'not_signed_in'
    if any(word in output for word in ['keychain', 'keyring', 'credential store']):
        reason = 'credential_store'
    elif any(word in output for word in ['permission denied', 'operation not permitted']):
        reason = 'permission'
    elif any(word in output for word in ['error loading config', 'error parsing', 'invalid config']):
        reason = 'configuration'
    elif 'api key' in output:
        reason = 'api_mode'
    return {'state': 'required', 'reason': reason, 'exitCode': status.returncode}


def require_chatgpt(binary, env):
    state = chatgpt_status(binary, env)
    if state['state'] != 'chatgpt':
        raise ValueError('Нужен вход Codex через ChatGPT. Выполните codex login и выберите свой Plus-аккаунт. Режим API-ключа помощник не использует.')


def execute_revision(prompt, job_id):
    set_progress(job_id, 'authenticating')
    binary, env = codex_binary(), clean_environment()
    require_chatgpt(binary, env)
    with LOCK:
        if job_id in CANCELLED:
            CANCELLED.discard(job_id)
            raise ValueError('Доработка остановлена. Исходная статья не изменена.')
    with tempfile.TemporaryDirectory(prefix='alfaprom-revision-') as folder:
        root = Path(folder)
        schema = {'type': 'object', 'properties': {'html': {'type': 'string'}}, 'required': ['html'], 'additionalProperties': False}
        schema_file, result_file = root / 'response-schema.json', root / 'result.json'
        schema_file.write_text(json.dumps(schema), encoding='utf-8')
        command = [binary, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
                   '--sandbox', 'read-only', '--json', '--color', 'never', '-c', 'model_provider="openai"',
                   '-c', 'forced_login_method="chatgpt"', '-c', 'features.shell_tool=false',
                   '--output-schema', str(schema_file), '--output-last-message', str(result_file), '-']
        instruction = ('Выполни редакционную доработку по заданию ниже. Не используй локальные файлы, shell, '
                       'внешние приложения, MCP или подагентов. Верни JSON по схеме: единственное поле html '
                       'с полным исправленным HTML. Сохрани техническую метку версии в html. '
                       'Не создавай файл на диске — верни содержимое в финальном ответе.\n\n' + prompt)
        events_path, errors_path = root / 'events.jsonl', root / 'errors.log'
        events_file, errors_file = events_path.open('w'), errors_path.open('w')
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=events_file, stderr=errors_file,
                                   text=True, env=env, cwd=root, start_new_session=True)
        set_progress(job_id, 'starting')
        stop = threading.Event()
        watcher = threading.Thread(target=watch_events, args=(events_path, job_id, stop), daemon=True)
        watcher.start()
        with LOCK:
            ACTIVE[job_id] = process
            if job_id in CANCELLED:
                os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(instruction, timeout=900)
            with LOCK:
                cancelled = job_id in CANCELLED
            if cancelled:
                raise ValueError('Доработка остановлена. Исходная статья не изменена.')
            if process.returncode:
                # Raw stderr can contain article fragments and local paths; never expose it to a website.
                combined = ((stdout or '') + (stderr or '') + errors_path.read_text(encoding='utf-8', errors='replace') + events_path.read_text(encoding='utf-8', errors='replace')).lower()
                if any(word in combined for word in ['rate_limit', 'usage limit', 'limit reached', 'quota', 'credits']):
                    raise ValueError('Лимит ChatGPT/Codex исчерпан или запрос недоступен по тарифу. Доработка остановлена; платный API не подключается.')
                raise ValueError('Codex не завершил запрос. Проверьте вход через ChatGPT, доступ к сети и лимиты подписки. Платного API-перехода нет.')
            if not result_file.is_file():
                raise ValueError('Codex не вернул итоговый HTML. Исходная статья не изменена.')
            set_progress(job_id, 'validating')
            data = json.loads(result_file.read_text(encoding='utf-8'))
            html = data.get('html')
            if not isinstance(html, str) or len(html.encode('utf-8')) > MAX_BODY or not html.strip():
                raise ValueError('Ответ не содержит подходящий HTML статьи.')
            set_progress(job_id, 'complete')
            return html
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate(timeout=15)
            raise ValueError('Доработка превысила 15 минут и остановлена. Исходный текст сохранён.')
        finally:
            stop.set()
            watcher.join(timeout=1)
            events_file.close()
            errors_file.close()
            with LOCK:
                ACTIVE.pop(job_id, None)
                CANCELLED.discard(job_id)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, status, data, content_type='application/json; charset=utf-8'):
        payload = data.encode('utf-8') if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        ancestors = ' '.join(PARENT_ORIGINS)
        policy = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors " + ancestors + "; base-uri 'none'"
        if self.path == '/studio':
            policy = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src https: data:; frame-src 'self' about:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        self.send_header('Content-Security-Policy', policy)
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def valid_host(self):
        return self.headers.get('Host') == HOST

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {'error': 'Host rejected'})
        if self.path == '/health':
            return self.send(200, {'service': 'alfaprom-seo-helper', 'version': 4})
        if self.path == '/studio':
            return self.send(200, studio_page(), 'text/html; charset=utf-8')
        if self.path != '/':
            return self.send(404, {'error': 'Not found'})
        page = (Path(__file__).parent / 'panel.html').read_text(encoding='utf-8')
        page = page.replace('__SESSION_JSON__', json.dumps(SESSION)).replace('__PARENTS_JSON__', json.dumps(PARENT_ORIGINS))
        self.send(200, page, 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path == '/studio':
            if not self.valid_host() or self.headers.get('Origin') not in PARENT_ORIGINS:
                return self.send(403, {'error': 'Перенос разрешён только из студии.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 20_000_000 or self.headers.get('Content-Type', '').split(';')[0] != 'application/x-www-form-urlencoded':
                    raise ValueError('Некорректный формат проекта или размер более 20 МБ.')
                fields = parse_qs(self.rfile.read(length).decode('utf-8'), max_num_fields=2)
                project = json.loads(fields.get('project', [''])[0])
                return self.send(200, studio_page(project), 'text/html; charset=utf-8')
            except (ValueError, UnicodeError) as exc:
                return self.send(400, {'error': str(exc)})
        if not self.valid_host() or self.headers.get('Origin') != ORIGIN or self.headers.get('X-Alfaprom-Session') != SESSION:
            return self.send(403, {'error': 'Доступ разрешён только подключённому локальному окну студии.'})
        if self.path not in ['/revise', '/cancel', '/progress', '/auth-status']:
            return self.send(404, {'error': 'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.send(413, {'error': 'Максимум 2 МБ.'})
            data = json.loads(self.rfile.read(length))
            job_id = data.get('jobId', '')
            if not isinstance(job_id, str) or not 10 <= len(job_id) <= 100:
                raise ValueError('Некорректный идентификатор задания.')
            if self.path == '/auth-status':
                return self.send(200, chatgpt_status(codex_binary(), clean_environment()))
            if self.path == '/progress':
                return self.send(200, progress_snapshot(job_id))
            if self.path == '/cancel':
                with LOCK:
                    if job_id in PROGRESS:
                        CANCELLED.add(job_id)
                    process = ACTIVE.get(job_id)
                    if process and process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                return self.send(200, {'cancelled': True})
            prompt = data.get('prompt')
            if not isinstance(prompt, str) or not 100 <= len(prompt) <= MAX_BODY:
                raise ValueError('Нужно полное редакционное задание.')
            # A single job per helper avoids accidental parallel use of plan allowance.
            if not JOB_LOCK.acquire(blocking=False):
                return self.send(409, {'error': 'Другая доработка уже выполняется. Дождитесь результата.'})
            try:
                set_progress(job_id, 'connecting')
                html = execute_revision(prompt, job_id)
                self.send(200, {'html': html, 'authMode': 'chatgpt'})
            finally:
                JOB_LOCK.release()
        except (ValueError, json.JSONDecodeError) as exc:
            self.send(400, {'error': str(exc)})
        except Exception:
            self.send(500, {'error': 'Локальный помощник не смог завершить запрос. Исходная статья не изменена.'})


JOB_LOCK = threading.Lock()
def stop_children():
    with LOCK:
        for process in list(ACTIVE.values()):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass


if __name__ == '__main__':
    print(f'Помощник АЛЬФАПРОМ запущен: {ORIGIN}')
    print('Только ChatGPT-вход Codex. API-ключи не используются.')
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    def terminate(_signal, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, terminate)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_children()
        server.server_close()
