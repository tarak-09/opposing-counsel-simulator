from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


class StructuredReasoningProvider(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT: ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
