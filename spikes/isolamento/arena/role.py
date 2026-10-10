"""Fixed I2 actions inside role-specific containers, credentials only from stdin."""
from __future__ import annotations
import base64,gzip,hashlib,io,json,os,secrets,socket,subprocess,sys,time
from pathlib import Path
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed
from gateway import BotGateway,QUIET
from arena_protocol import decode

RECORD_TYPES={'GameStartedEventForObserver','RoundStartedEvent','RoundEndedEventForObserver',
              'TickEventForObserver','GameEndedEventForObserver','GameAbortedEvent'}

def message(sock,timeout=10):
    return decode(sock.recv(timeout=timeout),limit=2*1024**2)

def client(url):
    return connect(url,open_timeout=3,close_timeout=1,compression=None,
                   max_size=2*1024**2,max_queue=16,proxy=None,logger=QUIET)

def wait_for(sock,kind,timeout=5):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        msg=message(sock,max(.01,until-time.monotonic()))
        if msg['type']==kind:return msg
    raise RuntimeError('EXPECTED_EVENT_MISSING')

def auth(url,secret,kind='ControllerHandshake'):
    sock=client(url)
    greeting=message(sock)
    if greeting['type']!='ServerHandshake' or greeting.get('version')!='1.4.0':
        sock.close();raise RuntimeError('ENGINE_VERSION_MISMATCH')
    sock.send(json.dumps({'type':kind,'sessionId':greeting['sessionId'],
                         'name':'RoboCopa I2','version':'0.1','secret':secret}))
    wait_for(sock,'BotListUpdate')
    return sock

def export(name,payload):
    print('RC_I2_ARTIFACT '+name+' '+base64.b64encode(payload).decode('ascii'),flush=True)

def referee(cfg):
    admin,engine_bot=cfg['admin'],cfg['engine_bot']
    (Path('/tmp')/'referee-canary').write_text('synthetic-referee-only')
    (Path('/tmp')/'control-secret').write_text(admin)
    identities={entry['token']:(entry['name'],'1.0') for entry in cfg['identities']}
    gateway=BotGateway(identities,engine_bot)
    process=subprocess.Popen(['java','-jar','/opt/engine/server.jar','--port','7655',
           '--controller-secrets',admin,'--bot-secrets',engine_bot,'--tps','-1',
           '--no-debug-mode','--no-breakpoint-mode'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ctrl=None
    stage='engine_start'
    try:
        end=time.monotonic()+20
        while time.monotonic()<end:
            try:ctrl=auth('ws://127.0.0.1:7655',admin);break
            except (OSError,ConnectionClosed,TimeoutError):time.sleep(.1)
        if ctrl is None:raise RuntimeError('ENGINE_NOT_READY')
        # Benign, owned-environment diagnostic: only TPS before any battle.
        raw_effect=False
        with client('ws://127.0.0.1:7655') as diagnostic:
            message(diagnostic)
            diagnostic.send(json.dumps({'type':'ChangeTps','tps':17}))
            try:raw_effect=wait_for(ctrl,'TpsChangedEvent',2).get('tps')==17
            except TimeoutError:pass
        ctrl.send(json.dumps({'type':'ChangeTps','tps':-1}));wait_for(ctrl,'TpsChangedEvent')
        upstream_negatives={}
        for kind in ('ControllerHandshake','ObserverHandshake'):
            with client('ws://127.0.0.1:7655') as invalid:
                greeting=message(invalid)
                invalid.send(json.dumps({'type':kind,'sessionId':greeting['sessionId'],
                    'name':'I2 invalid','version':'1.0','secret':engine_bot}))
                try:invalid.recv(timeout=2);denied=False
                except ConnectionClosed as e:denied=e.rcvd is not None and e.rcvd.code==1008
                upstream_negatives[kind]=denied
        if not all(upstream_negatives.values()):raise RuntimeError('ROLE_SECRET_NEGATIVE_FAILED')
        stage='gateway_ready'
        gateway.start()
        Path('/tmp/ready').touch()
        # Orchestrator performs negative tests then authorizes this known reference battle.
        until=time.monotonic()+90
        while not Path('/tmp/start').exists():
            if time.monotonic()>until:raise RuntimeError('START_SIGNAL_TIMEOUT')
            time.sleep(.05)
        # All blocked gateway messages were TPS=23; verify none reached the engine.
        blocked_control_unchanged=True
        stage='await_reference_bots'
        bots=[];until=time.monotonic()+45
        while time.monotonic()<until:
            event=message(ctrl,max(.1,until-time.monotonic()))
            if event['type']=='TpsChangedEvent' and event.get('tps')==23:
                blocked_control_unchanged=False
            if event['type']=='BotListUpdate':
                bots=[b for b in event['bots'] if b.get('name') in {'Walls','Spin Bot'}]
                if len(bots)==2:break
        if not blocked_control_unchanged:raise RuntimeError('CONTROL_MESSAGE_CROSSED_GATEWAY')
        if len(bots)!=2:raise RuntimeError('TWO_REFERENCE_BOTS_REQUIRED')
        if any(b.get('version')!='1.0' for b in bots):raise RuntimeError('BOT_VERSION_MISMATCH')
        setup={'gameType':'classic','arenaWidth':800,'arenaHeight':600,
            'minNumberOfParticipants':2,'numberOfRounds':3,'gunCoolingRate':.1,
            'maxInactivityTurns':450,'turnTimeout':30000,'readyTimeout':10000000,
            'defaultTurnsPerSecond':-1}
        for field in ('ArenaWidth','ArenaHeight','MinNumberOfParticipants','MaxNumberOfParticipants',
                      'NumberOfRounds','GunCoolingRate','MaxInactivityTurns','TurnTimeout','ReadyTimeout'):
            setup['is'+field+'Locked']=False
        stage='start_game'
        ctrl.send(json.dumps({'type':'StartGame','gameSetup':setup,'botAddresses':[
            {'host':b['host'],'port':b['port']} for b in bots]}))
        stage='observe_game'
        events=[];rounds=[];ticks=0;start=time.monotonic();total_bytes=0
        final=None
        while time.monotonic()-start<120:
            raw=ctrl.recv(timeout=15)
            event=decode(raw,limit=2*1024**2)
            kind=event['type']
            if kind in RECORD_TYPES:
                line=(raw+'\n').encode();total_bytes+=len(line)
                if total_bytes>48*1024**2:raise RuntimeError('REPLAY_BUDGET')
                events.append(line)
            if kind=='RoundEndedEventForObserver':rounds.append(event['roundNumber'])
            if kind=='TickEventForObserver':ticks+=1
            if kind=='GameAbortedEvent':raise RuntimeError('BATTLE_ABORTED')
            if kind=='GameEndedEventForObserver':final=event;break
        if final is None or final.get('numberOfRounds')!=3 or rounds!=[1,2,3] or ticks<1:
            raise RuntimeError('INCOMPLETE_BATTLE')
        rows=final['results']
        if len(rows)!=2 or {r['name'] for r in rows}!={'Walls','Spin Bot'}:
            raise RuntimeError('RESULT_IDENTITIES')
        results={'schema_version':1,'engine_version':'1.4.0',
            'source':'GameEndedEventForObserver','completed':True,'numberOfRounds':3,
            'roundEnds':rounds,'ticks':ticks,'duration_ms':round((time.monotonic()-start)*1000),
            'results':rows}
        raw_replay=b''.join(events)
        if any(v.encode() in raw_replay for v in [admin,engine_bot,*identities]):
            raise RuntimeError('SECRET_IN_REPLAY')
        payload=gzip.compress(raw_replay,mtime=0)
        report={'upstream_role_secrets_reject_bot_secret':upstream_negatives,
            'raw_engine_control_without_handshake_observed':raw_effect,
            'gateway_control_did_not_change_engine':blocked_control_unchanged,
            'gateway':gateway.report(),'server_artifact':json.loads(Path('/app/build-manifest.json').read_text()),
            'pid_namespace':os.readlink('/proc/self/ns/pid'),'network_namespace':os.readlink('/proc/self/ns/net'),
            'replay_sha256':hashlib.sha256(payload).hexdigest(),
            'replay_uncompressed_bytes':len(raw_replay)}
        for name,data in [('results.json',json.dumps(results).encode()),
                          ('referee-report.json',json.dumps(report).encode()),('recordings.battle.gz',payload)]:
            if any(v.encode() in data for v in [admin,engine_bot,*identities]):
                raise RuntimeError('SECRET_IN_EVIDENCE')
            export(name,data)
        stage='completed'
    finally:
        # Fixed stage names and enumerated counters only; never log a frame/token.
        print('I2_DIAGNOSTIC '+json.dumps({'stage':stage,'gateway':gateway.report()}),flush=True)
        gateway.close()
        if ctrl:ctrl.close()
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)

def bot(cfg):
    role=cfg['role'];name={'walls':'Walls','spin':'SpinBot'}[role]
    env=os.environ.copy();env.update(SERVER_URL=cfg['url'],SERVER_SECRET=cfg['token'])
    os.chdir('/opt/bot')
    os.execvpe('java',['java','-cp','lib/*:.',name],env)

def probe(cfg):
    url=cfg['url'];checks={}
    ref=cfg['referee_ip']
    # Positive TCP control: gateway must be reachable.
    with socket.create_connection((ref,7654),timeout=2):checks['gateway_tcp_reachable']=True
    targets={'raw_engine_denied':(ref,7655),'wrong_port_denied':(ref,7653),
             'host_canary_denied':(cfg['host_gateway'],cfg['host_port']),
             'peer_canary_denied':(cfg['peer_ip'],8766),'testnet_denied':('192.0.2.1',80),
             'docker_dns_denied':('127.0.0.11',53)}
    errors={}
    for label,target in targets.items():
        sock=socket.socket();sock.settimeout(1)
        try:code=sock.connect_ex(target)
        finally:sock.close()
        checks[label]=code!=0;errors[label]=code
    # UDP DNS denial is checked as well; .11 is deliberately not in loopback ACL.
    udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);udp.settimeout(1)
    try:
        udp.connect(('127.0.0.11',53));udp.send(b'\0'*12);udp.recv(16)
        checks['udp_dns_denied']=False
    except OSError:checks['udp_dns_denied']=True
    finally:udp.close()
    v6=socket.socket(socket.AF_INET6);v6.settimeout(1)
    try:checks['ipv6_denied']=v6.connect_ex(('2001:db8::1',80))!=0
    finally:v6.close()
    checks['referee_file_invisible']=not Path('/tmp/referee-canary').exists()
    checks['controller_file_invisible']=not Path('/tmp/control-secret').exists()
    checks['no_docker_socket']=not Path('/var/run/docker.sock').exists()
    checks['no_env_secret']=not any('SECRET' in key or 'TOKEN' in key for key in os.environ)
    cases={
      'controller_before_handshake':({'type':'ControllerHandshake'},False),
      'observer_before_handshake':({'type':'ObserverHandshake'},False),
      'wrong_token':({'type':'BotHandshake','name':'I2Probe','version':'1.0','authors':['test'],'secret':'wrong'},False),
      'control_after_bot_handshake':({'type':'ChangeTps','tps':23},True),
      'controller_after_bot_handshake':({'type':'ControllerHandshake'},True),
      'repeat_bot_handshake':({'type':'BotHandshake'},True),
    }
    for label,(payload,authenticate) in cases.items():
        with client(url) as ws:
            greeting=message(ws)
            if authenticate:
                ws.send(json.dumps({'type':'BotHandshake','sessionId':greeting['sessionId'],
                    'name':'I2Probe','version':'1.0','authors':['Test'],'secret':cfg['probe_token']}))
                ws.send('{"type":"BotReady"}')
            payload=dict(payload);payload.setdefault('sessionId',greeting['sessionId'])
            ws.send(json.dumps(payload))
            try:ws.recv(timeout=3);checks[label]=False
            except ConnectionClosed as e:checks[label]=e.rcvd is not None and e.rcvd.code==1008
        time.sleep(.1)
    report={'checks':checks,'socket_error_codes':errors,
       'pid_namespace':os.readlink('/proc/self/ns/pid'),
       'network_namespace':os.readlink('/proc/self/ns/net')}
    print(json.dumps(report),flush=True)
    if not all(checks.values()):raise RuntimeError('PROBE_FAILURE')

def canary():
    with socket.socket() as server:
        server.bind(('0.0.0.0',8766));server.listen(2)
        Path('/tmp/canary-ready').touch()
        while True:
            conn,_=server.accept()
            with conn:conn.sendall(b'I2_SYNTHETIC_CANARY')

def main():
    mode=sys.argv[1]
    if mode=='canary':canary();return
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536:raise RuntimeError('INPUT_LIMIT')
    cfg=json.loads(raw)
    if mode=='referee':referee(cfg)
    elif mode=='bot':bot(cfg)
    elif mode=='probe':probe(cfg)
    else:raise RuntimeError('MODE_DENIED')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        # No raw upstream frames, tokens, tracebacks or input echoed.
        reason=str(exc) if type(exc) is RuntimeError and str(exc).replace('_','').isupper() else type(exc).__name__
        print('I2_FAILURE '+reason,flush=True)
        raise SystemExit(1)
