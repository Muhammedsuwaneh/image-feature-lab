# Phase 3: Image Processing and Dataset Integration

Implement image preprocessing and integration of the scikit-learn Digits dataset.

### Part A: Image upload and preprocessing

Allow users to upload PNG, JPG, and JPEG images.

Implement the following pipeline:

1. Load the image using OpenCV.
2. Convert it to grayscale.
3. Resize it to 8 × 8 pixels.
4. Scale pixel intensities consistently with the Digits dataset.
5. Flatten the image into a 64-dimensional feature vector.
6. Return the processed image and feature vector to the QML interface.

The scikit-learn Digits dataset contains 8 × 8 grayscale images with pixel values in the range 0–16.

Pay attention to image intensity scaling and interpolation so uploaded images can be compared meaningfully with the reference dataset.

Display the original and processed images in the application.

### Part B: Digits dataset

Load the dataset using:

```python
from sklearn.datasets import load_digits
```

Implement functionality to:

- Load images and labels.
- Extract 64-dimensional feature vectors.
- Identify the ten digit classes (0–9).
- Create a reproducible stratified train/test split.
- Provide access to samples and labels.

The original 64-dimensional dataset must serve as the experimental baseline.

### Requirements

- Keep image processing and dataset loading in separate backend modules.
- Add appropriate error handling.
- Add tests for image preprocessing and dataset loading.
- Avoid modifying original dataset values.

At completion, report the dataset dimensions, preprocessing pipeline, files changed, and test results. Wait for approval.