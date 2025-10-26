# RAG Product Spec Ingestion

> Utilities for loading product specifications into Weaviate for semantic search

## Overview

Tools for ingesting product specification documents into Weaviate vector database, enabling semantic similarity search for cost model experimentation.

## Components

- **`weaviate_utils.py`** - Weaviate connection and schema management
- **`spec_ingest.py`** - Document processing and embedding generation
- **`rag1.py`** - CLI wrapper for ingestion

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export WEAVIATE_URL="https://<cluster>.weaviate.network"
export WEAVIATE_API_KEY="your-weaviate-key"
export OPENAI_API_KEY="your-openai-key"
```

### 3. Ingest Document

```bash
python rag1.py ./sample.pdf \
  --vendor "Acme" \
  --title "Acme 90° elbow" \
  --material PBT --material Stainless \
  --process injection_molding --process assembly \
  --weight-g 12.4 \
  --dims-mm 45 20 18
```

## Features

### Embedding Strategies

- **Document-level**: Embed entire document as single vector
- **Chunked**: Split document into chunks with separate embeddings

Control with `--strategy document` or `--strategy chunked` flags. Default: both strategies.

### Schema Management

```bash
# Rebuild schema (destructive - drops existing data)
python rag1.py ./spec.pdf --rebuild-schema
```

## Collections

**ArticleSpec** - Stores product specifications with embeddings
**CostModel** - Links specifications to cost indices

## Integration

The CLI prints Weaviate object IDs after ingestion. Use these IDs to:

- Reference specs in cost models
- Query similar articles via semantic search
- Provide context to GPT for cost analysis

## Resources

- **Weaviate Docs**: https://weaviate.io/developers/weaviate
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

---

See [main README](../README.md) for full project documentation.
