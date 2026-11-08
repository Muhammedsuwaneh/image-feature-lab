# Phase 5: k-Nearest-Neighbor Classification

Implement k-NN classification using the scikit-learn Digits dataset.

### Requirements

1. Use the original 64-dimensional image features as the baseline.
2. Use Euclidean distance.
3. Set k = 5 as the default.
4. Use the existing stratified training/test split.
5. Train the classifier using training data only.
6. Calculate test accuracy.
7. Support predictions for uploaded images.
8. Retrieve and display the nearest training samples and their labels.

Use an appropriate implementation, such as:

```python
from sklearn.neighbors import KNeighborsClassifier
```

### Display in the application

- Predicted digit.
- Nearest reference images.
- Labels of nearest neighbors.
- Distances to nearest neighbors.
- Overall test accuracy.

Keep classification functionality separate from the mathematical distance engine.

Make sure the uploaded image follows the same preprocessing pipeline as the reference dataset.

Do not present this as a production-grade recognition system. It is an experimental k-NN implementation for studying distance-based classification.

Add appropriate tests and report actual results.

At completion, explain the implementation and wait for approval.