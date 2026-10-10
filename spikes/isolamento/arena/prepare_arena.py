"""Image-build only: derive roles from upstream assets pinned in the existing lock."""
from pathlib import Path
import hashlib,json,zipfile,shutil

root=Path('/dist')
with zipfile.ZipFile(root/'runner.jar') as jar:
    payload=jar.read('robocode-tankroyale-server.jar')
(root/'referee').mkdir();(root/'referee/server.jar').write_bytes(payload)
bots=root/(root/'bots-root.txt').read_text().strip()
for name in ('Walls','SpinBot'):
    dest=root/'bots'/name;dest.mkdir(parents=True)
    for suffix in ('.java','.json'):
        shutil.copyfile(bots/name/(name+suffix),dest/(name+suffix))
    shutil.copytree(bots/'lib',dest/'lib')
(root/'build-manifest.json').write_text(json.dumps({
    'engine_version':'1.4.0','server_jar_sha256':hashlib.sha256(payload).hexdigest(),
    'derived_from_runner_sha256':hashlib.sha256((root/'runner.jar').read_bytes()).hexdigest(),
    'source':'pinned_official_runner_embedded_server'},indent=2))
