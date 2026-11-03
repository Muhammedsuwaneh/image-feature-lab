# Phase 1: Project Foundation and Architecture

You are developing **FeatureLab**, a scientific desktop application for the Mathematics for AI semester project.

**Research title:** Investigating Distance Concentration in Image Feature Spaces and Its Effect on Nearest-Neighbor Classification.

### Technology stack
- Python
- PyQt6
- Qt Quick / QML
- NumPy
- OpenCV
- Scikit-learn
- Matplotlib
- Pytest

### Your tasks

1. Inspect the existing project directory before making changes.
2. Understand existing files and avoid overwriting working implementations.
3. Propose a clean, modular architecture.
4. Separate backend calculations, image processing, dataset handling, machine learning, application services, ViewModels, and QML components.
5. Create the necessary project directories and initial files.
6. Configure the PyQt6 application entry point and QML loading.
7. Create `requirements.txt`, `.gitignore`, and an initial `README.md`.

Suggested structure:

```text
image-feature-lab/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── backend/
│   ├── services/
│   └── viewmodels/
├── ui/
│   ├── Main.qml
│   ├── pages/
│   └── components/
├── data/
├── resources/
└── tests/
```

You may improve this structure when technically justified.

### Important instructions
- Use PyQt6, not PySide6.
- Use QML, not Tkinter or web technologies.
- Keep mathematical logic independent of the interface.
- Avoid unnecessary abstractions and complexity.
- Do not implement the complete application yet.

At completion, explain the architecture, list created files, and provide instructions for launching the initial application.

Stop and wait for approval before proceeding.