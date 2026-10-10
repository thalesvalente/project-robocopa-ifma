from copy import deepcopy
import unittest
from services.worker_agent.arena_policy import ArenaPolicy,firewall,verify_namespace_target
from services.worker_agent.policy import PolicyError

IMAGE='sha256:'+'a'*64
RUN='b'*24
NET='rc-arena-net-'+RUN

def sample(role='walls'):
    limits=ArenaPolicy(role).limits()
    return {'Image':IMAGE,'Config':{'User':'10001:10001','Env':['HOME=/tmp'],
       'Labels':{'org.robocopa.isolation-run':RUN,'org.robocopa.arena-role':role}},
       'State':{'Pid':1234,'Running':True},
       'HostConfig':{'NetworkMode':NET,'ReadonlyRootfs':True,'Privileged':False,
        'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],
        'CgroupnsMode':'private','Memory':limits.memory_bytes,'MemorySwap':limits.memory_bytes,
        'NanoCpus':limits.nano_cpus,'PidsLimit':limits.pids,'Init':True,
        'LogConfig':{'Type':'none'},'Tmpfs':{'/tmp':f'rw,noexec,nosuid,nodev,size={limits.tmpfs_bytes},mode=1777'}}}

class ArenaPolicyTests(unittest.TestCase):
    def test_valid_roles(self):
        for role in ('referee','walls','spin'):
            self.assertTrue(all(ArenaPolicy(role).verify(sample(role),IMAGE,RUN,NET).values()))
    def test_unsafe_mutations(self):
        for field,value in [('NetworkMode','host'),('Privileged',True),('PidMode','container:x'),
           ('IpcMode','host'),('CapAdd',['NET_ADMIN']),('Binds',['/:/host']),('MemorySwap',-1),
           ('PortBindings',{'7654/tcp':[{'HostPort':'7654'}]})]:
            obj=sample();obj['HostConfig'][field]=value
            with self.subTest(field=field),self.assertRaises(PolicyError):ArenaPolicy('walls').verify(obj,IMAGE,RUN,NET)
    def test_secret_metadata_forbidden(self):
        obj=sample();obj['Config']['Env']=['ADMIN_SECRET=x']
        with self.assertRaises(PolicyError):ArenaPolicy('walls').verify(obj,IMAGE,RUN,NET)
    def test_role_mismatch(self):
        with self.assertRaises(PolicyError):ArenaPolicy('referee').verify(sample(),IMAGE,RUN,NET)
    def test_create_command_scope(self):
        args=ArenaPolicy('walls').create_args('rc-isolation-'+'c'*24,IMAGE,RUN,NET)
        self.assertEqual(args[args.index('--network')+1],NET)
        for flag in ('--privileged','--publish','--volume','--cap-add','--env'):self.assertNotIn(flag,args)
    def test_firewall_allows_only_gateway(self):
        text=firewall('walls','172.19.0.2',['172.19.0.3','172.19.0.4'])
        self.assertIn('-d 172.19.0.2/32 -p tcp --dport 7654 -j ACCEPT',text)
        self.assertNotIn('7655',text)
        self.assertNotIn('-o lo -j ACCEPT',text)
        self.assertIn('-d 127.0.0.1/32',text)
        self.assertNotIn('127.0.0.11',text)
    def test_ipv6_has_no_allow_rule(self):
        self.assertNotIn('ACCEPT',firewall('walls','172.19.0.2',['172.19.0.3','172.19.0.4'],ipv6=True))
    def test_referee_sources_are_limited(self):
        text=firewall('referee','172.19.0.2',['172.19.0.3','172.19.0.4'])
        self.assertEqual(text.count('--dport 7654'),2)
        self.assertNotIn('7655',text)
    def test_injected_address_and_network_denied(self):
        for ip in ('1.2.3.4\nCOMMIT','127.0.0.1','0.0.0.0','::1'):
            with self.subTest(ip=ip),self.assertRaises(ValueError):firewall('walls',ip,['172.19.0.3','172.19.0.4'])
    def test_host_namespace_denied(self):
        with self.assertRaises(PolicyError):verify_namespace_target(sample(),RUN,'net:[1]','net:[1]')
    def test_unowned_namespace_denied(self):
        with self.assertRaises(PolicyError):verify_namespace_target(sample(),'wrong','net:[2]','net:[1]')
    def test_stopped_namespace_denied(self):
        obj=sample();obj['State']['Running']=False
        with self.assertRaises(PolicyError):verify_namespace_target(obj,RUN,'net:[2]','net:[1]')
    def test_valid_namespace(self):
        self.assertEqual(verify_namespace_target(sample(),RUN,'net:[2]','net:[1]'),1234)
