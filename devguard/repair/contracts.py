"""Mac 2 internal types. Shared API/model/guard schemas remain owned by Mac 1."""

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any, Protocol

SELECTED_MODEL = "gemma4:e4b-it-q4_K_M"


class RepairError(Exception):
    """Only fixed, non-sensitive codes may cross the API boundary."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class GuardPort(Protocol):
    def sanitize(self, text: str, *, purpose: str) -> str:
        """Return approved local-model/export text, or raise RepairError to hold."""
        ...


class ModelPort(Protocol):
    @property
    def metadata(self) -> dict[str, str]:
        """Must include the selected explicit Q4 tag and a nonempty actual digest."""
        ...

    def next_action(self, messages: list[dict[str, Any]], tools: list[dict]) -> dict:
        """Call Mac 1's bounded shared queue; return one validated action object."""
        ...


@dataclass(frozen=True)
class ProjectSpec:
    project_id: str
    root: Path
    source_files: tuple[str, ...]
    writable_files: tuple[str, ...]
    trusted_tests: Path
    test_names: tuple[str, ...]
    image_id: str


@dataclass(frozen=True)
class TestResult:
    status: str
    output: str = field(default="", repr=False)
    exit_code: int | None = None


class VerifierPort(Protocol):
    def run(
        self, source: Path, spec: ProjectSpec, name: str, cancel: Event
    ) -> TestResult: ...


@dataclass
class Run:
    run_id: str
    incident_id: str
    project_id: str
    state: str = "QUEUED"
    candidate_id: str | None = None
    baseline: str | None = None
    verification: str | None = None
    reason_code: str | None = None
    model: dict[str, str] = field(default_factory=dict)
    completed_tools: list[str] = field(default_factory=list)
    cancel: Event = field(default_factory=Event, repr=False)

    def view(self) -> dict[str, Any]:
        return {k: v for k, v in vars(self).items() if k != "cancel"}
