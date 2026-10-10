#!/usr/bin/env python3
"""Read-only audit of an extracted I2 schema-2 evidence batch; never runs a bot."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.worker_agent.arena_evidence import validate_batch,EvidenceError

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path,help='Directory containing batch.json and battle-1/2')
    args=parser.parse_args()
    try:result=validate_batch(args.directory)
    except (EvidenceError,OSError,KeyError,TypeError,AttributeError,ValueError):
        print('FAIL: incomplete, unsafe or inconsistent I2 evidence.',file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
