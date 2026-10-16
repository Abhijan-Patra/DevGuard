"""Build with a minimal context: never upload the repo, .venv, .git or private inputs."""

import argparse
import io
import shutil
import subprocess
import tarfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", default="docker")
    args = parser.parse_args()
    docker = shutil.which(args.docker)
    if docker is None:
        parser.error("Docker CLI unavailable; finish Docker Desktop setup first")
    root = Path(__file__).resolve().parents[2]
    context = io.BytesIO()
    with tarfile.open(fileobj=context, mode="w") as archive:
        archive.add(root / "demo/backend/Dockerfile", arcname="Dockerfile")
        archive.add(
            root / "tests/backend/requirements-dev.lock",
            arcname="tests/backend/requirements-dev.lock",
        )
    subprocess.run(
        [docker, "build", "--tag", "devguard-runner:mac2", "-"],
        input=context.getvalue(),
        check=True,
    )
    subprocess.run(
        [docker, "image", "inspect", "devguard-runner:mac2", "--format", "{{.Id}}"],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
