"""Trusted demo registration. Never accept these paths/image IDs from model arguments."""

from pathlib import Path

from devguard.repair.contracts import ProjectSpec


def demo_project(repository_root: Path, image_id: str) -> ProjectSpec:
    repository_root = repository_root.resolve()
    return ProjectSpec(
        project_id="demo-cart",
        root=repository_root / "demo/backend",
        source_files=("cart.py", "main.py"),
        writable_files=("cart.py",),
        trusted_tests=repository_root / "trusted_tests",
        test_names=("cart",),
        image_id=image_id,
    )
