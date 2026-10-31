from dataclasses import dataclass

from ..models.provider import TokenUsage


class DraftError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class SourceRef:
    id: str
    version: str
    content_hash: str


@dataclass(frozen=True)
class SourceSnapshot:
    id: str
    version: str
    content_hash: str
    title: str
    origin: str
    text: str
    proposal_id: str | None
    is_public: bool


@dataclass(frozen=True)
class DraftRequest:
    proposal_id: str
    base_revision: int
    section: str
    instruction: str
    source_refs: tuple[SourceRef, ...]


@dataclass(frozen=True)
class Citation:
    source_id: str
    version: str
    content_hash: str
    title: str
    origin: str
    quote: str


@dataclass(frozen=True)
class DraftResult:
    text: str
    citations: tuple[Citation, ...]
    base_revision: int
    source_refs: tuple[SourceRef, ...]
    model_id: str | None
    usage: TokenUsage | None
    input_tokens: int
    finish_reason: str
    insufficient_evidence: bool
