"""Exercise the actual cleanup shell with a FAKE Docker function.

This checks error handling, not real Docker cleanup (covered by the PG CI job).
No daemon, containers, network or privileged operations are used by these tests.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT/'.github/workflows/i3-postgres.yml'


def cleanup_script():
    text = WORKFLOW.read_text()
    section = text.split('      - name: Limpeza apenas dos recursos desta execucao, comprovada\n',1)[1]
    body = section.split('        run: |\n',1)[1].split('      - uses:',1)[0]
    lines = body.splitlines()
    if any(line and not line.startswith('          ') for line in lines):
        raise AssertionError('UNEXPECTED_CLEANUP_INDENT')
    return '\n'.join(line[10:] if line else '' for line in lines)+'\n'


@unittest.skipUnless(shutil.which('bash'), 'Bash required for workflow error-handling fixture')
class PostgresCleanupTests(unittest.TestCase):
    def invoke(self, fail):
        prefix = r'''
docker() {
  case "$*" in
    *label=org.robocopa.i3pg.run*)
      if [ "$FAIL_QUERY" = containers ] && [ "$1" = ps ]; then return 47; fi
      if [ "$FAIL_QUERY" = volumes ] && [ "$1" = volume ]; then return 48; fi
      ;;
  esac
  return 0
}
python3() { printf 'VERIFIED' > "$MARKER"; }
'''
        with tempfile.TemporaryDirectory(prefix='pg-cleanup-fixture-') as tmp:
            marker = Path(tmp)/'marker'
            env = dict(os.environ,FAIL_QUERY=fail,MARKER=str(marker),
                RC_PG_CONTAINER='robocopa-i3pg-1-1',RC_PG_VOLUME='robocopa-i3pg-data-1-1',GITHUB_RUN_ID='1')
            run = subprocess.run(['bash','--noprofile','--norc'],input=prefix+cleanup_script(),
                text=True,capture_output=True,timeout=5,env=env,cwd=tmp)
            return run.returncode,marker.exists()

    def test_confirmed_absence_can_be_recorded(self):
        self.assertEqual(self.invoke('none'),(0,True))

    def test_container_query_failure_is_not_absence(self):
        self.assertEqual(self.invoke('containers'),(47,False))

    def test_volume_query_failure_is_not_absence(self):
        self.assertEqual(self.invoke('volumes'),(48,False))
