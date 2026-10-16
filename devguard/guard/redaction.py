"""Exact codepoint spans; no model-supplied replacement strings or raw maps."""

from devguard.schemas.guard import Category, Span


def redact(text: str, spans: list[Span], *, permit_overlap=False):
    ordered = sorted(spans, key=lambda span: (span.start, span.end))
    intervals = []
    for span in ordered:
        if span.end > len(text) or span.end <= span.start:
            raise ValueError("Invalid redaction span")
        if intervals and span.start < intervals[-1][1]:
            if not permit_overlap:
                raise ValueError("Overlapping model spans")
            start, end, categories = intervals[-1]
            intervals[-1] = (start, max(end, span.end), categories | {span.category})
        else:
            intervals.append((span.start, span.end, {span.category}))
    pieces, cursor = [], 0
    for number, (start, end, categories) in enumerate(intervals, 1):
        pieces.append(text[cursor:start])
        label = "CREDENTIAL" if Category.CREDENTIAL in categories else "REDACTED"
        pieces.append(f"[{label}_{number}]")
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)
