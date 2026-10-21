"""Explicit stdin/file context client for the local gate; never invokes arbitrary tools."""
import argparse
import json
from pathlib import Path
import sys

import httpx

from devguard.ui.session import load_local_token


def main():
    parser=argparse.ArgumentParser(description='Inspect text or an enrolled source file through the actual local guard')
    parser.add_argument('--task',default=None)
    parser.add_argument('--project',default=None)
    parser.add_argument('--path',default=None,help='Relative, explicitly enrolled source path; never a shell command')
    parser.add_argument('--deliver',action='store_true',help='Release approved inspected bytes to the ephemeral local composer')
    args=parser.parse_args()
    try:
        token=load_local_token('http://127.0.0.1:8765/api/v1')
        with httpx.Client(base_url='http://127.0.0.1:8765/api/v1',headers={'Authorization':'Bearer '+token},trust_env=False,follow_redirects=False,timeout=30) as client:
            if args.path:
                if not args.project:parser.error('--path requires --project')
                route='/context/read'
                body={'project_id':args.project,'path':args.path,'task':args.task,'content_version':1}
            else:
                raw=sys.stdin.buffer.read(32769)
                if len(raw)>32768:raise ValueError('INPUT_TOO_LARGE')
                text=raw.decode('utf-8')
                route='/guard/evaluate'
                body={'project_id':args.project,'task':args.task,'surface':'explicit_prompt',
                      'destination_id':'local-composer','content_version':1,'text':text}
            response=client.post(route,json=body)
            response.raise_for_status()
            result=response.json()
            metadata={k:result.get(k) for k in ('request_id','decision','status','reason_codes','expires_at')}
            if args.deliver:
                if result['status']!='READY' or result['decision'] not in {'ALLOW','SANITIZE'}:
                    print(json.dumps({**metadata,'delivered':False}))
                    return 2
                prefix='/context/requests/' if args.path else '/guard/requests/'
                receipt=client.post(prefix+result['request_id']+'/deliver',json={'content_version':1,'destination_id':'local-composer'})
                receipt.raise_for_status()
                metadata.update(receipt.json())
            # Metadata only: no raw/cleaned contents or bearer values in CLI logs.
            print(json.dumps(metadata))
            return 0 if result['status']=='READY' else 2
    except (ValueError,UnicodeError,httpx.HTTPError):
        print('{"error":"CONTEXT_HELD_OR_UNAVAILABLE"}')
        return 2


if __name__=='__main__':raise SystemExit(main())
