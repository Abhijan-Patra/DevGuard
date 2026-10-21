"""Check release file scope and required resources; never inspect live runtime data."""
from pathlib import Path, PurePosixPath
import sys
import tarfile
import zipfile

root = Path(sys.argv[1])
wheel, = root.glob('*.whl')
source, = root.glob('*.tar.gz')
for artifact in (wheel, source):
    if artifact.suffix == '.whl':
        with zipfile.ZipFile(artifact) as archive:names = archive.namelist()
    else:
        with tarfile.open(artifact) as archive:
            members = archive.getmembers()
            assert all(m.isfile() or m.isdir() for m in members), 'Links are not permitted in release archives'
            names = [m.name for m in members]
    for name in names:
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts, 'Unsafe archive path'
        assert not set(path.parts).intersection({'.git', '.devguard', '.venv', 'private-inputs', 'clipboard-history', 'snapshots', 'sandboxes', '__pycache__'}), 'Private/runtime directory included'
        assert not any(part.startswith('.env') and part != '.env.example' for part in path.parts), 'Private environment file included'
        assert path.suffix not in {'.log', '.db', '.sqlite', '.sqlite3', '.gguf', '.safetensors', '.pem', '.key', '.pyc'}, 'Private/runtime artifact included'
    for required in ('devguard/web/workspace.js', 'devguard/resources/demo/cart.py',
                     'devguard/resources/checks/test_cart.py', 'devguard/resources/demo/Dockerfile'):
        assert any(name.endswith(required) for name in names), 'Required runtime asset missing'
    print(artifact.name + ': required assets present; no excluded runtime files or unsafe archive paths')
