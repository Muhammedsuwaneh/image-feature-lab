# Phase 2: FeatureLab User Interface

Develop the main desktop interface for FeatureLab using **PyQt6 and Qt Quick/QML**.

The application should have a modern, clean, scientific dashboard suitable for an academic research project.

### Main interface

Create the following pages:

1. **Dashboard:** Project overview and dataset information.
2. **Image Analysis:** Upload and inspect an image.
3. **Distance Concentration:** Explore distance distributions and concentration.
4. **Dimensionality Experiments:** Compare different feature dimensions.
5. **Results:** View experimental metrics, charts, and comparisons.

### Interface requirements

- Create a main application window.
- Implement sidebar navigation.
- Use reusable QML components.
- Establish communication between QML and Python through appropriate ViewModels.
- Provide consistent typography, spacing, and visual hierarchy.
- Include suitable areas for charts, tables, images, and metrics.
- Make the interface suitable for a desktop application.

Do not display fabricated experimental results. Use empty states or explanatory placeholders where backend functionality is not yet available.

### Technical restrictions

- PyQt6 and QML only.
- No PySide6, Tkinter, React, or web frameworks.
- Keep UI code separate from mathematical calculations.
- Reuse the existing project architecture.

At completion, test application startup and navigation. Explain all changes and wait for approval before continuing.