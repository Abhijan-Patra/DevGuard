"""Actual Mac 2 diagnostics/baseline CLI. No duplicate backend/model server."""

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from threading import Event

from .contracts import RepairError
from .runner import DockerVerifier


def main() -> int:
    parser = argparse.ArgumentParser(description="DevGuard Mac 2 worker tools")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    baseline = sub.add_parser(
        "baseline", help="Run the declared buggy demo through restricted Docker"
    )
    baseline.add_argument("--image-id", required=True)
    baseline.add_argument("--docker", default="docker")
    trial = sub.add_parser(
        "trial", help="Use an operator-supplied Mac 1 integration factory"
    )
    trial.add_argument("--factory", required=True, help="trusted.module:create_service")
    trial.add_argument("--project", default="demo-cart")
    trial.add_argument("--signal", default="cart")
    args = parser.parse_args()
    if args.command == "doctor":
        tools = {n: shutil.which(n) for n in ("docker", "ollama", "codex")}
        docker = tools["docker"]
        app_cli = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
        if not docker and app_cli.exists():
            docker = str(app_cli)
            tools["docker"] = docker
        daemon = False
        if docker:
            try:
                result = subprocess.run(
                    [docker, "info", "--format", "{{.ServerVersion}}"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                daemon = result.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                pass
        print(
            json.dumps(
                {
                    "python": sys.version.split()[0],
                    "tools": tools,
                    "docker_daemon_ready": daemon,
                    "shared_model_guard_integration": "NOT_CONFIGURED_BY_THIS_CLI",
                },
                indent=2,
            )
        )
        return 0
    try:
        if args.command == "baseline":
            from devguard.bootstrap import ASSETS
            from devguard.repair.contracts import ProjectSpec
            spec = ProjectSpec('demo-cart', ASSETS / 'demo', ('cart.py', 'main.py'),
                               ('cart.py',), ASSETS / 'checks', ('cart',), args.image_id)
            result = DockerVerifier(args.docker).run(spec.root, spec, "cart", Event())
            print(
                json.dumps(
                    {
                        "scenario": "declared-buggy-demo",
                        "status": result.status,
                        "exit_code": result.exit_code,
                        "model_used": False,
                    }
                )
            )
            return 1 if result.status == "FAIL" else 0 if result.status == "PASS" else 2
        module_name, separator, factory_name = args.factory.partition(":")
        if not separator:
            raise RepairError("INVALID_FACTORY")
        factory = getattr(importlib.import_module(module_name), factory_name)
        service = factory()
        incident = service.create_incident(args.project, args.signal)
        run = service.queue(incident["incident_id"])
        service.execute(run.run_id)
        # Candidate diff is available through the live service/router, not dumped here.
        print(json.dumps(run.view(), indent=2))
        return 0 if run.state == "READY_FOR_REVIEW" else 2
    except RepairError as error:
        print(json.dumps({"state": "BLOCKED", "reason_code": error.code}))
        return 2
    except (ImportError, AttributeError, ValueError):
        print(
            json.dumps(
                {"state": "BLOCKED", "reason_code": "INTEGRATION_FACTORY_UNAVAILABLE"}
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
