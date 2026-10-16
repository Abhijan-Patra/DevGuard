import asyncio
import threading

import pytest

from devguard.repair.contracts import ProjectSpec


@pytest.fixture
def loop():
    event_loop = asyncio.new_event_loop()
    started = threading.Event()

    def run():
        event_loop.call_soon(started.set)
        event_loop.run_forever()

    thread = threading.Thread(target=run)
    thread.start()
    started.wait(timeout=2)
    yield event_loop
    event_loop.call_soon_threadsafe(event_loop.stop)
    thread.join(timeout=2)
    event_loop.close()


@pytest.fixture
def spec(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "cart.py").write_text("VALUE = 1\n", newline="\n")
    (root / "main.py").write_text("# independent dependency\n", newline="\n")
    checks = tmp_path / "checks"
    checks.mkdir()
    (checks / "test_cart.py").write_text("# protected verifier fixture\n", newline="\n")
    return ProjectSpec(
        "demo",
        root.resolve(),
        ("cart.py", "main.py"),
        ("cart.py",),
        checks,
        ("cart",),
        "sha256:" + "a" * 64,
    )
