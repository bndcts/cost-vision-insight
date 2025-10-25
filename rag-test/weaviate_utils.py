"""Utilities for connecting to Weaviate and ensuring the schema is provisioned.

This module keeps the schema definition centralized so the ingestion and
retrieval code can rely on consistent property naming.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.init import AdditionalConfig


ARTICLE_SPEC_COLLECTION = "ArticleSpec"
COST_MODEL_COLLECTION = "CostModel"


@dataclass(frozen=True)
class WeaviateConnectionSettings:
    """Runtime settings collected from the environment."""

    url: Optional[str] = None
    api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "WeaviateConnectionSettings":
        return cls(
            url=os.environ.get("WEAVIATE_URL"),
            api_key=os.environ.get("WEAVIATE_API_KEY"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
        )


def connect(settings: Optional[WeaviateConnectionSettings] = None) -> weaviate.WeaviateClient:
    """Create a Weaviate client using either cloud or local credentials.

    The caller is responsible for closing the client when finished.
    """

    resolved = settings or WeaviateConnectionSettings.from_env()
    headers = {}
    if resolved.openai_api_key:
        headers["X-OpenAI-Api-Key"] = resolved.openai_api_key

    if resolved.url:
        auth = AuthApiKey(resolved.api_key) if resolved.api_key else None
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=resolved.url,
            auth_credentials=auth,
            headers=headers or None,
            additional_config=AdditionalConfig(timeout=(15, 60)),
        )
    else:
        # Fallback assumes a local instance without authentication.
        client = weaviate.connect_to_local(
            host="127.0.0.1",
            port=8080,
            headers=headers or None,
            additional_config=AdditionalConfig(timeout=(15, 60)),
        )

    return client


def ensure_schema(client: weaviate.WeaviateClient, *, rebuild: bool = False) -> None:
    """Create the ArticleSpec and CostModel collections if missing.

    Set ``rebuild`` to True when you want to drop and recreate the schema.
    This will delete existing data, so the flag defaults to False.
    """

    if rebuild:
        client.collections.delete(ARTICLE_SPEC_COLLECTION, ignore=True)
        client.collections.delete(COST_MODEL_COLLECTION, ignore=True)

    if not client.collections.exists(ARTICLE_SPEC_COLLECTION):
        client.collections.create(
            name=ARTICLE_SPEC_COLLECTION,
            description="Product specification chunks and normalized metadata",
            vectorizer_config=Configure.Vectorizer.text2vec_openai(),
            properties=[
                Property(name="partNumber", data_type=DataType.TEXT, tokenization="field"),
                Property(name="vendor", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="materials", data_type=DataType.TEXT_ARRAY),
                Property(name="mediaType", data_type=DataType.TEXT),
                Property(name="weight_g", data_type=DataType.NUMBER),
                Property(name="dims_mm", data_type=DataType.NUMBER_ARRAY),
                Property(name="processes", data_type=DataType.TEXT_ARRAY),
                Property(name="text", data_type=DataType.TEXT),
                Property(name="embeddingScope", data_type=DataType.TEXT),
            ],
        )

    if not client.collections.exists(COST_MODEL_COLLECTION):
        client.collections.create(
            name=COST_MODEL_COLLECTION,
            description="Structured cost model snapshots and assumptions",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="material_cost_eur_per_unit", data_type=DataType.NUMBER),
                Property(name="labor_cost_eur_per_unit", data_type=DataType.NUMBER),
                Property(name="energy_cost_eur_per_unit", data_type=DataType.NUMBER),
                Property(name="overhead_eur_per_unit", data_type=DataType.NUMBER),
                Property(name="volume_assumption", data_type=DataType.NUMBER),
                Property(name="currency", data_type=DataType.TEXT),
                Property(name="notes", data_type=DataType.TEXT),
                Property(name="version", data_type=DataType.TEXT),
                Property(
                    name="spec",
                    data_type=DataType.CROSS_REFERENCE,
                    target_collection=ARTICLE_SPEC_COLLECTION,
                ),
            ],
        )


__all__ = [
    "ARTICLE_SPEC_COLLECTION",
    "COST_MODEL_COLLECTION",
    "WeaviateConnectionSettings",
    "connect",
    "ensure_schema",
]
