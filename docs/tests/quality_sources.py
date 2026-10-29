#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source and scoped-contract tests. Fixtures only; no inference or user account files."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'helper'))
import quality_sources as sources
import quality_schema
import alfaprom_helper as helper

URL = 'https://henkelman.com/en/support'
QUOTE = 'The selected packaging material must be suitable for the product and process.'
DOCUMENT = {'url': URL, 'finalUrl': URL, 'title': 'Technical Guide',
            'text': 'Technical Guide. ' + QUOTE + ' Details are verified for this fixture only.',
            'sha256': 'fixture-hash', 'checkedAt': '2026-10-29T10:00:00Z', 'publicAllowed': True}


def report():
    return {'version': 2, 'fingerprint': 'fixture', 'criteria': [
        {'id': 3, 'status': 'pass', 'reason': 'A detailed model judgement of the technical facts.'},
        {'id': 4, 'status': 'pass', 'reason': 'A detailed model judgement of the primary documents.'}],
        'issues': [], 'facts': [{'claim': 'A precise claim copied from the article.', 'sourceUrl': URL, 'sourceQuote': QUOTE}],
        'sources': [{'url': URL, 'title': 'Technical Guide', 'publisher': 'Henkelman',
                     'edition': 'Fixture edition', 'section': 'Fixture section', 'quote': QUOTE}], 'visuals': []}


class SourcesTests(unittest.TestCase):
    def test_only_approved_factory_technical_links_are_public(self):
        for url in [URL, 'https://www.hualianmachinery.com/download.html', 'https://www.hualian.biz/manual.pdf']:
            with self.subTest(url=url):
                self.assertTrue(sources.public_source_link(url))
        for url in ['https://henkelman.com/en/dealers', 'https://henkelman.com.evil.example/manual.pdf',
                    'https://dealers.henkelman.com/manual.pdf', 'https://www.hualianmachinery.com/product/test',
                    'http://henkelman.com/en/support', 'https://henkelman.com/en/support?order=1',
                    'https://user:pass@henkelman.com/manual.pdf', 'https://henkelman.com:444/manual.pdf']:
            with self.subTest(url=url):
                self.assertFalse(sources.public_source_link(url))

    def test_private_and_local_addresses_rejected(self):
        for ip in ['127.0.0.1', '10.0.0.1', '169.254.169.254', '192.168.1.1', '::1', 'fd00::1', '100.64.0.1']:
            with self.subTest(ip=ip), patch.object(socket, 'getaddrinfo', return_value=[(None, None, None, None, (ip, 443))]):
                with self.assertRaises(ValueError):
                    sources.checked_url('https://source.example/guide')

    def test_mixed_public_and_private_dns_rejected(self):
        records = [(None, None, None, None, ('8.8.8.8', 443)), (None, None, None, None, ('127.0.0.1', 443))]
        with patch.object(socket, 'getaddrinfo', return_value=records), self.assertRaises(ValueError):
            sources.checked_url(URL)

    def test_schemes_credentials_ports_and_control_characters_rejected(self):
        for url in ['file:///etc/passwd', 'http://example.org/doc', 'https://user:pass@example.org/doc',
                    'https://example.org:444/doc', 'https://example.org/doc\nHeader: injected', 'ftp://example.org/doc']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                sources.checked_url(url)

    def test_exact_quote_and_title_support_positive_evidence(self):
        with patch.object(sources, 'fetch_document', return_value=copy.deepcopy(DOCUMENT)):
            result = sources.verify_sources(report())
        self.assertTrue(result['facts'][0]['verification']['verified'])
        self.assertTrue(result['sources'][0]['verification']['verified'])
        self.assertEqual(result['sourceChecks']['verifiedUrls'], [URL])
        self.assertTrue(all(c['status'] == 'pass' for c in result['criteria']))

    def test_fabricated_quote_cannot_be_confirmed(self):
        data = report()
        data['facts'][0]['sourceQuote'] = 'A fabricated assertion that is absent from this manufacturer document.'
        with patch.object(sources, 'fetch_document', return_value=copy.deepcopy(DOCUMENT)):
            result = sources.verify_sources(data)
        self.assertFalse(result['facts'][0]['verification']['verified'])
        self.assertTrue(all(c['status'] == 'unverified' for c in result['criteria']))

    def test_fabricated_bibliographic_title_rejected(self):
        data = report()
        data['sources'][0]['title'] = 'A nonexistent manufacturer report of laboratory experiments'
        with patch.object(sources, 'fetch_document', return_value=copy.deepcopy(DOCUMENT)):
            result = sources.verify_sources(data)
        self.assertFalse(result['sources'][0]['verification']['verified'])
        self.assertFalse(result['facts'][0]['verification']['verified'])

    def test_unlisted_fact_source_not_confirmed(self):
        data = report()
        data['sources'] = []
        with patch.object(sources, 'fetch_document', return_value=copy.deepcopy(DOCUMENT)):
            result = sources.verify_sources(data)
        self.assertFalse(result['facts'][0]['verification']['verified'])
        self.assertTrue(all(c['status'] == 'unverified' for c in result['criteria']))

    def test_unavailable_document_is_honestly_unverified(self):
        with patch.object(sources, 'fetch_document', side_effect=ValueError('HTTP 403')):
            result = sources.verify_sources(report())
        self.assertIn('403', result['facts'][0]['verification']['reason'])
        self.assertEqual(result['sourceChecks']['verifiedUrls'], [])

    def test_sources_do_not_add_unrequested_criteria(self):
        data = report()
        data['criteria'] = [{'id': 7, 'status': 'pass', 'reason': 'A detailed judgement of the article links.'}]
        data['sources'], data['facts'] = [], []
        result = sources.verify_sources(data)
        self.assertEqual([c['id'] for c in result['criteria']], [7])

    def test_html_extraction_excludes_scripts_and_preserves_title(self):
        page = sources.TextPage()
        page.feed('<html><title>Technical Guide</title><script>invented evidence</script><p>Material &amp; product</p><style>bad</style></html>')
        text = ' '.join(page.parts)
        self.assertNotIn('invented evidence', text)
        self.assertNotIn('bad', text)
        self.assertIn('Material & product', text)
        self.assertEqual(''.join(page.title_parts), 'Technical Guide')

    def test_pdf_text_is_extracted_in_bounded_subprocess(self):
        sys.path.insert(0, str(ROOT / 'helper/vendor'))
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer = PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        stream.set_data(('BT /F1 12 Tf 10 200 Td (' + QUOTE + ') Tj ET').encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
        output = io.BytesIO()
        writer.write(output)
        text, _ = sources.pdf_text(output.getvalue())
        self.assertIn(QUOTE, text)

    def test_invalid_pdf_does_not_crash_helper(self):
        with self.assertRaises(ValueError):
            sources.pdf_text(b'%PDF-1.4 invalid data')

    def test_link_checks_cover_success_and_failure(self):
        def fetch(url):
            if 'missing' in url:
                raise ValueError('HTTP 404')
            return DOCUMENT
        with patch.object(sources, 'fetch_document', side_effect=fetch):
            result = sources.verify_links([URL, 'https://example.org/missing', URL])
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]['ok'])
        self.assertFalse(result[1]['ok'])

    def test_link_payload_is_bounded(self):
        for payload in ['not-an-array', [URL] * 41, [123]]:
            with self.subTest(payload_type=type(payload).__name__), self.assertRaises(ValueError):
                sources.verify_links(payload)


    def test_factory_redirect_outside_policy_cannot_pass_public_link_check(self):
        doc=copy.deepcopy(DOCUMENT);doc.update(finalUrl='https://dealer.example/cart',publicAllowed=False)
        with patch.object(sources,'fetch_document',return_value=doc):
            result=sources.verify_links([URL])
        self.assertFalse(result[0]['ok']);self.assertIn('перенаправляет',result[0]['reason'])

    def test_internal_link_redirect_to_other_site_does_not_pass(self):
        with patch.object(sources,'fetch_document',return_value=copy.deepcopy(DOCUMENT)):
            result=sources.verify_links(['https://alfaprom.org/catalog/'])
        self.assertFalse(result[0]['ok'])

    def test_gzip_and_deflate_are_read_with_decompressed_size_bound(self):
        import gzip,zlib
        from email.message import Message
        from urllib.parse import urlsplit
        class Response:
            status=200
            headers=Message()
            def __init__(self,data,encoding):self.data,self.encoding=data,encoding
            def read(self,limit):return self.data[:limit]
            def getheader(self,name,default=''):
                return {'Content-Type':'text/html','Content-Encoding':self.encoding}.get(name,default)
        class Connection:
            def __init__(self,*args):pass
            def request(self,*args,**kwargs):pass
            def getresponse(self):return response
            def close(self):pass
        for encoding,compress in [('gzip',gzip.compress),('deflate',zlib.compress)]:
            with self.subTest(encoding=encoding),tempfile.TemporaryDirectory() as cache:
                response=Response(compress(('<title>Technical Guide</title><p>'+QUOTE*5+'</p>').encode()),encoding)
                with patch.object(sources,'CACHE_ROOT',Path(cache)),patch.object(sources,'checked_url',return_value=(urlsplit(URL),'henkelman.com',['8.8.8.8'])),patch.object(sources,'PublicConnection',Connection):
                    self.assertIn(QUOTE,sources.fetch_document(URL)['text'])
        response=Response(gzip.compress(b'x'*10000001),'gzip')
        with tempfile.TemporaryDirectory() as cache,patch.object(sources,'CACHE_ROOT',Path(cache)),patch.object(sources,'checked_url',return_value=(urlsplit(URL),'henkelman.com',['8.8.8.8'])),patch.object(sources,'PublicConnection',Connection),self.assertRaisesRegex(ValueError,'размер'):
            sources.fetch_document(URL)

    def test_transient_network_failure_retries_once_without_fabricating_success(self):
        with patch.object(sources,'fetch_document',side_effect=[socket.timeout('fixture timeout'),copy.deepcopy(DOCUMENT)]) as fetch:
            result=sources.verify_links([URL])
        self.assertTrue(result[0]['ok']);self.assertEqual(fetch.call_count,2)

    def test_persistent_network_failure_is_unavailable_not_broken_url(self):
        with patch.object(sources,'fetch_document',side_effect=socket.timeout('fixture timeout')) as fetch:
            result=sources.verify_links([URL])
        self.assertFalse(result[0]['ok']);self.assertEqual(result[0]['kind'],'unavailable');self.assertEqual(fetch.call_count,2)


class ScopedContractsTests(unittest.TestCase):
    def run_result(self, operation, result):
        test = self

        class Process:
            pid, returncode = 999999, 0
            def __init__(self, command, **kwargs):
                test.assertIn('web_search="live"', command)
                test.assertIn('forced_login_method="chatgpt"', command)
                test.assertEqual(command[command.index('--model') + 1], 'gpt-6.1-sol')
                test.assertIn('model_reasoning_effort="high"', command)
                test.assertNotIn('OPENAI_API_KEY', kwargs['env'])
                self.path = Path(command[command.index('--output-last-message') + 1])
                self.schema = json.loads(Path(command[command.index('--output-schema') + 1]).read_text())
                test.assertFalse(self.schema['additionalProperties'])
            def communicate(self, instruction, timeout):
                self.path.write_text(json.dumps(result))
                return None, None

        with patch.object(helper, 'codex_binary', return_value='/mock/codex'), patch.object(helper.subprocess, 'Popen', Process), \
                patch.object(sources, 'fetch_document', return_value=copy.deepcopy(DOCUMENT)), \
                patch.dict(helper.os.environ, {'OPENAI_API_KEY': 'fixture-not-used'}):
            return helper.execute_task('Isolated contract fixture; no live model call.', 'scoped-test-job-180', operation)

    def test_patch_contract_does_not_return_full_article(self):
        schema = quality_schema.schema('patch')
        self.assertNotIn('html', schema['properties'])
        result = self.run_result('patch', {'version': 2, 'fingerprint': 'fixture', 'criteriaIds': [22],
            'replacements': [], 'seo': {'title': 'Title', 'description': 'Description', 'h1': 'H1'}, 'sources': [], 'notes': []})
        self.assertEqual(result['execution']['authMode'], 'chatgpt')

    def test_scoped_audit_independently_verifies_quoted_evidence(self):
        result = self.run_result('focused_audit', report())
        self.assertEqual(result['standard'], 2)
        self.assertTrue(result['facts'][0]['verification']['verified'])
        self.assertEqual(len(result['criteria']), 2)

    def test_schema_supports_one_criterion_without_forcing_23(self):
        schema = quality_schema.schema('focused_audit')
        self.assertEqual(schema['properties']['criteria']['minItems'], 1)
        self.assertEqual(schema['properties']['criteria']['maxItems'], 23)

    def test_wrong_contract_version_rejected(self):
        data = report()
        data['version'] = 1
        with self.assertRaises(ValueError):
            self.run_result('focused_audit', data)

    def test_unattached_images_cannot_be_claimed_as_reviewed(self):
        data = report()
        data['visuals'] = [{'assetId': 'a' * 32, 'status': 'pass', 'reason': 'Fabricated attachment assessment'}]
        with self.assertRaisesRegex(ValueError, 'вложенным'):
            self.run_result('focused_audit', data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
