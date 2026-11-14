# FeatureLab

FeatureLab is a Python, PyQt6 and Qt Quick/QML desktop research application for **Investigating Distance Concentration in Image Feature Spaces and Its Effect on Nearest-Neighbor Classification**. It measures real distances and classification outcomes from the scikit-learn Digits dataset and reproducible synthetic data. Charts and tables come from backend experiment outputs.

## Research objectives

- Investigate how dimensionality changes Euclidean distances and their relative variability.
- Compare distance concentration with held-out k-nearest-neighbor accuracy.
- Study irrelevant feature augmentation, standardization and PCA separately.
- Compare empirical squared-distance moments against their theoretical values.

## Install and launch

The validated environment uses Python 3.13.12 on Windows. Activate the existing environment, or create a new one:

```powershell
.\imagefeatureenv\Scripts\Activate.ps1
# Alternatively:
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\main.py
```

`requirements.txt` pins the direct dependencies used for validation: PyQt6 6.12.0, NumPy 2.5.4, OpenCV 5.0.0.93, scikit-learn 1.9.1, Matplotlib 3.11.2 and pytest 9.2.0. `requirements-lock.txt` records the complete installed dependency set; use `python -m pip install -r requirements-lock.txt` to request the same package versions. A fresh installation of the lock file has not been independently tested on other platforms.

The application fills the available desktop work area in borderless maximized mode, keeping the system taskbar visible. It has a custom FeatureLab title bar with a red circular close button at the upper right, without minimize or maximize controls. Other visible window states return to maximized mode.

Startup calls `sklearn.datasets.load_digits()` on the main thread through the dataset module, before constructing the QML window. The dataset and stratified split are therefore already available on the first displayed window; initialization does not depend on a dataset worker or a queued completion signal. The library includes the data: no user dataset folder, file selection, or download is needed. Importing scikit-learn can take a few seconds on a cold launch before the window appears. Baseline accuracy is evaluated separately in a background task and does not block experiments. The header and Dashboard distinguish ready and failure states. A visible banner reports the actual error and offers Retry dataset loading (or Retry baseline evaluation). Open **Dimensionality Experiments** or **Results** and select **Run experiment(s)** to compute the full suite. Experiments, baseline evaluation, and distance-chart analysis run in background threads; loading the small library dataset is a startup operation on the main thread. You can navigate while they execute; duplicate run actions are disabled. If the data is not loaded, the experiment action becomes Load dataset and run, and continues automatically after successful loading. Background failures also print a traceback in the terminal. Closing the application waits for active calculations to finish safely.

## Implemented features

- **Dashboard:** research overview and actual dataset dimensions and split counts.
- **Image Analysis:** PNG/JPG/JPEG selection; original and processed previews; 64 image features; predicted digit; five nearest training images with labels, dataset indices and Euclidean distances; baseline test accuracy.
- **Distance Concentration:** select a held-out query; measure its distance to every training reference; view mean, variance, standard deviation, ordinary-distance CV, contrast, nearest/farthest sample information and a measured histogram.
- **Dimensionality Experiments:** run the fixed, reproducible synthetic, irrelevant-feature, standardization and PCA conditions.
- **Results:** measured comparison table and six charts: dimensionality comparison, distance concentration, relative contrast, classification accuracy, nearest-distance distributions and synthetic theoretical validation.
- **Reproducible exports:** command-line execution saves raw results, metadata, per-seed measurements, a comparison CSV and six PNG figures.
- Background failures appear in the interface; the last successful experiment results are retained. Fonts are registered from local system files when Qt cannot discover them, with a bundled Matplotlib font as a fallback.

## Dataset and image processing

The source is `sklearn.datasets.load_digits`, included with scikit-learn; FeatureLab does not download a dataset. It contains **1,797 grayscale 8 x 8 images**, **64 features**, **10 classes (0-9)** and intensities in **[0,16]**. Original arrays are copied and marked read-only.

The default split uses `train_test_split(test_size=0.2, random_state=42, stratify=labels)`: **1,437 training samples and 360 held-out test samples**. Every condition in a suite shares this exact dataset and split. Exports record both index arrays and the split seed. Queries are compared only with training references, so a held-out query is excluded by index. A distinct reference with identical feature values can still have zero distance.

Uploaded images are decoded with OpenCV using a byte buffer, which supports Unicode paths on Windows. Transparent images are composited over white, and 16-bit PNG intensities are converted to 8-bit. For classification, the grayscale image is normalized to light strokes on a dark background using its border polarity. Foreground detection removes excess margins and ignores tiny isolated specks. The cropped glyph is centered on a square at source resolution, preserving aspect ratio, before downsampling to 8 x 8. Already-sized 8 x 8 inputs and aligned square reference-style layouts preserve their geometry. Intensities are scaled by 16/255, rounded and flattened to 64 floating-point values. Blank uploads report an error rather than an arbitrary digit. The lower-level `preprocess_image` API retains basic extraction by default; the app and `predict_image_with_knn` explicitly enable `normalize_digit=True`. Neighbors are retrieved only from the training split. The classifier uses **k=5**, Euclidean distances and uniform voting. Equal-distance neighbors use training order; tied class votes choose the smallest label. APIs expose both positions within the training split and original dataset indices to avoid mixing the two.

Uploads may contain either dark-on-light or light-on-dark strokes and surrounding margins. The application now corrects polarity and placement automatically. It expects a single clear digit; deskewing, multiple-character segmentation and complex-background recognition are not implemented. The original scikit-learn feature vectors, research experiments, uniform voting and k=5 are unchanged.

## Uploaded-digit prediction validation

The supplied stylized `digit_2.png` previously predicted **0** because the old pipeline resized a white background and dark strokes directly into a representation trained on the opposite polarity. With normalization the same training-only k-NN predicts **2**. The user-provided image is stored only as a regression fixture in `tests/fixtures/digit_2.png`; it is never added to training.

A separate robustness check rendered each of the 360 held-out images at 64 x 64 and added asymmetric padding (top 13, bottom 29, left 47, right 11 pixels), with optional polarity reversal. The measured diagnostic results are recorded in [upload-normalization.json](results/review/upload-normalization.json):

| Derived upload condition | Before normalization | After normalization |
| --- | ---: | ---: |
| Already aligned, enlarged images | 98.33% | 98.33% |
| Padded light strokes on dark background | 18.89% | 96.39% |
| Padded dark strokes on white background | 16.67% | 96.39% |
| Native 8 x 8 images with reversed polarity | 0.56% | 98.33% |

These are controlled transformations of Digits test samples, not a benchmark of arbitrary external handwriting. The app's displayed baseline accuracy still refers to the unchanged original held-out dataset, not uploaded-image accuracy. Unusual fonts, decorations, rotations and different stroke styles can still be misclassified.

## Mathematics and metric definitions

For vectors x and y:

- Euclidean distance: `D(x,y) = sqrt(sum_j (x_j-y_j)^2)`.
- Squared Euclidean distance: `D^2(x,y) = sum_j (x_j-y_j)^2`.
- Population variance and standard deviation use `ddof=0`.
- Ordinary-distance CV: `std(D)/mean(D)`.
- Squared-distance CV: `std(D^2)/mean(D^2)`. The helper `squared_distance_cv` accepts ordinary distances and squares them internally.
- Per-query relative contrast: `(D_max-D_min)/D_min`. A zero minimum and positive maximum gives infinity; all-zero distances give contrast 0. All-zero distance arrays also have CV 0 by convention. Small positive values are not treated as zero.

For independent Uniform[0,1] coordinates, the synthetic predictions are `E[D^2]=d/6`, `Var(D^2)=7d/180` and `CV(D^2)=sqrt(7/(5d))`. The synthetic chart compares squared-distance CV with squared-distance theory. Ordinary-distance CV is retained separately.

**Experiment mean, standard deviation and CV use all test-to-training distances**, rather than only the nearest five neighbors. Batched distances and combined population moments avoid allocating the complete query-by-reference-by-feature cube. For each condition the backend also stores per-query nearest/farthest distances, per-query relative contrasts and mean query CV. The table's mean contrast is the mean of the individual query contrasts, rather than the contrast of averaged extrema. Its values come directly from the backend; the UI does not calculate different statistics.

Noise experiments report arithmetic means of per-seed scalar metrics. The accuracy chart shows population standard deviation over the three noise seeds, **not** confidence intervals. Nearest-distance histograms pool one nearest distance per test query and seed. Accuracy is the fraction of correctly classified held-out labels. Distances from standardized and raw features have different units; compare their structure and accuracy rather than interpreting absolute distance scales as directly interchangeable.

## Experimental protocol

| Experiment | Conditions | Reproducibility |
| --- | --- | --- |
| Synthetic | Dimensions 2, 4, 8, 16, 32, 64, 128, 256; 2,000 independent pairs per dimension | NumPy generator seed 42 |
| Irrelevant features | 64, 96, 160 and 256 total features; original 64 coordinates preserved; appended independent Uniform[0,16] noise | Seeds 0, 1 and 2; same held-out split |
| Preprocessing | Original 64 features; standardized 64; PCA 16; PCA 32 | Each transformer fit once on training data, then reused to transform both splits; PCA full SVD, random_state=42 |

Standardization and PCA are separate conditions: PCA operates on the original training features, without preceding standardization. Full SVD avoids differences between independently randomized PCA bases. The 64-feature irrelevant condition intentionally repeats the original baseline as a consistency check. Its three repeated runs have no added noise and are identical, so their accuracy standard deviation is zero.

The UI exposes these fixed conditions rather than configurable parameters. Backend functions accept alternative feature counts, noise seeds and datasets for controlled experiments. Seed-level metrics and predictions remain available in exported JSON.

## Reproduce and inspect results

```powershell
python .\run_experiments.py --output results/review
```

This invokes the same backend suite as the desktop application and writes:

- `results.json`: full measurements, predictions, per-query extrema/contrasts, seed results, exact train/test indices, protocol metadata and dependency versions.
- `comparison.csv`: the same metrics used by the Results table.
- Six PNG figures generated from those measurements.

JSON represents non-finite values as strings such as `"Infinity"`, keeping the file valid JSON. Figure files are regenerated by rerunning the command. GUI results are retained in memory; use the command above for a persistent export.

Measured results from the validated environment are included in [results/review/comparison.csv](results/review/comparison.csv) and [results/review/results.json](results/review/results.json):

| Condition | All-distance mean | All-distance CV | Mean query contrast | Test accuracy |
| --- | ---: | ---: | ---: | ---: |
| Original 64 | 48.439 | 0.16793 | 3.12785 | 98.33% |
| Irrelevant 96 | 61.111 | 0.10939 | 1.10210 | 97.22% |
| Irrelevant 160 | 80.468 | 0.06990 | 0.56396 | 94.63% |
| Irrelevant 256 | 102.830 | 0.04854 | 0.35909 | 91.02% |
| Standardized 64 | 10.663 | 0.47021 | 12.70333 | 96.39% |
| PCA 16 | 44.369 | 0.19779 | 4.66770 | 98.33% |
| PCA 32 | 47.545 | 0.17349 | 3.47533 | 98.06% |

In these measured conditions, added irrelevant coordinates increase mean distances and reduce their relative variability and query contrast, while accuracy decreases. PCA 16 retains baseline accuracy on this split, and standardization does not improve it. These observations concern this dataset, split and noise protocol; distance concentration alone is not a proof that accuracy must decrease in every setting. The three noise seeds do not measure uncertainty across alternative data splits.

## Architecture

```text
main.py                         Qt application entry point
run_experiments.py              Reproducible command-line experiments and export
app/backend/calculations/       Mathematical metrics and bounded distance batches
app/backend/datasets/           Digits data and stratified splitting
app/backend/image_processing/   Image decoding and Digits feature extraction
app/backend/machine_learning/   Euclidean k-NN and training-neighbor mapping
app/backend/experiments/        Shared experiment evaluation and Matplotlib figures
app/backend/validation.py       Shared numerical input validation
app/services/                   Background jobs, research operations, previews,
                                font setup and experiment export
app/viewmodels/                 Qt properties, signals and application commands
ui/Main.qml                     Main window and navigation
ui/components/                  Shared presentation components
ui/pages/                       Five research pages
tests/                          Numerical, data, ML, export and GUI tests
results/review/                 Actual reproducible measurements and figures
.prompts/                       The eight original project specifications
```

The numerical backend is independent of Qt. Services coordinate backend operations. Workers emit results; ViewModel slots apply Qt property changes on the GUI thread. Matplotlib uses independent Agg figures with serialized rendering to protect shared font caches. QML pages receive their required ViewModel and theme during construction.

## Testing and technical review

```powershell
python -m pytest tests -q
python -m pip check
```

The tests configure Qt's offscreen platform and software rendering without changing normal launches. They cover:

- Distances, population statistics, ordinary versus squared CV, exact-zero behavior, small positive distances, theoretical moments, malformed inputs and non-finite values.
- Image formats, grayscale conversion, resizing, range mapping, corrupt/missing images, dataset dimensions, read-only arrays and stratified splits; uploaded-digit polarity, padding and transparency equivalence; blank-image rejection; the supplied stylized 2; and robustness across the full held-out digit set.
- Batched k-NN against direct distances, deterministic ties, invalid k/queries, accuracy and correct training-to-dataset neighbor mapping.
- Full-reference experiment statistics against independent NumPy calculations, reproducible noise, seed aggregation, and checks that each scaler/PCA fits once on training samples only.
- Real application entry-point startup from another working directory, dataset availability before the first GUI event loop (with no loading banner), a QML Run-button click producing all six charts, and safe close during initialization; all five QML pages; font glyph availability; uploaded-image predictions before/after dataset loading; clear and error states.
- Full background experiment execution with a GUI heartbeat, duplicate-run protection, all six rendered chart images, window capture, persistent export, legacy Windows console encoding and failure handling that retains previous results. Dataset regression tests also verify retry after load failure, running experiments before baseline evaluation completes, and keeping data/experiments available when baseline evaluation fails.

The review corrected inconsistent distance summaries, chart/backend metric disagreement, separately fitted PCA bases, incorrect neighbor label mapping, large temporary arrays, missing image prediction displays, missing font discovery, QML dependency initialization and blocking experiment/chart execution. Final validation: **96 tests passed, 0 failed** in the recorded run; `python -m pip check` reported no broken requirements. Python compilation and `git diff --check` also passed. Rendered [Results](results/review/application-results.png) and [Image Analysis](results/review/application-image-analysis.png) screenshots are included with the actual results. A final targeted image-page check also verified all seven image previews reach the ready state.

## Limitations and remaining work

- Experiment conditions are fixed in the interface. Custom conditions require calling the backend functions.
- Closing while work is active waits for it to finish; interactive cancellation is not implemented.
- Uploads now have automatic polarity correction, foreground cropping, aspect-ratio preservation and centering. Recognition still depends on digit style and image quality; deskewing, complex backgrounds and multiple-digit segmentation remain unsupported.
- Accuracy is evaluated on one fixed split. Additional split seeds, confidence intervals and broader datasets would be useful future research, rather than conclusions from the current measurements.
- Standardization can amplify rarely varying pixel coordinates. PCA and normalization choices should be studied as separate experimental factors.
- GUI tests and screenshots use offscreen rendering. Native file-dialog interaction, desktop GPU/driver behavior and other operating systems still need manual validation.
- The complete environment is recorded, but installation and results have not been independently reproduced in a fresh environment or on other hardware.
