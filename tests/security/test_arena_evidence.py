"""Synthetic fixtures for I2 evidence validation; never game or Docker evidence."""
from copy import deepcopy
import gzip
import json
import tempfile
from pathlib import Path
import unittest
from services.worker_agent import arena_evidence as e


def fixture():
    rows = []
    for idx, name in enumerate(('Walls', 'Spin Bot'), 1):
        rows.append(dict(id=idx, name=name, version='1.0', isTeam=False, rank=idx,
                         survival=50, lastSurvivorBonus=0, bulletDamage=10,
                         bulletKillBonus=0, ramDamage=0, ramKillBonus=0,
                         totalScore=60, firstPlaces=1, secondPlaces=2, thirdPlaces=0))
    result = dict(schema_version=1, source='GameEndedEventForObserver', engine_version='1.4.0',
                  completed=True, numberOfRounds=3, roundEnds=[1, 2, 3], ticks=3,
                  duration_ms=50, results=rows)
    events = [dict(type='GameStartedEventForObserver', gameSetup={'numberOfRounds': 3},
                   participants=[dict(id=r['id'], name=r['name'], version=r['version']) for r in rows])]
    for number in (1, 2, 3):
        events.extend([dict(type='RoundStartedEvent', roundNumber=number),
                       dict(type='TickEventForObserver', roundNumber=number, turnNumber=1,
                            botStates=[dict(id=r['id'], name=r['name'], version=r['version']) for r in rows]),
                       dict(type='RoundEndedEventForObserver', roundNumber=number, turnNumber=1, results=rows)])
    events.append(dict(type='GameEndedEventForObserver', numberOfRounds=3, results=rows))
    return result, events


def payload(result, events):
    return {'results.json': json.dumps(result).encode(),
            'recordings.battle.gz': gzip.compress(b'\n'.join(json.dumps(x).encode() for x in events))}


class ArenaEvidenceTests(unittest.TestCase):
    def test_valid_full_fixture(self):
        result, events = fixture()
        self.assertEqual(e.validate_replay(payload(result, events))['round_ends'], [1, 2, 3])
    def reject(self, mutate):
        result, events = fixture();mutate(result, events)
        with self.assertRaises(e.EvidenceError):e.validate_replay(payload(result, events))
    def test_bool_score_rejected(self):self.reject(lambda r, _: r['results'][0].update(totalScore=True))
    def test_bool_id_rejected(self):self.reject(lambda r, _: r['results'][0].update(id=True))
    def test_bool_ticks_rejected(self):self.reject(lambda r, _: r.update(ticks=True))
    def test_bool_duration_rejected(self):self.reject(lambda r, _: r.update(duration_ms=True))
    def test_missing_score_component_rejected(self):self.reject(lambda r, _: r['results'][0].pop('bulletKillBonus'))
    def test_negative_component_rejected(self):self.reject(lambda r, _: r['results'][0].update(survival=-1))
    def test_duplicate_id_rejected(self):self.reject(lambda r, _: r['results'][1].update(id=1))
    def test_rank_not_one_or_two(self):self.reject(lambda r, _: r['results'][0].update(rank=0))
    def test_equal_total_score_does_not_invent_tiebreaker(self):
        r, events = fixture()
        self.assertEqual(r['results'][0]['totalScore'], r['results'][1]['totalScore'])
        e.validate_replay(payload(r, events))
    def test_unexpected_result_field_rejected(self):self.reject(lambda r, _: r['results'][0].update(command='not allowed'))
    def test_missing_round_start_rejected(self):self.reject(lambda _, events: events.pop(1))
    def test_tick_after_end_rejected(self):self.reject(lambda _, events: events.append(deepcopy(events[2])))
    def test_tick_round_mismatch_rejected(self):self.reject(lambda _, events: events[2].update(roundNumber=2))
    def test_tick_backwards_rejected(self):
        def mutate(result, events):events.insert(3, deepcopy(events[2])); result['ticks'] += 1
        self.reject(mutate)
    def test_start_identity_differs(self):self.reject(lambda _, ev: ev[0]['participants'][0].update(name='Impostor'))
    def test_tick_identity_differs(self):self.reject(lambda _, ev: ev[2]['botStates'][0].update(id=999))
    def test_aborted_replay_rejected(self):self.reject(lambda _, ev: ev.insert(3, {'type': 'GameAbortedEvent'}))
    def test_missing_final_rejected(self):self.reject(lambda _, ev: ev.pop())
    def test_duplicate_json_and_nan_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b'{"a":1e9999}'):
            with self.subTest(raw=raw), self.assertRaises(e.EvidenceError):e.object_json(raw)
    def test_invalid_json_errors_not_echoed(self):
        with self.assertRaises(e.EvidenceError) as result:e.object_json(b'{private_secret')
        self.assertNotIn('private_secret', str(result.exception))
    def test_false_or_truthy_check_rejected(self):
        for value in (False, 1, 'true', None):
            with self.subTest(value=value), self.assertRaises(e.EvidenceError):e.require_checks({'present': value}, {'present'})
    def test_missing_check_rejected(self):
        with self.assertRaises(e.EvidenceError):e.require_checks({}, {'present'})
    def test_empty_checks_do_not_vacuously_pass(self):
        with self.assertRaises(e.EvidenceError):e.require_checks({}, set())
    def test_compressed_secret_rejected(self):
        r, events = fixture();events[0]['canary'] = 'TEST_PRIVATE_SECRET'
        with self.assertRaisesRegex(e.EvidenceError, 'SECRET'):
            e.validate_replay(payload(r, events), secrets_list=['TEST_PRIVATE_SECRET'])
    def test_gzip_budget_rejected(self):
        r, events = fixture()
        with self.assertRaises(e.EvidenceError):e.validate_replay(payload(r, events), max_uncompressed=20)
    def test_symlink_file_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); (p/'target').write_bytes(b'{}')
            try: (p/'link').symlink_to(p/'target')
            except OSError: self.skipTest('symlinks unsupported by local OS')
            with self.assertRaises(e.EvidenceError): e.read_file(p/'link', 20)
    def test_oversized_file_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'file'; p.write_bytes(b'x'*21)
            with self.assertRaises(e.EvidenceError): e.read_file(p, 20)
    def test_list_name_reports_evidence_error(self):self.reject(lambda r, _: r['results'][0].update(name=[]))
    def test_list_game_setup_reports_evidence_error(self):self.reject(lambda _, ev: ev[0].update(gameSetup=[]))
    def test_bool_roundends_rejected(self):self.reject(lambda r, _: r.update(roundEnds=[True,2,3]))
    def test_bool_only_in_final_rejected(self):
        r,ev=fixture();ev[-1]['results']=deepcopy(r['results']);ev[-1]['results'][0]['id']=True
        with self.assertRaises(e.EvidenceError):e.validate_replay(payload(r,ev))

if __name__ == '__main__': unittest.main()
