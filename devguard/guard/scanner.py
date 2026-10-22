"""Bounded local credential detectors. Raw findings never leave this module."""

import asyncio
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from devguard.schemas.guard import Category, Span


@dataclass
class ScanResult:
    spans: list[Span]
    complete: bool


# Generic security patterns, not demo strings or fixture IDs. Gitleaks supplies
# its independently maintained provider rules in addition to these baselines.
PATTERNS = (
    (re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z]+ )?PRIVATE KEY-----"), 0),
    (re.compile(r"(?i)\b(?:[a-z0-9]+[_-])*(?:api[_-]?key|access[_-]?token|password|client[_-]?secret|secret[_-]?access[_-]?key|access[_-]?key[_-]?id|token)\s*[:=]\s*[\"']?([^\s\"';,}]{8,})"), 1),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), 0),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{16,}\b"), 0),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), 0),
    (re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/-]{12,}=*)"), 1),
    (re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:]+:([^\s/@]+)@"), 1),
)
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}(?![\w-])")

# Narrow imperative policy-override detector. This is defense in depth, not an
# exhaustive injection classifier. Discussion/quotation may still need review.
POLICY_OVERRIDE = re.compile(
    r"(?im)(?:^|[.!?]\s+|:\s+)(?:please\s+)?"
    r"(?:ignore|disregard|disable|bypass|override)\b[^\n.!?]{0,80}"
    r"\b(?:privacy\s+(?:rules|policy|checks)|security\s+(?:filters|rules|policy)|"
    r"(?:previous|system|guard)\s+instructions|(?:the\s+)?(?:privacy\s+)?guard)\b[^\n.!?]*"
)


def baseline_spans(text: str):
    spans = [Span(start=m.start(group), end=m.end(group), category=Category.CREDENTIAL)
             for pattern, group in PATTERNS for m in pattern.finditer(text)
             if not re.fullmatch(r"\[(?:CREDENTIAL|REDACTED)_\d+\]", m.group(group))]
    spans.extend(Span(start=m.start(), end=m.end(), category=Category.PERSONAL_DATA)
                 for m in EMAIL.finditer(text))
    spans.extend(Span(start=m.start(), end=m.end(), category=Category.PROMPT_INJECTION)
                 for m in POLICY_OVERRIDE.finditer(text))
    return spans


@dataclass
class CredentialScanner:
    binary: str | None = field(default=None)

    def __post_init__(self):
        if self.binary is None:
            local = Path(".devguard/tools/gitleaks.exe" if os.name == "nt" else ".devguard/tools/gitleaks")
            self.binary = str(local.resolve()) if local.is_file() else shutil.which("gitleaks")

    @property
    def available(self):
        return self.binary is not None and os.access(self.binary, os.X_OK)

    async def scan(self, text: str):
        spans = baseline_spans(text)
        if not self.available:
            return ScanResult(spans, complete=False)
        process = None
        try:
            # Empty, trusted cwd/config environment prevents a selected repo's
            # allowlist/config from downgrading the embedded credential rules.
            with tempfile.TemporaryDirectory(prefix="devguard-scan-") as directory:
                process = await asyncio.create_subprocess_exec(
                    self.binary, "stdin", "--no-banner", "--log-level", "error",
                    "--report-format", "json", "--report-path", "-",
                    "--exit-code", "0", "--ignore-gitleaks-allow",
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL, cwd=directory,
                    env={**{key: os.environ[key] for key in ('SystemRoot', 'WINDIR') if key in os.environ},
                         "PATH": os.defpath, "HOME": directory, "USERPROFILE": directory},
                )
                stdout, _ = await asyncio.wait_for(process.communicate(text.encode()), timeout=5)
            if process.returncode or len(stdout) > 1024 * 1024:
                return ScanResult(spans, complete=False)
            findings = json.loads(stdout or b"[]")
            if not isinstance(findings, list):
                return ScanResult(spans, complete=False)
            for finding in findings:
                secret = finding.get("Secret")
                if not isinstance(secret, str) or not secret or secret not in text:
                    return ScanResult(spans, complete=False)
                offset = 0
                while (start := text.find(secret, offset)) >= 0:
                    spans.append(Span(start=start, end=start + len(secret), category=Category.CREDENTIAL))
                    offset = start + len(secret)
            return ScanResult(spans, complete=True)
        except (OSError, asyncio.TimeoutError, ValueError, AttributeError):
            return ScanResult(spans, complete=False)
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()
