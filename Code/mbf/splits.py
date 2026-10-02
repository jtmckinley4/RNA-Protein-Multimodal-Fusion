"""Deterministic train and test splits, shared by every stage.

The same dataset sample always yields the same splits, so Stage 1 probes and later
fusion runs can be evaluated on identical rows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, train_test_split


def grouped_folds(groups, n_splits=5):
    """Return (train, test) index pairs that keep each group within one fold.

    With the sequence strings as groups, identical sequences never fall on both sides.
    These are the folds probe_scores uses when it receives groups.
    """
    n = len(groups)
    return list(GroupKFold(n_splits=n_splits).split(np.zeros((n, 1)), groups=groups))


def holdout_split(n, test_size=0.3, seed=42):
    """Return (train, test) row indices for the CCA and retrieval analyses.

    This reproduces the Stage 1 split, which is random by row rather than grouped, so
    copies of a duplicated sequence can fall on both sides.
    """
    return train_test_split(np.arange(n), test_size=test_size, random_state=seed)


def official_split(dataset):
    """Return {split name: row indices} from the dataset's published split column.

    Use these for comparisons with published results. In mRNA_Stability.csv thousands
    of test sequences also occur in training, so they overstate generalization.
    """
    column = dataset.spec.split_column
    if column is None:
        raise ValueError(f"{dataset.spec.key} has no published split column")
    values = dataset.rows[column].to_numpy()
    return {name: np.flatnonzero(values == name) for name in pd.unique(values)}
