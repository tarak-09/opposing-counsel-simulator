from __future__ import annotations

import json
import logging
import math
import time
from collections import Counter

import httpx
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.config import get_settings
from app.llm.types import EmbeddingProvider, ModelT, StructuredReasoningProvider


logger = logging.getLogger(__name__)


class OpenAICompatibleReasoningProvider(StructuredReasoningProvider):
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT:
        return self._generate_json_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((httpx.HTTPError, ValueError)),
        reraise=True,
    )
    def _generate_json_with_retry(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema(),
            },
        }
        t0 = time.monotonic()
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.llm_model,
                    "temperature": 0.1,
                    "response_format": response_format,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
        latency_ms = round((time.monotonic() - t0) * 1000)
        usage = payload.get("usage", {})
        logger.info(
            "llm call model=%s response_model=%s latency_ms=%d "
            "prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            self.settings.llm_model,
            response_model.__name__,
            latency_ms,
            usage.get("prompt_tokens", "?"),
            usage.get("completion_tokens", "?"),
            usage.get("total_tokens", "?"),
        )
        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        else:
            text = content
        if not text:
            raise ValueError("Model returned empty content")
        return response_model.model_validate_json(text)


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.settings = get_settings()

    def embed(self, texts: list[str]) -> list[list[float]]:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                f"{self.settings.embedding_base_url.rstrip('/')}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.settings.embedding_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.settings.embedding_model, "input": texts},
            )
            response.raise_for_status()
            payload = response.json()
        return [item["embedding"] for item in payload["data"]]


class HashEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.settings = get_settings()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embed(text, self.settings.embedding_dimension) for text in texts]


def get_reasoning_provider() -> StructuredReasoningProvider | None:
    settings = get_settings()
    if settings.llm_api_key and settings.llm_provider == "openai_compatible":
        logger.debug("reasoning provider=openai_compatible model=%s", settings.llm_model)
        return OpenAICompatibleReasoningProvider()
    logger.debug("reasoning provider=none; rule-based fallback will be used")
    return None


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_api_key and settings.embedding_provider == "openai_compatible":
        logger.debug("embedding provider=openai_compatible model=%s", settings.embedding_model)
        return OpenAICompatibleEmbeddingProvider()
    logger.debug("embedding provider=hash (local fallback)")
    return HashEmbeddingProvider()


def json_dumps_pretty(payload: BaseModel | dict[str, object]) -> str:
    if isinstance(payload, BaseModel):
        return payload.model_dump_json(indent=2)
    return json.dumps(payload, indent=2)


def _hash_embed(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    tokens = [token for token in text.lower().split() if token]
    counts = Counter(tokens)
    for token, count in counts.items():
        bucket = hash(token) % dimensions
        sign = -1.0 if hash(f"{token}:sign") % 2 else 1.0
        vector[bucket] += sign * float(count)
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
