#!/usr/bin/env python3
"""Small real containment probes: ONLY disposable GitHub-hosted Ubuntu CI.

Refuses operator Windows/WSL/Desktop. Does not install a VM, accept arbitrary
payloads, publish ports or connect to a private network. Never production.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.worker_agent.bounded import capture, ProcessBoundError
from services.worker_agent.policy import ProbePolicy, PolicyError, require_disposable_ci

POLICY = ProbePolicy()
CASES = ('baseline', 'filesystem', 'network', 'cpu', 'pids', 'tmpfs',
         'memory', 'timeout', 'output')


def docker(args, timeout=20, max_bytes=131072, check=True):
    result = capture(['docker', *args], timeout=timeout, max_bytes=max_bytes)
    if check and result.returncode:
        raise RuntimeError('DOCKER_OPERATION_FAILED:' + args[0])
    return result


def inspect(name):
    return json.loads(docker(['inspect', name]).output)[0]


def owned_remove(name, run_id):
    data = inspect(name)
    if data['Config'].get('Labels', {}).get('org.robocopa.isolation-run') != run_id:
        raise RuntimeError('CLEANUP_OWNERSHIP_MISMATCH')
    docker(['rm', '-f', name])
    exists = docker(['inspect', name], check=False)
    if exists.returncode == 0:
        raise RuntimeError('CLEANUP_NOT_CONFIRMED')


def main() -> int:
    # This guard runs before files are created or the Docker CLI is touched.
    require_disposable_ci(dict(os.environ), platform.system(), platform.release())
    endpoint = docker(['context', 'inspect', '--format', '{{.Endpoints.docker.Host}}']).output.decode().strip()
    if endpoint != 'unix:///var/run/docker.sock':
        raise PolicyError('LOCAL_DISPOSABLE_DAEMON_REQUIRED')
    details = docker(['info', '--format', '{{.OSType}}|{{.OperatingSystem}}|{{.CgroupVersion}}|{{.ServerVersion}}']).output.decode().strip().split('|')
    if len(details) != 4 or details[0] != 'linux' or 'desktop' in details[1].lower() or details[2] != '2':
        raise PolicyError('LINUX_CGROUP2_NON_DESKTOP_REQUIRED')
    run_id = uuid.uuid4().hex[:24]
    folder = ROOT / '.local' / 'security-i1'
    if (ROOT / '.local').is_symlink() or folder.is_symlink():
        raise PolicyError('SYMLINKED_OUTPUT')
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + run_id)
    output.mkdir()
    tag = 'robocopa-ifma/isolation-probe:' + run_id
    report = {'schema_version': 1, 'status': 'FAILED', 'environment': 'github-hosted-linux',
              'scope': 'bounded_synthetic_containment_not_production',
              'commit': os.getenv('GITHUB_SHA'), 'engine_version': details[3],
              'kernel': platform.release(), 'policy_sha256': POLICY.digest, 'cases': [],
              'host_vm_tested': False, 'student_submission_enabled': False}
    sentinel = Path('/tmp/rc-isolation-host-' + run_id)
    built = False
    try:
        sentinel.write_text('SYNTHETIC_HOST_ONLY', encoding='ascii')
        assert sentinel.is_file()
        docker(['build', '-t', tag, str(ROOT / 'spikes/isolamento/probes')], timeout=300,
               max_bytes=2*1024**2)
        built = True
        image = docker(['image', 'inspect', '--format', '{{.Id}}', tag]).output.decode().strip()
        report['image_id'] = image
        for case in CASES:
            name = 'rc-isolation-' + uuid.uuid4().hex[:24]
            row = {'case': case, 'status': 'FAILED'}
            report['cases'].append(row)
            created = False
            try:
                args = POLICY.create_args(name, image, case, run_id)
                # Only the path of our own synthetic host fixture, never its contents or secrets.
                index = args.index(image)
                args[index:index] = ['--env', 'ROBOCOPA_HOST_CANARY_PATH=' + str(sentinel)]
                docker(args); created = True
                row['configuration_checks'] = POLICY.verify(inspect(name), image, run_id)
                if case in ('timeout', 'output'):
                    expected = 'TIMEOUT' if case == 'timeout' else 'OUTPUT_LIMIT'
                    try:
                        docker(['start', '-a', name], timeout=1.5 if case=='timeout' else 10,
                               max_bytes=8192, check=False)
                    except ProcessBoundError as exc:
                        if exc.reason != expected:
                            raise
                        row['observed_limit'] = exc.reason
                        row['captured_bytes_at_most'] = len(exc.output)
                    else:
                        raise RuntimeError('EXPECTED_EXTERNAL_LIMIT_NOT_OBSERVED')
                else:
                    result = docker(['start', '-a', name], timeout=15, max_bytes=8192, check=False)
                    final = inspect(name)
                    if case == 'memory':
                        row['oom_killed'] = final['State']['OOMKilled'] is True
                        row['exit_code'] = final['State']['ExitCode']
                        if not row['oom_killed'] or row['exit_code'] != 137:
                            raise RuntimeError('MEMORY_OOM_NOT_OBSERVED')
                    else:
                        if result.returncode or final['State']['ExitCode'] != 0:
                            raise RuntimeError('PROBE_FAILED:' + case)
                        payload = json.loads(result.output)
                        if payload.get('case') != case or not payload.get('checks') or not all(payload['checks'].values()):
                            raise RuntimeError('PROBE_CHECKS_FAILED:' + case)
                        row['observations'] = payload
                row['status'] = 'PASS'
            except Exception as exc:
                row['failure_type'] = type(exc).__name__
                row['status'] = 'FAILED'
                raise
            finally:
                try:
                    if created:
                        owned_remove(name, run_id)
                    row['cleanup_verified'] = True
                except Exception:
                    row['status'] = 'FAILED'
                    row['cleanup_verified'] = False
                    raise
            print('PASS bounded probe:', case, flush=True)
        leftovers = docker(['ps', '-aq', '--filter', 'label=org.robocopa.isolation-run=' + run_id]).output.strip()
        if leftovers:
            raise RuntimeError('ORPHANED_TEST_CONTAINERS')
        report['cleanup_verified'] = True
        report['status'] = 'PASS'
    finally:
        sentinel.unlink(missing_ok=True)
        try:
            if built:
                docker(['image', 'rm', tag], timeout=30)
            report['image_cleanup_verified'] = True
        except Exception:
            report['status'] = 'FAILED'
            report['image_cleanup_verified'] = False
            raise
        finally:
            (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            print(report['status'] + ': ' + str(output.relative_to(ROOT)), flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, ProcessBoundError) as error:
        # Deliberately excludes stdout, argument lists, fixture paths and environment.
        print('BLOCKED/FAILED: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
