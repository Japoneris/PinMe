"""Folder scanner: hash computation, metadata extraction, and DB upsert logic."""
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path

from PIL import Image as PilImage
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Folder, Image


SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".bmp", ".tiff", ".tif", ".avif",
}


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------

def compute_hash(path: Path) -> str:
    """Compute SHA-256 of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_metadata(path: Path) -> dict:
    """Extract mimetype, dimensions, and file size."""
    mimetype, _ = mimetypes.guess_type(str(path))
    size_bytes = path.stat().st_size

    width, height = None, None
    try:
        with PilImage.open(path) as img:
            width, height = img.size
            if mimetype is None:
                mimetype = PilImage.MIME.get(img.format)
    except Exception:
        pass  # Not a valid image Pillow can open; still record it

    return {
        "mimetype": mimetype,
        "width": width,
        "height": height,
        "size_bytes": size_bytes,
    }


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def iter_images(root: Path):
    """Yield all image file paths under root recursively."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def scan_folder(session: Session, folder_path: str, verbose: bool = True) -> dict:
    """Scan a folder and upsert image records into the DB.

    Returns a summary dict with counts.
    """
    root = Path(folder_path).resolve()

    if not root.exists():
        print(f"  [SKIP] Folder does not exist: {root}")
        return {"skipped": 0, "added": 0, "updated": 0, "errors": 0}

    # Upsert Folder record
    folder = session.query(Folder).filter_by(path=str(root)).first()
    if folder is None:
        folder = Folder(path=str(root))
        session.add(folder)
        session.flush()

    counts = {"added": 0, "updated": 0, "errors": 0}

    for img_path in iter_images(root):
        try:
            file_hash = compute_hash(img_path)
        except Exception as e:
            if verbose:
                print(f"  [ERROR] Cannot hash {img_path}: {e}")
            counts["errors"] += 1
            continue

        existing = session.query(Image).filter_by(hash=file_hash).first()

        if existing is not None:
            # Same content already indexed — update path if it moved
            if existing.path != str(img_path):
                if verbose:
                    print(f"  [MOVE]  {existing.path} → {img_path}")
                existing.path = str(img_path)
                existing.updated_at = datetime.utcnow()
                counts["updated"] += 1
            # else: identical, nothing to do
            continue

        # Path-level duplicate check (different hash, same path — file was replaced)
        by_path = session.query(Image).filter_by(path=str(img_path)).first()
        if by_path is not None:
            if verbose:
                print(f"  [REPLACE] {img_path} (old hash {by_path.hash[:8]}… → {file_hash[:8]}…)")
            meta = extract_metadata(img_path)
            by_path.hash = file_hash
            by_path.image_embedded = False
            by_path.text_embedded = False
            by_path.updated_at = datetime.utcnow()
            by_path.__dict__.update(meta)
            counts["updated"] += 1
            continue

        # New image
        meta = extract_metadata(img_path)
        image = Image(
            hash=file_hash,
            path=str(img_path),
            folder_id=folder.id,
            **meta,
        )
        session.add(image)
        counts["added"] += 1

        if verbose:
            print(f"  [ADD]   {img_path.name}  ({meta['width']}x{meta['height']}, {meta['size_bytes'] // 1024} KB)")

    folder.last_scanned_at = datetime.utcnow()
    session.commit()

    return counts
