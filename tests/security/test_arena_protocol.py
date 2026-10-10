import json
import unittest
from services.worker_agent import arena_protocol as p

TOKEN='a'*40
IDENTITIES={TOKEN:('Walls','1.0')}

def hs(**kw):
    data={'type':'BotHandshake','sessionId':'session','name':'Walls','version':'1.0',
          'authors':['Test'],'secret':TOKEN}
    data.update(kw)
    return json.dumps(data)

class ArenaProtocolTests(unittest.TestCase):
    def test_handshake_rewrites_secret_and_metadata(self):
        name,d=p.handshake(hs(),session='session',identities=IDENTITIES,upstream_secret='engine')
        self.assertEqual(name,'Walls'); self.assertEqual(d['secret'],'engine')
        self.assertNotIn(TOKEN,json.dumps(d))
    def test_bad_credentials(self):
        for value in ('bad','\u00e9',0,None,'x'*129):
            with self.subTest(value=value),self.assertRaises(p.ProtocolDenied):
                p.handshake(hs(secret=value),session='session',identities=IDENTITIES,upstream_secret='engine')
    def test_identity_and_session(self):
        for change in ({'name':'Spin Bot'},{'version':'2'},{'sessionId':'else'},{'teamId':1}):
            with self.subTest(change=change),self.assertRaises(p.ProtocolDenied):
                p.handshake(hs(**change),session='session',identities=IDENTITIES,upstream_secret='engine')
    def test_roles_not_bot(self):
        for role in ('ControllerHandshake','ObserverHandshake','StopGame'):
            with self.subTest(role=role),self.assertRaises(p.ProtocolDenied):
                p.handshake(hs(type=role),session='session',identities=IDENTITIES,upstream_secret='engine')
    def test_all_control_messages_denied(self):
        for kind in ('ChangeTps','StartGame','StopGame','PauseGame','ResumeGame','NextTurn',
                     'BotPolicyUpdate','EnableDebugMode','DisableDebugMode','BotHandshake',
                     'ControllerHandshake','ObserverHandshake','Unknown'):
            with self.subTest(kind=kind),self.assertRaises(p.ProtocolDenied):p.intent(json.dumps({'type':kind}))
    def test_valid_ready(self):self.assertEqual(p.intent('{"type":"BotReady"}'),{'type':'BotReady'})
    def test_valid_intent(self):
        data={'type':'BotIntent','turnRate':8,'targetSpeed':6,'firepower':2,'bodyColor':'#FFFF00','rescan':True}
        self.assertEqual(p.intent(json.dumps(data)),data)
    def test_ready_extra_fields(self):
        with self.assertRaises(p.ProtocolDenied):p.intent('{"type":"BotReady","command":"x"}')
    def test_bad_intent_values(self):
        for key,value in [('targetSpeed',True),('targetSpeed',1e20),('targetSpeed',10**500),('rescan',1),
                          ('bodyColor','red'),('stdOut','x'*2049),('unknown',3),('debugGraphics','x')]:
            with self.subTest(key=key),self.assertRaises(p.ProtocolDenied):
                p.intent(json.dumps({'type':'BotIntent',key:value}))
    def test_invalid_json(self):
        for raw in ('[]','null','{}','{"type":"BotIntent","x":NaN}',
                    '{"type":"BotReady","type":"StopGame"}', b'{"type":"BotReady"}',
                    'x'*16385,'[ '*1000, '{"type":"BotIntent","targetSpeed":Infinity}'):
            with self.subTest(raw=str(raw)[:25]),self.assertRaises(p.ProtocolDenied):p.decode(raw)
    def test_errors_do_not_echo_input(self):
        with self.assertRaises(p.ProtocolDenied) as e:
            p.handshake(hs(secret='private-token'),session='session',identities=IDENTITIES,upstream_secret='engine')
        self.assertNotIn('private-token',str(e.exception))
    def test_official_sdk_false_droid_metadata(self):
        name, normalized=p.handshake(hs(isDroid=False),session='session',identities=IDENTITIES,upstream_secret='engine')
        self.assertEqual(name,'Walls')
        self.assertNotIn('isDroid',normalized)
    def test_non_reference_droid_metadata_rejected(self):
        for value in (True,1,'false',None):
            with self.subTest(value=value),self.assertRaises(p.ProtocolDenied):
                p.handshake(hs(isDroid=value),session='session',identities=IDENTITIES,upstream_secret='engine')
    def test_empty_sdk_team_array_normalized(self):
        self.assertEqual(p.intent('{"type":"BotIntent","teamMessages":[],"targetSpeed":6}'),{'type':'BotIntent','targetSpeed':6})
    def test_actual_team_messages_still_denied(self):
        for value in (None,{},'', [{'message':'anything'}]):
            with self.subTest(value=value),self.assertRaises(p.ProtocolDenied):
                p.intent(json.dumps({'type':'BotIntent','teamMessages':value}))
