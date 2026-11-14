"""Input validation shared by the numerical backend."""

import operator

import numpy as np


def positive_integer(value: int, name: str) -> int:
    try:
        if isinstance(value, (bool, np.bool_)):
            raise TypeError
        result = operator.index(value)
    except TypeError as error:
        raise ValueError(f"{name} must be a positive integer.") from error
    if result <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return result


def feature_matrix(values, name: str, *, allow_empty: bool = False) -> np.ndarray:
    source = np.asarray(values)
    dtype = np.float32 if source.dtype == np.float32 else np.float64
    matrix = np.asarray(source, dtype=dtype)
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        raise ValueError(f"{name} must be a 2D array with at least one feature.")
    if not allow_empty and matrix.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one sample.")
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must contain only finite values.")
    return matrix
