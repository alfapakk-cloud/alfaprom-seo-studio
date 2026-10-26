#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build isolated browser regression page; serve repository on loopback port 8765."""
from pathlib import Path
root = Path(__file__).resolve().parents[2]
source = (root / 'index.html').read_text(encoding='utf-8')
source = source.replace("const KEY='alfaprom_seo_studio_mvp_v01'", "const KEY='alfaprom_regression_test_v17'")
tests = (root / 'docs/tests/quality-engine.browser.js').read_text(encoding='utf-8')
generation = (root / 'docs/tests/generation.browser.js').read_text(encoding='utf-8')
ui = (root / 'docs/tests/ui.browser.js').read_text(encoding='utf-8')
update = (root / 'docs/tests/generation161.browser.js').read_text(encoding='utf-8')
formats = (root / 'docs/tests/formats17.browser.js').read_text(encoding='utf-8')
marker = ' const failed=tests.filter(t=>!t.ok);'
assert tests.count(marker) == 1
tests = tests.replace(marker, generation + '\n' + ui + '\n' + update + '\n' + formats + '\n' + marker).replace('</script', '<\\/script')
head, tail = source.rsplit('</body>', 1)
(root / '.quality-tests.html').write_text(head + '<script>' + tests + '</script></body>' + tail, encoding='utf-8')
print('Open http://127.0.0.1:8765/.quality-tests.html after starting python3 -m http.server 8765')

