"""Small CI-only containment policy. NOT the production or game-network policy."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ProbePolicy:
    memory_bytes: int = 64 * 1024**2
    nano_cpus: int = 500_000_000
    pids: int = 16
    tmpfs_bytes: int = 4 * 1024**2
    uid: str = '10001:10001'

    @property
    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()

    def create_args(self, name: str, image: str, case: str, run_id: str) -> list[str]:
        if not re.fullmatch(r'rc-isolation-[0-9a-f]{24}', name):
            raise PolicyError('NAME_INVALID')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
            raise PolicyError('IMAGE_MUST_BE_CONTENT_ID')
        if not re.fullmatch(r'[0-9a-f]{24}', run_id):
            raise PolicyError('RUN_INVALID')
        if case not in {'baseline', 'filesystem', 'network', 'cpu', 'pids',
                        'memory', 'tmpfs', 'timeout', 'output'}:
            raise PolicyError('CASE_INVALID')
        return ['create', '--name', name, '--label', 'org.robocopa.isolation-run=' + run_id,
                '--network', 'none', '--read-only', '--user', self.uid,
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--memory', str(self.memory_bytes), '--memory-swap', str(self.memory_bytes),
                '--cpus', str(self.nano_cpus / 1e9), '--pids-limit', str(self.pids),
                '--cgroupns', 'private', '--init', '--log-driver', 'none',
                '--tmpfs', f'/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs_bytes},mode=1777',
                image, case]

    def verify(self, info: dict, expected_image: str, run_id: str) -> dict[str, bool]:
        host, cfg = info.get('HostConfig', {}), info.get('Config', {})
        security = host.get('SecurityOpt') or []
        tmpfs = host.get('Tmpfs') or {}
        checks = {
            'ownership': cfg.get('Labels', {}).get('org.robocopa.isolation-run') == run_id,
            'image_content_id': info.get('Image') == expected_image,
            'network_none': host.get('NetworkMode') == 'none',
            'read_only': host.get('ReadonlyRootfs') is True,
            'not_privileged': host.get('Privileged') is False,
            'non_root': cfg.get('User') == self.uid,
            'no_host_mounts': not host.get('Binds') and not host.get('Mounts')
                              and all(m.get('Type') == 'tmpfs' and m.get('Destination') == '/tmp'
                                      for m in (info.get('Mounts') or [])),
            'no_ports': not host.get('PortBindings') and not host.get('PublishAllPorts'),
            'no_devices': not host.get('Devices') and not host.get('DeviceRequests'),
            'capabilities': 'ALL' in (host.get('CapDrop') or []) and not host.get('CapAdd'),
            'no_new_privileges': 'no-new-privileges' in security,
            'seccomp_not_disabled': not any('unconfined' in x for x in security),
            'no_host_namespaces': host.get('PidMode', '') != 'host'
                                  and host.get('IpcMode', '') != 'host'
                                  and host.get('CgroupnsMode') == 'private'
                                  and host.get('UsernsMode', '') != 'host',
            'memory': host.get('Memory') == self.memory_bytes,
            'swap_disabled': host.get('MemorySwap') == self.memory_bytes,
            'cpu': host.get('NanoCpus') == self.nano_cpus,
            'pids': host.get('PidsLimit') == self.pids,
            'init': host.get('Init') is True,
            'no_persistent_logs': host.get('LogConfig', {}).get('Type') == 'none',
            'tmpfs_bounded': set(tmpfs) == {'/tmp'} and all(
                x in tmpfs.get('/tmp', '').split(',') for x in
                ('noexec', 'nosuid', 'nodev', f'size={self.tmpfs_bytes}')),
        }
        if not all(checks.values()):
            raise PolicyError('POLICY_MISMATCH:' + ','.join(k for k,v in checks.items() if not v))
        return checks


def require_disposable_ci(env: dict, system: str, release: str) -> None:
    """Accidental-use guard, NOT cryptographic attestation of the caller."""
    valid = (system == 'Linux' and 'microsoft' not in release.lower()
             and env.get('GITHUB_ACTIONS') == 'true'
             and env.get('RUNNER_ENVIRONMENT') == 'github-hosted'
             and env.get('GITHUB_REPOSITORY') == 'thalesvalente/project-robocopa-ifma'
             and not env.get('DOCKER_HOST') and not env.get('DOCKER_CONTEXT'))
    if not valid:
        raise PolicyError('DISPOSABLE_GITHUB_CI_REQUIRED_NOT_OPERATOR_HOST')
