import subprocess,os,json,time
from pathlib import Path
root=Path(os.environ['DEVGUARD_NATIVE_TRIAL_DIR']).resolve()
mode=os.environ.get('TRIAL_MODE','text');(root/'mode').write_text(mode)
prompt='Please explain what an addition function does.'
if mode=='blocked':prompt='Please debug this login failure: password=synthetic-native-prompt-74629180'
if mode=='managed':prompt='Read the registered clean.py source using the DevGuard managed tool.'
if mode=='shell':prompt='Please create the requested marker using a shell tool.'
env={**os.environ,'CODEX_HOME':str(root/'codex-home')}
cmd=[os.environ.get('DEVGUARD_CODEX_BIN','codex'),'exec','--skip-git-repo-check','--ephemeral','--json','-C',str(root/'project'),prompt]
try:
 r=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=45)
 (root/('codex-'+mode+'.private-output')).write_text(r.stdout+r.stderr)
 print(json.dumps({'mode':mode,'exit_code':r.returncode,'hook_held_feedback':'DevGuard held this request' in r.stdout+r.stderr,'tool_name_present':'devguard' in r.stdout,'timed_out':False}))
except subprocess.TimeoutExpired as e:
 (root/('codex-'+mode+'.private-output')).write_bytes((e.stdout or b'')+(e.stderr or b''))
 print(json.dumps({'mode':mode,'timed_out':True}))
