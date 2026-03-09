#!/usr/bin/env python3
"""CLI for searching images via the PintMe Search API."""
import argparse
import sys

import requests


def _do_search(url: str, payload: dict) -> None:
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"Error: could not connect to search API at {url.rsplit('/search', 1)[0]}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e} — {r.text}")
        sys.exit(1)

    data = r.json()
    results = data["results"]

    if not results:
        print("No results found.")
        return

    print(f"\nQuery type : {data['query_type']}")
    print(f"Query      : {data['query']}")
    print(f"Results    : {len(results)}\n")
    print(f"{'#':<4} {'Distance':>10}  {'File'}")
    print("-" * 72)

    for res in results:
        fname = res["path"]
        dims  = f"{res['width']}x{res['height']}" if res.get("width") else "?"
        size  = f"{res['size_bytes'] // 1024} KB" if res.get("size_bytes") else "?"
        print(f"#{res['rank']:<3} {res['distance']:>10.4f}  {fname}")
        print(f"     dims={dims}  size={size}  mime={res.get('mimetype', '?')}")
        if res.get("caption"):
            caption_preview = res["caption"][:100].replace("\n", " ")
            print(f"     caption: {caption_preview}...")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Search images by text or visual similarity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search.py text "a deer in a forest"
  python search.py image /path/to/photo.jpg
  python search.py text "anime girl" --n 5
  python search.py image ./query.jpg --server http://localhost:8200
        """,
    )
    parser.add_argument("--server", default="http://localhost:8200", help="Search API base URL")
    sub = parser.add_subparsers(dest="mode", required=True)

    text_p = sub.add_parser("text", help="Search by text description")
    text_p.add_argument("query", help="Text query")
    text_p.add_argument("--n", type=int, default=5, help="Number of results (default: 5)")

    img_p = sub.add_parser("image", help="Search by image similarity")
    img_p.add_argument("input", help="Image path, URL, or base64")
    img_p.add_argument("--n", type=int, default=5, help="Number of results (default: 5)")

    args = parser.parse_args()

    if args.mode == "text":
        _do_search(f"{args.server}/search/text", {"query": args.query, "n_results": args.n})
    else:
        input_data = args.input
        # Resolve local paths to absolute so the embedding server can find the file
        if not input_data.startswith(("http://", "https://", "data:image")):
            from pathlib import Path
            p = Path(input_data)
            if p.exists():
                input_data = str(p.resolve())
        _do_search(f"{args.server}/search/image", {"input": input_data, "n_results": args.n})


if __name__ == "__main__":
    main()
