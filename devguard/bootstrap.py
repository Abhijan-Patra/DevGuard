"""Packaged public demo assets and minimal Docker context; no checkout required."""
import io
import hashlib
from pathlib import Path
import subprocess
import tarfile

ASSETS = Path(__file__).resolve().parent / 'resources'


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


# Version the preparation profile as well as public inputs. Upgrades must not
# silently reuse an old test environment under the historical shared tag.
RUNNER_TAG = 'devguard-verifier:local-' + hashlib.sha256(b'single-platform-v1\0' + build_context()).hexdigest()[:12]


def build_runner(docker):
    # A locally prepared, single-platform verifier does not need an OCI index
    # with attestation descriptors. Keep image-ID resolution unambiguous.
    subprocess.run([docker, 'build', '--provenance=false', '--tag', RUNNER_TAG, '-'], input=build_context(), check=True)
