"""Offline contract tests for I2. No Docker/networks/VM are used here."""
from __future__ import annotations
import base64
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = load('i2_gateway', 'spikes/isolamento/i2/gateway.py')
CONTROL = load('i2_controller', 'spikes/isolamento/i2/controller.py')
HARNESS = load('i2_harness', 'scripts/run_isolation_i2.py')


class I2GatewayTests(unittest.TestCase):
    def test_valid_bot_handshake(self):
        msg = json.dumps({'type': 'BotHandshake', 'name': 'Walls',
                          'version': '1.0', 'sessionId': 'synthetic'})
        self.assertEqual(GATE.check_bot_payload(msg, first=True), 'BotHandshake')

    def test_bot_actions_only_after_handshake(self):
        for t in ['BotIntent', 'BotReady', 'TeamMessage']:
            self.assertEqual(GATE.check_bot_payload(json.dumps({'type': t}), first=False), t)
            with self.assertRaises(GATE.FilterError):
                GATE.check_bot_payload(json.dumps({'type': t}), first=True)

    def test_control_types_never_forwarded(self):
        for kind in GATE.CONTROL_TYPES:
            for first in [True, False]:
                with self.subTest(kind=kind, first=first):
                    with self.assertRaisesRegex(GATE.FilterError, 'TYPE_DENIED'):
                        GATE.check_bot_payload(json.dumps({'type': kind}), first=first)
        self.assertTrue({'StartGame', 'StopGame', 'ControllerHandshake'} <= GATE.CONTROL_TYPES)

    def test_bots_cannot_create_second_handshake(self):
        msg = json.dumps({'type': 'BotHandshake', 'name': 'Walls',
                          'version': '1.0', 'sessionId': 'synthetic'})
        with self.assertRaisesRegex(GATE.FilterError, 'DUPLICATE_HANDSHAKE'):
            GATE.check_bot_payload(msg, first=False)

    def test_invalid_names_and_versions(self):
        for name, version in [('Other', '1.0'), ('Walls', '2.0')]:
            msg = json.dumps({'type': 'BotHandshake', 'name': name,
                              'version': version, 'sessionId': 'synthetic'})
            with self.assertRaises(GATE.FilterError):
                GATE.check_bot_payload(msg, first=True)

    def test_binary_and_oversized_rejected(self):
        with self.assertRaises(GATE.FilterError):
            GATE.check_bot_payload(b'{}', first=True)
        with self.assertRaises(GATE.FilterError):
            GATE.check_bot_payload('x' * (GATE.MAX_INBOUND + 1), first=False)

    def test_json_and_missing_type_rejected(self):
        for v in ['[]', 'null', '{', '{}', '{"type": 12}']:
            with self.subTest(value=v), self.assertRaises(GATE.FilterError):
                GATE.check_bot_payload(v, first=False)


class I2ControllerTests(unittest.TestCase):
    def test_roster_uses_real_server_addresses(self):
        roster = [{'name': 'Walls', 'version': '1.0', 'host': '10.10.0.4', 'port': 34220},
                  {'name': 'Spin Bot', 'version': '1.0', 'host': '10.10.0.5', 'port': 34221}]
        self.assertEqual(CONTROL.validate_bot_roster(roster),
                         [{'host': '10.10.0.4', 'port': 34220},
                          {'host': '10.10.0.5', 'port': 34221}])

    def test_duplicates_or_other_bot_fails(self):
        for roster in [[], [{'name': 'Walls','version': '1.0','host': 'a','port': 2}],
                       [{'name': 'Walls','version': '1.0','host': 'a','port': 2},
                        {'name': 'Walls','version': '1.0','host': 'a','port': 3}],
                       [{'name': 'Walls','version': '1.0','host': 'a','port': 2},
                        {'name': 'Spin Bot','version': '1.0','host': 'a','port': 2}]]:
            with self.subTest(roster=roster), self.assertRaises(CONTROL.ProtocolError):
                CONTROL.validate_bot_roster(roster)

    def test_game_setup_is_bounded_and_classic(self):
        data = CONTROL.setup_classic()
        self.assertEqual(data['gameType'], 'classic')
        self.assertEqual(data['numberOfRounds'], 3)
        self.assertEqual(data['maxNumberOfParticipants'], 2)
        self.assertGreater(data['turnTimeout'], 0)

    def test_results_require_official_rounds(self):
        event = {'type': 'GameEndedEventForObserver', 'numberOfRounds': 3,
                 'results': [{'name': 'Walls', 'version': '1.0', 'rank': 1,
                              'totalScore': 190, 'firstPlaces': 2},
                             {'name': 'Spin Bot', 'version': '1.0', 'rank': 2,
                              'totalScore': 120, 'firstPlaces': 1}]}
        result = CONTROL.validate_final(event, [1, 2, 3], 1, 500)
        self.assertTrue(result['completed'])
        self.assertEqual(result['source'], 'GameEndedEventForObserver')
        with self.assertRaises(CONTROL.ProtocolError):
            CONTROL.validate_final(event, [1, 2], 1, 500)
        with self.assertRaises(CONTROL.ProtocolError):
            CONTROL.validate_final(event, [1, 2, 3], 1, 0)


class I2HarnessTests(unittest.TestCase):
    def test_runtime_network_separation(self):
        game, trusted, run = 'game', 'trusted', 'a'*24
        wanted = {'referee': {trusted}, 'gateway': {game,trusted},
                  'controller': {trusted}, 'Walls': {game}, 'SpinBot': {game}, 'probe': {game}}
        infos={}
        for name, net in wanted.items():
            infos[name] = {'Config': {'Labels': {HARNESS.LABEL: run}},
                'NetworkSettings': {'Networks': {x:{} for x in net}},
                'HostConfig': {'PortBindings':{},'PublishAllPorts':False,
                               'Binds':None,'Mounts':None,'Privileged':False,
                               'ReadonlyRootfs':True,'NetworkMode':game if game in net else trusted,
                               'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],
                               'Memory': 64*1024**2,'NanoCpus':500_000_000,'PidsLimit':16}}
        checks=HARNESS.enforce_networks(infos,game,trusted,run)
        self.assertEqual(len(checks),6)
        self.assertTrue(all(all(v.values()) for v in checks.values()))
        infos['Walls']['NetworkSettings']['Networks'][trusted] = {}
        with self.assertRaisesRegex(RuntimeError,'ROLE_OR_CONTAINER_POLICY_INVALID'):
            HARNESS.enforce_networks(infos,game,trusted,run)

    def test_battle_artifact_requires_real_events(self):
        rows=[{'name':'Walls','version':'1.0','rank':1,'totalScore':190,'firstPlaces':2},
              {'name':'Spin Bot','version':'1.0','rank':2,'totalScore':120,'firstPlaces':1}]
        result={'source':'GameEndedEventForObserver','engine_version':'1.4.0',
                'completed':True,'numberOfRounds':3,'observedRoundEnds':[1,2,3],
                'results': rows}
        events=[{'type':'GameStartedEventForObserver','participants':[
            {'name':'Walls','version':'1.0'},{'name':'Spin Bot','version':'1.0'}]}]
        events += [{'type':'TickEventForObserver'}]
        events += [{'type':'RoundEndedEventForObserver','roundNumber':i} for i in (1,2,3)]
        events += [{'type':'GameEndedEventForObserver','numberOfRounds':3,'results':rows}]
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            replay=gzip.compress(''.join(json.dumps(e)+'\n' for e in events).encode())
            stream=b''.join(b'ROBOCOPA_I2_ARTIFACT '+name+b' '+base64.b64encode(payload)+b'\n'
                            for name,payload in ((b'results.json',json.dumps(result).encode()),
                                                 (b'reference.battle.gz',replay)))
            data,digest=HARNESS.decode_artifacts(stream,folder)
            self.assertEqual(data['results'][0]['totalScore'],190)
            self.assertEqual(len(digest),64)
            with self.assertRaises(ValueError):
                HARNESS.decode_artifacts(b'ROBOCOPA_I2_ARTIFACT other.json AAA=\n',folder)


if __name__ == '__main__':
    unittest.main()
