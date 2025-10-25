from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from spec_ingest import ChunkingConfig, ProductSpecMetadata, SpecIngestor
from weaviate_utils import connect, ensure_schema


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a product specification document into Weaviate.",
    )
    parser.add_argument("document", type=Path, help="Path to the product spec (PDF or text).")
    parser.add_argument(
        "--part-number",
        dest="part_number",
        help="Optional part number extracted from the spec.",
    )
    parser.add_argument("--vendor", help="Vendor or manufacturer name.")
    parser.add_argument("--title", help="Short human-readable title for the spec.")
    parser.add_argument(
        "--material",
        dest="materials",
        action="append",
        help="Material (repeatable).",
    )
    parser.add_argument(
        "--process",
        dest="processes",
        action="append",
        help="Manufacturing process tag (repeatable).",
    )
    parser.add_argument("--weight-g", type=float, help="Approximate part weight in grams.")
    parser.add_argument(
        "--dims-mm",
        nargs="+",
        type=float,
        help="Linear dimensions in millimetres, e.g. L W H.",
    )
    parser.add_argument(
        "--strategy",
        action="append",
        choices=["document", "chunked"],
        help="Ingestion strategy (repeat for multiple). Default is both.",
    )
    parser.add_argument(
        "--chunk-tokens",
        type=int,
        default=900,
        help="Maximum tokens per chunk when using the chunked strategy.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=120,
        help="Token overlap between chunks when using the chunked strategy.",
    )
    parser.add_argument(
        "--rebuild-schema",
        action="store_true",
        help="Drop and recreate the ArticleSpec/CostModel collections.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    if not args.document.exists():
        logging.error("Document path does not exist: %%s", args.document)
        return 1

    client = connect()
    ensure_schema(client, rebuild=args.rebuild_schema)

    metadata = ProductSpecMetadata(
        partNumber=args.part_number,
        vendor=args.vendor,
        title=args.title,
        materials=args.materials or [],
        mediaType=None,
        weight_g=args.weight_g,
        dims_mm=args.dims_mm,
        processes=args.processes or [],
    )

    strategies = args.strategy or ["document", "chunked"]
    chunking = ChunkingConfig(max_tokens=args.chunk_tokens, overlap_tokens=args.chunk_overlap)

    ingestor = SpecIngestor(client=client, chunking=chunking)
    uuids = ingestor.ingest_document(
        document_path=args.document,
        metadata=metadata,
        strategies=strategies,
    )

    logging.info("Inserted %%d objects into ArticleSpec", len(uuids))
    for obj_uuid in uuids:
        print(obj_uuid)

    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
