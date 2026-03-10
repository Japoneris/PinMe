"""
Plot the width/height distribution of all images stored in the images/ directory.

Usage:
    python plot_dimensions.py [--images-dir PATH] [--bins N] [--output FILE]

The script reads every supported image file, collects (width, height) pairs,
then shows three panels:
  1. 2-D scatter plot  – one dot per unique (w, h) pair, sized by count
  2. Width histogram
  3. Height histogram
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from PIL import Image, UnidentifiedImageError

IMAGES_DIR = Path(__file__).parent / "images"
SUPPORTED = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def collect_dimensions(images_dir: Path) -> list[tuple[int, int]]:
    dims = []
    skipped = 0
    files = [f for f in images_dir.iterdir() if f.suffix.lower() in SUPPORTED]
    for path in files:
        try:
            with Image.open(path) as img:
                dims.append(img.size)  # (width, height)
        except (UnidentifiedImageError, Exception):
            skipped += 1
    if skipped:
        print(f"Skipped {skipped} unreadable file(s).", file=sys.stderr)
    return dims


def plot(dims: list[tuple[int, int]], bins: int, output: str | None) -> None:
    widths  = [w for w, _ in dims]
    heights = [h for _, h in dims]

    counts = Counter(dims)
    uw, uh = zip(*counts.keys())
    sizes  = list(counts.values())
    max_s  = max(sizes)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(f"Image dimension distribution  ({len(dims)} images)", fontsize=13)

    # ── 1. Scatter: width × height, dot size ∝ count ──────────────────────────
    ax = axes[0]
    scatter = ax.scatter(
        uw, uh,
        s=[50 + 300 * (s / max_s) for s in sizes],
        c=sizes,
        cmap="plasma",
        alpha=0.7,
        edgecolors="white",
        linewidths=0.4,
    )
    cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("Count", fontsize=9)
    ax.set_xlabel("Width (px)")
    ax.set_ylabel("Height (px)")
    ax.set_title("Width × Height (bubble = count)")
    ax.grid(True, linestyle="--", alpha=0.4)

    # ── 2. Width histogram ─────────────────────────────────────────────────────
    ax = axes[1]
    ax.hist(widths, bins=bins, color="#4C9BE8", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Width (px)")
    ax.set_ylabel("Number of images")
    ax.set_title("Width distribution")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    # ── 3. Height histogram ────────────────────────────────────────────────────
    ax = axes[2]
    ax.hist(heights, bins=bins, color="#E8834C", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Height (px)")
    ax.set_ylabel("Number of images")
    ax.set_title("Height distribution")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if output:
        fig.savefig(output, dpi=150)
        print(f"Saved to {output}")
    else:
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot image dimension distribution.")
    parser.add_argument("--images-dir", default=str(IMAGES_DIR), help="Path to images folder")
    parser.add_argument("--bins", type=int, default=30, help="Number of histogram bins (default: 30)")
    parser.add_argument("--output", default=None, help="Save plot to file instead of showing it (e.g. plot.png)")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    if not images_dir.is_dir():
        sys.exit(f"Directory not found: {images_dir}")

    dims = collect_dimensions(images_dir)
    if not dims:
        sys.exit("No readable images found.")

    print(f"Loaded {len(dims)} images.")
    plot(dims, bins=args.bins, output=args.output)


if __name__ == "__main__":
    main()
