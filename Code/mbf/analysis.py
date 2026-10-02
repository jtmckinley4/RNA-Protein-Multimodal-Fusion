"""Representation analyses shared by the notebooks.

Linear probes, representation similarity (CKA, mutual k-NN, CCA retrieval, RSA), the
composition control, the attention-motif test, and summary tables and figures. The
functions reproduce those defined inline in Stage1_refactor.ipynb.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.stats import mannwhitneyu, rankdata, spearmanr
from sklearn.cross_decomposition import CCA
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def probe_scores(X, y, groups=None, continuous=True):
    """Return the five held-out fold scores of a standardized linear probe.

    Continuous targets use RidgeCV over 20 log-spaced penalties and R^2. With `groups`
    (the retained sequence strings), GroupKFold keeps identical sequences in one fold.
    """
    if continuous:
        model, scoring = RidgeCV(alphas=np.logspace(-3, 5, 20)), "r2"
    else:
        model, scoring = LogisticRegression(max_iter=2000), "accuracy"
    pipeline = Pipeline([("scale", StandardScaler()), ("model", model)])
    if groups is not None:
        return cross_val_score(pipeline, X, y, cv=GroupKFold(n_splits=5), groups=groups, scoring=scoring)
    return cross_val_score(pipeline, X, y, cv=5, scoring=scoring)


def probe_table(embeddings, targets, groups):
    """Return mean and fold SD of probe R^2 for every (embedding, target) combination.

    embeddings: {name: matrix}; targets: {target name: vector}.
    """
    rows = []
    for name, X in embeddings.items():
        row = {"encoder": name}
        for target, y in targets.items():
            scores = probe_scores(X, y, groups=groups)
            row[f"{target} R2"] = scores.mean()
            row[f"{target} SD"] = scores.std()
        rows.append(row)
    return pd.DataFrame(rows).set_index("encoder")


# ---------------------------------------------------------------------------
# Representation similarity
# ---------------------------------------------------------------------------

def linear_cka(X, Y):
    """Return linear CKA for representations with matching example rows."""
    X_centered = X - X.mean(axis=0, keepdims=True)
    Y_centered = Y - Y.mean(axis=0, keepdims=True)
    numerator = np.linalg.norm(Y_centered.T @ X_centered, ord="fro") ** 2
    norm_x = np.linalg.norm(X_centered.T @ X_centered, ord="fro")
    norm_y = np.linalg.norm(Y_centered.T @ Y_centered, ord="fro")
    return numerator / (norm_x * norm_y)


def mutual_knn_alignment(X, Y, k=10):
    """Average neighbor-set overlap after discarding each first returned index."""
    n = X.shape[0]
    neighbors_x = NearestNeighbors(n_neighbors=k + 1).fit(X).kneighbors(X, return_distance=False)
    neighbors_y = NearestNeighbors(n_neighbors=k + 1).fit(Y).kneighbors(Y, return_distance=False)
    overlaps = [len(set(neighbors_x[i, 1:]) & set(neighbors_y[i, 1:])) / k for i in range(n)]
    return np.mean(overlaps)


def cca_retrieval(X_a, X_b, train_idx, test_idx, seed, n_pca=50, n_cca=10, ks=(1, 5, 10)):
    """Fit PCA then CCA on training rows; return held-out correlations and retrieval.

    Matches the Stage1_refactor.ipynb procedure: PCA with 50 components per space, CCA
    with 10 components, correlations of each component pair on the test rows, and
    Recall@k for querying the second space with the first in the CCA space.
    """
    n_pca = min(n_pca, len(train_idx) - 1, X_a.shape[1], X_b.shape[1])
    pca_a = PCA(n_components=n_pca, random_state=seed).fit(X_a[train_idx])
    pca_b = PCA(n_components=n_pca, random_state=seed).fit(X_b[train_idx])
    cca = CCA(n_components=n_cca).fit(pca_a.transform(X_a[train_idx]), pca_b.transform(X_b[train_idx]))
    a_c, b_c = cca.transform(pca_a.transform(X_a[test_idx]), pca_b.transform(X_b[test_idx]))
    corrs = np.array([np.corrcoef(a_c[:, i], b_c[:, i])[0, 1] for i in range(n_cca)])
    n_test = len(test_idx)
    neighbors = NearestNeighbors(n_neighbors=min(max(ks), n_test)).fit(b_c).kneighbors(
        a_c, return_distance=False
    )
    recall = {k: np.mean([i in neighbors[i, :k] for i in range(n_test)]) for k in ks}
    return {"correlations": corrs, "recall": recall, "test_coords": (a_c, b_c)}


def compute_rsa(embeddings_a, embeddings_b):
    """Compare matched pairwise correlation distances using Spearman correlation."""
    return spearmanr(pdist(embeddings_a, metric="correlation"), pdist(embeddings_b, metric="correlation"))


def mantel_p_value(embeddings_a, embeddings_b, n_permutations=499, seed=42):
    """Permutation p-value for the RSA correlation, reordering the sequences of embeddings_b."""
    rank_a = rankdata(pdist(embeddings_a, metric="correlation"))
    rank_b = squareform(rankdata(pdist(embeddings_b, metric="correlation")))
    z_a = (rank_a - rank_a.mean()) / rank_a.std()

    def correlation_with_a(rank_matrix):
        r = squareform(rank_matrix, checks=False)
        return np.mean(z_a * (r - r.mean()) / r.std())

    observed = correlation_with_a(rank_b)
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(n_permutations):
        order = rng.permutation(len(rank_b))
        if correlation_with_a(rank_b[np.ix_(order, order)]) >= observed:
            exceed += 1
    return (exceed + 1) / (n_permutations + 1)


def pairwise_matrix(names, function):
    """Return a symmetric DataFrame of function(a, b) over every pair of names.

    The diagonal is left empty because each metric compares two different encoders.
    """
    matrix = pd.DataFrame(np.nan, index=names, columns=names)
    for a, b in itertools.combinations(names, 2):
        value = function(a, b)
        matrix.loc[a, b] = matrix.loc[b, a] = value
    return matrix


# ---------------------------------------------------------------------------
# Composition control
# ---------------------------------------------------------------------------

def residualize(X, F):
    """Remove the least-squares fit on standardized F, with an intercept, from every column of X."""
    F_s = StandardScaler().fit_transform(F)
    design = np.column_stack([np.ones(len(F_s)), F_s])
    coef, *_ = np.linalg.lstsq(design, X, rcond=None)
    return X - design @ coef


def composition_share(X, X_residual):
    """Share of an embedding's total variance explained by the composition fit (in sample)."""
    total = ((X - X.mean(axis=0)) ** 2).sum()
    return 1 - (X_residual ** 2).sum() / total


# ---------------------------------------------------------------------------
# Attention at candidate motifs
# ---------------------------------------------------------------------------

def attention_motif_overlap(attention_score, motif_hits):
    """One-sided Mann-Whitney comparison of attention at motif positions versus elsewhere."""
    def _test(positions):
        others = set(range(len(attention_score))) - positions
        if not positions or not others:
            return None
        at, off = attention_score[list(positions)], attention_score[list(others)]
        return {
            "mean_at_motifs": at.mean(),
            "mean_elsewhere": off.mean(),
            "p_value": mannwhitneyu(at, off, alternative="greater").pvalue,
        }

    all_positions, by_name = set(), {}
    for start, end, name in motif_hits:
        positions = set(range(start, min(end, len(attention_score))))
        all_positions |= positions
        by_name.setdefault(name, set()).update(positions)
    result = _test(all_positions)
    if result is not None:
        result["by_motif"] = {name: _test(p) for name, p in by_name.items()}
    return result


# ---------------------------------------------------------------------------
# Tables and figures
# ---------------------------------------------------------------------------

def pair_table(matrices, pairs, labels, modality):
    """Return one row per encoder pair with each metric from a dict of pairwise matrices."""
    rows = []
    for a, b in pairs:
        same = modality[a] == modality[b]
        row = {
            "pair": f"{labels[a]} / {labels[b]}",
            "comparison": f"within {modality[a]}" if same else "across modalities",
        }
        row.update({name: m.loc[a, b] for name, m in matrices.items()})
        rows.append(row)
    return pd.DataFrame(rows).set_index("pair")


def plot_matrices(matrices, labels, diverging=(), fmt="{:.2f}"):
    """Draw encoder-by-encoder heatmaps side by side, annotated with their values.

    Titles listed in `diverging` use a symmetric red-blue scale centered on zero.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(matrices), figsize=(6.2 * len(matrices), 5.6), squeeze=False)
    for ax, (title, m) in zip(axes[0], matrices.items()):
        values = m.values.astype(float)
        if title in diverging:
            bound = np.nanmax(np.abs(values)) or 1.0
            im = ax.imshow(values, cmap="RdBu_r", vmin=-bound, vmax=bound)
            dark = lambda v: abs(v) > 0.6 * bound
        else:
            top = np.nanmax(values) or 1.0
            im = ax.imshow(values, cmap="Greens", vmin=0, vmax=top)
            dark = lambda v: v > 0.6 * top
        names = [labels.get(k, k) for k in m.index]
        ax.set_xticks(range(len(names)), names, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(names)), names, fontsize=8)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                if not np.isnan(values[i, j]):
                    ax.text(j, i, fmt.format(values[i, j]), ha="center", va="center", fontsize=7,
                            color="white" if dark(values[i, j]) else "black")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    plt.show()
