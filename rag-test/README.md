# RAG Product Spec Ingestion

Utilities for loading product specification documents into Weaviate, keeping the schema flexible for cost model experimentation.

## Key Components
- `weaviate_utils.py` provisions the `ArticleSpec` and `CostModel` collections and centralizes connection logic.
- `spec_ingest.py` extracts text, chunks it when needed, and persists both full-document and chunked embeddings.
- `rag1.py` offers a CLI wrapper so you can ingest a new spec with a single command.

## Quick Start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Export credentials (use your own values):
   ```bash
   export WEAVIATE_URL="https://<cluster>.weaviate.network"
   export WEAVIATE_API_KEY="..."
   export OPENAI_API_KEY="..."
   ```
3. Ingest a spec using both embedding strategies:
   ```bash
   python rag1.py ./sample.pdf \
     --vendor "Acme" \
     --title "Acme 90° elbow" \
     --material PBT --material Stainless \
     --process injection_molding --process assembly \
     --weight-g 12.4 \
     --dims-mm 45 20 18
   ```

### Strategy Control
Use `--strategy document` or `--strategy chunked` flags to restrict ingestion to a single representation. When omitted, both strategies run, giving you the choice of which Weaviate object IDs to reference later.

### Schema Rebuilds
`--rebuild-schema` drops and recreates the collections; handy while iterating, but destructive.

## Next Steps
- Attach cost models via the `CostModel` collection and link them with the stored spec UUIDs.
- When you are ready to call GPT, feed it the list of relevant `ArticleSpec` object IDs (the CLI prints them) so you can control which embeddings/indices it should consult.
