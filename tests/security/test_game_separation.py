"""I2 contract tests: mocked inspect/fixtures explicitly distinct from CI battle."""
from __future__ import annotations
import copy, gzip, importlib.util, json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from services.worker_agent.game_policy import GamePolicy, PolicyError, ROLE_ENV, ROLE_COMMANDS, LABEL, addresses, network_args, verify_network
SPEC=importlib.util.spec_from_file_location('separation_harness',ROOT/'scripts/run_engine_separation.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
RUN='a'*24;IMAGE='sha256:'+'b'*64;NETWORK='rc-i2-'+RUN+'-a'


def fixture(role='walls'):
    p=GamePolicy(role)
    return {'Image':IMAGE,'Config':{'User':'10001:10001','Labels':{LABEL:RUN,'org.robocopa.i2-role':role},
        'Cmd':ROLE_COMMANDS[role],'Env':[k+'=fixture' for k in ROLE_ENV[role]]},
        'NetworkSettings':{'Networks':{NETWORK:{}}},'Mounts':[],
        'HostConfig':{'ReadonlyRootfs':True,'Privileged':False,'Binds':None,'Mounts':None,
          'PortBindings':{},'PublishAllPorts':False,'CapDrop':['ALL'],'CapAdd':[],
          'SecurityOpt':['no-new-privileges'],'Memory':p.memory,'MemorySwap':p.memory,
          'NanoCpus':1000000000,'PidsLimit':96,'CgroupnsMode':'private','Init':True,
          'LogConfig':{'Type':'none'},'Tmpfs':{'/tmp':f'rw,noexec,nosuid,nodev,size={p.tmpfs},mode=1777'},
          'Dns':['127.0.0.1'],'Sysctls':{'net.ipv4.ip_forward':'0','net.ipv6.conf.all.disable_ipv6':'1'}}}


def netfixture():return {'Labels':{LABEL:RUN},'Driver':'bridge','Internal':True,'EnableIPv6':False,
    'Options':{'com.docker.network.bridge.gateway_mode_ipv4':'isolated'},'IPAM':{'Config':[{'Subnet':'172.28.0.0/16'}]}}


class RuntimePolicyTests(unittest.TestCase):
    def test_all_roles(self):
        for role in ROLE_COMMANDS:
            with self.subTest(role=role):self.assertTrue(all(GamePolicy(role).verify(fixture(role),IMAGE,RUN,{NETWORK}).values()))
    def test_wrong_owner(self):
        d=fixture();d['Config']['Labels'][LABEL]='x'
        with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_host_mount(self):
        d=fixture();d['HostConfig']['Binds']=['/host:/guest']
        with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_foreign_network(self):
        d=fixture();d['NetworkSettings']['Networks']['bridge']={}
        with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_bot_cannot_receive_admin(self):
        d=fixture();d['Config']['Env'].append('ADMIN_SECRET=fixture')
        with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_bot_cannot_receive_backend_secret(self):
        d=fixture();d['Config']['Env'].append('BACKEND_SECRET=fixture')
        with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_missing_role_config(self):
        d=fixture();d['Config']['Env']=[]
        with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_gateway_no_admin(self):
        d=fixture('gateway');d['Config']['Env'].append('ADMIN_SECRET=fixture')
        with self.assertRaises(PolicyError):GamePolicy('gateway').verify(d,IMAGE,RUN,{NETWORK})
    def test_no_raw_credentials_in_args(self):
        args=GamePolicy('walls').create_args('rc-i2-'+RUN+'-walls',IMAGE,RUN,NETWORK,'172.28.0.3')
        self.assertIn('BOT_SECRET',args);self.assertNotIn('fixture',args)
    def test_injection_name(self):
        with self.assertRaises(PolicyError):GamePolicy('walls').create_args('x;anything',IMAGE,RUN,NETWORK,'172.28.0.3')
    def test_mutable_image(self):
        with self.assertRaises(PolicyError):GamePolicy('walls').create_args('rc-i2-'+RUN+'-walls','image:latest',RUN,NETWORK,'172.28.0.3')
    def test_no_host_mount_publish_flags(self):
        args=GamePolicy('judge').create_args('rc-i2-'+RUN+'-judge',IMAGE,RUN,NETWORK,'172.28.0.2')
        for flag in ('--privileged','--volume','-v','--publish','-p'):self.assertNotIn(flag,args)
    def test_mutations_denied(self):
        changes={'Memory':0,'MemorySwap':-1,'NanoCpus':0,'PidsLimit':0,'Privileged':True,
            'ReadonlyRootfs':False,'PortBindings':{'7654/tcp':[{'HostPort':'7654'}]},'CapAdd':['NET_ADMIN'],
            'SecurityOpt':['seccomp=unconfined'],'PidMode':'host','CgroupnsMode':'host','Dns':['8.8.8.8'],
            'Tmpfs':{'/tmp':'size=0'},'Sysctls':{'net.ipv4.ip_forward':'1','net.ipv6.conf.all.disable_ipv6':'0'}}
        for field,value in changes.items():
            with self.subTest(field=field):
                d=fixture();d['HostConfig'][field]=value
                with self.assertRaises(PolicyError):GamePolicy('walls').verify(d,IMAGE,RUN,{NETWORK})
    def test_undefined_role(self):
        with self.assertRaises(PolicyError):GamePolicy('arbitrary')
    def test_policy_digest_role_bound(self):self.assertNotEqual(GamePolicy('walls').digest,GamePolicy('judge').digest)


class NetworkTests(unittest.TestCase):
    def test_isolated_network(self):self.assertTrue(all(verify_network(netfixture(),RUN).values()))
    def test_internal_not_enough(self):
        d=netfixture();d['Options']={}
        with self.assertRaises(PolicyError):verify_network(d,RUN)
    def test_ipv6_rejected(self):
        d=netfixture();d['EnableIPv6']=True
        with self.assertRaises(PolicyError):verify_network(d,RUN)
    def test_owner_network(self):
        with self.assertRaises(PolicyError):verify_network(netfixture(),'other')
    def test_creation_required_options(self):
        args=network_args(NETWORK,RUN);self.assertIn('--internal',args)
        self.assertIn('com.docker.network.bridge.gateway_mode_ipv4=isolated',args)
    def test_address_plan(self):self.assertEqual(addresses(netfixture()),('172.28.0.2','172.28.0.3'))
    def test_no_public_subnet(self):
        d=netfixture();d['IPAM']['Config'][0]['Subnet']='8.8.8.0/24'
        with self.assertRaises(PolicyError):addresses(d)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.result={'source':'GameEndedEventForObserver','engine_version':'1.4.0','completed':True,
            'numberOfRounds':3,'observedTicks':3,'observedRoundEnds':[1,2,3],
            'results':[{'name':'Walls','version':'1.0','rank':1,'totalScore':10},{'name':'Spin Bot','version':'1.0','rank':2,'totalScore':5}]}
        self.events=[{'type':'GameStartedEventForObserver'}]
        for r in range(1,4):self.events += [{'type':'RoundStartedEvent','roundNumber':r},{'type':'TickEventForObserver','roundNumber':r},{'type':'RoundEndedEventForObserver','roundNumber':r}]
        self.events += [{'type':'GameEndedEventForObserver','numberOfRounds':3,'results':copy.deepcopy(self.result['results'])}]
    def check(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.battle.gz';p.write_bytes(gzip.compress(('\n'.join(json.dumps(x) for x in self.events)).encode()))
            return M.validate_replay(p,self.result)
    def test_real_contract_fixture(self):self.assertTrue(self.check()['results_equal'])
    def test_wrong_source(self):
        self.result['source']='BotOutput'
        with self.assertRaises(ValueError):self.check()
    def test_replay_score_changed(self):
        self.events[-1]['results'][0]['totalScore']=999
        with self.assertRaises(ValueError):self.check()
    def test_missing_round(self):
        self.events=[e for e in self.events if not(e['type']=='RoundEndedEventForObserver' and e['roundNumber']==2)]
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_final(self):
        self.events.append(self.events[-1])
        with self.assertRaises(ValueError):self.check()
    def test_bad_identity(self):
        self.result['results'][0]['name']='Unknown'
        with self.assertRaises(ValueError):self.check()
    def test_boolean_score_denied(self):
        self.result['results'][0]['totalScore']=True;self.events[-1]['results']=self.result['results']
        with self.assertRaises(ValueError):self.check()
    def test_raw_handshake_not_in_recording(self):
        self.events.append({'type':'ServerHandshake','secret':'fixture'})
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_json_denied(self):
        with self.assertRaises(ValueError):M.strict_json('{"type":"BotIntent","type":"PauseGame"}')
    def test_nan_json_denied(self):
        with self.assertRaises(ValueError):M.strict_json('{"value":NaN}')

if __name__=='__main__':unittest.main()
