# Phase 6: Dimensionality and Distance Concentration Experiments

Implement the main experiments for investigating distance concentration in image feature spaces.

This is the central experimental phase of FeatureLab.

### Experiment A: Synthetic data

Generate independent Uniform[0,1] random vectors and investigate dimensions:

- 2
- 4
- 8
- 16
- 32
- 64
- 128
- 256

Calculate empirical mean squared distance, variance, and coefficient of variation.

Compare the empirical measurements with the theoretical results implemented in Phase 4.

### Experiment B: Adding irrelevant features

Use the scikit-learn Digits dataset.

Compare:

- 64 features: original baseline.
- 96 features.
- 160 features.
- 256 features.

Append independently generated irrelevant features sampled from Uniform[0,16].

Requirements:

- Preserve the original 64 image features.
- Use reproducible random seeds.
- Repeat the experiments with multiple seeds.
- Maintain the same stratified train/test split.
- Use Euclidean distance.
- Use k = 5 for k-NN.

For each condition, calculate:

- Mean distance.
- Standard deviation.
- Coefficient of variation.
- Relative distance contrast.
- Nearest and farthest distance distributions.
- k-NN test accuracy.

### Experiment C: Standardization and PCA

Compare:

1. Original 64-dimensional features.
2. Standardized features.
3. PCA with 16 components.
4. PCA with 32 components.

Use `StandardScaler` and `PCA` from scikit-learn.

**Prevent data leakage:** Fit preprocessing transformations using training data only, then transform the test data using the fitted transformations.

### Experimental consistency

- Use consistent data splits across comparisons.
- Record random seeds.
- Store actual experimental results.
- Do not assume accuracy must decrease.
- Report the measured outcomes without fabricating conclusions.

Implement reusable experiment functions and connect them to the existing application architecture.

At completion, provide a summary of experiments implemented and actual preliminary results. Wait for approval.