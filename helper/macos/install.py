#!/usr/bin/env python3
"""Install this project's URL handler in the current user's Applications folder."""
from pathlib import Path
import plistlib
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
source = Path('/private/tmp/alfaprom-macos-build/ALFAPROM Helper.app')
destination = Path.home() / 'Applications/ALFAPROM Helper.app'
if not source.is_dir():
    raise SystemExit('Сначала выполните python3 helper/macos/build.py')
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(source)], check=True)
if destination.is_symlink():
    raise SystemExit('Папка назначения является ссылкой; установка отменена.')
if destination.exists():
    info = plistlib.loads((destination / 'Contents/Info.plist').read_bytes())
    if info.get('CFBundleIdentifier') != 'org.alfaprom.seo-helper':
        raise SystemExit('В папке назначения другое приложение; установка отменена.')
    shutil.rmtree(destination)
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(source, destination)
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(destination)], check=True)
register = '/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister'
subprocess.run([register, '-f', str(destination)], check=True)
print(f'Установлено: {destination}')
print('Ссылка запуска: alfaprom-seo://start')
