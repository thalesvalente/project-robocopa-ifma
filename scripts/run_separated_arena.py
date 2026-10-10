#!/usr/bin/env python3
"""I2 reference experiments: owned disposable GitHub CI only, not operator host.

ACLs are installed only in verified child namespaces. No host mounts, published
ports, student code or Docker metadata credentials. Cleanup fails closed.
"""
from __future__ import annotations
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,os,platform,re,secrets,shlex,socket,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.worker_agent.bounded import capture,ProcessBoundError
from services.worker_agent.policy import require_disposable_ci,PolicyError
from services.worker_agent.arena_policy import ArenaPolicy,firewall,verify_namespace_target,LABEL
from services.worker_agent.arena_evidence import (validate_replay,validate_batch,
    validate_battle,require_checks,POLICY_CHECKS,PROBE_CHECKS)

ROLES=('referee','walls','spin')

def command(args,*,data=None,timeout=25,limit=1024**2,check=True):
    result=capture(args,timeout=timeout,max_bytes=limit,input_bytes=data,cwd=ROOT)
    if check and result.returncode:
        if args[0]=='sudo':
            detail=result.output.decode('utf-8',errors='replace')[:400]
            print('SUPERVISOR_FAILURE '+detail,file=sys.stderr,flush=True)
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
        for line in expected:command(prefix+[tool,'-C',*shlex.split(line)[1:]])
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

def build_images(out,images=None,tags=None):
    images={} if images is None else images
    tags={} if tags is None else tags
    unique=uuid.uuid4().hex[:12]
    for role in ROLES:
        tag=f'robocopa-i2-{unique}:{role}'
        if docker('image','ls','-q','--filter','reference='+tag).output.strip():
            raise PolicyError('BUILD_TAG_ALREADY_EXISTS')
        tags[role]=tag
        result=docker('build','-f','spikes/isolamento/arena/Dockerfile','--target',role,
                      '-t',tag,'.',timeout=600,limit=4*1024**2,check=False)
        (out/f'build-{role}.log').write_bytes(result.output)
        if result.returncode:raise RuntimeError('BUILD_FAILED_'+role)
        images[role]=docker('image','inspect','--format','{{.Id}}',tag).output.decode().strip()
    return images,tags

def cleanup_images(tags,images):
    clean=True
    for role,tag in tags.items():
        try:
            if role not in ROLES or not re.fullmatch(r'robocopa-i2-[0-9a-f]{12}:'+role,tag):
                raise PolicyError('IMAGE_TAG_OWNERSHIP')
            present=docker('image','ls','-q','--filter','reference='+tag).output.strip()
            if not present:continue
            current=docker('image','inspect','--format','{{.Id}}',tag)
            if role in images and current.output.decode().strip()!=images[role]:
                raise PolicyError('IMAGE_CONTENT_CHANGED')
            docker('image','rm',tag,timeout=30)
            if docker('image','ls','-q','--filter','reference='+tag).output.strip():clean=False
        except Exception:clean=False
    return clean

class ExpectedAbort(RuntimeError):
    pass

def one_battle(images,out,*,abort_at=None):
    if abort_at not in (None,'after_containers','after_ready'):
        raise ValueError('ABORT_STAGE_NOT_ALLOWED')
    run_id=secrets.token_hex(12)
    network='rc-arena-net-'+run_id
    names={role:'rc-isolation-'+secrets.token_hex(12) for role in ROLES}
    created=[];bridge_created=False
    admin=secrets.token_urlsafe(32);engine_bot=secrets.token_urlsafe(32)
    tokens={role:secrets.token_urlsafe(32) for role in ('walls','spin','probe')}
    secret_values=[admin,engine_bot,*tokens.values()]
    report={'schema_version':2,'run_id':run_id,'status':'FAILED','host_vm_tested':False,'student_submission_enabled':False}
    pool=ThreadPoolExecutor(max_workers=3)
    tasks=[];host_canary=None
    try:
        docker('network','create','--driver','bridge','--internal','--label',LABEL+'='+run_id,network)
        bridge_created=True
        network_info=json.loads(docker('network','inspect',network).output)[0]
        if (network_info.get('Internal') is not True or network_info.get('EnableIPv6') is not False
                or network_info.get('Driver')!='bridge' or network_info.get('Labels',{}).get(LABEL)!=run_id):
            raise PolicyError('NETWORK_NOT_INTERNAL_OWNED')
        gateway_ip=network_info['IPAM']['Config'][0]['Gateway']
        report['policy']={}
        for role in ROLES:
            args=ArenaPolicy(role).create_args(names[role],images[role],run_id,network)
            docker(*args);created.append(names[role])
            report['policy'][role]=ArenaPolicy(role).verify(info(names[role]),images[role],run_id,network)
            docker('start',names[role])
        if abort_at=='after_containers':raise ExpectedAbort(abort_at)
        for role in ROLES:
            report['policy'][role]=ArenaPolicy(role).verify(info(names[role]),images[role],run_id,network)
            require_checks(report['policy'][role],POLICY_CHECKS)
        effective_network=json.loads(docker('network','inspect',network).output)[0]
        if set(effective_network.get('Containers',{}))!={info(name)['Id'] for name in names.values()}:
            raise PolicyError('NETWORK_ENDPOINT_SET')
        ips={role:info(names[role])['NetworkSettings']['Networks'][network]['IPAddress'] for role in ROLES}
        before_host_filter=host_filter()
        report['firewall']={role:install_firewall(names[role],run_id,role,ips['referee'],[ips['walls'],ips['spin']]) for role in ROLES}
        report['host_rules_unchanged_during_acl_setup']=host_filter()==before_host_filter
        if not report['host_rules_unchanged_during_acl_setup']:raise PolicyError('HOST_RULES_CHANGED')
        report['namespace_ids']={role:{ns:namespace(info(names[role])['State']['Pid'],ns)
                                      for ns in ('pid','net','mnt')} for role in ROLES}
        report['host_namespace_ids']={ns:os.readlink('/proc/self/ns/'+ns) for ns in ('pid','net','mnt')}
        for ns in ('pid','net','mnt'):
            ids={report['namespace_ids'][role][ns] for role in ROLES}|{report['host_namespace_ids'][ns]}
            if len(ids)!=4:raise PolicyError('SHARED_EXECUTION_NAMESPACE')
        host_canary=socket.socket();host_canary.bind((gateway_ip,0));host_canary.listen(8)
        host_port=host_canary.getsockname()[1]
        with socket.create_connection((gateway_ip,host_port),timeout=1):pass
        for role in ('walls','spin'):
            docker('exec','-d',names[role],'python','/app/role.py','canary')
            wait_file(names[role],'/tmp/canary-ready')
            docker('exec',names[role],'python','-c',
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
        if abort_at=='after_ready':raise ExpectedAbort(abort_at)
        report['network_and_protocol_probes']={}
        report['bot_output_acl_reject_packets']={}
        for role,peer in (('walls','spin'),('spin','walls')):
            probe=role_exec(names[role],'probe',{'url':f"ws://{ips['referee']}:7654",
               'referee_ip':ips['referee'],'host_gateway':gateway_ip,'host_port':host_port,
               'peer_ip':ips[peer],'probe_token':tokens['probe']},timeout=30)
            if any(s.encode() in probe.output for s in secret_values):raise ValueError('SECRET_IN_PROBE')
            if probe.returncode:
                (out/(role+'-probe-failure.log')).write_bytes(probe.output)
                raise RuntimeError('NEGATIVE_PROBES_FAILED')
            evidence=strict_json(probe.output)
            require_checks(evidence.get('checks'),PROBE_CHECKS)
            report['network_and_protocol_probes'][role]=evidence
            report['bot_output_acl_reject_packets'][role]=rejected_packets(names[role],run_id)
        report['positive_host_peer_canaries']=True
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
    except ExpectedAbort as error:
        report['status']='EXPECTED_ABORT';report['abort_injected']=str(error)
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
        try:
            report['remaining_owned_containers']=bool(docker('ps','-aq','--filter','label='+LABEL+'='+run_id).output.strip())
            report['remaining_owned_networks']=bool(docker('network','ls','-q','--filter','label='+LABEL+'='+run_id).output.strip())
        except Exception:
            clean=False;report['cleanup_completed']=False
            report['remaining_owned_containers']=report['remaining_owned_networks']=None
        if not clean or report['remaining_owned_containers'] or report['remaining_owned_networks']:report['status']='FAILED'
        raw=json.dumps(report,indent=2).encode()
        if any(s.encode() in raw for s in secret_values):raise ValueError('SECRET_IN_REPORT')
        (out/'report.json').write_bytes(raw)
    if report['status'] not in ('PASS','EXPECTED_ABORT'):raise RuntimeError('CLEANUP_NOT_CONFIRMED')
    if abort_at and report.get('abort_injected')!=abort_at:raise RuntimeError('ABORT_NOT_REACHED')
    if not abort_at:validate_battle(out)
    return report

def main():
    require_disposable_ci(dict(os.environ),platform.system(),platform.release())
    engine=json.loads(docker('info','--format','{{json .}}').output)
    if engine.get('OSType')!='linux' or 'desktop' in str(engine.get('OperatingSystem','')).lower():
        raise PolicyError('DESKTOP_NOT_ALLOWED')
    root=ROOT/'.local/security-i2'
    if (ROOT/'.local').is_symlink() or root.is_symlink():raise ValueError('EVIDENCE_SYMLINK')
    out=root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    images={};tags={}
    batch={'schema_version':2,'status':'FAILED','host_vm_tested':False,
           'student_submission_enabled':False,'battles':[],'abort_checks':[],
           'image_cleanup_completed':False}
    try:
        build_images(out,images,tags)
        for index in (1,2):
            name=f'battle-{index}';folder=out/name;folder.mkdir()
            report=one_battle(images,folder)
            batch['battles'].append(name)
            print('PASS: separated reference battle',index,'rounds',report['replay']['round_ends'],flush=True)
        for checkpoint in ('after_containers','after_ready'):
            name='abort-'+checkpoint;folder=out/name;folder.mkdir()
            one_battle(images,folder,abort_at=checkpoint)
            batch['abort_checks'].append(name)
            print('PASS: fixed abort and owned cleanup',checkpoint,flush=True)
        batch['status']='PASS'
    finally:
        batch['image_cleanup_completed']=cleanup_images(tags,images)
        if not batch['image_cleanup_completed']:batch['status']='FAILED'
        batch['images']=images
        revision=command(['git','rev-parse','HEAD'],check=False)
        batch['project_commit']=revision.output.decode().strip() if revision.returncode==0 else 'unavailable'
        (out/'batch.json').write_text(json.dumps(batch,indent=2)+'\n',encoding='utf-8')
    validate_batch(out)
    print('PASS: .local/security-i2/'+out.name,flush=True)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,ProcessBoundError) as error:
        print('BLOCKED/FAIL I2:',str(error),file=sys.stderr)
        raise SystemExit(1)
