"""Synthetic replay/identity fixtures; actual replays are inspected separately in CI."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import run_mobile_spike as app

SHA='a'*64
ROWS=[{'name':'Aprendiz','version':SHA[:12],'rank':1,'totalScore':20,'firstPlaces':2,'secondPlaces':1},
      {'name':'Walls','version':'1.0','rank':2,'totalScore':10,'firstPlaces':1,'secondPlaces':2}]
RESULT={'completed':True,'source':'BattleResults','engine_version':'1.4.0','numberOfRounds':3,
        'program_sha256':SHA,'observedRoundEnds':[1,2,3],'observedTicks':3,'results':ROWS}
def events():
    return [{'type':'GameStartedEventForObserver','gameSetup':{'numberOfRounds':3},'participants':ROWS},
            *[{'type':'RoundEndedEventForObserver','roundNumber':i} for i in [1,2,3]],
            {'type':'TickEventForObserver','roundNumber':1,'turnNumber':1,
             'botStates':[{'id':1,'name':'Aprendiz','x':100,'y':100,'direction':0,'energy':90,'speed':6}]},
            {'type':'GameEndedEventForObserver','results':ROWS}]
class ReplayTest(unittest.TestCase):
    def test_identity(self):app.validate_result(RESULT,SHA)
    def test_wrong_hash(self):
        with self.assertRaises(ValueError):app.validate_result(RESULT,'b'*64)
    def test_incomplete_rounds(self):
        result=copy.deepcopy(RESULT);result['observedRoundEnds']=[1,2]
        with self.assertRaises(ValueError):app.validate_result(result,SHA)
    def inspect(self,data):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'test.battle.gz'
            file.write_bytes(gzip.compress(b'\n'.join(json.dumps(e).encode() for e in data)))
            return app.replay_summary(file,RESULT)
    def test_real_fields_only(self):
        result=self.inspect(events());self.assertEqual(result['mean_abs_speed'],6)
    def test_replay_disagreement(self):
        data=copy.deepcopy(events());data[-1]['results'][0]['totalScore']=999
        with self.assertRaises(ValueError):self.inspect(data)
    def test_no_end(self):
        with self.assertRaises(ValueError):self.inspect(events()[:-1])
    def test_nan_rejected(self):
        data=events();data[-2]['botStates'][0]['speed']=float('nan')
        with self.assertRaises(ValueError):self.inspect(data)

if __name__ == '__main__': unittest.main()
