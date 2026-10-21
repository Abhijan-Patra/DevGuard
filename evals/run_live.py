"""Run real synthetic privacy cases; preserve mismatches and never change the oracle."""
import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import time

import httpx

from devguard.ui.session import load_local_token

ROOT=Path(__file__).resolve().parents[1]


def run(selected):
    cases=json.loads((ROOT/'evals/cases/privacy_cases.json').read_text())
    token=load_local_token('http://127.0.0.1:8765/api/v1')
    results=[]
    with httpx.Client(base_url='http://127.0.0.1:8765/api/v1',headers={'Authorization':'Bearer '+token},trust_env=False,timeout=30) as client:
        runtime=client.get('/status').json()['runtime']
        if not runtime.get('model_ready'):raise RuntimeError('MODEL_UNAVAILABLE')
        for case in cases:
            if case['id'] not in selected:continue
            # P06 is a managed-tool path test and P07 requires dependency-failure
            # injection. They cannot be benchmarked as ordinary text requests.
            if case['id'] not in {'P01','P02','P03','P04','P05'}:
                results.append({'case_id':case['id'],'execution':'UNRUN','reason':'REQUIRES_SEPARATE_BOUNDARY_HARNESS'})
                continue
            started=time.monotonic()
            response=client.post('/guard/evaluate',json={'project_id':None,'surface':case['surface'],
                'task':case['task'],'destination_id':'local-preview','content_version':time.time_ns(),'text':case['synthetic_input']})
            response.raise_for_status()
            actual=response.json()
            codes=actual['reason_codes']
            row={'case_id':case['id'],'execution':'RAN','expected_decision':case['expected_decision'],
                 'actual_decision':actual['decision'],'status':actual['status'],'reason_codes':codes,
                 'expected_reasons_present':set(case['expected_reason_codes']).issubset(codes),
                 'decision_matches_expectation':actual['decision']==case['expected_decision'],
                 'approved_preview_available':actual['safe_preview'] is not None,
                 'elapsed_seconds':round(time.monotonic()-started,3),'external_delivery':False}
            results.append(row)
            print(json.dumps(row),flush=True)
    return {'timestamp':datetime.now(UTC).isoformat(),'scope':'Real loopback guard + pinned Gemma; declared synthetic cases; no external delivery',
            'runtime':runtime,'catalogue_unchanged':True,'destination_mapping':'configured-coding-client -> local-preview (inspection only)',
            'results':results,'perfect_accuracy_claimed':False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cases',nargs='+',default=['P01','P02','P03','P04','P05'])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=run(set(args.cases))
    args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
