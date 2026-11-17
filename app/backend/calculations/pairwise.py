"""Euclidean distances with bounded temporary allocations."""

import numpy as np

from app.backend.validation import feature_matrix, positive_integer


def distance_batches(reference_samples, queries, *, batch_size: int = 64):
    references = feature_matrix(reference_samples, "Reference samples")
    queries = feature_matrix(queries, "Queries", allow_empty=True)
    batch_size = positive_integer(batch_size, "batch_size")

    if queries.shape[1] != references.shape[1]:
        raise ValueError("Query and reference feature dimensions must match.")

    # Bound the distance matrix to about 16 MiB. Matrix multiplication avoids a
    # queries x 60,000 references x 784 features difference cube for MNIST.
    batch_size = min(batch_size, max(1, 2**21 // len(references)))
    reference_norms = np.einsum("ij,ij->i", references, references, dtype=np.float64)

    for start in range(0, len(queries), batch_size):
        batch = queries[start : start + batch_size].astype(np.float64, copy=False)
        query_norms = np.einsum("ij,ij->i", batch, batch)
        distances = np.empty((len(batch), len(references)), dtype=np.float64)

        for offset in range(0, len(references), 4096):
            # Convert only a bounded reference block, retaining float64 distance
            # precision without doubling all 60,000 float32 training vectors.
            block = references[offset : offset + 4096].astype(np.float64, copy=False)
            distances[:, offset : offset + len(block)] = batch @ block.T

        distances *= -2
        distances += reference_norms[None, :]
        distances += query_norms[:, None]
        tolerance = 64 * np.finfo(float).eps * (reference_norms[None, :] + query_norms[:, None])

        # Recompute near-identical pairs directly so cancellation cannot turn
        # distinct samples into zero-distance neighbors, or zero into nonzero.
        for row in range(len(batch)):
            close = np.flatnonzero(distances[row] <= tolerance[row])

            for offset in range(0, len(close), 128):
                indices = close[offset : offset + 128]
                differences = references[indices] - batch[row]
                distances[row, indices] = np.einsum("ij,ij->i", differences, differences)

        np.maximum(distances, 0, out=distances)
        np.sqrt(distances, out=distances)

        if not np.all(np.isfinite(distances)):
            raise ValueError("Distances overflowed; reduce the magnitude of feature values.")

        yield start, distances
