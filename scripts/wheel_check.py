"""Cross-platform clean wheel installation and API smoke, no model/clipboard reads."""
from pathlib import Path
import os
import subprocess
import sys
import venv

root = Path(os.environ['RUNNER_TEMP']) / 'devguard-installed'
venv.EnvBuilder(with_pip=True).create(root)
python = root / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
wheel, = Path('dist').glob('*.whl')
subprocess.run([str(python), '-m', 'pip', 'install', str(wheel.resolve())+'[clipboard,client]'], check=True)
subprocess.run([str(python), '-m', 'pip', 'check'], check=True)
subprocess.run([str(python), '-I', 'scripts/release_smoke.py', '--output',
                str(Path(os.environ['RUNNER_TEMP']) / 'wheel-smoke.json')], check=True)
