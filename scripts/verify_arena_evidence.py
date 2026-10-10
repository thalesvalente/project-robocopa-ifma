#!/usr/bin/env python3
"""Read-only I2 audit. Use --reconciled for the strict pre-I3 evidence gate."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.worker_agent.arena_evidence import validate_batch,EvidenceError

from services.worker_agent.arena_reconciliation import validate_reconciled_batch

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path,help='Directory containing batch.json and battle-1/2')
    parser.add_argument('--reconciled',action='store_true',help='Require new five-scenario source-bound evidence')
    parser.add_argument('--expected-source-commit',help='Head SHA verified outside the artifact')
    parser.add_argument('--expected-workflow-run-id',type=int,help='Workflow run verified outside the artifact')
    args=parser.parse_args()
    if not args.reconciled and (args.expected_source_commit or args.expected_workflow_run_id):
        parser.error('Expected provenance requires --reconciled')
    try:
        result=(validate_reconciled_batch(args.directory,expected_source_commit=args.expected_source_commit,
                expected_workflow_run_id=args.expected_workflow_run_id) if args.reconciled else validate_batch(args.directory))
    except (EvidenceError,OSError,KeyError,TypeError,AttributeError,ValueError):
        print('FAIL: incomplete, unsafe or inconsistent I2 evidence.',file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
