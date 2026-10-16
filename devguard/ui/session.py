"""Explicit local operator enrolment. Tokens stay in non-widget server session state."""
import os
from pathlib import Path
import stat
from urllib.parse import urlsplit
from devguard.ui.client import DevGuardError


def load_local_token(base_url):
    url=urlsplit(base_url)
    if (url.scheme!='http' or url.hostname not in {'127.0.0.1','localhost'}
            or url.port!=8765 or url.path.rstrip('/')!='/api/v1'
            or url.username or url.password or url.query or url.fragment):
        raise DevGuardError('Local enrolment requires the default DevGuard endpoint on this Mac.',code='LOCAL_ENROLMENT_REQUIRED')
    path=Path(__file__).resolve().parents[2]/'.devguard/session-token'
    fd=None
    try:
        if path.parent.is_symlink() or path.is_symlink():raise ValueError
        fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_mode&0o077
                or (hasattr(os,'getuid') and info.st_uid!=os.getuid())):raise ValueError
        token=os.read(fd,513).decode().strip()
        if not 32<=len(token)<=128:raise ValueError
        return token
    except (OSError,ValueError,UnicodeError):
        raise DevGuardError('Start the backend on this Mac first; its private operator token is unavailable.',code='LOCAL_TOKEN_UNAVAILABLE') from None
    finally:
        if fd is not None:os.close(fd)
