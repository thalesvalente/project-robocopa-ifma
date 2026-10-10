"""Policy tests with explicitly synthetic inspect fixtures; not runtime proof."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.worker_agent.policy import ProbePolicy, PolicyError, require_disposable_ci

POLICY = ProbePolicy()
RUN = 'a'*24
IMAGE = 'sha256:'+'b'*64


def fixture():
    return {'Image': IMAGE, 'Mounts': [], 'Config': {'User': POLICY.uid,
        'Labels': {'org.robocopa.isolation-run': RUN}},
        'HostConfig': {'NetworkMode':'none','ReadonlyRootfs':True,'Privileged':False,
            'Binds':None,'Mounts':[],'PortBindings':{},'PublishAllPorts':False,
            'Devices':[], 'DeviceRequests':[], 'CapDrop':['ALL'],'CapAdd':[],
            'SecurityOpt':['no-new-privileges'], 'PidMode':'','IpcMode':'private',
            'CgroupnsMode':'private', 'Memory': POLICY.memory_bytes,
            'MemorySwap':POLICY.memory_bytes,'NanoCpus':POLICY.nano_cpus,
            'PidsLimit':POLICY.pids,'Init':True,'LogConfig':{'Type':'none'},
            'Tmpfs':{'/tmp':f'rw,noexec,nosuid,nodev,size={POLICY.tmpfs_bytes},mode=1777'}}}


class PolicyTests(unittest.TestCase):
    def test_allowed_policy(self): self.assertTrue(all(POLICY.verify(fixture(), IMAGE, RUN).values()))
    def test_reject_wrong_image(self):
        with self.assertRaises(PolicyError): POLICY.verify(fixture(), 'sha256:'+'c'*64, RUN)
    def test_reject_wrong_ownership(self):
        with self.assertRaises(PolicyError): POLICY.verify(fixture(), IMAGE, 'd'*24)
    def test_denies_unsafe_configuration_mutations(self):
        cases={'NetworkMode':'host','ReadonlyRootfs':False,'Privileged':True,
            'Binds':['/:/host'],'Mounts':[{'Type':'bind','Source':'/'}],
            'PortBindings':{'80/tcp':[{}]},'PublishAllPorts':True,
            'Devices':[{}],'DeviceRequests':[{}],'CapAdd':['SYS_ADMIN'],'CapDrop':[],
            'SecurityOpt':['no-new-privileges','seccomp=unconfined'],
            'PidMode':'host','IpcMode':'host','CgroupnsMode':'host','UsernsMode':'host',
            'Memory':0,'MemorySwap':-1,'NanoCpus':0,'PidsLimit':-1,
            'Init':False,'LogConfig':{'Type':'json-file'},'Tmpfs':{'/tmp':'rw,size=4m'}}
        for key,value in cases.items():
            with self.subTest(key=key):
                info=fixture(); info['HostConfig'][key]=value
                with self.assertRaises(PolicyError): POLICY.verify(info,IMAGE,RUN)
    def test_untracked_mount_denied(self):
        info=fixture(); info['Mounts']=[{'Type':'bind','Source':'/etc'}]
        with self.assertRaises(PolicyError): POLICY.verify(info,IMAGE,RUN)
    def test_only_fixed_tmpfs_allowed(self):
        info=fixture();info['Mounts']=[{'Type':'tmpfs','Destination':'/tmp'}]
        self.assertTrue(all(POLICY.verify(info,IMAGE,RUN).values()))
    def test_root_denied(self):
        info=fixture(); info['Config']['User']='0'
        with self.assertRaises(PolicyError): POLICY.verify(info,IMAGE,RUN)
    def test_command_has_no_mounts_or_public_ports(self):
        args=POLICY.create_args('rc-isolation-'+'d'*24,IMAGE,'baseline',RUN)
        self.assertNotIn('--privileged',args); self.assertNotIn('-v',args); self.assertNotIn('-p',args)
    def test_unapproved_case_denied(self):
        with self.assertRaises(PolicyError): POLICY.create_args('rc-isolation-'+'d'*24,IMAGE,'shell',RUN)
    def test_tag_not_content_id_denied(self):
        with self.assertRaises(PolicyError): POLICY.create_args('rc-isolation-'+'d'*24,'python:latest','baseline',RUN)
    def test_name_injection_denied(self):
        with self.assertRaises(PolicyError): POLICY.create_args('other-project',IMAGE,'baseline',RUN)
    def test_local_machine_denied(self):
        with self.assertRaises(PolicyError): require_disposable_ci({},'Windows','11')
    def test_wsl_denied_even_with_ci_environment(self):
        env={'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted',
             'GITHUB_REPOSITORY':'thalesvalente/project-robocopa-ifma'}
        with self.assertRaises(PolicyError): require_disposable_ci(env,'Linux','microsoft-standard-WSL2')
    def test_remote_daemon_environment_denied(self):
        env={'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted',
             'GITHUB_REPOSITORY':'thalesvalente/project-robocopa-ifma','DOCKER_HOST':'ssh://other'}
        with self.assertRaises(PolicyError): require_disposable_ci(env,'Linux','6.8.0')
    def test_hosted_linux_guard(self):
        env={'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted',
             'GITHUB_REPOSITORY':'thalesvalente/project-robocopa-ifma'}
        require_disposable_ci(env,'Linux','6.8.0')
