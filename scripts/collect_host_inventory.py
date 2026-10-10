#!/usr/bin/env python3
"""Inventário técnico local para a hospedagem da RoboCopa IFMA.

Somente leitura, sem privilégios administrativos, sem acesso externo.
Não registra identificadores do computador, contas, IPs ou credenciais.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess


SCHEMA_VERSION = 3
OUTPUT_NAME = 'inventory-v3.json'
COMMANDS = ('git', 'uv', 'docker', 'wsl', 'node', 'npm', 'java', 'nvidia-smi')


# Seleção explícita de propriedades: não se exportam objetos CIM completos.
WINDOWS_PROBE = r'''
$ErrorActionPreference = 'Stop'
$cpu = @(Get-CimInstance Win32_Processor | ForEach-Object {
    [ordered]@{
        model = [string]$_.Name
        physical_cores = [int]$_.NumberOfCores
        logical_processors = [int]$_.NumberOfLogicalProcessors
        virtualization_firmware_enabled = [bool]$_.VirtualizationFirmwareEnabled
    }
})
$machine = Get-CimInstance Win32_ComputerSystem
$osinfo = Get-CimInstance Win32_OperatingSystem
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object {
    [ordered]@{ model = [string]$_.Name; driver_version = [string]$_.DriverVersion }
})
$memory = @(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
    [ordered]@{ capacity_bytes = [int64]$_.Capacity; speed_mhz = [int]$_.Speed }
})
$volumes = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
    [ordered]@{ drive = [string]$_.DeviceID; capacity_bytes = [int64]$_.Size; free_bytes = [int64]$_.FreeSpace }
})
$disks = @()
try {
    $disks = @(Get-PhysicalDisk -ErrorAction Stop | ForEach-Object {
        [ordered]@{ model = [string]$_.FriendlyName; media_type = [string]$_.MediaType; bus_type = [string]$_.BusType; capacity_bytes = [int64]$_.Size }
    })
} catch {}
$network = @()
try {
    $network = @(Get-NetAdapter -Physical -ErrorAction Stop | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
        [ordered]@{ link_speed_bits_per_second = [int64]$_.TransmitLinkSpeed }
    })
} catch {}
$firewall = @()
try {
    $firewall = @(Get-NetFirewallProfile -ErrorAction Stop | ForEach-Object {
        [ordered]@{ profile = [string]$_.Name; enabled = [bool]$_.Enabled }
    })
} catch {}
$ports = @()
try {
    $wanted = @(80, 443, 3000, 5432, 8080, 8765)
    $ports = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Where-Object { $wanted -contains [int]$_.LocalPort } |
        Select-Object -ExpandProperty LocalPort -Unique)
} catch {}
$result = [ordered]@{
    cpu = $cpu
    ram = [ordered]@{
        installed_bytes = [int64]$machine.TotalPhysicalMemory
        available_bytes = [int64]$osinfo.FreePhysicalMemory * 1024
        modules = $memory
    }
    os = [ordered]@{
        edition = [string]$osinfo.Caption
        build = [string]$osinfo.BuildNumber
        uptime_hours = [Math]::Round(((Get-Date) - $osinfo.LastBootUpTime).TotalHours, 1)
        hypervisor_present = [bool]$machine.HypervisorPresent
    }
    gpu = $gpus
    volumes = $volumes
    physical_disks = $disks
    network_link_only = $network
    firewall_profiles = $firewall
    checked_ports = @($wanted | ForEach-Object {
        [ordered]@{ port = [int]$_; listening = [bool]($ports -contains $_) }
    })
}
$result | ConvertTo-Json -Depth 8 -Compress
'''


def _decode_stdout(raw: bytes) -> str:
    if not raw:
        return ''
    if b'\x00' in raw[:160]:
        # A saída do wsl.exe pode usar UTF-16 LE mesmo quando redirecionada.
        return raw.decode('utf-16-le', errors='replace').lstrip('\ufeff')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('cp1252', errors='replace')


def _run(args: list[str], timeout: int = 8) -> str | None:
    """Não usa shell; stderr e erros nunca entram no relatório."""
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                check=False, timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    return _decode_stdout(result.stdout).strip()


def _windows_details() -> dict:
    powershell = shutil.which('powershell.exe') or shutil.which('powershell')
    if not powershell:
        return {'status': 'powershell_unavailable'}
    payload = _run([powershell, '-NoLogo', '-NoProfile', '-NonInteractive',
                    '-Command', WINDOWS_PROBE], timeout=25)
    if payload is None:
        return {'status': 'windows_probe_failed'}
    try:
        result = json.loads(payload)
    except (ValueError, TypeError):
        return {'status': 'windows_probe_unreadable'}
    if not isinstance(result, dict) or not isinstance(result.get('cpu'), list):
        return {'status': 'windows_probe_invalid'}
    return {'status': 'ok', **result}


def _docker_details() -> dict:
    docker = shutil.which('docker')
    if not docker:
        return {'cli_available': False, 'daemon_accessible': False}
    result = {'cli_available': True, 'daemon_accessible': False}
    output = _run([docker, 'info', '--format',
                   '{{.ServerVersion}}|{{.OSType}}|{{.NCPU}}|{{.MemTotal}}'], timeout=10)
    if output:
        parts = output.split('|')
        if len(parts) == 4 and parts[2].strip().isdigit() and parts[3].strip().isdigit():
            result.update({'daemon_accessible': True, 'server_version': parts[0].strip(),
                           'os_type': parts[1].strip(), 'allocated_cpus': int(parts[2]),
                           'allocated_memory_bytes': int(parts[3])})
    if result['daemon_accessible']:
        docker_root = _run([docker, 'info', '--format', '{{.DockerRootDir}}'], timeout=8)
        if docker_root is not None:
            result['docker_root_dir'] = ('/var/lib/docker' if docker_root == '/var/lib/docker'
                                         else '[custom_path_redacted]')
        result['storage_usage'] = _docker_storage_usage(docker)
        result['windows_disk_image_location'] = 'not_identified_from_linux_docker_root'
    compose = _run([docker, 'compose', 'version', '--short'], timeout=7)
    if compose and re.fullmatch(r'[vV]?[0-9][0-9A-Za-z.+-]*', compose):
        result['compose_version'] = compose
    return result


def _docker_storage_usage(docker: str) -> dict:
    """Docker system df em JSON por linha, sem nomes de recursos."""
    raw = _run([docker, 'system', 'df', '--format', 'json'], timeout=35)
    if raw is None:
        return {'status': 'unavailable'}
    allowed_types = {'Images', 'Containers', 'Local Volumes', 'Build Cache'}
    rows: list[dict] = []
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            return {'status': 'unreadable'}
        if not isinstance(value, dict) or value.get('Type') not in allowed_types:
            continue
        try:
            total = int(value['TotalCount'])
            active = int(value['Active'])
            if not (0 <= active <= total):
                return {'status': 'unreadable'}
        except (KeyError, TypeError, ValueError):
            return {'status': 'unreadable'}
        size = str(value.get('Size', ''))
        reclaimable = str(value.get('Reclaimable', ''))
        # Whitelist: numeros, unidades e percentuais, sem IDs ou nomes.
        pattern = r'[0-9]+(?:[.,][0-9]+)?\s*[A-Za-z]{0,4}'
        if not re.fullmatch(pattern, size):
            return {'status': 'unreadable'}
        if not re.fullmatch(pattern + r'(?:\s*\([0-9]+%\))?', reclaimable):
            return {'status': 'unreadable'}
        rows.append({'type': value['Type'], 'total': total, 'active': active,
                     'size': size, 'reclaimable': reclaimable})
    return {'status': 'ok', 'categories': rows} if rows else {'status': 'empty'}


def _safe_wsl_name(name: str) -> str:
    """Nomes comuns autorizados; nomes personalizados sao mascarados."""
    if name == 'docker-desktop':
        return name
    if name in ('Ubuntu', 'Debian', 'openSUSE', 'kali-linux'):
        return name
    if re.fullmatch(r'Ubuntu-\d{2}\.\d{2}', name):
        return name
    return '[custom_name_redacted]'


def _wsl_status(executable: str) -> dict:
    raw = _run([executable, '--status'], timeout=9)
    if raw is None:
        return {'status': 'unavailable'}
    result = {'status': 'ok'}
    for line in raw.splitlines():
        if ':' not in line:
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        normalized = key.casefold()
        if normalized in ('default distribution', 'distribuição padrão',
                          'distribuicao padrao'):
            result['default_distribution'] = _safe_wsl_name(value)
        elif normalized in ('default version', 'versão padrão', 'versao padrao'):
            if value in ('1', '2'):
                result['default_version'] = int(value)
    return result


def _wsl_details() -> dict:
    executable = shutil.which('wsl') or shutil.which('wsl.exe')
    if not executable:
        return {'cli_available': False}
    result = {'cli_available': True, 'status': _wsl_status(executable)}
    output = _run([executable, '--list', '--verbose'], timeout=9)
    if output is None:
        result['distros_query_ok'] = False
    else:
        distros = []
        for line in output.splitlines():
            match = re.match(r'^\s*\*?\s*(.+?)\s{2,}(.+?)\s{2,}([12])\s*$', line)
            if not match:
                continue
            name, state, version_text = match.groups()
            normalized_state = state.strip().casefold()
            if normalized_state in ('running', 'em execução', 'em execucao'):
                status = 'running'
            elif normalized_state in ('stopped', 'parado'):
                status = 'stopped'
            else:
                status = 'other'
            distros.append({'distribution': _safe_wsl_name(name.strip()),
                            'state': status, 'version': int(version_text)})
        result.update({'distros_query_ok': True,
                       'distribution_count': len(distros),
                       'wsl2_distribution_count': sum(d['version'] == 2 for d in distros),
                       'distributions': distros})
    return result


def _nvidia_details() -> list[dict]:
    executable = shutil.which('nvidia-smi')
    if not executable:
        return []
    output = _run([executable, '--query-gpu=name,memory.total,driver_version',
                   '--format=csv,noheader,nounits'], timeout=8)
    if output is None:
        return []
    result = []
    for line in output.splitlines():
        parts = [value.strip() for value in line.split(',')]
        if (len(parts) == 3 and re.fullmatch(r'[0-9]+', parts[1])
                and len(parts[0]) <= 120 and len(parts[2]) <= 30):
            result.append({'model': parts[0], 'vram_mib': int(parts[1]),
                           'driver_version': parts[2]})
    return result


def collect(root: Path) -> dict:
    usage = shutil.disk_usage(root)
    result = {
        'schema_version': SCHEMA_VERSION,
        'collected_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Planejamento da hospedagem local do MVP RoboCopa IFMA',
        'system': {'os': platform.system(), 'release': platform.release(),
                   'architecture': platform.machine(), 'python': platform.python_version(),
                   'logical_cpu_count': os.cpu_count()},
        'project_volume': {'capacity_bytes': usage.total, 'free_bytes': usage.free},
        'tools_installed': {name: shutil.which(name) is not None for name in COMMANDS},
        'windows_hardware': (_windows_details() if platform.system() == 'Windows'
                             else {'status': 'not_windows'}),
        'nvidia_gpu': _nvidia_details(),
        'docker': _docker_details(),
        'wsl': (_wsl_details() if platform.system() == 'Windows'
                else {'cli_available': False, 'status': 'not_windows'}),
        'not_collected': ['username', 'hostname', 'ip_addresses', 'mac_addresses',
                          'serial_numbers', 'wifi_ssid', 'credentials', 'personal_files',
                          'process_names', 'container_names'],
        'manual_validation_required': [
            'Velocidade de upload (teste voluntário)',
            'CGNAT / IPv4 público / IPv6 e política do provedor',
            'Estabilidade e disponibilidade da conexão e energia',
            'Estratégia de backup externo e restauração testada',
            'Isolamento efetivo de códigos de robôs não confiáveis',
            'Política de suspensão e reinícios do Windows',
            'Capacidade de armazenamento após instalação e logs',
            'Verificar local do disco virtual: Docker Desktop > Settings > Resources > Advanced',
        ],
    }
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    directory = root / '.local'
    if directory.is_symlink():
        raise SystemExit('Recusado: .local é um link simbólico.')
    directory.mkdir(exist_ok=True)
    target = directory / OUTPUT_NAME
    if target.exists() or target.is_symlink():
        raise SystemExit(f'{OUTPUT_NAME} já existe. Revise ou renomeie antes de uma nova coleta.')
    with target.open('x', encoding='utf-8') as handle:
        json.dump(collect(root), handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(f'Inventário v3 salvo em .local/{OUTPUT_NAME}. Revise antes de compartilhar; não faça commit.')


if __name__ == '__main__':
    main()
