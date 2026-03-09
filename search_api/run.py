#!/usr/bin/env python3
"""Entry point for the PintMe search API."""
import argparse
import os

import uvicorn

ROOT_DEFAULT_DB     = None   # resolved at import time in server.py via ROOT
ROOT_DEFAULT_CHROMA = None


def main():
    parser = argparse.ArgumentParser(description="PintMe Search API")
    parser.add_argument("--host",       default="0.0.0.0",              help="Host to bind to")
    parser.add_argument("--port",       type=int, default=8200,          help="Port to bind to")
    parser.add_argument("--reload",     action="store_true",             help="Enable auto-reload")
    parser.add_argument("--embed-server", default="http://localhost:8100", help="Embedding server URL")
    parser.add_argument("--db",         default=None,                    help="SQLite DB path")
    parser.add_argument("--chroma-dir", default=None,                    help="ChromaDB persist directory")
    args = parser.parse_args()

    os.environ["EMBED_SERVER"] = args.embed_server
    if args.db:
        os.environ["DB_PATH"] = args.db
    if args.chroma_dir:
        os.environ["CHROMA_DIR"] = args.chroma_dir

    uvicorn.run("server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
