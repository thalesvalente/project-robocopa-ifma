"""Fixed synthetic probes with small absolute budgets; never user programs.

Run only through the disposable GitHub CI harness. No kernel exploits, scanning,
personal files or external service traffic. network=none is verified first.
"""
from __future__ import annotations
import errno
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


def baseline() -> dict:
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines())
    cg = Path('/sys/fs/cgroup')
    values = {name: (cg / name).read_text().strip() for name in
              ('memory.max', 'memory.swap.max', 'pids.max', 'cpu.max')}
    checks = {
        'uid': os.getuid() == 10001,
        'no_capabilities': int(status['CapEff'].strip(), 16) == 0,
        'no_new_privileges': status['NoNewPrivs'].strip() == '1',
        'seccomp_filter_active': status['Seccomp'].strip() == '2',
        'memory_cgroup': values['memory.max'] == str(64 * 1024**2),
        'swap_cgroup': values['memory.swap.max'] == '0',
        'pids_cgroup': values['pids.max'] == '16',
        'cpu_cgroup': values['cpu.max'] == '50000 100000',
    }
    return {'checks': checks, 'cgroup_values': values}


def filesystem() -> dict:
    allowed = Path('/tmp/allowed-fixture')
    allowed.write_text('SYNTHETIC_ALLOWED')
    readback = allowed.read_text() == 'SYNTHETIC_ALLOWED'
    allowed.unlink()
    denied_errno = None
    try:
        Path('/opt/probe/forbidden-write').write_text('synthetic')
    except OSError as exc:
        denied_errno = exc.errno
    canary = os.environ.get('ROBOCOPA_HOST_CANARY_PATH', '')
    if not canary.startswith('/tmp/rc-isolation-host-'):
        raise ValueError('Missing synthetic fixture path')
    socket_paths = ('/var/run/docker.sock', '/run/docker.sock', '/run/containerd/containerd.sock')
    return {'checks': {'tmpfs_positive_control': readback,
                       'image_readable': Path('/opt/probe/probe.py').is_file(),
                       'rootfs_write_denied_readonly': denied_errno == errno.EROFS,
                       'host_canary_not_visible': not Path(canary).exists(),
                       'no_control_sockets': not any(Path(p).exists() for p in socket_paths),
                       'no_control_secrets_in_env': not any(k in os.environ for k in
                           ('GITHUB_TOKEN', 'POSTGRES_PASSWORD', 'DOCKER_HOST', 'ACTIONS_RUNTIME_TOKEN'))},
            'write_errno': denied_errno}


def network() -> dict:
    with socket.socket() as server, socket.socket() as client:
        server.bind(('127.0.0.1', 0)); server.listen(1)
        client.settimeout(1); client.connect(server.getsockname())
        accepted, _ = server.accept()
        with accepted:
            client.sendall(b'CONTROL'); control = accepted.recv(7) == b'CONTROL'
    error = None
    with socket.socket() as client:
        client.settimeout(1)
        try:
            # TEST-NET-1, non-routable documentation target; no network interface exists.
            client.connect(('192.0.2.1', 9))
        except OSError as exc:
            error = exc.errno
    raw_denied = False
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.close()
    except PermissionError:
        raw_denied = True
    interfaces = set(os.listdir('/sys/class/net'))
    return {'checks': {'loopback_positive_control': control,
                       'only_loopback_interface': interfaces == {'lo'},
                       'external_route_denied': error in (errno.ENETUNREACH, errno.EHOSTUNREACH),
                       'raw_socket_denied': raw_denied}, 'connect_errno': error}


def cpu() -> dict:
    def stats():
        return {k: int(v) for k, v in (line.split() for line in
                    Path('/sys/fs/cgroup/cpu.stat').read_text().splitlines())}
    before = stats(); start = time.monotonic(); counter = 0
    while time.monotonic() - start < 1.5:
        counter += 1
    after = stats()
    delta = after['nr_throttled'] - before['nr_throttled']
    return {'checks': {'made_progress': counter > 0, 'cfs_throttling_observed': delta > 0},
            'throttled_periods_delta': delta, 'elapsed_seconds': round(time.monotonic()-start, 3)}


def pids() -> dict:
    children = []; observed = None
    try:
        # At most 24 attempted short-lived sleep processes, within cgroup pids.max=16.
        for _ in range(24):
            try:
                children.append(subprocess.Popen(['/bin/sleep', '5'], stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            except OSError as exc:
                observed = exc.errno
                break
        peak = int(Path('/sys/fs/cgroup/pids.current').read_text())
    finally:
        for child in children:
            child.terminate()
        for child in children:
            child.wait(timeout=2)
    return {'checks': {'children_positive_control': len(children) > 0,
                       'pids_limit_denied': observed == errno.EAGAIN,
                       'limit_not_exceeded': peak <= 16,
                       'children_reaped': all(p.poll() is not None for p in children)},
            'children_started': len(children), 'observed_errno': observed, 'peak_pids': peak}


def tmpfs() -> dict:
    observed = None; written = 0
    try:
        with Path('/tmp/fill-fixture').open('wb', buffering=0) as f:
            for _ in range(8):  # bounded 8 MiB request into a 4 MiB tmpfs
                written += f.write(b'X' * 1024**2)
    except OSError as exc:
        observed = exc.errno
    finally:
        Path('/tmp/fill-fixture').unlink(missing_ok=True)
    return {'checks': {'write_positive_control': written > 0,
                       'tmpfs_quota_denied': observed == errno.ENOSPC,
                       'write_within_tmpfs_budget': written <= 4*1024**2},
            'observed_errno': observed, 'written_bytes': written}


def main():
    if os.name != 'posix' or os.getuid() != 10001 or os.getenv('ROBOCOPA_CONTAINED_PROBE') != '1':
        raise SystemExit('REFUSED: controlled container required')
    base = baseline()
    if not all(base['checks'].values()):
        print(json.dumps(base)); raise SystemExit(3)
    case = sys.argv[1]
    if case == 'memory':
        # Single 96 MiB request against hard 64 MiB cgroup (swap disabled).
        bytearray(96*1024**2)
        raise SystemExit('FAIL: cgroup did not enforce memory budget')
    if case == 'timeout':
        subprocess.Popen(['/bin/sleep', '60'])
        time.sleep(60)  # external watchdog must remove this container and its child
        raise SystemExit('FAIL: watchdog did not terminate fixture')
    if case == 'output':
        for _ in range(256):
            os.write(1, b'X' * 4096)  # capped fixture: 1 MiB; collector budget: 8 KiB
        return
    functions = {'baseline': lambda: base, 'filesystem': filesystem, 'network': network,
                 'cpu': cpu, 'pids': pids, 'tmpfs': tmpfs}
    result = functions[case]()
    result['case'] = case
    print(json.dumps(result, sort_keys=True))
    if not all(result['checks'].values()):
        raise SystemExit(3)


if __name__ == '__main__':
    main()
