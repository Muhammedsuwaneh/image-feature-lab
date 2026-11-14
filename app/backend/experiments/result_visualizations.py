from __future__ import annotations

import base64
from io import BytesIO
from threading import RLock
from typing import Any, Callable

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


_render_lock = RLock()


def _render_chart(draw: Callable[[Axes], None]) -> str:
    # Matplotlib's font caches are shared even when using independent figures.
    with _render_lock:
        return _render_chart_locked(draw)


def _render_chart_locked(draw: Callable[[Axes], None]) -> str:
    figure = Figure(figsize=(7.2, 3.2), dpi=120)
    FigureCanvasAgg(figure)
    axes = figure.subplots()
    figure.patch.set_facecolor("#F7F9F7")
    axes.set_facecolor("#F7F9F7")
    draw(axes)
    axes.grid(axis="y", color="#DCE3DD", linewidth=0.7)
    axes.set_axisbelow(True)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.spines["left"].set_color("#AAB5AC")
    axes.spines["bottom"].set_color("#AAB5AC")
    axes.tick_params(colors="#34453B", labelsize=8)
    axes.xaxis.label.set_color("#34453B")
    axes.yaxis.label.set_color("#34453B")
    buffer = BytesIO()
    figure.savefig(buffer, format="png", facecolor=figure.get_facecolor(), bbox_inches="tight")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _condition_data(results: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for size, metrics in sorted(results["irrelevant_features"].items()):
        rows.append({
            "label": f"Irrelevant {size}",
            "feature_count": int(size),
            "nearest_distances": np.asarray(metrics["nearest_distances"], dtype=np.float64),
            "farthest_distances": np.asarray(metrics["farthest_distances"], dtype=np.float64),
            "test_accuracy": float(metrics["test_accuracy"]),
            "mean_distance": float(metrics["mean_distance"]),
            "distance_std": float(metrics["distance_std"]),
            "coefficient_of_variation": float(metrics["coefficient_of_variation"]),
            "relative_contrast": float(metrics["relative_distance_contrast"]),
            "test_accuracy_std": float(metrics.get("test_accuracy_std", 0.0)),
        })

    feature_counts = {"original": 784, "standardized": 784, "pca_16": 16, "pca_32": 32}
    labels = {"original": "Original", "standardized": "Standardized", "pca_16": "PCA 16", "pca_32": "PCA 32"}
    for name, metrics in results["standardization_and_pca"].items():
        rows.append({
            "label": labels[name],
            "feature_count": int(metrics.get("feature_size", feature_counts[name])),
            "nearest_distances": np.asarray(metrics["nearest_distances"], dtype=np.float64),
            "farthest_distances": np.asarray(metrics["farthest_distances"], dtype=np.float64),
            "test_accuracy": float(metrics["test_accuracy"]),
            "mean_distance": float(metrics["mean_distance"]),
            "distance_std": float(metrics["distance_std"]),
            "coefficient_of_variation": float(metrics["coefficient_of_variation"]),
            "relative_contrast": float(metrics["relative_distance_contrast"]),
            "test_accuracy_std": 0.0,
        })

    return rows


def render_distance_distribution_chart(distances: np.ndarray) -> str:
    """Render a measured one-query distance distribution as a PNG data URL."""
    values = np.asarray(distances, dtype=np.float64).ravel()
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Distance distribution must contain finite values.")

    def draw(axes: Axes) -> None:
        axes.hist(values, bins=32, color="#247A57", edgecolor="#FFFFFF", linewidth=0.5)
        axes.set_xlabel("Euclidean distance to training sample")
        axes.set_ylabel("Number of training samples")

    return _render_chart(draw)


def build_result_visualizations(results: dict[str, Any]) -> dict[str, Any]:
    """Render chart images and table rows directly from completed experiment outputs."""
    irrelevant = results["irrelevant_features"]
    synthetic = results["synthetic"]
    conditions = _condition_data(results)
    chart_images: list[dict[str, str]] = []

    def add_chart(title: str, caption: str, draw: Callable[[Axes], None]) -> None:
        chart_images.append({"title": title, "caption": caption, "source": _render_chart(draw)})

    dimensions = np.asarray(sorted(irrelevant), dtype=np.int64)
    dimension_rows = [next(row for row in conditions if row["label"] == f"Irrelevant {size}") for size in dimensions]

    def draw_dimension_comparison(axes: Axes) -> None:
        mean_distances = [item["mean_distance"] for item in dimension_rows]
        accuracies = [item["test_accuracy"] * 100.0 for item in dimension_rows]
        axes.plot(dimensions, mean_distances, color="#247A57", marker="o", linewidth=2, label="Mean distance to all references")
        axes.set_xlabel("Feature count")
        axes.set_ylabel("Mean Euclidean distance")
        accuracy_axes = axes.twinx()
        accuracy_axes.plot(dimensions, accuracies, color="#C56A3D", marker="s", linewidth=1.8, label="Test accuracy")
        accuracy_axes.set_ylabel("Test accuracy (%)", color="#C56A3D")
        accuracy_axes.tick_params(axis="y", colors="#C56A3D", labelsize=8)
        accuracy_axes.spines["top"].set_visible(False)
        lines, labels = axes.get_legend_handles_labels()
        accuracy_lines, accuracy_labels = accuracy_axes.get_legend_handles_labels()
        axes.legend(lines + accuracy_lines, labels + accuracy_labels, frameon=False, fontsize=8, loc="best")

    add_chart("Dimensionality comparison", "Mean test-to-training distance and test accuracy across augmented feature spaces.", draw_dimension_comparison)

    def draw_concentration(axes: Axes) -> None:
        cvs = [item["coefficient_of_variation"] for item in dimension_rows]
        axes.plot(dimensions, cvs, color="#247A57", marker="o", linewidth=2)
        axes.set_xlabel("Feature count")
        axes.set_ylabel("All-distance coefficient of variation")
        axes.set_xticks(dimensions)

    add_chart("Distance concentration", "Population CV of all test-to-training distances; scalar metrics averaged over noise seeds.", draw_concentration)

    def draw_relative_contrast(axes: Axes) -> None:
        labels = [item["label"] for item in conditions]
        values = [item["relative_contrast"] for item in conditions]
        positions = np.arange(len(labels))
        finite_values = [value if np.isfinite(value) else 0.0 for value in values]
        axes.bar(positions, finite_values, color=["#247A57" if "PCA" not in label else "#C56A3D" for label in labels])
        for position, value in zip(positions, values):
            if not np.isfinite(value):
                axes.text(position, 0, "infinity", rotation=90, ha="center", va="bottom", fontsize=8)
        axes.set_xticks(positions, labels, rotation=28, ha="right")
        axes.set_ylabel("Relative nearest/farthest contrast")

    add_chart("Relative distance contrast", "Mean per-query (farthest - nearest) / nearest; exact zero minima can give infinity.", draw_relative_contrast)

    def draw_accuracy(axes: Axes) -> None:
        labels = [item["label"] for item in conditions]
        values = [item["test_accuracy"] * 100.0 for item in conditions]
        positions = np.arange(len(labels))
        errors = [item["test_accuracy_std"] * 100.0 for item in conditions]
        axes.bar(positions, values, yerr=errors, capsize=3, color="#247A57")
        axes.set_xticks(positions, labels, rotation=28, ha="right")
        axes.set_ylabel("Test accuracy (%)")
        axes.set_ylim(0, 100)

    add_chart("Classification performance", "Held-out k-NN accuracy; error bars show population std over noise seeds, not confidence intervals.", draw_accuracy)

    def draw_distributions(axes: Axes) -> None:
        selected = [item for item in conditions if item["label"] in {"Original", "Irrelevant 2352", "Standardized", "PCA 16", "PCA 32"}]
        colors = ["#247A57", "#C56A3D", "#3E7890", "#8B6B42", "#6E8C65"]
        for item, color in zip(selected, colors):
            axes.hist(item["nearest_distances"], bins=24, density=True, histtype="step", linewidth=1.7, color=color, label=item["label"])
        axes.set_xlabel("Nearest-neighbor distance")
        axes.set_ylabel("Density")
        axes.legend(frameon=False, fontsize=7)

    add_chart("Nearest-distance distributions", "Empirical nearest-neighbor distance distributions from selected test conditions.", draw_distributions)

    def draw_theoretical_validation(axes: Axes) -> None:
        synthetic_dimensions = np.asarray(sorted(synthetic), dtype=np.int64)
        empirical = [synthetic[int(size)]["coefficient_of_variation"] for size in synthetic_dimensions]
        theoretical = [synthetic[int(size)]["theoretical_squared_distance_cv"] for size in synthetic_dimensions]
        axes.plot(synthetic_dimensions, empirical, color="#247A57", marker="o", linewidth=2, label="Empirical squared-distance CV")
        axes.plot(synthetic_dimensions, theoretical, color="#C56A3D", marker="s", linestyle="--", linewidth=1.7, label="Theoretical squared-distance CV")
        axes.set_xlabel("Synthetic dimension")
        axes.set_ylabel("Coefficient of variation")
        axes.legend(frameon=False, fontsize=8)

    add_chart("Synthetic theoretical validation", "Empirical and theoretical coefficients of variation for squared distances.", draw_theoretical_validation)

    comparison_rows = [
        {key: value for key, value in row.items() if key not in {"nearest_distances", "farthest_distances"}}
        for row in conditions
    ]
    return {"charts": chart_images, "comparison_rows": comparison_rows}
