import subprocess,os,json,time
from datetime import UTC,datetime
from pathlib import Path
from importlib.metadata import version
root=Path(os.environ['DEVGUARD_NATIVE_TRIAL_DIR']).resolve()

def lines(name):
 p=root/name
 return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
rows=[]
for client in ('codex','claude'):
 for mode in ('blocked','text','managed','sensitive','traversal',*(['shell'] if client=='codex' else [])):
  hb=len(lines('hook-events.jsonl'));pb=len(lines('provider-events.jsonl'));start=time.monotonic()
  r=subprocess.run([str(Path.cwd()/'.venv/bin/python'),str(Path(__file__).parent/('run_'+client+'.py'))],capture_output=True,text=True,env={**os.environ,'TRIAL_MODE':mode},timeout=55)
  result=json.loads(r.stdout.strip());hooks=lines('hook-events.jsonl')[hb:];posts=lines('provider-events.jsonl')[pb:]
  passed=not result.get('timed_out') and all(not p['sensitive_marker_received'] and not p['held_prompt_received'] for p in posts)
  if mode=='blocked':passed=passed and not posts and any(h['event']=='UserPromptSubmit' and h['blocked'] for h in hooks)
  if mode=='text':passed=passed and bool(posts) and any(h['event']=='UserPromptSubmit' and not h['blocked'] for h in hooks)
  if mode=='managed':passed=passed and any(p['managed_text_received'] for p in posts) and any(h['event']=='PostToolUse' and not h['blocked'] for h in hooks)
  if mode=='sensitive':passed=passed and any(p['redacted_placeholder_received'] for p in posts) and any(h['event']=='PostToolUse' and not h['blocked'] for h in hooks)
  if mode=='traversal':passed=passed and any(p['held_result_received'] for p in posts)
  if mode=='shell':passed=passed and any(h['event']=='PreToolUse' and h['tool']=='Bash' and h['blocked'] for h in hooks) and not (root/'project/native-should-not-exist').exists()
  row={'client':client,'case':mode,'passed':bool(passed),'provider_requests':len(posts),'hook_events':hooks,'sensitive_marker_received':any(p['sensitive_marker_received'] or p['held_prompt_received'] for p in posts),'elapsed_seconds':round(time.monotonic()-start,3)}
  rows.append(row);print(json.dumps(row),flush=True)
report={'timestamp':datetime.now(UTC).isoformat(),'scope':'Actual installed CLI hook events and MCP transport with real local pinned Gemma; local synthetic provider protocol fixture, no coding-model inference or cloud delivery','client_versions':{'codex':subprocess.check_output([os.environ.get('DEVGUARD_CODEX_BIN','codex'),'--version'],text=True).strip(),'claude':subprocess.check_output(['claude','--version'],text=True).strip(),'mcp_sdk':version('mcp')},'codex_hook_trust':'Reviewed and trusted through native /hooks UI in isolated CODEX_HOME; no bypass flag','global_configuration_changed':False,'general_clipboard_accessed':False,'cloud_client_delivery_verified':False,'results':rows,'limitations':['Exact CLI versions and configured event paths only','Untrusted/skipped/crashed/timed-out hooks can fail open at client level; managed source server holds its own output','Automatic context, attachments, hosted tools, desktop variants, transcripts and telemetry are outside these measurements','Claude account was not signed in; synthetic API transport used; client-reported cost is not an actual provider charge']}
(root/'native-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
