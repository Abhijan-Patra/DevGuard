"""Lazy macOS NSPasteboard bridge. Construction/status do not read clipboard text."""

import sys


class ClipboardUnsupported(Exception):
    pass


class UnsupportedClipboard:
    available = False


class MacClipboard:
    available = True

    def __init__(self):
        import AppKit
        import objc
        self.appkit, self.objc = AppKit, objc
        self.board = None

    def _board(self):
        if self.board is None:
            self.board = self.appkit.NSPasteboard.generalPasteboard()
        return self.board

    def counter(self):
        with self.objc.autorelease_pool():
            return int(self._board().changeCount())

    def read_text(self, limit):
        with self.objc.autorelease_pool():
            board = self._board()
            kind = self.appkit.NSPasteboardTypeString
            if kind not in (board.types() or []):
                return "NON_TEXT", None
            data = board.dataForType_(kind)
            if data is None:
                return "UNAVAILABLE", None
            if data.length() > limit:
                return "OVERSIZE", None
            try:
                return "TEXT", bytes(data).decode("utf-8", errors="strict")
            except UnicodeError:
                return "UNAVAILABLE", None

    def write_text(self, expected_counter, text):
        # NSPasteboard has no cross-application compare-and-swap. These checks
        # minimise the race; a lost ownership/write is reported, never retried.
        with self.objc.autorelease_pool():
            board = self._board()
            if int(board.changeCount()) != expected_counter:
                return None
            owned = int(board.clearContents())
            if int(board.changeCount()) != owned:
                return None
            if not board.setString_forType_(text, self.appkit.NSPasteboardTypeString):
                return None
            after = int(board.changeCount())
            return after if after == owned else None


def native_clipboard():
    if sys.platform == "darwin":
        try:
            return MacClipboard()
        except (ImportError, OSError):
            pass
    if sys.platform == "win32":
        try:
            return WindowsClipboard()
        except (ImportError, OSError):
            pass
    return UnsupportedClipboard()


class ClipboardBusy(Exception):
    """Transient clipboard contention; retry next poll without disabling consent."""


class WindowsClipboard:
    """CF_UNICODETEXT only. No text read until the service observes a new copy."""
    available = True

    def __init__(self, api=None):
        self.api = api if api is not None else _WindowsClipboardAPI()

    def counter(self):
        return self.api.counter()

    def read_text(self, limit):
        return self.api.read_text(limit)

    def write_text(self, expected_counter, text):
        if '\0' in text:
            return None
        return self.api.write_text(expected_counter, text)


class _WindowsClipboardAPI:
    def __init__(self):
        import ctypes
        from ctypes import wintypes
        import win32clipboard, win32gui
        self.clip, self.gui = win32clipboard, win32gui
        self.ctypes = ctypes
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.user.GetClipboardData.argtypes = [wintypes.UINT]
        self.user.GetClipboardData.restype = wintypes.HANDLE
        self.kernel.GlobalSize.argtypes = [wintypes.HANDLE]
        self.kernel.GlobalSize.restype = ctypes.c_size_t
        self.kernel.GlobalLock.argtypes = [wintypes.HANDLE]
        self.kernel.GlobalLock.restype = ctypes.c_void_p
        self.kernel.GlobalUnlock.argtypes = [wintypes.HANDLE]
        self.kernel.GlobalUnlock.restype = wintypes.BOOL

    def counter(self):
        return int(self.clip.GetClipboardSequenceNumber())

    def _open(self, window=0):
        try:
            self.clip.OpenClipboard(window)
        except Exception:
            raise ClipboardBusy() from None

    def read_text(self, limit):
        self._open()
        try:
            if not self.clip.IsClipboardFormatAvailable(13):
                return 'NON_TEXT', None
            handle = self.user.GetClipboardData(13)
            if not handle:
                return 'UNAVAILABLE', None
            size = self.kernel.GlobalSize(handle)
            # UTF-16 can be twice the UTF-8 byte budget for ASCII. Bound before copying.
            if size < 2 or size % 2:
                return 'UNAVAILABLE', None
            if size > 2 * (limit + 1):
                return 'OVERSIZE', None
            pointer = self.kernel.GlobalLock(handle)
            if not pointer:
                return 'UNAVAILABLE', None
            try:
                raw = self.ctypes.string_at(pointer, size)
            finally:
                self.kernel.GlobalUnlock(handle)
            end = next((i for i in range(0, len(raw), 2) if raw[i:i+2] == b'\0\0'), None)
            if end is None:
                return 'UNAVAILABLE', None
            try:
                text = raw[:end].decode('utf-16-le', errors='strict')
                if len(text.encode('utf-8')) > limit:
                    return 'OVERSIZE', None
                return 'TEXT', text
            except UnicodeError:
                return 'UNAVAILABLE', None
        finally:
            self.clip.CloseClipboard()

    def write_text(self, expected_counter, text):
        # A real owner window is required: OpenClipboard(NULL)+EmptyClipboard
        # makes SetClipboardData fail. The message-only window is thread-local.
        window = self.gui.CreateWindowEx(0, 'STATIC', 'DevGuard clipboard owner',
            0, 0, 0, 0, 0, -3, 0, 0, None)
        try:
            self._open(window)
            try:
                if self.counter() != expected_counter:
                    return None
                self.clip.EmptyClipboard()
                self.clip.SetClipboardData(13, text)
                return self.counter()
            finally:
                self.clip.CloseClipboard()
        finally:
            self.gui.DestroyWindow(window)
