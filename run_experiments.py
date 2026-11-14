"""Run the same fixed experiment suite used by the desktop application."""

import argparse
import sys

from app.backend.experiments.dimensionality_experiments import run_all_dimensionality_experiments
from app.services.experiment_export import export_experiment_results


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # Windows consoles may use an encoding that cannot represent project paths.
        sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/latest", help="Directory for JSON, CSV and six PNG charts")
    args = parser.parse_args()
    results = run_all_dimensionality_experiments()
    path = export_experiment_results(results, args.output)
    print(f"Saved experiment records and charts to {path.resolve().parent}")
    for size, metrics in results["irrelevant_features"].items():
        print(f"{size} features: accuracy={metrics['test_accuracy']:.6f}, CV={metrics['coefficient_of_variation']:.6f}")
    for name, metrics in results["standardization_and_pca"].items():
        print(f"{name}: accuracy={metrics['test_accuracy']:.6f}, CV={metrics['coefficient_of_variation']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
