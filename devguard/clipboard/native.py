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
    return UnsupportedClipboard()
