"""Download only pinned upstream assets during IMAGE BUILD, never at runtime."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import urllib.request
import zipfile


def verified(data: bytes, expected: dict) -> bytes:
    if len(data) != expected['size'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
        raise ValueError('Upstream asset checksum/size mismatch; execution refused')
    return data


def extract_checked(archive: Path, root: Path) -> None:
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if sum(m.file_size for m in members) > 40 * 1024**2:
            raise ValueError('Archive too large')
        for item in members:
            path = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (path.is_absolute() or '..' in path.parts or '\\' in item.filename
                    or ':' in item.filename or stat.S_ISLNK(mode)):
                raise ValueError('Unsafe ZIP member')
        for item in members:
            destination = root.joinpath(*PurePosixPath(item.filename).parts)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with source.open(item) as src, destination.open('xb') as dest:
                    shutil.copyfileobj(src, dest)
                destination.chmod(0o755 if destination.suffix == '.sh' else 0o644)


def main() -> None:
    base = Path(__file__).resolve().parent
    lock = json.loads((base / 'upstream.lock.json').read_text())
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for filename, asset in lock['artifacts'].items():
        req = urllib.request.Request(asset['url'], headers={'User-Agent': 'RoboCopa-IFMA-spike/1'})
        with urllib.request.urlopen(req, timeout=90) as response:
            data = response.read(asset['size'] + 1)
        (out / filename).write_bytes(verified(data, asset))
    staging = out / 'samples'
    extract_checked(out / 'samples.zip', staging)
    walls = list(staging.rglob('Walls/Walls.json'))
    if len(walls) != 1:
        raise ValueError('Unexpected sample archive layout')
    bots = walls[0].parent.parent
    for name in lock['bots']:
        config = json.loads((bots / name / (name + '.json')).read_text())
        if config.get('name') != name:
            raise ValueError('Unexpected official bot identity')
    (out / 'bots-root.txt').write_text(str(bots.relative_to(out)), encoding='utf-8')
    shutil.copyfile(base / 'upstream.lock.json', out / 'upstream.lock.json')
    print('PASS: pinned runner and official samples verified; no mutable latest download')


if __name__ == '__main__':
    main()
