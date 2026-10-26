#!/usr/bin/env python3
"""Build a local macOS launcher without installing or changing sign-in settings."""
from pathlib import Path
import plistlib
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
APP = Path('/private/tmp/alfaprom-macos-build/ALFAPROM Helper.app')
contents = APP / 'Contents'
macos = contents / 'MacOS'
resources = contents / 'Resources'
macos.mkdir(parents=True, exist_ok=True)
(resources / 'helper').mkdir(parents=True, exist_ok=True)
for name in ['alfaprom_helper.py', 'panel.html', 'media.py']:
    shutil.copy2(ROOT / 'helper' / name, resources / 'helper' / name)
shutil.copytree(ROOT / 'helper/lib', resources / 'helper/lib', dirs_exist_ok=True)
for library in (resources / 'helper/lib').glob('*.dylib'):
    subprocess.run(['codesign', '--force', '--sign', '-', '--timestamp=none', str(library)], check=True)
shutil.copy2(ROOT / 'generation.js', resources / 'helper' / 'generation.js')
# UI updates use the existing protocol-8 backend and do not change sign-in settings.
(resources / 'helper' / 'studio.html').write_text((ROOT / 'index.html').read_text(encoding='utf-8').replace('generation.js?v=1.6.0', 'generation.js'), encoding='utf-8')
info = {
    'CFBundleIdentifier': 'org.alfaprom.seo-helper',
    'CFBundleName': 'ALFAPROM Helper',
    'CFBundleDisplayName': 'Помощник АЛЬФАПРОМ',
    'CFBundleExecutable': 'ALFAPROMHelper',
    'CFBundlePackageType': 'APPL',
    'CFBundleShortVersionString': '1.6.0',
    'CFBundleVersion': '9',
    'LSMinimumSystemVersion': '12.0',
    'LSUIElement': True,
    'CFBundleURLTypes': [{'CFBundleURLName': 'org.alfaprom.seo-helper.start', 'CFBundleTypeRole': 'Viewer', 'CFBundleURLSchemes': ['alfaprom-seo']}],
    'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True},
}
(contents / 'Info.plist').write_bytes(plistlib.dumps(info))
cache = '/private/tmp/alfaprom-swift-module-cache'
subprocess.run(['swiftc', '-module-cache-path', cache, '-target', 'arm64-apple-macos12.0',
                str(ROOT / 'helper/macos/HelperURL.swift'), str(ROOT / 'helper/macos/Launcher.swift'),
                '-o', str(macos / 'ALFAPROMHelper')], check=True)
for attr in ['com.apple.FinderInfo', 'com.apple.ResourceFork']:
    subprocess.run(['/usr/bin/xattr', '-dr', attr, str(APP)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['codesign', '--force', '--sign', '-', '--timestamp=none', str(APP)], check=True)
with zipfile.ZipFile(ROOT / 'alfaprom-mac-helper.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in APP.rglob('*'):
        archive.write(path, str(Path(APP.name) / path.relative_to(APP)))
print(APP)

