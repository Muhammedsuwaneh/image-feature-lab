import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from app.services.experiment_export import json_value


def test_export_converts_numpy_and_unbounded_contrast_to_valid_json():
    record = {"contrast": np.inf, "values": np.array([1, 2]), "seed": np.int64(42), "other": (np.float64(0.5),)}
    converted = json_value(record)
    assert converted == {"contrast": "Infinity", "values": [1, 2], "seed": 42, "other": [0.5]}
    assert json.loads(json.dumps(converted, allow_nan=False)) == converted


def test_command_line_experiments_export_with_legacy_console_encoding(tmp_path):
    project = Path(__file__).resolve().parents[1]
    directory = tmp_path / "results-\u0130"
    environment = dict(os.environ, PYTHONIOENCODING="cp1252")
    result = subprocess.run(
        [sys.executable, str(project / "run_experiments.py"), "--output", str(directory), "--train-samples", "600", "--test-samples", "100"],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads((directory / "results.json").read_text(encoding="utf-8"))
    assert set(record["synthetic"]) == {"2", "4", "8", "16", "32", "64", "128", "256"}
    assert set(record["irrelevant_features"]) == {"784", "1024", "1568", "2352"}
    assert record["metadata"]["noise_seeds"] == [0, 1, 2]
    assert len(record["standardization_and_pca"]) == 4
    assert len(list(directory.glob("*.png"))) == 6
