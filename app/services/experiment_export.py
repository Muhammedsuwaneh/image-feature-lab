"""Portable experiment records and figures for reproducing the research."""

import base64
import csv
import json
import math
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np


def json_value(value):
    if isinstance(value, np.ndarray):
        return json_value(value.tolist())
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity" if value < 0 else "NaN"
    return value


def export_experiment_results(results: dict, output_directory: str | Path) -> Path:
    from app.backend.experiments.result_visualizations import build_result_visualizations

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    visualizations = build_result_visualizations(results)
    record = dict(results)
    record["environment"] = {
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ("tensorflow", "keras", "numpy", "scikit-learn", "matplotlib", "opencv-python", "PyQt6")},
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    record["comparison_rows"] = visualizations["comparison_rows"]
    result_file = directory / "results.json"
    result_file.write_text(json.dumps(json_value(record), indent=2, allow_nan=False), encoding="utf-8")
    rows = visualizations["comparison_rows"]
    if rows:
        with (directory / "comparison.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for index, chart in enumerate(visualizations["charts"], start=1):
        name = chart["title"].lower().replace(" ", "-")
        (directory / f"{index:02d}-{name}.png").write_bytes(base64.b64decode(chart["source"].split(",", 1)[1]))
    return result_file
