#!/usr/bin/env python3
"""I2 finite integration experiment; disposable GitHub runner ONLY, never operator host.
Four containers and three isolated networks. No student source or public endpoint.
"""
from __future__ import annotations
from datetime import datetime, timezone
import gzip, hashlib, importlib.util, ipaddress, json, os, platform, secrets, socket, sys, threading, time, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.worker_agent.policy import require_disposable_ci, PolicyError
from services.worker_agent.game_policy import GamePolicy, network_args, verify_network, addresses, LABEL
from services.worker_agent.bounded import capture, ProcessBoundError
ROOT=Path(__file__).resolve().parents[1]
CP='/opt/i2/classes:/opt/i2/api.jar:/opt/i2/server.jar:/opt/i2/runner.jar'
CASES=('controller_role','observer_role','before_auth_control','after_auth_control','second_handshake','wrong_identity','wrong_secret','duplicate_json','message_limit')

class OperationError(RuntimeError):
    def __init__(self, output: bytes):
        super().__init__('COMMAND_FAILED');self.output=output

def command(args,timeout=20,limit=2*1024**2,env=None):
    r=capture(args,timeout=timeout,max_bytes=limit,env=env)
    if r.returncode:raise OperationError(r.output)
    return r.output

def docker(*args,timeout=20,limit=2*1024**2,env=None):
    return command(['docker',*args],timeout,limit,env)

def inspect(name):return json.loads(docker('inspect',name))[0]

def jexec(name,cls,*args,timeout=15,limit=65536):
    return docker('exec',name,'java','-cp',CP,cls,*args,timeout=timeout,limit=limit)

def payload(output):
    return json.loads(next(line for line in reversed(output.decode('utf-8').splitlines()) if line.startswith('{')))

def wait_probe(name,mode,path=None):
    for _ in range(30):
        try:jexec(name,'Probe',mode,*([path] if path else []));return
        except (RuntimeError,ProcessBoundError):time.sleep(.3)
    raise RuntimeError('READY_TIMEOUT')

def strict_json(raw):
    def unique(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError('DUPLICATE_JSON_KEY')
            obj[key]=value
        return obj
    def constant(_):raise ValueError('NON_FINITE_JSON')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=constant)

def validate_replay(path: Path, results: dict) -> dict:
    if results.get('source')!='GameEndedEventForObserver' or results.get('engine_version')!='1.4.0' or results.get('completed') is not True:raise ValueError('UNTRUSTED_RESULT')
    if results.get('numberOfRounds')!=3:raise ValueError('ROUND_COUNT')
    rows=results.get('results',[])
    if len(rows)!=2 or {r.get('name') for r in rows}!={'Walls','Spin Bot'} or any(r.get('version')!='1.0' for r in rows):raise ValueError('IDENTITIES')
    ticks=0;rounds=[];starts=0;ends=[];size=0
    with gzip.open(path,'rb') as f:
        while raw:=f.readline(2*1024**2+1):
            size+=len(raw)
            if len(raw)>2*1024**2 or size>64*1024**2:raise ValueError('REPLAY_LIMIT')
            e=strict_json(raw);t=e.get('type')
            if t=='GameStartedEventForObserver':starts+=1
            elif t=='TickEventForObserver':ticks+=1
            elif t=='RoundEndedEventForObserver':rounds.append(e['roundNumber'])
            elif t=='GameEndedEventForObserver':ends.append(e)
            elif t not in ('RoundStartedEvent',):raise ValueError('REPLAY_EVENT')
    if starts!=1 or rounds!=[1,2,3] or len(ends)!=1 or ticks<1 or results.get('observedTicks')!=ticks:raise ValueError('INCOMPLETE_REPLAY')
    if ends[0]['results']!=rows or ends[0]['numberOfRounds']!=3 or results.get('observedRoundEnds')!=rounds:raise ValueError('RESULT_REPLAY_MISMATCH')
    for row in rows:
        if type(row.get('totalScore')) is not int or row['totalScore']<0 or row.get('rank') not in (1,2):raise ValueError('SCORE')
    return {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'compressed_bytes':path.stat().st_size,'uncompressed_bytes':size,'ticks':ticks,'rounds':rounds,'results_equal':True}

def run():
    require_disposable_ci(dict(os.environ),platform.system(),platform.release())
    endpoint=docker('context','inspect','--format','{{.Endpoints.docker.Host}}').decode().strip()
    if endpoint!='unix:///var/run/docker.sock':raise PolicyError('LOCAL_CI_DAEMON_REQUIRED')
    info=json.loads(docker('info','--format','{{json .}}'))
    if info.get('OSType')!='linux' or any(s in info.get('OperatingSystem','').lower() for s in ('desktop','wsl')):raise PolicyError('DEDICATED_CI_DAEMON_REQUIRED')
    run_id=uuid.uuid4().hex[:24];out=ROOT/'.local/engine-separation'/run_id
    if any(p.is_symlink() for p in (ROOT/'.local',out.parent)):raise ValueError('SYMLINK')
    out.mkdir(parents=True)
    report={'schema_version':1,'status':'FAILED','scope':'I2_TRUSTED_REFERENCE_BOTS_CI_ONLY','run_id':run_id,'engine_version':'1.4.0','host_vm_tested':False,'student_submission_enabled':False,'source_commit':os.environ.get('GITHUB_SHA','unavailable'),'started_at':datetime.now(timezone.utc).isoformat(),'containers':{},'networks':{},'negative_tests':{},'stage':'build'}
    created=[];nets=[];tags=[];server=None
    values={'ADMIN_SECRET':secrets.token_urlsafe(32),'BACKEND_SECRET':secrets.token_urlsafe(32),'FRONT_A':secrets.token_urlsafe(32),'FRONT_B':secrets.token_urlsafe(32)}
    try:
        imageids={}
        for role in ('judge','gateway','bot'):
            tag='robocopa-ifma/i2-'+role+':'+run_id
            built=capture(['docker','build','--target',role,'-t',tag,'-f',str(ROOT/'spikes/isolamento/engine-separation/Dockerfile'),str(ROOT)],timeout=900,max_bytes=8*1024**2)
            (out/('build-'+role+'.log')).write_bytes(built.output)
            if built.returncode:raise OperationError(built.output)
            tags.append(tag);imageids[role]=docker('image','inspect','--format','{{.Id}}',tag).decode().strip()
        report['images']=imageids;report['stage']='networks'
        netmap={key:f'rc-i2-{run_id}-{key}' for key in ('a','b','back')};ips={}
        for key,name in netmap.items():
            docker(*network_args(name,run_id));nets.append(name)
            ni=json.loads(docker('network','inspect',name))[0];checks=verify_network(ni,run_id);ips[key]=addresses(ni)
            addrs=json.loads(command(['ip','-j','-4','address','show','dev','br-'+ni['Id'][:12]]))
            checks['no_bridge_ipv4']=all(not i.get('addr_info') for i in addrs)
            if not checks['no_bridge_ipv4']:raise PolicyError('BRIDGE_HOST_ADDRESS')
            report['networks'][key]=checks
        values.update(BIND_A=ips['a'][0],BIND_B=ips['b'][0],BACKEND_URL='ws://'+ips['back'][0]+':7654')
        names={r:f'rc-i2-{run_id}-{r}' for r in ('judge','gateway','walls','spin')}
        expected={'judge':{netmap['back']},'gateway':set(netmap.values()),'walls':{netmap['a']},'spin':{netmap['b']}}
        report['stage']='create'
        for role in names:
            netkey='a' if role=='walls' else 'b' if role=='spin' else 'back'
            ip=ips[netkey][0] if role=='judge' else ips[netkey][1]
            env=dict(os.environ);env.update(values)
            if role in ('walls','spin'):
                key='a' if role=='walls' else 'b'
                env.update(BOT_NAME='Walls' if role=='walls' else 'Spin Bot',BOT_SECRET=values['FRONT_'+key.upper()],BOT_SERVER_URL='ws://'+ips[key][0]+':8765')
            pol=GamePolicy(role);img=imageids['bot' if role in ('walls','spin') else role]
            docker(*pol.create_args(names[role],img,run_id,netmap[netkey],ip),env=env);created.append(names[role])
            if role=='gateway':
                for key in ('a','b'):docker('network','connect','--ip',ips[key][0],netmap[key],names[role])
            report['containers'][role]={'policy_sha256':pol.digest,'checks':pol.verify(inspect(names[role]),img,run_id,expected[role])}
        docker('start',*created)
        for key,net in netmap.items():
            members=json.loads(docker('network','inspect',net))[0]['Containers']
            if len(members)!=2:raise PolicyError('NETWORK_MEMBERSHIP_COUNT')
            report['networks'][key]['exactly_two_members']=True
        wait_probe(names['judge'],'ready');wait_probe(names['gateway'],'read','/tmp/gateway-ready')
        for role in ('walls','spin'):wait_probe(names[role],'read','/tmp/bot-idle')
        pids=[inspect(n)['State']['Pid'] for n in created]
        if len(set(pids))!=4 or any(p<=0 for p in pids):raise PolicyError('DISTINCT_CONTAINERS')
        report['distinct_runtime_processes']=True
        ns=[payload(jexec(n,'Probe','namespaces')) for n in created]
        report['namespace_checks']={k:len({item[k] for item in ns})==4 for k in ('pid','mount','network')}
        if not all(report['namespace_checks'].values()):raise PolicyError('SHARED_NAMESPACE')
        report['gateway_contract']=payload(jexec(names['gateway'],'ContractTest'))
        report['stage']='network-probes'
        server=socket.socket();server.bind(('0.0.0.0',0));server.listen(8);server.settimeout(.3)
        def accept():
            while True:
                try:c,_=server.accept();c.close()
                except socket.timeout:continue
                except OSError:return
        thread=threading.Thread(target=accept,daemon=True);thread.start()
        host_ip=json.loads(docker('network','inspect','bridge'))[0]['IPAM']['Config'][0]['Gateway']
        if not ipaddress.ip_address(host_ip).is_private:raise PolicyError('SYNTHETIC_HOST_CANARY')
        with socket.create_connection((host_ip,server.getsockname()[1]),timeout=2):pass
        report['host_canary_positive']=True
        for role,other in (('walls','b'),('spin','a')):
            report['negative_tests'][role]={'network':payload(jexec(names[role],'Probe','network',ips[other][1],ips['back'][0],host_ip,str(server.getsockname()[1]),timeout=20)),'protocol':[]}
            for case in CASES:
                time.sleep(.2)
                response=payload(jexec(names[role],'Probe','deny',case,timeout=10))
                if response.get('denied') is not True:raise ValueError('PROTOCOL_NOT_DENIED')
                report['negative_tests'][role]['protocol'].append(response)
        server.close();thread.join(1);server=None
        report['stage']='battle';time.sleep(.5)
        for role in ('walls','spin'):jexec(names[role],'Probe','start')
        output=jexec(names['judge'],'Judge','battle',timeout=210,limit=8*1024**2)
        for value in values.values():
            if not value.startswith(('ws://',)) and len(value)>30:output=output.replace(value.encode(),b'[REDACTED]')
        stream=out/'runtime.stream';stream.write_bytes(output)
        spec=importlib.util.spec_from_file_location('tank_reference',ROOT/'scripts/run_tank_spike.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref);ref.extract_stream(stream,out)
        results=strict_json((out/'results.json').read_text());replays=list((out/'recordings').glob('*.battle.gz'))
        if len(replays)!=1:raise ValueError('ONE_REPLAY')
        report['replay']=validate_replay(replays[0],results)
        report['gateway_stats']=payload(jexec(names['gateway'],'Probe','read','/tmp/gate-report.json'));report['result_summary']=results['results']
        for data in [(out/'results.json').read_bytes(),gzip.decompress(replays[0].read_bytes()),(out/'engine.log').read_bytes()]:
            if any(value.encode() in data for key,value in values.items() if key in ('ADMIN_SECRET','BACKEND_SECRET','FRONT_A','FRONT_B')):raise ValueError('SECRET_IN_ARTIFACT')
        if report['gateway_stats'].get('forwarded_intents',0)<1:raise ValueError('NO_REAL_INTENTS')
        report['status']='PASS';report['stage']='verified'
    except Exception as error:
        diagnostic=getattr(error,'output',b'')
        if not isinstance(diagnostic,bytes):diagnostic=b''
        for value in values.values():diagnostic=diagnostic.replace(value.encode(),b'[REDACTED]')
        report['failure']={'type':type(error).__name__,'stage':report['stage'],'diagnostic':diagnostic[-4096:].decode('utf-8',errors='replace')}
        raise RuntimeError('I2_FAILED_AT_'+report['stage']) from None
    finally:
        if server:server.close()
        errors=[]
        for name in reversed(created):
            try:
                if inspect(name).get('Config',{}).get('Labels',{}).get(LABEL)!=run_id:raise PolicyError('CLEANUP_OWNERSHIP')
                docker('rm','-f',name)
            except Exception:errors.append('container_cleanup')
        for name in reversed(nets):
            try:
                ni=json.loads(docker('network','inspect',name))[0]
                if ni.get('Labels',{}).get(LABEL)!=run_id:raise PolicyError('CLEANUP_NETWORK_OWNERSHIP')
                docker('network','rm',name)
            except Exception:errors.append('network_cleanup')
        for tag in tags:
            try:docker('image','rm',tag)
            except Exception:errors.append('image_tag_cleanup')
        try:
            if docker('ps','-aq','--filter','label='+LABEL+'='+run_id).strip():errors.append('owned_container_remaining')
            if docker('network','ls','-q','--filter','label='+LABEL+'='+run_id).strip():errors.append('owned_network_remaining')
        except Exception:errors.append('cleanup_verification')
        report['cleanup']={'containers_removed':len(created),'networks_removed':len(nets),'errors':errors,'verified':not errors}
        if errors:report['status']='FAILED'
        if report['status']!='PASS':
            for name in ('runtime.stream','engine.log','results.json'):(out/name).unlink(missing_ok=True)
            for path in (out/'recordings').glob('*'):path.unlink()
        (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report['status']+': .local/engine-separation/'+run_id)
    if report['status']!='PASS':raise RuntimeError('I2_NOT_VERIFIED')
    return out

if __name__=='__main__':
    try:run()
    except Exception as error:
        print('BLOCKED/FAILED: '+str(error),file=sys.stderr);raise SystemExit(1)
