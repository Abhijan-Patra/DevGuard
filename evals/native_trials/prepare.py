"""Create a new private, synthetic-only native CLI boundary trial directory."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shlex
import sys

from devguard.client_config import prepare


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    root=args.directory.absolute();repo=Path(__file__).resolve().parents[2]
    if root.is_relative_to(repo):raise SystemExit('Use a new private temporary directory outside the repository')
    root.mkdir(mode=0o700,exist_ok=False)
    (root/'project').mkdir();sources=root/'sources';sources.mkdir()
    (sources/'sample.py').write_text('VALUE = 42\npassword = "synthetic-native-sensitive-47912680"\n')
    (sources/'clean.py').write_text('def add(a, b):\n    return a + b\n')
    for name in ('operator','adapter'):
        path=root/(name+'-token');path.write_text(secrets.token_urlsafe(32));path.chmod(0o600)
    image=json.loads((repo/'.devguard/local-projects.json').read_text())['projects'][0]['image_id']
    (root/'projects.json').write_text(json.dumps({'projects':[{'project_id':'native-demo','root':str(sources),
        'source_files':['sample.py','clean.py'],'writable_files':['sample.py'],'trusted_tests':str(repo/'trusted_tests'),
        'test_names':['cart'],'image_id':image}]}))
    (root/'repo-path').write_text(str(repo))
    profiles=root/'profiles';prepare(profiles,root/'adapter-token','http://127.0.0.1:8766/api/v1')
    (profiles/'codex').rename(root/'codex-home')
    cfg=root/'codex-home/config.toml'
    cfg.write_text('model = "native-boundary-fixture"\nmodel_provider = "boundary"\napproval_policy = "never"\n'+cfg.read_text()+
        '\n[model_providers.boundary]\nname = "Synthetic local boundary fixture - not a coding model"\n'
        'base_url = "http://127.0.0.1:8899/v1"\nwire_api = "responses"\nrequires_openai_auth = false\n'+
        f'[projects.{json.dumps(str(root/"project"))}]\ntrust_level = "trusted"\n')
    command=shlex.join([sys.executable,str(Path(__file__).parent/'hook_probe.py')])
    hooks={'hooks':{event:[{'matcher':'.*','hooks':[{'type':'command','command':command,'timeout':25}]}]
                    for event in ('UserPromptSubmit','PreToolUse','PostToolUse')}}
    (root/'codex-home/hooks.json').write_text(json.dumps(hooks,indent=2)+'\n')
    (root/'claude-settings.json').write_text(json.dumps(hooks,indent=2)+'\n')
    print('Synthetic trial prepared. Review native hooks before running. No global configuration changed.')

if __name__=='__main__':main()
