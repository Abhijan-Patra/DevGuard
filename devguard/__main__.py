"""Start the loopback control API with a private local session token."""

import argparse
import os
from pathlib import Path
import secrets
import stat
import sys

import uvicorn

from devguard.api.app import create_app
from devguard.config import MODEL, Settings
from devguard.storage.audit import AuditStore
from devguard.api.repair_integration import demo_repair_factory
from devguard.api.repair_integration import projects_repair_factory
from devguard.repair.projects import load_projects


def session_token(name='session-token', variable="DEVGUARD_SESSION_TOKEN"):
    configured = os.environ.get(variable)
    if configured:
        return configured
    directory = Path(".devguard")
    if directory.is_symlink():
        raise ValueError("Runtime directory must not be a symlink")
    directory.mkdir(mode=0o700, exist_ok=True)
    token_file = directory / name
    try:
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(token_file, flags)
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or (os.name != "nt" and (info.st_mode & 0o077 or info.st_uid != os.getuid()))):
                raise ValueError("Session token must be a private regular file")
            return stream.read(512).strip()
    else:
        with os.fdopen(fd, "w") as stream:
            token = secrets.token_urlsafe(32)
            stream.write(token)
        return token


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {'start', 'stop', 'status', 'doctor'}:
        from devguard.local import main as launch
        return launch(argv)
    if argv and argv[0] == 'serve':
        argv.pop(0)
    from importlib.metadata import version
    parser = argparse.ArgumentParser(description="DevGuard local control API",
        epilog='User commands: devguard doctor | devguard start | devguard status | devguard stop. Use serve for foreground/API-only operation.')
    parser.add_argument('--version', action='version', version='DevGuard ' + version('devguard'))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo-image-id", help="Opt into the named cart demo using an existing sha256 Docker image ID")
    parser.add_argument('--projects-config', type=Path, help='Reviewed local JSON manifest; roots and tests cannot be changed over HTTP')
    parser.add_argument('--no-browser-pairing', action='store_true', help='Disable same-origin local workspace enrolment')
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port between 1024 and 65535')
    if sys.platform not in {'darwin', 'linux'}:
        parser.error('This local preview supports macOS/Linux; Windows native capture is not implemented')
    if args.projects_config:
        args.projects_config = args.projects_config.expanduser().resolve(strict=True)
    from devguard.local import private_root, ROOT
    private_root()
    os.chdir(ROOT)
    settings = Settings(session_token(),
        ollama_url=os.environ.get('DEVGUARD_OLLAMA_URL', 'http://127.0.0.1:11434'),
        model=os.environ.get('DEVGUARD_MODEL', MODEL),
        adapter_token=session_token('client-token', 'DEVGUARD_ADAPTER_TOKEN'))
    print("DevGuard: http://127.0.0.1:%s (clipboard capture starts disabled)" % args.port)
    print("Operator token stays local in .devguard/session-token unless configured by environment.")
    audit = AuditStore(Path(".devguard") / "audit.sqlite3")
    factory = demo_repair_factory(Path.cwd(), args.demo_image_id) if args.demo_image_id else None
    if args.projects_config:
        if args.demo_image_id:
            parser.error('Choose --projects-config or --demo-image-id')
        factory = projects_repair_factory(Path.cwd(), load_projects(args.projects_config))
    uvicorn.run(create_app(settings, audit=audit, repair_factory=factory,
                           browser_workspace=not args.no_browser_pairing),
                host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    raise SystemExit(main())
