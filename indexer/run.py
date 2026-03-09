#!/usr/bin/env python3
"""CLI entry point for the PintMe image indexer."""
import argparse
import json
from pathlib import Path

from db import get_session
from scanner import scan_folder


def main():
    parser = argparse.ArgumentParser(description="PintMe image indexer")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent.parent / "config.json"),
        help="Path to config.json (default: ../config.json)",
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).parent.parent / "pintme.db"),
        help="Path to SQLite database (default: ../pintme.db)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress per-file output")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        raise SystemExit(1)

    with open(config_path) as f:
        config = json.load(f)

    folders = config.get("explore", [])
    if not folders:
        print("No folders listed under 'explore' in config.json.")
        raise SystemExit(0)

    session = get_session(args.db)

    total = {"added": 0, "updated": 0, "errors": 0}

    for folder in folders:
        print(f"\nScanning: {folder}")
        counts = scan_folder(session, folder, verbose=not args.quiet)
        for k in total:
            total[k] += counts[k]

    print(f"\nDone. Added: {total['added']}  Updated: {total['updated']}  Errors: {total['errors']}")


if __name__ == "__main__":
    main()
