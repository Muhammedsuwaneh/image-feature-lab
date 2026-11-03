# FeatureLab

FeatureLab is a scientific desktop application for investigating distance concentration in image feature spaces and its effect on nearest-neighbor classification.

The project uses Python, PyQt6, Qt Quick/QML, NumPy, OpenCV, scikit-learn, Matplotlib, and pytest. The current interface provides navigation, image preview, experiment setup, and result views. Dataset processing, feature extraction, distance analysis, and model evaluation remain future implementation work; the UI does not fabricate experimental results.

## Architecture

- `app/backend/calculations`: interface-independent mathematical calculations.
- `app/backend/image_processing`: image loading and feature extraction.
- `app/backend/datasets`: dataset access and preparation.
- `app/backend/machine_learning`: classifiers, evaluation, and experiment logic.
- `app/services`: coordination between backend capabilities and the UI.
- `app/viewmodels`: Qt-facing state and commands for QML.
- `ui`: QML application window, pages, and reusable components.
- `tests`: automated tests for backend and application behavior.
- `data` and `resources`: datasets and application assets.

The current entry point loads `ui/Main.qml` and exposes `app/viewmodels/feature_lab_view_model.py` to QML. Mathematical and data-processing code will remain independent of QML.

## Setup and launch

From the project directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Launch the desktop application with:

```powershell
python main.py
```

Run the test suite with:

```powershell
python -m pytest
```
