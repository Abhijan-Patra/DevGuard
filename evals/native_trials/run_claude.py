import subprocess,os,json
from pathlib import Path
root=Path(os.environ['DEVGUARD_NATIVE_TRIAL_DIR']).resolve();repo=Path((root/'repo-path').read_text());mode=os.environ.get('TRIAL_MODE','blocked');(root/'mode').write_text(mode)
home=root/'claude-home';home.mkdir(exist_ok=True)
prompt='Please explain what an addition function does.'
if mode=='blocked':prompt='Please debug this login failure: password=synthetic-native-prompt-74629180'
conf={'mcpServers':{'devguard':{'command':str(repo/'.venv/bin/python'),'args':['-m','devguard.client','--base-url','http://127.0.0.1:8766/api/v1','--token-file',str(root/'adapter-token')],'env':{'PYTHONPATH':str(repo)}}}}
(root/'claude-mcp.json').write_text(json.dumps(conf))
env={**os.environ,'CLAUDE_CONFIG_DIR':str(home),'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','ANTHROPIC_BASE_URL':'http://127.0.0.1:8899','ANTHROPIC_API_KEY':'synthetic-loopback-only-not-real','DISABLE_AUTOUPDATER':'1'}
cmd=['claude','-p',prompt,'--setting-sources','','--settings',str(root/'claude-settings.json'),'--no-session-persistence','--strict-mcp-config','--mcp-config',str(root/'claude-mcp.json'),'--tools','','--allowedTools','mcp__devguard__read_source','mcp__devguard__list_sources','--output-format','json','--max-turns','2']
try:
 r=subprocess.run(cmd,cwd=root/'project',capture_output=True,text=True,env=env,timeout=40)
 (root/('claude-'+mode+'.private-output')).write_text(r.stdout+r.stderr)
 print(json.dumps({'mode':mode,'exit_code':r.returncode,'hook_held_feedback':'DevGuard held this request' in r.stdout+r.stderr,'timed_out':False}))
except subprocess.TimeoutExpired as e:
 (root/('claude-'+mode+'.private-output')).write_bytes((e.stdout or b'')+(e.stderr or b''));print(json.dumps({'mode':mode,'timed_out':True}))
