"""Registry of labeled sequence datasets, and the inputs each encoder reads from them.

Every entry names its file, sequence and label columns, task, published split column,
and setting. In the "derived" setting (Setting A in the README), each row holds one
coding sequence: DNA encoders read it in DNA letters, RNA encoders read it in RNA
letters, and protein encoders read its translation. Datasets whose rows carry separate
DNA, transcript, and protein sequences, such as IsoFormer's GTEx data (Setting B), will
add a second setting.
"""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .encoders import encoder_input
from .sequences import is_in_frame_and_starts_correctly, translate_cds


@dataclass(frozen=True)
class DatasetSpec:
    """A labeled sequence dataset and where its encoder inputs come from.

    path is relative to the Code directory. split_column names the column holding the
    published train, validation, and test assignment, when the file has one.
    """

    key: str
    label: str
    path: str
    sequence_column: str
    label_column: str
    task: str
    setting: str
    split_column: str | None = None
    source: str = ""


_CODONBERT = "CodonBERT fine-tuning benchmark, github.com/Sanofi-Public/CodonBERT"

DATASETS = {
    d.key: d
    for d in [
        DatasetSpec("mrna_stability", "mRNA stability", "mRNA_Stability.csv", "Sequence", "Value",
                    task="regression", setting="derived", split_column="Split", source=_CODONBERT),
        DatasetSpec("mrfp_expression", "mRFP expression (synonymous-recoding control)",
                    "mRFP_Expression.csv", "Sequence", "Value",
                    task="regression", setting="derived", split_column="Split", source=_CODONBERT),
    ]
}


def is_retained(seq):
    """Apply the Stage 1 filters to one uppercase, stripped coding sequence.

    A sequence is kept when its length is a multiple of three, it starts with ATG or
    AUG, and it translates to at least five amino acids.
    """
    return is_in_frame_and_starts_correctly(seq) and len(translate_cds(seq)) >= 5


@dataclass
class Dataset:
    """The retained rows of one dataset, in input order.

    rows keeps the original file index and columns, so published splits and other
    columns stay attached to each retained sequence. n_sampled counts the rows before
    filtering, and dropped counts the rows each filter removed.
    """

    spec: DatasetSpec
    rows: pd.DataFrame
    sequences: list[str]
    labels: np.ndarray
    n_sampled: int = 0
    dropped: dict = field(default_factory=dict)

    @property
    def groups(self):
        """Cross-validation groups: identical sequences share a group."""
        return self.sequences

    @property
    def lengths(self):
        """Sequence lengths as a one-column matrix, for the length-only baseline probe."""
        return np.array([len(s) for s in self.sequences]).reshape(-1, 1)

    def inputs_for(self, encoder):
        """Return the string each retained row contributes to one encoder."""
        if self.spec.setting != "derived":
            raise NotImplementedError(f"inputs for the {self.spec.setting!r} setting")
        return [encoder_input(encoder, s) for s in self.sequences]


def sample_rows(key, n_rows=None, seed=42, data_dir="."):
    """Return a registered dataset's rows with a sequence, sampled before any filtering.

    With n_rows, n_rows rows are drawn without replacement using seed; otherwise every
    row is returned. data_dir is the directory holding the files, the Code directory by
    default.
    """
    spec = DATASETS[key]
    df = pd.read_csv(os.path.join(data_dir, spec.path)).dropna(subset=[spec.sequence_column])
    return df if n_rows is None else df.sample(n=n_rows, random_state=seed)


def retain(spec, df):
    """Apply the Stage 1 filters to sampled rows, keeping their order."""
    sequences = [str(value).strip().upper() for value in df[spec.sequence_column]]
    in_frame = np.array([is_in_frame_and_starts_correctly(s) for s in sequences], dtype=bool)
    keep = np.array([is_retained(s) for s in sequences], dtype=bool)
    rows = df[keep]
    return Dataset(
        spec=spec,
        rows=rows,
        sequences=[s for s, kept in zip(sequences, keep) if kept],
        labels=rows[spec.label_column].to_numpy(),
        n_sampled=len(df),
        dropped={
            "failed the length or start check": int((~in_frame).sum()),
            "translated to fewer than five amino acids": int((in_frame & ~keep).sum()),
        },
    )


def load_dataset(key, n_rows=None, seed=42, data_dir="."):
    """Load a registered dataset, sample it, and keep the rows that pass the Stage 1 filters."""
    return retain(DATASETS[key], sample_rows(key, n_rows, seed, data_dir))


def audit(key, data_dir=".", length_limit=1000):
    """Summarize properties of the whole file that matter for comparisons with published results.

    Reports rows and distinct sequences, rows per published split and the distinct
    sequences shared by each pair of splits, repeated sequences and how many carry
    differing labels, the median label SD within a repeated sequence, and the share of
    rows no longer than length_limit nucleotides.
    """
    spec = DATASETS[key]
    df = pd.read_csv(os.path.join(data_dir, spec.path))
    seqs = df[spec.sequence_column].astype(str).str.strip().str.upper()
    summary = {"Rows": len(df), "Distinct sequences": seqs.nunique()}
    if spec.split_column is not None:
        splits = df[spec.split_column]
        summary["Rows per split"] = splits.value_counts().to_dict()
        sets = {name: set(seqs[splits == name]) for name in splits.unique()}
        for a, b in itertools.combinations(sorted(sets), 2):
            summary[f"Distinct sequences in both {a} and {b}"] = len(sets[a] & sets[b])
    by_sequence = df.assign(seq=seqs).groupby("seq")[spec.label_column].agg(["count", "nunique", "std"])
    repeated = by_sequence[by_sequence["count"] > 1]
    summary["Repeated sequences"] = len(repeated)
    summary["Repeated sequences with differing labels"] = int((repeated["nunique"] > 1).sum())
    summary["Median label SD within a repeated sequence"] = repeated["std"].median()
    summary[f"Share of rows with at most {length_limit:,} nucleotides"] = (seqs.str.len() <= length_limit).mean()
    return pd.Series(summary, name=spec.label, dtype=object)
