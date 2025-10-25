"""Ingestion utilities for pushing product specifications into Weaviate.

The module supports two embedding strategies:
1. ``document`` – push the entire specification as a single chunk.
2. ``chunked`` – extract text, split into manageable chunks, and store each chunk.

Use ``SpecIngestor`` to orchestrate parsing, chunking, and Weaviate persistence.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from pydantic import BaseModel, Field, validator

from weaviate_utils import ARTICLE_SPEC_COLLECTION

try:
    import tiktoken  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    tiktoken = None  # type: ignore


LOGGER = logging.getLogger(__name__)


class ProductSpecMetadata(BaseModel):
    """Normalized metadata that aligns with the ArticleSpec schema."""

    partNumber: Optional[str] = None
    vendor: Optional[str] = None
    title: Optional[str] = None
    materials: List[str] = Field(default_factory=list)
    mediaType: Optional[str] = None
    weight_g: Optional[float] = None
    dims_mm: Optional[List[float]] = None
    processes: List[str] = Field(default_factory=list)

    @validator("materials", "processes", allow_reuse=True)
    def _strip_items(cls, values: Iterable[str]) -> List[str]:  # noqa: N805
        return [v.strip() for v in values if v and v.strip()]

    @validator("dims_mm", pre=True)
    def _normalize_dims(cls, value: Optional[Iterable[float]]) -> Optional[List[float]]:  # noqa: N805
        if value is None:
            return None
        floats = []
        for item in value:
            try:
                floats.append(float(item))
            except (TypeError, ValueError):
                LOGGER.warning("Skipping non-numeric dimension value: %s", item)
        return floats or None

    def as_properties(self) -> dict:
        payload = self.dict(exclude_none=True)
        payload.setdefault("mediaType", "unknown")
        return payload


@dataclass
class ChunkingConfig:
    max_tokens: int = 900
    overlap_tokens: int = 120
    approximate_chars_per_token: int = 4


def _split_by_tokens(text: str, max_tokens: int, overlap: int) -> List[str]:
    if not text:
        return []

    if tiktoken:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        chunks: List[str] = []
        start = 0
        length = len(tokens)
        while start < length:
            end = min(start + max_tokens, length)
            chunk_tokens = tokens[start:end]
            chunks.append(enc.decode(chunk_tokens))
            if end == length:
                break
            start = max(0, end - overlap)
        return chunks

    # Character-based fallback if tiktoken is unavailable.
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunks.append(text[start:end])
        if end == length:
            break
        start = max(0, end - overlap_chars)
    return chunks


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF (fitz) is required to extract text from PDF documents."
            ) from exc
        doc = fitz.open(path.as_posix())
        return "\n".join(page.get_text("text") for page in doc)

    return path.read_text(encoding="utf-8")


@dataclass
class SpecIngestor:
    client: "weaviate.WeaviateClient"
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)

    def ingest_document(
        self,
        document_path: Path,
        metadata: ProductSpecMetadata,
        *,
        strategies: Sequence[str] = ("document", "chunked"),
        chunking_override: Optional[ChunkingConfig] = None,
    ) -> List[str]:
        """Insert the product specification using the requested strategies.

        Returns the list of UUIDs inserted into Weaviate.
        """

        if not strategies:
            raise ValueError("Provide at least one ingestion strategy.")

        text = extract_text(document_path)
        if not text.strip():
            raise ValueError(f"No text extracted from {document_path}.")

        base_properties = metadata.as_properties()
        media_type = base_properties.get("mediaType") or _guess_media_type(document_path)
        base_properties["mediaType"] = media_type

        collection = self.client.collections.get(ARTICLE_SPEC_COLLECTION)
        uuids: List[str] = []

        resolved_chunking = chunking_override or self.chunking

        for strategy in strategies:
            strategy_lower = strategy.lower()
            if strategy_lower == "document":
                chunk_uuid = str(uuid.uuid4())
                properties = {
                    **base_properties,
                    "text": text,
                    "embeddingScope": "document",
                }
                collection.data.insert(properties=properties, uuid=chunk_uuid)
                uuids.append(chunk_uuid)
            elif strategy_lower == "chunked":
                chunks = _split_by_tokens(
                    text,
                    max_tokens=resolved_chunking.max_tokens,
                    overlap=resolved_chunking.overlap_tokens,
                )
                for chunk_text in chunks:
                    if not chunk_text.strip():
                        continue
                    chunk_uuid = str(uuid.uuid4())
                    properties = {
                        **base_properties,
                        "text": chunk_text,
                        "embeddingScope": "chunk",
                    }
                    collection.data.insert(properties=properties, uuid=chunk_uuid)
                    uuids.append(chunk_uuid)
            else:
                raise ValueError(f"Unsupported ingestion strategy: {strategy}")

        return uuids


def _guess_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".txt", ".md"}:
        return "text"
    if suffix in {".png", ".jpg", ".jpeg"}:
        return "image"
    return "unknown"


__all__ = [
    "ProductSpecMetadata",
    "ChunkingConfig",
    "SpecIngestor",
    "extract_text",
]
