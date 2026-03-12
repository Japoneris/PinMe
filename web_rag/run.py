#!/usr/bin/env python3
"""CLI entry point for the PintMe web-image RAG embedding pipeline."""
import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chroma import get_client, get_web_image_collection, get_web_text_collection
from embedder import get_unique_hashes, process_web_image_embeddings, process_web_text_embeddings

ROOT = Path(__file__).parent.parent
FIREFOX_DIR = ROOT / "Firefox_pinner"


def main():
    parser = argparse.ArgumentParser(description="PintMe web-image RAG embedding pipeline")
    parser.add_argument("--db",         default=str(FIREFOX_DIR / "pintest.db"),  help="pintest.db path")
    parser.add_argument("--images-dir", default=str(FIREFOX_DIR / "images"),      help="Firefox_pinner/images/ directory")
    parser.add_argument("--chroma-dir", default=str(ROOT / "chromadb"),           help="ChromaDB persist directory")
    parser.add_argument("--server",     default="http://localhost:8100",           help="Embedding server base URL")
    parser.add_argument("--skip-image", action="store_true",                       help="Skip image embedding step")
    parser.add_argument("--skip-text",  action="store_true",                       help="Skip text (caption) embedding step")
    parser.add_argument("--quiet",      action="store_true",                       help="Suppress per-file output")
    args = parser.parse_args()

    verbose = not args.quiet

    records = get_unique_hashes(args.db)
    print(f"Found {len(records)} unique hashes in {args.db}")

    chroma     = get_client(args.chroma_dir)
    image_col  = get_web_image_collection(chroma)
    text_col   = get_web_text_collection(chroma)

    if not args.skip_image:
        print("\n=== Web image embeddings (DINOv2) ===")
        counts = process_web_image_embeddings(records, args.images_dir, image_col, args.server, verbose)
        print(f"Done. Embedded: {counts['done']}  Skipped: {counts['skipped']}  Errors: {counts['errors']}")

    if not args.skip_text:
        print("\n=== Web text embeddings (caption → MiniLM) ===")
        counts = process_web_text_embeddings(records, args.images_dir, text_col, args.server, verbose)
        print(f"Done. Embedded: {counts['done']}  Skipped: {counts['skipped']}  Errors: {counts['errors']}")


if __name__ == "__main__":
    main()
