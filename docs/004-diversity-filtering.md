# 004 — Diversity Filtering

## Motivation

Image collections often contain near-duplicates (same photo at different resolutions, slight crops, etc.). Without filtering, the top results can be dominated by these redundant copies, reducing the usefulness of a search.

## Approach

A greedy diversity pass is applied client-side in the GUI after the raw results arrive:

```
kept = []
for candidate in results_sorted_by_distance_to_query:
    if all(cosine_dist(candidate, k) > d for k in kept):
        kept.append(candidate)
    if len(kept) == N_RESULTS:
        break
```

This is **O(N² × D)** where N is the candidate pool and D is the embedding dimension, which is fast enough for N ≤ a few hundred.

## Oversampling

When diversity is enabled the GUI requests `4 × N_RESULTS` candidates from the search API so that after filtering enough results remain to fill the grid. The factor 4 is a fixed constant (`OVERSAMPLE = 4`).

## Embeddings

To compute pairwise distances, the search API must return embedding vectors alongside the usual metadata. This is controlled by the `include_embeddings: bool` flag in the request body (default `false`). The search API passes it to ChromaDB via `include=["distances", "embeddings"]`.

## Distance metric

Standard cosine distance: `1 - dot(a, b) / (‖a‖ · ‖b‖)`. Computed with NumPy in `gui/app.py::_cosine_dist`.

## Configuration

The exclusion threshold `d` is exposed as the **Exclusion distance** slider in the sidebar (range 0.01–1.0). A toggle enables/disables the feature so the user can compare diverse vs. standard results.
