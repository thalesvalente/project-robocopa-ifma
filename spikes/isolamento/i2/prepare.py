"""Fetch exactly two release assets, verify before extracting in build-only stage."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request

sys.path.insert(0, '/build')
from reference_prepare import extract_checked


def load_verified(url: str, expected_sha: str, expected_size: int) -> bytes:
    if not url.startswith('https://github.com/robocode-dev/tank-royale/releases/download/v1.4.0/'):
        raise ValueError('unexpected upstream download origin')
    request = urllib.request.Request(url, headers={'User-Agent': 'RoboCopa-I2/1'})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read(expected_size + 1)
    if len(data) != expected_size or hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError('upstream checksum mismatch')
    return data


def main() -> None:
    root = Path('/dist')
    root.mkdir(exist_ok=True, parents=True)
    lock = json.loads(Path('/build/upstream.lock.json').read_text())
    for key, filename in [('server', 'server.jar'), ('bot_archive', 'bots.zip')]:
        item = lock[key]
        (root / filename).write_bytes(load_verified(item['url'], item['sha256'], item['size']))
    extract_checked(root / 'bots.zip', root / 'stage')
    dirs = list((root / 'stage').rglob('Walls/Walls.json'))
    if len(dirs) != 1:
        raise ValueError('unexpected sample archive layout')
    bots = dirs[0].parent.parent
    lib = bots / 'lib'
    if not lib.is_dir() or not list(lib.glob('*.jar')):
        raise ValueError('missing sample bot api libraries')
    out = root / 'bots'
    out.mkdir()
    shutil.copytree(lib, out / 'lib')
    for folder, identity in lock['bots'].items():
        path = bots / folder
        config = json.loads((path / (folder + '.json')).read_text())
        if config.get('name') != identity or config.get('version') != '1.0':
            raise ValueError('unexpected bot identity')
        shutil.copytree(path, out / folder)
    (root / 'bots.zip').unlink()
    shutil.rmtree(root / 'stage')
    print('PASS I2 upstream version/sha256/size and bot identities')


if __name__ == '__main__':
    main()
