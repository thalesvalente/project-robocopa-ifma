#!/usr/bin/env python3
"""Record real bootstrap evidence; never mark local deployment or human gates complete."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
from bootstrap_speckit import REQUIRED, load_lock
from verify_planning import validate

root = Path(__file__).resolve().parents[1]
lock = load_lock(root)
run_url = os.environ.get('RUN_URL', '')
if not run_url.startswith('https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/'):
    raise SystemExit('FAIL: registro automático exige URL do run autorizado.')
for path in REQUIRED:
    if not (root / path).is_file():
        raise SystemExit(f'FAIL: falta {path}; instalação não confirmada.')
files = {}
for directory in ('.specify', '.agents'):
    for path in sorted((root / directory).rglob('*')):
        if path.is_file():
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
record = {
    'scope': 'Bootstrap real em runner GitHub-hosted; não é a máquina do responsável.',
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'run_url': run_url,
    'input_commit': os.environ.get('GITHUB_SHA'),
    'platform': platform.system(),
    'python': platform.python_version(),
    'upstream_commit': lock['commit'],
    'required_files_checked': [str(p) for p in REQUIRED],
    'constitution_preservation_check': 'sha256sum -c executado pelo workflow antes deste registro',
    'file_count': len(files),
    'sha256': files,
    'native_mcp_connected': False,
    'product_tests_executed': False,
    'host_deployed': False,
}
p = root / 'docs/qualidade/evidencias/SPECKIT-CI.json'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
lock['native_cli_initialized'] = True
lock['validated_environment'] = 'GitHub-hosted runner; não é a máquina do responsável'
lock['evidence'] = p.relative_to(root).as_posix()
lock['notes'] = 'CLI inicializada e arquivos presentes no ambiente de CI. MCP nesta conversa e instalação local continuam não estabelecidos.'
(root / 'tools/speckit.lock.json').write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
backlog_path = root / 'docs/planejamento/backlog.json'
backlog = json.loads(backlog_path.read_text(encoding='utf-8'))
validate(backlog)
completed = {
    'S00-T01': 'Base publicada na branch de trabalho; checkout e validação do commit de entrada executados.',
    'S00-T02': 'CLI oficial fixada executada; templates/comandos conferidos e constituição preservada. Ambiente: GitHub-hosted, não host do MVP.',
    'S00-T03': 'Minuta de constituição e processo versionada; ratificação humana continua em S00-T06.',
    'S00-T04': 'Backlog 10/60, modelos e visões publicados e verificados; acompanhamento adicional por issues não altera os contratos.',
}
for task in backlog['sprints'][0]['tasks']:
    if task['id'] in completed:
        task['status'] = 'CONCLUIDA'
        task['evidence'] = [completed[task['id']], run_url, 'docs/qualidade/evidencias/SPECKIT-CI.json']
validate(backlog)
backlog_path.write_text(json.dumps(backlog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tasks_path = root / 'specs/000-governanca/tasks.md'
text = tasks_path.read_text(encoding='utf-8')
for tid in ('T002', 'T003', 'T004', 'T005'):
    text = text.replace(f'- [ ] {tid}', f'- [x] {tid}')
text += '\nEvidência de T002–T005: ' + run_url + '. Conferir conclusão do run e commit gerado; não é homologação do MVP.\n'
tasks_path.write_text(text, encoding='utf-8')
print(f'PASS: {len(files)} arquivos registrados com SHA-256; gates locais/humanos preservados.')
