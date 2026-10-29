from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from .pep import PepRequest, PepResponse
from .projection import PublishableProjection
from .values import GenerationRequest, GenerationResult, KeyRef, RelationTuple, RetrievedItem


@runtime_checkable
class IRetrievalStrategy(Protocol):
    async def retrieve(
        self,
        *,
        query: str,
        tenant_id: str,
        top_k: int = 8,
        confidential_surface: bool = False,
    ) -> Sequence[RetrievedItem]:
        ...


@runtime_checkable
class IVectorStore(Protocol):
    async def upsert(self, items: Sequence[RetrievedItem]) -> None:
        ...

    async def search(self, query_vector: Sequence[float], top_k: int) -> Sequence[RetrievedItem]:
        ...


@runtime_checkable
class ILexicalIndex(Protocol):
    async def upsert(self, items: Sequence[RetrievedItem]) -> None:
        ...

    async def search(self, query: str, top_k: int) -> Sequence[RetrievedItem]:
        ...


@runtime_checkable
class IGraph(Protocol):
    async def upsert(self, relations: Sequence[RelationTuple]) -> None:
        ...

    async def neighborhood(self, node_id: str, depth: int = 1) -> Sequence[RelationTuple]:
        ...


@runtime_checkable
class IModelProvider(Protocol):
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        ...


@runtime_checkable
class IModelRouter(Protocol):
    async def route(self, request: GenerationRequest) -> GenerationResult:
        ...


@runtime_checkable
class IKms(Protocol):
    async def get_key(self, *, tenant_id: str, purpose: str) -> KeyRef:
        ...


@runtime_checkable
class IAuditSink(Protocol):
    async def emit(self, event: object) -> None:
        ...


@runtime_checkable
class IPep(Protocol):
    async def authorize(self, request: PepRequest) -> PepResponse:
        ...


@runtime_checkable
class IGrantStore(Protocol):
    async def publish(self, projection: PublishableProjection) -> None:
        ...


@runtime_checkable
class IRevocationAuthority(Protocol):
    async def is_revoked(self, *, tenant_id: str, resource_id: str) -> bool:
        ...


@runtime_checkable
class IExchangeFeed(Protocol):
    async def publish(self, projection: PublishableProjection) -> None:
        ...