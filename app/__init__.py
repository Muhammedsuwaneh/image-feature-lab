"""FeatureLab application package."""

import os

# Keep MNIST matrix operations from taking every CPU thread from the Qt UI.
# Explicit user settings take precedence over these application defaults.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "4")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")
