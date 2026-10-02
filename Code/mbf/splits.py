"""Deterministic train and test splits, shared by every stage.

The same dataset sample always yields the same splits, so Stage 1 probes and later
fusion runs can be evaluated on identical rows.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def grouped_folds(groups, n_splits=5, seed=42):
    """Return (train, test) row indices with each group in exactly one held-out fold.

    A group's fold is the SHA-256 hash of the seed and its string, modulo n_splits, so the
    assignment is the same on every machine and library version, identical sequences
    always share a fold, and a sequence keeps its fold in any sample that contains it.
    Stage1_refactor.ipynb defines the same function. These are the folds probe_scores
    uses when it receives groups.
    """
    fold_of_row = np.array([
        int(hashlib.sha256(f"{seed}:{g}".encode()).hexdigest(), 16) % n_splits
        for g in groups
    ])
    folds = [
        (np.flatnonzero(fold_of_row != k), np.flatnonzero(fold_of_row == k))
        for k in range(n_splits)
    ]
    if any(len(test) == 0 for _, test in folds):
        raise ValueError("A fold received no rows; use more groups or fewer folds.")
    return folds


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
