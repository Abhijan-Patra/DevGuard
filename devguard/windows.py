"""Windows-only OS boundaries, imported lazily. Local NTFS paths only.

Directory handles deny delete sharing while in use, pinning every ancestor;
reparse points, alternate streams, devices and multiple hard links are refused.
Runtime objects are created with protected user/SYSTEM ACLs, never chmod alone.
"""
import contextlib
import os
from pathlib import Path, PurePosixPath

# Win32 FILE_READ_ATTRIBUTES and FILE_FLAG_OPEN_REPARSE_POINT. The pinned
# pywin32 win32con module does not export these two SDK constants.
FILE_READ_ATTRIBUTES = 0x80
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000


def relative_parts(name):
    parts = name.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {f'{s}{i}' for s in ('COM', 'LPT') for i in '123456789¹²³'}
    if (not name or len(parts) > 32 or PurePosixPath(name).is_absolute()
            or any(c in name for c in '\\:\0<>"|?*')
            or any(p in {'', '.', '..'} or p.endswith((' ', '.')) or
                   p.split('.')[0].rstrip(' ').upper() in reserved or any(ord(c) < 32 for c in p) for p in parts)):
        raise OSError('WINDOWS_PATH_DENIED')
    return parts


def _api():
    import win32api, win32con, win32file, win32security, pywintypes
    return win32api, win32con, win32file, win32security, pywintypes


def user_sid():
    api, con, _, security, _ = _api()
    token = security.OpenProcessToken(api.GetCurrentProcess(), con.TOKEN_QUERY)
    try:
        return security.GetTokenInformation(token, security.TokenUser)[0]
    finally:
        token.Close()


def private_attributes():
    _, _, _, security, types = _api()
    sid = security.ConvertSidToStringSid(user_sid())
    descriptor = security.ConvertStringSecurityDescriptorToSecurityDescriptor(
        f'O:{sid}D:P(A;OICI;FA;;;{sid})(A;OICI;FA;;;SY)', 1)
    attributes = types.SECURITY_ATTRIBUTES()
    attributes.SECURITY_DESCRIPTOR = descriptor
    return attributes


def check_private(handle):
    _, con, file, security, _ = _api()
    info = file.GetFileInformationByHandle(handle)
    if info[0] & con.FILE_ATTRIBUTE_REPARSE_POINT or (not info[0] & con.FILE_ATTRIBUTE_DIRECTORY and info[7] != 1):
        raise OSError('PRIVATE_REGULAR_OBJECT_REQUIRED')
    sd = security.GetSecurityInfo(handle, security.SE_FILE_OBJECT,
                                 security.OWNER_SECURITY_INFORMATION | security.DACL_SECURITY_INFORMATION)
    owner = security.ConvertSidToStringSid(sd.GetSecurityDescriptorOwner())
    sid = security.ConvertSidToStringSid(user_sid())
    acl = sd.GetSecurityDescriptorDacl()
    if owner != sid or acl is None:
        raise OSError('PRIVATE_USER_ACL_REQUIRED')
    allowed = {sid, 'S-1-5-18', 'S-1-5-32-544'}  # operator, SYSTEM, local administrators
    for i in range(acl.GetAceCount()):
        ace = acl.GetAce(i)
        # Fail closed on unfamiliar/object/callback grants, even inherited ones.
        if ace[0][0] == security.ACCESS_DENIED_ACE_TYPE:
            continue
        if ace[0][0] != security.ACCESS_ALLOWED_ACE_TYPE or security.ConvertSidToStringSid(ace[2]) not in allowed:
            raise OSError('PRIVATE_USER_ACL_REQUIRED')


def local_path(path):
    path = Path(path).absolute()
    if not path.drive or path.drive.startswith('\\\\') or str(path).startswith('\\\\'):
        raise OSError('LOCAL_WINDOWS_VOLUME_REQUIRED')
    api, _, file, _, _ = _api()
    if file.GetDriveType(path.anchor) != 3 or api.GetVolumeInformation(path.anchor)[4].upper() != 'NTFS':
        raise OSError('LOCAL_NTFS_VOLUME_REQUIRED')
    return path


@contextlib.contextmanager
def anchored_directory(path):
    """Lock all directory names against replacement; do not follow junctions."""
    _, con, file, _, _ = _api()
    path = local_path(path)
    handles = []
    try:
        current = Path(path.anchor)
        for part in ('', *path.parts[1:]):
            if part:
                relative_parts(part)
                current /= part
            handle = file.CreateFile(str(current), FILE_READ_ATTRIBUTES | con.READ_CONTROL,
                con.FILE_SHARE_READ, None, con.OPEN_EXISTING,
                con.FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None)
            handles.append(handle)
            actual = file.GetFinalPathNameByHandle(handle, 0)
            if os.path.normcase(actual.removeprefix('\\\\?\\')) != os.path.normcase(str(current)):
                raise OSError('DIRECTORY_ALIAS_DENIED')
            info = file.GetFileInformationByHandle(handle)
            if info[0] & con.FILE_ATTRIBUTE_REPARSE_POINT or not info[0] & con.FILE_ATTRIBUTE_DIRECTORY:
                raise OSError('REPARSE_DIRECTORY_DENIED')
        yield handles[-1]
    except Exception as error:
        import pywintypes
        if isinstance(error, pywintypes.error):
            if error.winerror in {2, 3}:
                raise FileNotFoundError('WINDOWS_OBJECT_NOT_FOUND') from None
            if error.winerror in {80, 183}:
                raise FileExistsError('WINDOWS_OBJECT_EXISTS') from None
            raise OSError('WINDOWS_DIRECTORY_HELD') from None
        raise
    finally:
        for handle in reversed(handles):
            handle.Close()


def private_directory(path):
    _, con, file, _, _ = _api()
    path = local_path(path)
    if not path.parent.exists():
        private_directory(path.parent)
    with anchored_directory(path.parent):
        if not path.exists():
            file.CreateDirectory(str(path), private_attributes())
        with anchored_directory(path) as handle:
            check_private(handle)


def private_open(path, flags, mode=0o600):
    """Return a CRT fd only after handle-based type, link and ACL validation."""
    import msvcrt
    _, con, file, _, _ = _api()
    path = local_path(path)
    access = con.GENERIC_READ if not flags & (os.O_WRONLY | os.O_RDWR) else con.GENERIC_READ | con.GENERIC_WRITE
    creation = con.CREATE_NEW if flags & os.O_EXCL else con.OPEN_ALWAYS if flags & os.O_CREAT else con.OPEN_EXISTING
    with anchored_directory(path.parent) as parent:
        check_private(parent)
        handle = file.CreateFile(str(path), access | con.READ_CONTROL,
            con.FILE_SHARE_READ | con.FILE_SHARE_WRITE, private_attributes(), creation,
            FILE_FLAG_OPEN_REPARSE_POINT, None)
        try:
            check_private(handle)
            fd = msvcrt.open_osfhandle(handle.Detach(), flags & ~os.O_CREAT & ~os.O_EXCL | os.O_BINARY)
        except BaseException:
            handle.Close()
            raise
    if flags & os.O_TRUNC:
        os.ftruncate(fd, 0)
    if flags & os.O_APPEND:
        os.lseek(fd, 0, os.SEEK_END)
    return fd


def read_source(root, name, limit):
    _, con, file, _, _ = _api()
    parts = relative_parts(name)
    path = local_path(root).joinpath(*parts)
    with anchored_directory(path.parent):
        handle = file.CreateFile(str(path), con.GENERIC_READ, con.FILE_SHARE_READ, None,
            con.OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT | con.FILE_FLAG_SEQUENTIAL_SCAN, None)
        try:
            actual = file.GetFinalPathNameByHandle(handle, 0)
            if os.path.normcase(actual.removeprefix('\\\\?\\')) != os.path.normcase(str(path)):
                raise OSError('SOURCE_ALIAS_DENIED')
            info = file.GetFileInformationByHandle(handle)
            if info[0] & (con.FILE_ATTRIBUTE_DIRECTORY | con.FILE_ATTRIBUTE_REPARSE_POINT) or info[7] != 1:
                raise OSError('REGULAR_SOURCE_REQUIRED')
            size = (info[5] << 32) | info[6]
            if size > limit:
                raise OSError('SOURCE_TOO_LARGE')
            data = file.ReadFile(handle, max(1, size))[1] if size else b''
            after = file.GetFileInformationByHandle(handle)
            if len(data) != size or (info[0], info[3:]) != (after[0], after[3:]):
                raise OSError('SOURCE_CHANGED')
            return data
        finally:
            handle.Close()


def replace_source(root, name, data, originals, read):
    """Parents stay pinned; source digests are checked immediately before rename."""
    import uuid
    path = local_path(root).joinpath(*relative_parts(name))
    with anchored_directory(path.parent):
        temporary = path.with_name('.devguard-patch-' + uuid.uuid4().hex)
        try:
            # Parent is operator-selected source; inherit its ACL for the replacement.
            with temporary.open('xb') as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            # Preserve the original file's access restrictions, rather than
            # replacing a private source ACL with the directory's broader ACL.
            _, con, file, security, _ = _api()
            handle = file.CreateFile(str(path), con.READ_CONTROL, con.FILE_SHARE_READ,
                None, con.OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT, None)
            try:
                info = file.GetFileInformationByHandle(handle)
                if info[0] & (con.FILE_ATTRIBUTE_DIRECTORY | con.FILE_ATTRIBUTE_REPARSE_POINT) or info[7] != 1:
                    raise OSError('REGULAR_SOURCE_REQUIRED')
                sd = security.GetSecurityInfo(handle, security.SE_FILE_OBJECT, security.DACL_SECURITY_INFORMATION)
                acl = sd.GetSecurityDescriptorDacl()
                if acl is None:
                    raise OSError('SOURCE_ACL_REQUIRED')
                security.SetNamedSecurityInfo(str(temporary), security.SE_FILE_OBJECT,
                    security.DACL_SECURITY_INFORMATION | security.PROTECTED_DACL_SECURITY_INFORMATION,
                    None, None, acl, None)
            finally:
                handle.Close()
            if any(read(root, n) != content for n, content in originals.items()):
                raise OSError('STALE_SOURCE')
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def process_identity(pid):
    import psutil
    try:
        process = psutil.Process(pid)
        with process.oneshot():
            return process.cmdline(), str(process.create_time())
    except (psutil.Error, OSError):
        return [], ''


def exact_pull_active(model):
    import psutil
    try:
        for process in psutil.process_iter(['name', 'cmdline']):
            args = process.info['cmdline'] or []
            if ((process.info['name'] or '').lower() == 'ollama.exe' and
                    len(args) >= 3 and args[1] in {'pull', 'run'} and args[2] == model):
                return True
    except psutil.Error:
        # Unable to establish absence: do not start a duplicate download.
        raise RuntimeError('Cannot inspect active Ollama downloads; startup is held') from None
    return False


@contextlib.contextmanager
def graceful_server(server, name):
    import threading
    import win32event
    if not name or not __import__('re').fullmatch(r'Local\\DevGuard-[0-9a-f]{64}', name):
        raise RuntimeError('Invalid private shutdown event')
    event = win32event.CreateEvent(private_attributes(), True, False, name)
    done = threading.Event()
    def monitor():
        while not done.is_set():
            if win32event.WaitForSingleObject(event, 200) == win32event.WAIT_OBJECT_0:
                server.should_exit = True
                return
    thread = threading.Thread(target=monitor, name='devguard-shutdown', daemon=True)
    thread.start()
    try:
        yield
    finally:
        done.set();thread.join(timeout=2);event.Close()


def signal_shutdown(name):
    import win32event
    event = win32event.OpenEvent(2, False, name)  # EVENT_MODIFY_STATE
    try:
        win32event.SetEvent(event)
    finally:
        event.Close()


# PyWin32 exceptions are not OSError. Normalize at the native boundary without
# reflecting filenames or private Windows exception payloads into the API/log.
def _normalize_errors(function):
    import functools
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        import pywintypes
        try:
            return function(*args, **kwargs)
        except pywintypes.error as error:
            code = error.winerror
            if code in {2, 3}:
                raise FileNotFoundError('WINDOWS_OBJECT_NOT_FOUND') from None
            if code in {80, 183}:
                raise FileExistsError('WINDOWS_OBJECT_EXISTS') from None
            raise OSError('WINDOWS_OPERATION_HELD') from None
    return wrapped

for _name in ('private_directory', 'private_open', 'check_private', 'read_source',
              'replace_source', 'signal_shutdown'):
    globals()[_name] = _normalize_errors(globals()[_name])
