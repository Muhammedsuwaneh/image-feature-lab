"""Euclidean distances with bounded temporary allocations."""

import numpy as np

from app.backend.validation import feature_matrix, positive_integer


def distance_batches(reference_samples, queries, *, batch_size: int = 16):
    references = feature_matrix(reference_samples, "Reference samples")
    queries = feature_matrix(queries, "Queries", allow_empty=True)
    batch_size = positive_integer(batch_size, "batch_size")
    if queries.shape[1] != references.shape[1]:
        raise ValueError("Query and reference feature dimensions must match.")
    # Bound each difference array to approximately 16 MiB even for wider inputs.
    batch_size = min(batch_size, max(1, 2**21 // references.size))
    for start in range(0, len(queries), batch_size):
        batch = queries[start : start + batch_size]
        differences = batch[:, None, :] - references[None, :, :]
        # einsum avoids a second queries x references x features temporary.
        distances = np.sqrt(np.einsum("ijk,ijk->ij", differences, differences))
        if not np.all(np.isfinite(distances)):
            raise ValueError("Distances overflowed; reduce the magnitude of feature values.")
        yield start, distances
