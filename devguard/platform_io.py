"""Private runtime files and cross-process locks, with OS-specific enforcement."""
import contextlib
import os
from pathlib import Path
import stat


def private_directory(path):
    if os.name == 'nt':
        from devguard.windows import private_directory as create
        return create(path)
    path = Path(path)
    if path.is_symlink():
        raise RuntimeError('Runtime directory cannot be a symlink')
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if info.st_mode & 0o077 or info.st_uid != os.getuid():
        raise RuntimeError('Runtime directory must be private (mode 0700)')


def private_open(path, flags, mode=0o600):
    if os.name == 'nt':
        from devguard.windows import private_open as open_file
        return open_file(path, flags, mode)
    # Validate before any truncation, including a pre-existing hard link.
    fd = os.open(path, (flags & ~os.O_TRUNC) | getattr(os, 'O_NOFOLLOW', 0), mode)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_mode & 0o077 or info.st_uid != os.getuid()):
            raise RuntimeError('Runtime files must be private, regular and owned by this user')
        if flags & os.O_TRUNC:
            os.ftruncate(fd, 0)
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextlib.contextmanager
def file_lock(path, *, blocking=False):
    fd = private_open(path, os.O_RDWR | os.O_CREAT)
    with os.fdopen(fd, 'r+b') as stream:
        if os.name == 'nt':
            import msvcrt
            if not os.fstat(stream.fileno()).st_size:
                stream.write(b'\0');stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
            except OSError:
                raise BlockingIOError('Another launcher operation is active; do not start a duplicate') from None
            try:
                yield
            finally:
                stream.seek(0);msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            yield
