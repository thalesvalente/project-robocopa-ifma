"""I2 private bridge + per-container netns ACLs, only in disposable CI.

The trusted supervisor has host privileges, but rules are applied strictly to
verified child namespaces. Never invoked from a public endpoint or student code.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from ipaddress import IPv4Address
import re
from .policy import ProbePolicy, PolicyError

GAME_PORT=7654
ENGINE_PORT=7655
LABEL='org.robocopa.isolation-run'

@dataclass(frozen=True)
class ArenaPolicy:
    role: str

    def limits(self) -> ProbePolicy:
        if self.role not in ('referee','walls','spin'):
            raise PolicyError('ROLE_INVALID')
        return ProbePolicy(memory_bytes=(1024 if self.role=='referee' else 512)*1024**2,
             nano_cpus=1_000_000_000,pids=128,tmpfs_bytes=128*1024**2)

    def create_args(self,name,image,run_id,network):
        if not re.fullmatch(r'rc-arena-net-[0-9a-f]{24}', network):
            raise PolicyError('NETWORK_INVALID')
        args=self.limits().create_args(name,image,'baseline',run_id)[:-1]
        args[args.index('--network')+1]=network
        args[-1:-1]=['--label','org.robocopa.arena-role='+self.role]
        return args

    def verify(self, info, image, run_id, network):
        if info.get('HostConfig',{}).get('NetworkMode')!=network:
            raise PolicyError('NETWORK_MISMATCH')
        cfg=info.get('Config',{}); host=info.get('HostConfig',{})
        if cfg.get('Labels',{}).get('org.robocopa.arena-role')!=self.role:
            raise PolicyError('ROLE_MISMATCH')
        if host.get('PidMode','') not in ('','private') or host.get('IpcMode','') not in ('','private'):
            raise PolicyError('SHARED_NAMESPACES_DENIED')
        if any('SECRET' in v.partition('=')[0].upper() or 'TOKEN' in v.partition('=')[0].upper()
               for v in cfg.get('Env',[])):
            raise PolicyError('SECRET_IN_CONTAINER_METADATA')
        copy=deepcopy(info);copy['HostConfig']['NetworkMode']='none'
        result=self.limits().verify(copy,image,run_id)
        result.pop('network_none')
        result.update(private_bridge=True,role=True,separate_pid_ipc=True,no_metadata_secrets=True)
        return result

def ipv4(value):
    address=IPv4Address(value)
    if address.is_loopback or address.is_multicast or address.is_unspecified:
        raise PolicyError('UNSAFE_NETWORK_ADDRESS')
    return str(address)

def firewall(role: str, referee_ip: str, bot_ips: list[str], *, ipv6=False) -> str:
    """Only numeric validated addresses enter the restore file. No host rules."""
    if role not in ('referee','walls','spin') or len(bot_ips)!=2:
        raise PolicyError('ROLE_OR_PEERS_INVALID')
    ref=ipv4(referee_ip); peers=[ipv4(p) for p in bot_ips]
    if len(set([ref,*peers]))!=3:
        raise PolicyError('DUPLICATE_ADDRESS')
    rows=['*filter',':INPUT DROP [0:0]',':FORWARD DROP [0:0]',':OUTPUT DROP [0:0]']
    if not ipv6:
        rows += ['-A INPUT -i lo -s 127.0.0.1/32 -j ACCEPT','-A OUTPUT -o lo -d 127.0.0.1/32 -j ACCEPT',
                 '-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT',
                 '-A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT']
        if role=='referee':
            rows += [f'-A INPUT -s {p}/32 -p tcp --dport {GAME_PORT} -j ACCEPT' for p in peers]
        else:
            rows += [f'-A OUTPUT -d {ref}/32 -p tcp --dport {GAME_PORT} -j ACCEPT']
        rows += ['-A OUTPUT -j REJECT --reject-with icmp-port-unreachable']
    else:
        rows += ['-A OUTPUT -j REJECT --reject-with icmp6-port-unreachable']
    rows += ['COMMIT','']
    return '\n'.join(rows)

def verify_namespace_target(info,run_id,net_inode,host_inode):
    pid=info.get('State',{}).get('Pid')
    if (info.get('Config',{}).get('Labels',{}).get(LABEL)!=run_id
        or info.get('State',{}).get('Running') is not True or type(pid) is not int or pid<=1
        or not re.fullmatch(r'net:\[\d+\]',net_inode) or net_inode==host_inode):
        raise PolicyError('NAMESPACE_TARGET_DENIED')
    return pid
