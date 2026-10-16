"""Start the loopback control API with a private local session token."""

import argparse
import os
from pathlib import Path
import secrets
import stat

import uvicorn

from devguard.api.app import create_app
from devguard.config import Settings
from devguard.storage.audit import AuditStore
from devguard.api.repair_integration import demo_repair_factory


def session_token():
    configured = os.environ.get("DEVGUARD_SESSION_TOKEN")
    if configured:
        return configured
    directory = Path(".devguard")
    if directory.is_symlink():
        raise ValueError("Runtime directory must not be a symlink")
    directory.mkdir(mode=0o700, exist_ok=True)
    token_file = directory / "session-token"
    try:
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(token_file, flags)
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
                raise ValueError("Session token must be a private regular file")
            return stream.read(512).strip()
    else:
        with os.fdopen(fd, "w") as stream:
            token = secrets.token_urlsafe(32)
            stream.write(token)
        return token


def main():
    parser = argparse.ArgumentParser(description="DevGuard local control API")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo-image-id", help="Opt into the named cart demo using an existing sha256 Docker image ID")
    args = parser.parse_args()
    settings = Settings.from_environment(session_token())
    print("DevGuard: http://127.0.0.1:%s (clipboard capture starts disabled)" % args.port)
    print("Operator token stays local in .devguard/session-token unless configured by environment.")
    audit = AuditStore(Path(".devguard") / "audit.sqlite3")
    factory = demo_repair_factory(Path.cwd(), args.demo_image_id) if args.demo_image_id else None
    uvicorn.run(create_app(settings, audit=audit, repair_factory=factory),
                host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
