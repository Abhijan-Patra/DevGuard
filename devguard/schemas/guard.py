from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_TEXT_BYTES = 32 * 1024


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class Decision(StrEnum):
    ALLOW = "ALLOW"
    SANITIZE = "SANITIZE"
    LOCAL_ONLY = "LOCAL_ONLY"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class Category(StrEnum):
    CREDENTIAL = "CREDENTIAL"
    PERSONAL_DATA = "PERSONAL_DATA"
    CONFIDENTIAL = "CONFIDENTIAL"
    IRRELEVANT = "IRRELEVANT"
    PROMPT_INJECTION = "PROMPT_INJECTION"


class GuardInput(StrictModel):
    project_id: str | None = Field(default=None, max_length=100)
    task: str | None = Field(default=None, max_length=2048)
    surface: str = Field(pattern=r"^(explicit_prompt|tool_result|file_read|clipboard)$")
    destination_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    content_version: int = Field(ge=0, strict=True)
    text: str = Field(max_length=MAX_TEXT_BYTES, repr=False)

    @field_validator("text")
    @classmethod
    def bound_bytes(cls, value):
        if len(value.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("Text exceeds the local inspection byte budget")
        return value

    @field_validator("task")
    @classmethod
    def explicit_task(cls, value):
        return value.strip() or None if value is not None else None


class Span(StrictModel):
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    category: Category


class ModelProposal(StrictModel):
    decision: Decision
    spans: list[Span] = Field(max_length=256)


class DeliveryInput(StrictModel):
    content_version: int = Field(ge=0, strict=True)
    destination_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")


class ClipboardEnable(StrictModel):
    consent: bool = Field(strict=True)
    task: str | None = Field(default=None, max_length=2048)


class ClipboardCopy(StrictModel):
    content_version: int = Field(ge=0, strict=True)
