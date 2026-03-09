#!/usr/bin/env python3
"""CLI for inspecting the PintMe SQLite database."""
import argparse
import sys
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from indexer.db import get_session
from models import Image, Folder

ROOT = Path(__file__).parent.parent


def _print_image(img: Image) -> None:
    dims = f"{img.width}x{img.height}" if img.width else "unknown"
    size = f"{img.size_bytes // 1024} KB" if img.size_bytes else "unknown"
    print(f"  hash     : {img.hash}")
    print(f"  path     : {img.path}")
    print(f"  mime     : {img.mimetype or '?'}  dims={dims}  size={size}")
    print(f"  embedded : image={img.image_embedded}  text={img.text_embedded}")
    print(f"  indexed  : {img.indexed_at}  updated={img.updated_at}")
    if img.caption:
        caption_preview = img.caption[:120].replace("\n", " ")
        print(f"  caption  : {caption_preview}...")
    else:
        print(f"  caption  : (none)")
    print()


def cmd_lookup(args) -> None:
    """Look up images by hash prefix."""
    session = get_session(args.db)
    prefix = args.prefix.lower()
    images = session.query(Image).filter(Image.hash.like(f"{prefix}%")).all()

    if not images:
        print(f"No images found with hash starting with '{prefix}'.")
        return

    print(f"\n{len(images)} image(s) matching hash prefix '{prefix}':\n")
    for img in images:
        _print_image(img)


def cmd_list(args) -> None:
    """List all indexed images."""
    session = get_session(args.db)
    images = session.query(Image).order_by(Image.indexed_at.desc()).all()

    if not images:
        print("No images in the database.")
        return

    print(f"\n{len(images)} image(s) in database:\n")
    print(f"{'HASH':>10}  {'DIMS':>12}  {'SIZE':>8}  {'IMG':>5}  {'TXT':>5}  PATH")
    print("-" * 90)
    for img in images:
        dims = f"{img.width}x{img.height}" if img.width else "?"
        size = f"{img.size_bytes // 1024}KB" if img.size_bytes else "?"
        print(
            f"{img.hash[:8]}  {dims:>12}  {size:>8}"
            f"  {'yes':>5}  {'yes' if img.text_embedded else 'no':>5}  {img.path}"
        )


def cmd_folders(args) -> None:
    """List tracked folders."""
    session = get_session(args.db)
    folders = session.query(Folder).all()

    if not folders:
        print("No folders tracked.")
        return

    print(f"\n{len(folders)} tracked folder(s):\n")
    for f in folders:
        n_images = len(f.images)
        print(f"  [{f.id}] {f.path}")
        print(f"       images={n_images}  added={f.added_at}  last_scan={f.last_scanned_at}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the PintMe SQLite database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python db.py lookup a4fd            # find image(s) whose hash starts with a4fd
  python db.py lookup a4fd6487        # more specific prefix
  python db.py list                   # list all images
  python db.py folders                # list tracked folders
  python db.py list --db /other/path/pintme.db
        """,
    )
    parser.add_argument("--db", default=str(ROOT / "pintme.db"), help="SQLite DB path")

    sub = parser.add_subparsers(dest="command", required=True)

    lookup_p = sub.add_parser("lookup", help="Find image(s) by hash prefix")
    lookup_p.add_argument("prefix", help="Beginning of the SHA-256 hash")

    sub.add_parser("list", help="List all indexed images")
    sub.add_parser("folders", help="List tracked root folders")

    args = parser.parse_args()

    if args.command == "lookup":
        cmd_lookup(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "folders":
        cmd_folders(args)


if __name__ == "__main__":
    main()
