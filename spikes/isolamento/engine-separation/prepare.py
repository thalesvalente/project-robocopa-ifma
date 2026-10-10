"""Extract dependencies from already hash-verified official release assets."""
from pathlib import Path
import sys, zipfile, shutil, hashlib, json

root = Path(sys.argv[1])
with zipfile.ZipFile(root / 'runner.jar') as jar:
    entries = [n for n in jar.namelist() if n == 'robocode-tankroyale-server.jar']
    if len(entries) != 1: raise ValueError('PINNED_NESTED_SERVER_MISSING')
    server = jar.read(entries[0])
(root / 'server.jar').write_bytes(server)
api = list((root / 'samples').rglob('robocode-tankroyale-bot-api-1.4.0.jar'))
if len(api) != 1: raise ValueError('PINNED_SAMPLE_API_MISSING')
shutil.copyfile(api[0], root / 'api.jar')
bots = root / (root / 'bots-root.txt').read_text().strip()
for name in ('Walls', 'SpinBot'):
    dest = root / 'bots' / name
    dest.mkdir(parents=True)
    for extension in ('java', 'json'):
        shutil.copyfile(bots / name / f'{name}.{extension}', dest / f'{name}.{extension}')
print('Verified parent assets; nested components:',json.dumps({n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('server.jar','api.jar')}))
