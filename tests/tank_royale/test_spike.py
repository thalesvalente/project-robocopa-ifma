"""Synthetic unit fixtures only; real-engine evidence is a separate CI stage."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

runner = load('runner', ROOT / 'scripts/run_tank_spike.py')
prepare = load('prepare', ROOT / 'spikes/tank-royale/prepare.py')

def fixture():
    return {'completed': True, 'source': 'BattleResults', 'engine_version': '1.4.0',
            'numberOfRounds': 5, 'observedTicks': 100, 'duration_ms': 1000,
            'results': [dict(name=name, version='1.0', rank=rank, totalScore=100, survival=10,
                             bulletDamage=90, ramDamage=0, firstPlaces=2, secondPlaces=3)
                        for name,rank in [('Walls',1), ('Spin Bot',2)]]}

def contract():
    return {'Config': {'User':'10001:10001'}, 'HostConfig': {
        'NetworkMode':'none','ReadonlyRootfs':True,'Privileged':False,
        'Binds':None,'Mounts':None,'PortBindings':{},'CapDrop':['ALL'],
        'SecurityOpt':['no-new-privileges'], 'Memory':2*1024**3,
        'NanoCpus':2_000_000_000,'PidsLimit':256}}

class SpikeTest(unittest.TestCase):
    def test_official_identity_contract(self):
        runner.verify_results(fixture())
    def test_incomplete_battle_rejected(self):
        data = fixture(); data['completed'] = False
        with self.assertRaises(ValueError): runner.verify_results(data)
    def test_wrong_round_count_rejected(self):
        data = fixture(); data['numberOfRounds'] = 1
        with self.assertRaises(ValueError): runner.verify_results(data)
    def test_unexpected_bot_rejected(self):
        data = fixture(); data['results'][0]['name'] = 'StudentCode'
        with self.assertRaises(ValueError): runner.verify_results(data)
    def test_no_tick_evidence_rejected(self):
        data = fixture(); data['observedTicks'] = 0
        with self.assertRaises(ValueError): runner.verify_results(data)
    def test_negative_score_rejected(self):
        data = fixture(); data['results'][0]['totalScore'] = -1
        with self.assertRaises(ValueError): runner.verify_results(data)
    def test_docker_policy(self):
        self.assertTrue(all(runner.inspect_contract(contract()).values()))
    def test_host_network_rejected(self):
        data = contract(); data['HostConfig']['NetworkMode'] = 'host'
        with self.assertRaises(ValueError): runner.inspect_contract(data)
    def test_host_bind_rejected(self):
        data = contract(); data['HostConfig']['Binds'] = ['/home:/host']
        with self.assertRaises(ValueError): runner.inspect_contract(data)
    def test_root_rejected(self):
        data = contract(); data['Config']['User'] = 'root'
        with self.assertRaises(ValueError): runner.inspect_contract(data)
    def test_unbounded_memory_rejected(self):
        data = contract(); data['HostConfig']['Memory'] = 0
        with self.assertRaises(ValueError): runner.inspect_contract(data)
    def test_verified_download(self):
        body = b'pinned reference asset'
        self.assertEqual(prepare.verified(body, {'size':len(body), 'sha256':hashlib.sha256(body).hexdigest()}), body)
    def test_checksum_failure(self):
        with self.assertRaises(ValueError): prepare.verified(b'changed', {'size':7,'sha256':'0'*64})
    def test_zip_slip_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.zip'
            with zipfile.ZipFile(path,'w') as z: z.writestr('../escape.txt','bad')
            with self.assertRaises(ValueError): prepare.extract_checked(path,Path(tmp)/'out')
            self.assertFalse((Path(tmp)/'escape.txt').exists())
    def test_zip_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.zip'
            with zipfile.ZipFile(path,'w') as z:
                info=zipfile.ZipInfo('link'); info.external_attr=0o120777<<16
                z.writestr(info,'/etc/passwd')
            with self.assertRaises(ValueError): prepare.extract_checked(path,Path(tmp)/'out')
    def test_good_zip_extracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ok.zip'
            with zipfile.ZipFile(path,'w') as z: z.writestr('Walls/Walls.json','{}')
            prepare.extract_checked(path,Path(tmp)/'out')
            self.assertEqual((Path(tmp)/'out/Walls/Walls.json').read_text(),'{}')
    def test_replay_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.battle.gz'
            path.write_bytes(gzip.compress(b'unit-test-only '*200))
            self.assertGreater(runner.verify_replay(path)['uncompressed_bytes'],1000)
    def test_corrupt_replay_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.battle.gz'; path.write_bytes(b'not gzip')
            with self.assertRaises(OSError): runner.verify_replay(path)
    def test_stream_preserves_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); stream=out/'runtime.stream'
            replay=gzip.compress(b'fixture-only '*200)
            stream.write_bytes(b'LOG\nROBOCOPA_ARTIFACT results.json ' + base64.b64encode(b'{"unit":true}') + b'\nROBOCOPA_ARTIFACT recordings/game-test.battle.gz '+base64.b64encode(replay)+b'\n')
            runner.extract_stream(stream,out)
            self.assertEqual((out/'recordings/game-test.battle.gz').read_bytes(),replay)
            self.assertEqual((out/'engine.log').read_bytes(),b'LOG\n')
            self.assertFalse(stream.exists())
    def test_stream_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); stream=out/'runtime.stream'
            stream.write_bytes(b'ROBOCOPA_ARTIFACT ../escape Zm9v\n')
            with self.assertRaises(ValueError): runner.extract_stream(stream,out)
    def test_stream_partial_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); stream=out/'runtime.stream'; stream.write_bytes(b'engine failed\n')
            with self.assertRaises(ValueError): runner.extract_stream(stream,out)
    def test_wrong_bot_version_rejected(self):
        data=fixture(); data['results'][0]['version']='unverified'
        with self.assertRaises(ValueError): runner.verify_results(data)
    def test_pinned_lock(self):
        lock=json.loads((ROOT/'spikes/tank-royale/upstream.lock.json').read_text())
        self.assertEqual(lock['engine_version'],'1.4.0')
        self.assertEqual(lock['bots'],['Walls','SpinBot'])
        for asset in lock['artifacts'].values():
            self.assertIn('/download/v1.4.0/',asset['url'])
            self.assertEqual(len(asset['sha256']),64)

if __name__ == '__main__': unittest.main()
