"""Packaged public demo assets and minimal Docker context; no checkout required."""
import io
from pathlib import Path
import subprocess
import tarfile

ASSETS = Path(__file__).resolve().parent / 'resources'
RUNNER_TAG = 'devguard-runner:mac2'  # Keep existing prepared images usable.


def build_context():
    context = io.BytesIO()
    with tarfile.open(fileobj=context, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for source, name in ((ASSETS / 'demo/Dockerfile', 'Dockerfile'),
                             (ASSETS / 'demo/requirements-dev.lock', 'tests/backend/requirements-dev.lock')):
            data = source.read_bytes()
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o644
            archive.addfile(member, io.BytesIO(data))
    return context.getvalue()


def build_runner(docker):
    subprocess.run([docker, 'build', '--tag', RUNNER_TAG, '-'], input=build_context(), check=True)
