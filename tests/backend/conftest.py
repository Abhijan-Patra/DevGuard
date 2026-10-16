import pytest

from devguard.repair.contracts import ProjectSpec


@pytest.fixture
def spec(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "cart.py").write_text("VALUE = 1\n")
    (root / "main.py").write_text("# independent dependency\n")
    checks = tmp_path / "checks"
    checks.mkdir()
    (checks / "test_cart.py").write_text("# protected verifier fixture\n")
    return ProjectSpec(
        "demo",
        root.resolve(),
        ("cart.py", "main.py"),
        ("cart.py",),
        checks,
        ("cart",),
        "sha256:" + "a" * 64,
    )
