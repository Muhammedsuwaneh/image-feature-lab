import base64
import math

from app.viewmodels.feature_lab_view_model import FeatureLabViewModel


def test_distance_concentration_uses_held_out_query_and_training_references():
    view_model = FeatureLabViewModel()

    view_model.analyzeDistanceConcentration(0)

    result = view_model.distanceConcentrationResult
    assert result["reference_count"] == view_model.datasetTrainCount
    assert result["query_index"] not in view_model._digits_dataset.train_indices
    assert result["nearest_sample_label"] in view_model.datasetClasses
    assert result["farthest_sample_label"] in view_model.datasetClasses
    assert result["minimum_distance"] <= result["mean_distance"] <= result["maximum_distance"]
    assert result["standard_deviation"] >= 0.0
    assert result["variance"] >= 0.0
    assert math.isfinite(result["coefficient_of_variation"])
    assert math.isfinite(result["relative_distance_contrast"])
    assert base64.b64decode(view_model.distanceConcentrationChart.split(",", 1)[1]).startswith(
        b"\x89PNG\r\n\x1a\n"
    )


def test_distance_concentration_reports_invalid_test_selection():
    view_model = FeatureLabViewModel()

    view_model.analyzeDistanceConcentration(view_model.datasetTestCount)

    assert "error" in view_model.distanceConcentrationResult
    assert view_model.distanceConcentrationChart == ""
