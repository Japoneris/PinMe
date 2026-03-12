# 005 — Indexer: Stale Record Removal and Progress Display

## Stale Record Removal

After scanning a folder, the indexer now detects images that were present in the database but no longer exist on disk, and removes their records.

### Implementation

`scan_folder` was extended to return the set of absolute paths it observed on disk alongside the usual counts. A new `purge_missing` function then queries the DB for records under the same folder root whose path is absent from that set and deletes them.

### Behaviour

| Scenario | Action |
|---|---|
| File still on disk | Kept |
| File missing from disk | Deleted by default |
| `--keep-missing` flag passed | Kept (no deletion) |

The summary line now includes a **Removed** counter:

```
Done. Added: 3  Updated: 1  Removed: 2  Errors: 0
```

### `--keep-missing`

Pass this flag to preserve records for images that have disappeared from disk (e.g. temporarily unmounted drives):

```bash
python run.py --keep-missing
```

## Progress Display

Previously, the indexer gave no indication of how far through a folder it was. The generator is now materialised into a list upfront so the total is known, and every log line is prefixed with `[current/total]`:

```
  [1/342] [ADD]   photo.jpg  (3024×4032, 2048 KB)
  [2/342] [MOVE]  /old/path.jpg → /new/path.jpg
  ...
```

The upfront directory walk adds a small delay before processing begins but is negligible compared to per-file hashing time.
