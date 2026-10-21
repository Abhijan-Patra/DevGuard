import os
import sys
from pathlib import Path
root=Path(os.environ['DEVGUARD_NATIVE_TRIAL_DIR']).resolve();repo=Path((root/'repo-path').read_text());sys.path.insert(0,str(repo))
import uvicorn
from devguard.api.app import create_app
from devguard.config import Settings
from devguard.storage.audit import AuditStore
from devguard.api.repair_integration import projects_repair_factory
from devguard.repair.projects import load_projects
settings=Settings((root/'operator-token').read_text(),adapter_token=(root/'adapter-token').read_text())
app=create_app(settings,audit=AuditStore(root/'audit.sqlite3'),repair_factory=projects_repair_factory(repo,load_projects(root/'projects.json')))
uvicorn.run(app,host='127.0.0.1',port=8766,access_log=False,log_level='error')
