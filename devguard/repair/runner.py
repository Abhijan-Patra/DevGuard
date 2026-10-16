"""Named checks only, no shell, no host-execution fallback."""

import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from threading import Event

from .contracts import ProjectSpec, RepairError, TestResult


class DockerVerifier:
    def __init__(self, docker: str = "docker", timeout: float = 45):
        self.docker = shutil.which(docker)
        self.timeout = timeout

    def command(
        self, source: Path, spec: ProjectSpec, name: str, container: str
    ) -> list[str]:
        if not self.docker:
            raise RepairError("DOCKER_UNAVAILABLE")
        if name not in spec.test_names or not re.fullmatch(r"[a-zA-Z0-9_]+", name):
            raise RepairError("TEST_DENIED")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", spec.image_id):
            raise RepairError("IMAGE_NOT_PINNED")
        if not spec.trusted_tests.is_dir() or spec.trusted_tests.is_symlink():
            raise RepairError("VERIFIER_UNAVAILABLE")
        return [
            self.docker,
            "run",
            "--rm",
            "--pull=never",
            "--name",
            container,
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=64",
            "--memory=1g",
            "--memory-swap=1g",
            "--cpus=2",
            "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "--workdir=/workspace",
            "--mount",
            f"type=bind,src={source},dst=/workspace,readonly",
            "--mount",
            f"type=bind,src={spec.trusted_tests},dst=/checks,readonly",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=PYTHONPYCACHEPREFIX=/tmp/pycache",
            "--env=PYTHONPATH=/workspace",
            "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            "--env=HOME=/tmp",
            "--entrypoint=python",
            spec.image_id,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--tb=line",
            "--disable-warnings",
            "--no-header",
            f"/checks/test_{name}.py",
        ]

    def run(
        self, source: Path, spec: ProjectSpec, name: str, cancel: Event
    ) -> TestResult:
        if cancel.is_set():
            return TestResult("CANCELED")
        if not source.is_dir() or source.is_symlink() or source.resolve() != source:
            raise RepairError("SOURCE_UNAVAILABLE")
        if spec.trusted_tests.resolve() != spec.trusted_tests or any(
            "," in str(path) for path in (source, spec.trusted_tests)
        ):
            raise RepairError("VERIFIER_UNAVAILABLE")
        container = "devguard-" + uuid.uuid4().hex
        command = self.command(source, spec, name, container)
        chunks: list[bytes] = []
        overflow = Event()
        env = {
            k: v
            for k, v in os.environ.items()
            if k in {"PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG"}
        }
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
        )

        def drain() -> None:
            size = 0
            assert process.stdout is not None
            while block := process.stdout.read(4096):
                size += len(block)
                if size <= 32768:
                    chunks.append(block)
                else:
                    overflow.set()

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        deadline = time.monotonic() + self.timeout
        status = None
        try:
            while process.poll() is None:
                if cancel.is_set():
                    status = "CANCELED"
                elif overflow.is_set():
                    status = "ERROR"
                elif time.monotonic() >= deadline:
                    status = "TIMEOUT"
                if status:
                    process.kill()
                    break
                time.sleep(0.05)
            process.wait(timeout=5)
        finally:
            # Stop only this run's named container, including when the CLI was killed.
            try:
                subprocess.run(
                    [self.docker, "rm", "-f", container],
                    capture_output=True,
                    timeout=10,
                    env=env,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
            reader.join(timeout=2)
            if process.stdout:
                process.stdout.close()
        if overflow.is_set():
            status = "ERROR"
        if status is None:
            status = (
                "PASS"
                if process.returncode == 0
                else "FAIL"
                if process.returncode == 1
                else "ERROR"
            )
        return TestResult(
            status,
            b"".join(chunks).decode("utf-8", errors="replace"),
            process.returncode,
        )
