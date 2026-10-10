#!/usr/bin/env python3
"""I2 real reference battles in disposable GitHub CI only, not on the operator host.

No global firewall rules, mounts, published ports, secrets in CLI or student input.
The supervisor configures ONLY owned container network namespaces before payloads.
"""
from __future__ import annotations
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import gzip,hashlib,json,os,platform,re,secrets,shlex,socket,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.worker_agent.bounded import capture,ProcessBoundError
from services.worker_agent.policy import require_disposable_ci,PolicyError
from services.worker_agent.arena_policy import ArenaPolicy,firewall,verify_namespace_target,LABEL

ROLES=('referee','walls','spin')

def command(args,*,data=None,timeout=25,limit=1024**2,check=True):
    result=capture(args,timeout=timeout,max_bytes=limit,input_bytes=data,cwd=ROOT)
    if check and result.returncode:
        # Only fixed supervisor utility failures: no credentials or stdin content.
        if args[0]=='sudo':
            detail=result.output.decode('utf-8',errors='replace')[:400]
            print('SUPERVISOR_FAILURE '+detail, file=sys.stderr, flush=True)
        raise RuntimeError('COMMAND_FAILED:'+args[0]+':'+str(result.returncode))
    return result

def docker(*args,data=None,timeout=25,limit=1024**2,check=True):
    return command(['docker',*args],data=data,timeout=timeout,limit=limit,check=check)

def info(name):return json.loads(docker('inspect',name).output)[0]

def files_from_stream(raw: bytes,secrets_list:list[str]) -> dict[str,bytes]:
    if any(secret.encode() in raw for secret in secrets_list):raise ValueError('SECRET_IN_OUTPUT')
    files={}
    for line in raw.splitlines():
        if not line.startswith(b'RC_I2_ARTIFACT '):continue
        _,name,data=line.split(b' ',2)
        name=name.decode('ascii')
        if name not in {'results.json','referee-report.json','recordings.battle.gz'} or name in files:
            raise ValueError('ARTIFACT_NAME_OR_DUPLICATE')
        decoded=base64.b64decode(data,validate=True)
        if len(decoded)>16*1024**2:raise ValueError('ARTIFACT_LIMIT')
        if any(secret.encode() in decoded for secret in secrets_list):raise ValueError('SECRET_IN_ARTIFACT')
        files[name]=decoded
    if set(files)!={'results.json','referee-report.json','recordings.battle.gz'}:
        raise ValueError('ARTIFACT_INCOMPLETE')
    return files

def strict_json(raw):
    def pairs(items):
        value={}
        for k,v in items:
            if k in value:raise ValueError('DUPLICATE_JSON_KEY')
            value[k]=v
        return value
    return json.loads(raw,object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NON_FINITE_JSON')))

def validate_replay(files:dict[str,bytes],secrets_list=()):
    result=strict_json(files['results.json'])
    if result.get('source')!='GameEndedEventForObserver' or result.get('engine_version')!='1.4.0' or result.get('completed') is not True:
        raise ValueError('RESULT_SOURCE')
    if result.get('numberOfRounds')!=3:raise ValueError('RESULT_ROUNDS')
    rows=result.get('results',[])
    if len(rows)!=2 or {r.get('name') for r in rows}!={'Walls','Spin Bot'}:
        raise ValueError('RESULT_BOTS')
    for row in rows:
        if row.get('version')!='1.0' or type(row.get('totalScore')) is not int or row['totalScore']<0:
            raise ValueError('RESULT_FIELDS')
    import io
    with gzip.GzipFile(fileobj=io.BytesIO(files['recordings.battle.gz'])) as stream:
        raw=stream.read(48*1024**2+1)
    if len(raw)>48*1024**2:raise ValueError('REPLAY_LIMIT')
    if any(secret.encode() in raw for secret in secrets_list):raise ValueError('SECRET_IN_REPLAY')
    rounds=[];finals=[];ticks=0;started=0
    for line in raw.splitlines():
        item=strict_json(line)
        if item['type']=='GameStartedEventForObserver':started+=1
        if item['type']=='RoundEndedEventForObserver':rounds.append(item['roundNumber'])
        if item['type']=='TickEventForObserver':ticks+=1
        if item['type']=='GameEndedEventForObserver':finals.append(item)
        if item['type']=='GameAbortedEvent':raise ValueError('ABORTED_REPLAY')
    if started!=1 or rounds!=[1,2,3] or len(finals)!=1 or ticks<1:
        raise ValueError('REPLAY_COMPLETENESS')
    if finals[0]['results']!=rows or finals[0]['numberOfRounds']!=3 or result.get('ticks')!=ticks:
        raise ValueError('RESULT_REPLAY_MISMATCH')
    return {'ticks':ticks,'round_ends':rounds,'sha256':hashlib.sha256(files['recordings.battle.gz']).hexdigest()}

def namespace(pid,kind):
    if type(pid) is not int or pid<=1 or kind not in ('pid','net','mnt'):
        raise PolicyError('NAMESPACE_ARGUMENT')
    return command(['sudo','-n','readlink',f'/proc/{pid}/ns/{kind}']).output.decode().strip()

def host_filter():
    text=command(['sudo','-n','iptables-save']).output.decode()
    return '\n'.join(re.sub(r'\[\d+:\d+\]','[0:0]',line)
                     for line in text.splitlines() if line.startswith((':','-A')))

def rejected_packets(name,run_id):
    obj=info(name);pid=obj['State']['Pid']
    verify_namespace_target(obj,run_id,namespace(pid,'net'),os.readlink('/proc/self/ns/net'))
    text=command(['sudo','-n','nsenter','--target',str(pid),'--net','--','iptables-save','-c']).output.decode()
    match=re.search(r'\[(\d+):\d+\] -A OUTPUT -j REJECT',text)
    if not match or int(match[1])<1:raise PolicyError('NO_OBSERVED_FIREWALL_REJECTION')
    return int(match[1])

def install_firewall(name,run_id,role,ref_ip,bot_ips):
    current=info(name)
    host_inode=os.readlink('/proc/self/ns/net')
    pid=current['State']['Pid'];target=namespace(pid,'net')
    verify_namespace_target(current,run_id,target,host_inode)
    prefix=['sudo','-n','nsenter','--target',str(pid),'--net','--']
    entered=command(prefix+['readlink','/proc/self/ns/net']).output.decode().strip()
    if entered!=target or entered==host_inode:raise PolicyError('NAMESPACE_ENTRY_MISMATCH')
    hashes={}
    for ipv6,tool in ((False,'iptables'),(True,'ip6tables')):
        rules=firewall(role,ref_ip,bot_ips,ipv6=ipv6)
        command(prefix+[tool+'-restore','-w','3'],data=rules.encode())
        dump=command(prefix+[tool,'-S']).output.decode()
        for chain in ('INPUT','OUTPUT','FORWARD'):
            if f'-P {chain} DROP' not in dump:raise PolicyError('FIREWALL_DEFAULT_POLICY')
        expected=[line for line in rules.splitlines() if line.startswith('-A ')]
        if len([line for line in dump.splitlines() if line.startswith('-A ')])!=len(expected):
            raise PolicyError('FIREWALL_UNEXPECTED_RULE')
        for line in expected:
            command(prefix+[tool,'-C',*shlex.split(line)[1:]])
        hashes[tool]=hashlib.sha256(dump.encode()).hexdigest()
    if os.readlink('/proc/self/ns/net')!=host_inode:raise PolicyError('HOST_NAMESPACE_CHANGED')
    return {'verified':True,'netns':target,'host_netns_distinct':True,'rules_sha256':hashes}

def wait_file(name,path,timeout=25):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if docker('exec',name,'test','-f',path,timeout=3,check=False).returncode==0:return
        time.sleep(.15)
    raise RuntimeError('READY_TIMEOUT')

def role_exec(name,mode,payload,timeout=200):
    return docker('exec','-i',name,'python','-u','/app/role.py',mode,
                  data=json.dumps(payload).encode(),timeout=timeout,limit=24*1024**2,check=False)

def build_images(out):
    images={};tags={}
    unique=uuid.uuid4().hex[:12]
    for role in ROLES:
        tag=f'robocopa-i2-{unique}:{role}'
        result=docker('build','-f','spikes/isolamento/arena/Dockerfile','--target',role,
                      '-t',tag,'.',timeout=600,limit=4*1024**2,check=False)
        (out/f'build-{role}.log').write_bytes(result.output)
        if result.returncode:raise RuntimeError('BUILD_FAILED_'+role)
        images[role]=docker('image','inspect','--format','{{.Id}}',tag).output.decode().strip()
        tags[role]=tag
    return images,tags

def one_battle(images,out):
    run_id=secrets.token_hex(12)
    network='rc-arena-net-'+run_id
    names={role:'rc-isolation-'+secrets.token_hex(12) for role in ROLES}
    created=[];bridge_created=False
    admin=secrets.token_urlsafe(32);engine_bot=secrets.token_urlsafe(32)
    tokens={role:secrets.token_urlsafe(32) for role in ('walls','spin','probe')}
    secret_values=[admin,engine_bot,*tokens.values()]
    report={'run_id':run_id,'status':'FAILED','host_vm_tested':False,'student_submission_enabled':False}
    pool=ThreadPoolExecutor(max_workers=3)
    tasks=[]
    host_canary=None
    try:
        docker('network','create','--driver','bridge','--internal','--label',LABEL+'='+run_id,network)
        bridge_created=True
        network_info=json.loads(docker('network','inspect',network).output)[0]
        if network_info.get('Internal') is not True or network_info.get('Labels',{}).get(LABEL)!=run_id:
            raise PolicyError('NETWORK_NOT_INTERNAL_OWNED')
        gateway_ip=network_info['IPAM']['Config'][0]['Gateway']
        report['policy']={}
        for role in ROLES:
            args=ArenaPolicy(role).create_args(names[role],images[role],run_id,network)
            docker(*args);created.append(names[role])
            report['policy'][role]=ArenaPolicy(role).verify(info(names[role]),images[role],run_id,network)
            docker('start',names[role])  # only fixed idle process
        ips={role:info(names[role])['NetworkSettings']['Networks'][network]['IPAddress'] for role in ROLES}
        before_host_filter=host_filter()
        report['firewall']={role:install_firewall(names[role],run_id,role,ips['referee'],[ips['walls'],ips['spin']]) for role in ROLES}
        report['host_rules_unchanged_during_acl_setup']=host_filter()==before_host_filter
        if not report['host_rules_unchanged_during_acl_setup']:raise PolicyError('HOST_RULES_CHANGED')
        # Distinct PID/network namespaces, not just distinct names.
        report['namespace_ids']={role:{ns:namespace(info(names[role])['State']['Pid'],ns)
                                      for ns in ('pid','net','mnt')} for role in ROLES}
        for ns in ('pid','net','mnt'):
            if len({report['namespace_ids'][role][ns] for role in ROLES})!=3:
                raise PolicyError('SHARED_EXECUTION_NAMESPACE')
        # Positive canaries prove that peer/host denials aren't merely absent services.
        host_canary=socket.socket();host_canary.bind((gateway_ip,0));host_canary.listen(8)
        host_port=host_canary.getsockname()[1]
        with socket.create_connection((gateway_ip,host_port),timeout=1):pass
        docker('exec','-d',names['spin'],'python','/app/role.py','canary')
        wait_file(names['spin'],'/tmp/canary-ready')
        docker('exec',names['spin'],'python','-c',
            "import socket; s=socket.create_connection(('127.0.0.1',8766),1); assert s.recv(64)==b'I2_SYNTHETIC_CANARY'")
        ref_config={'admin':admin,'engine_bot':engine_bot,'identities':[
            {'name':'Walls','token':tokens['walls']},{'name':'Spin Bot','token':tokens['spin']},
            {'name':'I2Probe','token':tokens['probe']}]}
        ref_future=pool.submit(role_exec,names['referee'],'referee',ref_config,210);tasks.append(ref_future)
        try:wait_file(names['referee'],'/tmp/ready',timeout=30)
        except RuntimeError:
            if ref_future.done():
                output=ref_future.result().output
                if not any(s.encode() in output for s in secret_values):(out/'referee-failure.log').write_bytes(output)
            raise
        probe=role_exec(names['walls'],'probe',{'url':f"ws://{ips['referee']}:7654",
           'referee_ip':ips['referee'],'host_gateway':gateway_ip,'host_port':host_port,
           'peer_ip':ips['spin'],'probe_token':tokens['probe']},timeout=30)
        if any(s.encode() in probe.output for s in secret_values):raise ValueError('SECRET_IN_PROBE')
        # Preserve only fixed synthetic checks, never raw protocol messages or tokens.
        if probe.returncode:
            (out/'probe-failure.log').write_bytes(probe.output)
            raise RuntimeError('NEGATIVE_PROBES_FAILED')
        report['network_and_protocol_probes']=json.loads(probe.output)
        if not all(report['network_and_protocol_probes']['checks'].values()):raise RuntimeError('PROBE_CHECK_FALSE')
        report['positive_host_peer_canaries']=True
        report['bot_output_acl_reject_packets']=rejected_packets(names['walls'],run_id)
        for role in ('walls','spin'):
            tasks.append(pool.submit(role_exec,names[role],'bot',{'role':role,
              'url':f"ws://{ips['referee']}:7654",'token':tokens[role]},190))
        docker('exec',names['referee'],'touch','/tmp/start')
        ref_result=ref_future.result(timeout=215)
        if ref_result.returncode:
            if not any(s.encode() in ref_result.output for s in secret_values):(out/'referee-failure.log').write_bytes(ref_result.output)
            raise RuntimeError('REFEREE_FAILED')
        files=files_from_stream(ref_result.output,secret_values)
        report['replay']=validate_replay(files,secret_values)
        report['referee']=json.loads(files['referee-report.json'])
        if not report['referee']['gateway_control_did_not_change_engine']:raise RuntimeError('CONTROL_NOT_CONTAINED')
        for filename,payload in files.items():(out/filename).write_bytes(payload)
        report['status']='PASS'
    finally:
        if host_canary:host_canary.close()
        clean=True
        for name in reversed(created):
            try:
                if info(name).get('Config',{}).get('Labels',{}).get(LABEL)!=run_id:
                    raise PolicyError('CLEANUP_OWNERSHIP')
                docker('rm','-f',name)
            except Exception:clean=False
        if bridge_created:
            try:
                ni=json.loads(docker('network','inspect',network).output)[0]
                if ni.get('Labels',{}).get(LABEL)!=run_id:raise PolicyError('NETWORK_CLEANUP_OWNERSHIP')
                docker('network','rm',network)
            except Exception:clean=False
        pool.shutdown(wait=True,cancel_futures=True)
        report['cleanup_completed']=clean
        report['remaining_owned_containers']=bool(docker('ps','-aq','--filter','label='+LABEL+'='+run_id).output.strip())
        report['remaining_owned_networks']=bool(docker('network','ls','-q','--filter','label='+LABEL+'='+run_id).output.strip())
        if not clean or report['remaining_owned_containers'] or report['remaining_owned_networks']:report['status']='FAILED'
        raw=json.dumps(report,indent=2).encode()
        if any(s.encode() in raw for s in secret_values):raise ValueError('SECRET_IN_REPORT')
        (out/'report.json').write_bytes(raw)
    if report['status']!='PASS':raise RuntimeError('CLEANUP_NOT_CONFIRMED')
    return report

def main():
    require_disposable_ci(dict(os.environ),platform.system(),platform.release())
    engine=json.loads(docker('info','--format','{{json .}}').output)
    if engine.get('OSType')!='linux' or 'desktop' in str(engine.get('OperatingSystem','')).lower():
        raise PolicyError('DESKTOP_NOT_ALLOWED')
    root=ROOT/'.local/security-i2'
    if (ROOT/'.local').is_symlink() or root.is_symlink():raise ValueError('EVIDENCE_SYMLINK')
    out=root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    images,tags=build_images(out)
    try:
        for index in (1,2):
            folder=out/f'battle-{index}';folder.mkdir()
            report=one_battle(images,folder)
            print('PASS: separated reference battle',index,'rounds',report['replay']['round_ends'],flush=True)
        print('PASS: .local/security-i2/'+out.name,flush=True)
    finally:
        for tag in tags.values():docker('image','rm',tag,timeout=30,check=False)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,ProcessBoundError) as error:
        print('BLOCKED/FAIL I2:',str(error),file=sys.stderr)
        raise SystemExit(1)
