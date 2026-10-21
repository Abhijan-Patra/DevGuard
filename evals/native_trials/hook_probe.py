import sys,subprocess,json,os
from pathlib import Path
root=Path(os.environ['DEVGUARD_NATIVE_TRIAL_DIR']).resolve();repo=Path((root/'repo-path').read_text())
raw=sys.stdin.buffer.read(65537)
env={**os.environ,'PYTHONPATH':str(repo),'DEVGUARD_BASE_URL':'http://127.0.0.1:8766/api/v1','DEVGUARD_CLIENT_TOKEN_FILE':str(root/'adapter-token'),'DEVGUARD_PROJECT_ID':'native-demo','DEVGUARD_DESTINATION_ID':'local-preview','DEVGUARD_MANAGED_TOOLS':'1'}
try:
 r=subprocess.run([str(repo/'.venv/bin/python'),'-m','devguard.client_hook'],input=raw,capture_output=True,env=env,timeout=23)
 event=json.loads(raw);out=json.loads(r.stdout or '{}')
 blocked=out.get('decision')=='block' or out.get('hookSpecificOutput',{}).get('permissionDecision')=='deny' or r.returncode==2
 tool=event.get('tool_name');tool=tool if tool in {'Bash','Read','apply_patch','mcp__devguard__list_sources','mcp__devguard__read_source'} else 'other'
 with (root/'hook-events.jsonl').open('a') as f:f.write(json.dumps({'event':event.get('hook_event_name'),'tool':tool,'blocked':blocked})+'\n')
 sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);raise SystemExit(r.returncode)
except Exception:
 print('DevGuard native trial held',file=sys.stderr);raise SystemExit(2)
