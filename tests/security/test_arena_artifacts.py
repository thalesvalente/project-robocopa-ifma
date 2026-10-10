"""Synthetic artifacts only; these tests do not run the game engine or Docker."""
import base64,gzip,importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('separated_arena',ROOT/'scripts/run_separated_arena.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


def fixture():
    rows=[{'name':'Walls','version':'1.0','totalScore':50},{'name':'Spin Bot','version':'1.0','totalScore':20}]
    final={'type':'GameEndedEventForObserver','numberOfRounds':3,'results':rows}
    events=[{'type':'GameStartedEventForObserver'}]
    for r in (1,2,3):
        events += [{'type':'TickEventForObserver','roundNumber':r},
                   {'type':'RoundEndedEventForObserver','roundNumber':r}]
    events.append(final)
    return {'results.json':json.dumps({'source':'GameEndedEventForObserver','engine_version':'1.4.0',
                'completed':True,'numberOfRounds':3,'ticks':3,'results':rows}).encode(),
            'referee-report.json':b'{}','recordings.battle.gz':gzip.compress(
                b'\n'.join(json.dumps(e).encode() for e in events))}

def frames(files):
    return b'\n'.join(b'RC_I2_ARTIFACT '+n.encode()+b' '+base64.b64encode(v) for n,v in files.items())

class ArtifactTests(unittest.TestCase):
    def test_fixture_roundtrip(self):
        files=fixture();self.assertEqual(M.files_from_stream(frames(files),[]),files)
        self.assertEqual(M.validate_replay(files)['round_ends'],[1,2,3])
    def test_traversal(self):
        with self.assertRaises(ValueError):M.files_from_stream(b'RC_I2_ARTIFACT ../.env YQ==',[])
    def test_duplicate_artifact(self):
        data=frames(fixture())
        with self.assertRaises(ValueError):M.files_from_stream(data+b'\n'+data,[])
    def test_partial_frames(self):
        files=fixture();files.pop('results.json')
        with self.assertRaises(ValueError):M.files_from_stream(frames(files),[])
    def test_encoded_secret_not_bypassed(self):
        files=fixture();files['referee-report.json']=b'{"bad":"SECRET_CANARY_123"}'
        with self.assertRaisesRegex(ValueError,'SECRET'):M.files_from_stream(frames(files),['SECRET_CANARY_123'])
    def test_compressed_secret_not_bypassed(self):
        files=fixture();files['recordings.battle.gz']=gzip.compress(gzip.decompress(files['recordings.battle.gz'])+b'\nSECRET_CANARY_123')
        with self.assertRaisesRegex(ValueError,'SECRET'):M.validate_replay(files,['SECRET_CANARY_123'])
    def test_no_compressed_replay(self):
        files=fixture();files['recordings.battle.gz']=b'bad'
        with self.assertRaises(OSError):M.validate_replay(files)
    def test_wrong_score(self):
        files=fixture();r=json.loads(files['results.json']);r['results'][0]['totalScore']=51
        files['results.json']=json.dumps(r).encode()
        with self.assertRaises(ValueError):M.validate_replay(files)
    def test_wrong_rounds(self):
        files=fixture();files['recordings.battle.gz']=gzip.compress(gzip.decompress(files['recordings.battle.gz']).replace(b'"roundNumber": 2',b'"roundNumber": 1'))
        with self.assertRaises(ValueError):M.validate_replay(files)
    def test_nan_or_duplicate_json(self):
        for raw in ('{"a":NaN}','{"a":1,"a":2}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):M.strict_json(raw)
    def test_source_not_bot_output(self):
        files=fixture();r=json.loads(files['results.json']);r['source']='stdout'
        files['results.json']=json.dumps(r).encode()
        with self.assertRaises(ValueError):M.validate_replay(files)

if __name__=='__main__':unittest.main()
