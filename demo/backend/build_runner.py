"""Build with a minimal context: never upload the repo, .venv, .git or private inputs."""

import argparse
import io
import shutil
import subprocess
import tarfile
from pathlib import Path


def build_context(root: Path) -> bytes:
    context = io.BytesIO()
    # A regular USTAR first member is recognized as a context by Docker's stdin
    # detection. Avoid PAX metadata and host usernames, fractional mtimes, etc.
    with tarfile.open(
        fileobj=context, mode="w", format=tarfile.USTAR_FORMAT
    ) as archive:
        for source, name in [
            (root / "demo/backend/Dockerfile", "Dockerfile"),
            (
                root / "tests/backend/requirements-dev.lock",
                "tests/backend/requirements-dev.lock",
            ),
        ]:
            data = source.read_bytes()
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(data))
    return context.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", default="docker")
    args = parser.parse_args()
    docker = shutil.which(args.docker)
    if docker is None:
        parser.error("Docker CLI unavailable; finish Docker Desktop setup first")
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        [docker, "build", "--tag", "devguard-runner:mac2", "-"],
        input=build_context(root),
        check=True,
    )
    subprocess.run(
        [docker, "image", "inspect", "devguard-runner:mac2", "--format", "{{.Id}}"],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
