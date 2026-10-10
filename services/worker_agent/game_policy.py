"""CI I2 policy: fixed trusted bots, a protocol gateway, and a separate judge.

This is not a production policy and does not authorize student submissions.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import re
from .policy import PolicyError

LABEL = 'org.robocopa.i2-run'
ROLE_COMMANDS = {'judge': ['Judge', 'server'], 'gateway': ['ProtocolGate'],
                 'walls': ['Probe', 'idle'], 'spin': ['Probe', 'idle']}
ROLE_ENV = {'judge': {'ADMIN_SECRET', 'BACKEND_SECRET'},
            'gateway': {'BIND_A', 'BIND_B', 'FRONT_A', 'FRONT_B', 'BACKEND_SECRET', 'BACKEND_URL'},
            'walls': {'BOT_NAME', 'BOT_SECRET', 'BOT_SERVER_URL'},
            'spin': {'BOT_NAME', 'BOT_SECRET', 'BOT_SERVER_URL'}}


def network_args(name: str, run_id: str) -> list[str]:
    if not re.fullmatch(r'rc-i2-[0-9a-f]{24}-(?:a|b|back)', name) or run_id not in name:
        raise PolicyError('NETWORK_NAME')
    return ['network', 'create', '--driver', 'bridge', '--internal', '--label', LABEL+'='+run_id,
            '--opt', 'com.docker.network.bridge.gateway_mode_ipv4=isolated', name]


def verify_network(info: dict, run_id: str) -> dict[str, bool]:
    checks = {'owned': info.get('Labels', {}).get(LABEL) == run_id,
              'bridge': info.get('Driver') == 'bridge',
              'internal': info.get('Internal') is True,
              'isolated_gateway': info.get('Options', {}).get('com.docker.network.bridge.gateway_mode_ipv4') == 'isolated',
              'ipv6_off': info.get('EnableIPv6') is False}
    if not all(checks.values()): raise PolicyError('NETWORK_POLICY_MISMATCH')
    return checks


def addresses(info: dict) -> tuple[str, str]:
    configs = info.get('IPAM', {}).get('Config', [])
    if len(configs) != 1: raise PolicyError('IPAM_CONFIG')
    network = ipaddress.ip_network(configs[0]['Subnet'])
    if network.version != 4 or not network.is_private or network.num_addresses < 8:
        raise PolicyError('IPAM_SCOPE')
    return str(network.network_address+2), str(network.network_address+3)


@dataclass(frozen=True)
class GamePolicy:
    role: str

    def __post_init__(self):
        if self.role not in ROLE_COMMANDS: raise PolicyError('ROLE')

    @property
    def memory(self): return (1024 if self.role == 'judge' else 512) * 1024**2
    @property
    def tmpfs(self): return (128 if self.role == 'judge' else 32) * 1024**2
    @property
    def digest(self):
        return hashlib.sha256(json.dumps({'version':'i2/1','role':self.role,'memory':self.memory,
            'cpus':1,'pids':96,'tmpfs':self.tmpfs,'network':'per-bot-isolated-gateway'},sort_keys=True).encode()).hexdigest()

    def create_args(self, name: str, image: str, run_id: str, network: str, ip: str) -> list[str]:
        if not re.fullmatch(r'rc-i2-[0-9a-f]{24}-(?:judge|gateway|walls|spin)', name) or not name.endswith(self.role) or run_id not in name:
            raise PolicyError('NAME')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', image): raise PolicyError('IMAGE_NOT_CONTENT_ID')
        if not re.fullmatch(r'[0-9a-f]{24}', run_id): raise PolicyError('RUN')
        if not re.fullmatch(r'rc-i2-[0-9a-f]{24}-(?:a|b|back)', network) or run_id not in network:
            raise PolicyError('NETWORK')
        if ipaddress.ip_address(ip).version != 4 or not ipaddress.ip_address(ip).is_private: raise PolicyError('ADDRESS')
        args=['create','--name',name,'--label',LABEL+'='+run_id,'--label','org.robocopa.i2-role='+self.role,
              '--network',network,'--ip',ip,'--read-only','--user','10001:10001','--cap-drop','ALL',
              '--security-opt','no-new-privileges','--memory',str(self.memory),'--memory-swap',str(self.memory),
              '--cpus','1','--pids-limit','96','--cgroupns','private','--init','--log-driver','none',
              '--dns','127.0.0.1','--sysctl','net.ipv4.ip_forward=0',
              '--sysctl','net.ipv6.conf.all.disable_ipv6=1',
              '--tmpfs',f'/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs},mode=1777']
        for key in sorted(ROLE_ENV[self.role]): args += ['--env',key]
        return args+[image,*ROLE_COMMANDS[self.role]]

    def verify(self, info: dict, image: str, run_id: str, networks: set[str]) -> dict[str,bool]:
        h=info.get('HostConfig', {});c=info.get('Config', {});sec=h.get('SecurityOpt') or []
        env={x.split('=',1)[0] for x in c.get('Env',[])}
        forbidden={'GITHUB_TOKEN','POSTGRES_PASSWORD','AWS_SECRET_ACCESS_KEY'}
        if self.role != 'judge':forbidden.add('ADMIN_SECRET')
        if self.role in ('walls','spin'):forbidden |= {'BACKEND_SECRET','FRONT_A','FRONT_B'}
        tmp=h.get('Tmpfs') or {};flags=tmp.get('/tmp','').split(',')
        checks={
            'owned': c.get('Labels',{}).get(LABEL)==run_id,
            'role': c.get('Labels',{}).get('org.robocopa.i2-role')==self.role,
            'image': info.get('Image')==image,
            'fixed_command': c.get('Cmd')==ROLE_COMMANDS[self.role],
            'network_membership': set(info.get('NetworkSettings',{}).get('Networks',{}))==networks,
            'non_root':c.get('User')=='10001:10001',
            'read_only':h.get('ReadonlyRootfs') is True,
            'unprivileged':h.get('Privileged') is False,
            'no_mounts':not h.get('Binds') and not h.get('Mounts') and all(m.get('Type')=='tmpfs' and m.get('Destination')=='/tmp' for m in info.get('Mounts',[])),
            'no_ports':not h.get('PortBindings') and not h.get('PublishAllPorts'),
            'no_devices':not h.get('Devices') and not h.get('DeviceRequests'),
            'caps_none':'ALL' in (h.get('CapDrop') or []) and not h.get('CapAdd'),
            'nnp':'no-new-privileges' in sec,
            'seccomp_enabled':not any('unconfined' in s for s in sec),
            'namespaces':h.get('PidMode')!='host' and h.get('IpcMode')!='host' and h.get('UsernsMode')!='host' and h.get('CgroupnsMode')=='private',
            'ram':h.get('Memory')==self.memory,
            'swap':h.get('MemorySwap')==self.memory,
            'cpu':h.get('NanoCpus')==1000000000,
            'pids':h.get('PidsLimit')==96,
            'tmpfs':set(tmp)=={'/tmp'} and all(v in flags for v in ('noexec','nosuid','nodev',f'size={self.tmpfs}')),
            'init':h.get('Init') is True,
            'logging':h.get('LogConfig',{}).get('Type')=='none',
            'no_ip_forward':h.get('Sysctls',{}).get('net.ipv4.ip_forward')=='0',
            'ipv6_disabled':h.get('Sysctls',{}).get('net.ipv6.conf.all.disable_ipv6')=='1',
            'no_upstream_dns':h.get('Dns')==['127.0.0.1'],
            'role_credentials':not env.intersection(forbidden) and ROLE_ENV[self.role].issubset(env),
        }
        if not all(checks.values()):raise PolicyError('GAME_POLICY_MISMATCH:'+','.join(k for k,v in checks.items() if not v))
        return checks
