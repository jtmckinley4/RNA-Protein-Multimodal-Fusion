"""Shared functions for the Stage 1 representation-analysis notebooks.

Stage1_multimodel.ipynb and Stage1_GTEx.ipynb import this module so that every
notebook computes each metric with the same implementation. The analysis
functions reproduce those defined inline in Stage1_refactor.ipynb.
"""

from __future__ import annotations

import gc
import hashlib
import itertools
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import multimolecule  # noqa: F401  (registers the RNA-FM and mRNA-FM classes with Transformers)
from Bio.Seq import Seq
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
# Encoders
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Encoder:
    """A frozen pretrained encoder and the input it reads.

    alphabet: "dna" (U replaced by T), "rna" (T replaced by U), or "protein"
    (translated coding sequence). loader: "auto" for checkpoints that load with
    the Transformers auto classes, "remote_esm" for Nucleotide Transformer v2,
    and "remote_dnabert2" for DNABERT-2.
    """

    key: str
    label: str
    modality: str
    checkpoint: str
    alphabet: str
    max_len: int
    loader: str = "auto"
    revision: str | None = None


ENCODERS = {
    e.key: e
    for e in [
        Encoder("nt500m", "NT 500M human-ref", "DNA",
                "InstaDeepAI/nucleotide-transformer-500m-human-ref", "dna", 1000),
        Encoder("ntv2_100m", "NT v2 100M multi-species", "DNA",
                "InstaDeepAI/nucleotide-transformer-v2-100m-multi-species", "dna", 2048,
                loader="remote_esm", revision="f34324c6fde36a4f635f0f1f06cac5d25acd6798"),
        Encoder("dnabert2", "DNABERT-2", "DNA",
                "zhihan1996/DNABERT-2-117M", "dna", 1024,
                loader="remote_dnabert2", revision="7bce263b15377fc15361f52cfab88f8b586abda0"),
        Encoder("rnafm", "RNA-FM", "RNA", "multimolecule/rnafm", "rna", 1024),
        Encoder("mrnafm", "mRNA-FM", "RNA", "multimolecule/mrnafm", "rna", 1024),
        Encoder("esm2_8m", "ESM-2 8M", "protein", "facebook/esm2_t6_8M_UR50D", "protein", 1024),
        Encoder("esm2_35m", "ESM-2 35M", "protein", "facebook/esm2_t12_35M_UR50D", "protein", 1024),
        Encoder("esm2_150m", "ESM-2 150M", "protein", "facebook/esm2_t30_150M_UR50D", "protein", 1024),
    ]
}

# Configuration fields that Transformers 5 no longer sets by default but that the
# remote model code reads.
_REMOTE_CONFIG_DEFAULTS = {
    "remote_esm": {"is_decoder": False, "add_cross_attention": False},
    "remote_dnabert2": {"is_decoder": False},
}
# Remote base-model class, checkpoint key prefix, and weights file for each remote loader.
_REMOTE_CLASSES = {
    "remote_esm": ("modeling_esm.EsmModel", "esm.", "model.safetensors"),
    "remote_dnabert2": ("bert_layers.BertModel", "bert.", "pytorch_model.bin"),
}


def select_device():
    """Return "cuda", "mps", or "cpu", in that order of preference."""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def apply_transformers5_compat():
    """Let the Nucleotide Transformer v2 and DNABERT-2 remote code run under Transformers 5.

    1. DNABERT-2 optionally imports `triton`, which is unavailable on macOS. Its code falls
       back to PyTorch attention when that import fails, but Transformers rejects the file
       before the fallback can run. `triton` is removed from that pre-import check only.
    2. Nucleotide Transformer v2 imports `find_pruneable_heads_and_indices` and calls
       `get_head_mask`, which Transformers 5 removed. Equivalent helpers are restored;
       head masking is never used here.
    """
    import transformers.dynamic_module_utils as dmu
    import transformers.pytorch_utils as pu
    from transformers.modeling_utils import PreTrainedModel

    if not getattr(dmu, "_stage1_triton_patch", False):
        original_get_imports = dmu.get_imports
        dmu.get_imports = lambda filename: [
            m for m in original_get_imports(filename) if m != "triton"
        ]
        dmu._stage1_triton_patch = True

    if not hasattr(pu, "find_pruneable_heads_and_indices"):
        def find_pruneable_heads_and_indices(heads, n_heads, head_size, already_pruned_heads):
            mask = torch.ones(n_heads, head_size)
            heads = set(heads) - already_pruned_heads
            for head in heads:
                head = head - sum(1 if h < head else 0 for h in already_pruned_heads)
                mask[head] = 0
            mask = mask.view(-1).contiguous().eq(1)
            index = torch.arange(len(mask))[mask].long()
            return heads, index

        pu.find_pruneable_heads_and_indices = find_pruneable_heads_and_indices

    if not hasattr(PreTrainedModel, "get_head_mask"):
        def get_head_mask(self, head_mask, num_hidden_layers, is_attention_chunked=False):
            if head_mask is not None:
                raise NotImplementedError("Head masking is not supported here.")
            return [None] * num_hidden_layers

        PreTrainedModel.get_head_mask = get_head_mask


def _load_checkpoint_state(repo, filename, revision):
    """Return a checkpoint's state dict, using the local Hugging Face cache when available."""
    from huggingface_hub import hf_hub_download

    try:
        path = hf_hub_download(repo, filename, revision=revision, local_files_only=True)
    except Exception:
        path = hf_hub_download(repo, filename, revision=revision)
    if filename.endswith(".safetensors"):
        from safetensors.torch import load_file

        return load_file(path)
    return torch.load(path, map_location="cpu", weights_only=True)


def _load_remote_model(encoder):
    """Build a remote-code base model on the CPU and load its checkpoint weights.

    Transformers 5 constructs models on a placeholder device before loading weights.
    DNABERT-2 computes its ALiBi tensor and Nucleotide Transformer v2 its rotary
    frequencies during construction, so both are built directly instead. Only the
    unused pooler may be absent from the checkpoint.
    """
    from transformers import AutoConfig
    from transformers.dynamic_module_utils import get_class_from_dynamic_module

    class_ref, prefix, weights_file = _REMOTE_CLASSES[encoder.loader]
    config = AutoConfig.from_pretrained(
        encoder.checkpoint, trust_remote_code=True, revision=encoder.revision
    )
    for name, value in _REMOTE_CONFIG_DEFAULTS[encoder.loader].items():
        if getattr(config, name, None) is None:
            setattr(config, name, value)
    if encoder.loader == "remote_dnabert2" and getattr(config, "pad_token_id", None) is None:
        config.pad_token_id = 3  # [PAD] in the DNABERT-2 tokenizer

    model_class = get_class_from_dynamic_module(
        class_ref, encoder.checkpoint, revision=encoder.revision
    )
    model = model_class(config)
    state = {
        k[len(prefix):]: v
        for k, v in _load_checkpoint_state(encoder.checkpoint, weights_file, encoder.revision).items()
        if k.startswith(prefix)
    }
    missing, unexpected = model.load_state_dict(state, strict=False)
    missing = [k for k in missing if not k.startswith("pooler.")]
    if missing or unexpected:
        raise RuntimeError(
            f"{encoder.key}: weights did not match (missing={missing}, unexpected={unexpected})"
        )
    return model


def load_encoder(encoder, device, eager_attention=False):
    """Return (tokenizer, model) for an Encoder, on device and in evaluation mode."""
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        encoder.checkpoint, trust_remote_code=True, revision=encoder.revision
    )
    if encoder.loader == "auto":
        kwargs = {"attn_implementation": "eager"} if eager_attention else {}
        model = AutoModel.from_pretrained(
            encoder.checkpoint, trust_remote_code=True, revision=encoder.revision, **kwargs
        )
    else:
        apply_transformers5_compat()
        model = _load_remote_model(encoder)
    return tokenizer, model.to(device).eval()


def free_memory():
    """Release cached memory after a model is deleted, before loading the next one."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()


# ---------------------------------------------------------------------------
# Sequences
# ---------------------------------------------------------------------------

def is_in_frame_and_starts_correctly(seq):
    """Check for a length divisible by three and an ATG or AUG start."""
    seq = seq.upper().strip()
    return len(seq) % 3 == 0 and seq.startswith(("ATG", "AUG"))


def translate_cds(seq):
    """Translate complete codons using the standard code, up to the first stop."""
    trimmed_seq = seq[: len(seq) - (len(seq) % 3)]
    return str(Seq(trimmed_seq).translate(to_stop=True))


def rna_to_dna(seq):
    """Return an uppercase sequence with U replaced by T."""
    return seq.upper().replace("U", "T")


def dna_to_rna(seq):
    """Return an uppercase sequence with T replaced by U."""
    return seq.upper().replace("T", "U")


def retained_rows(df, seq_col, label_col=None):
    """Apply the Stage 1 filters and return (sequences, labels, lengths) in input order.

    A row is kept when its length is a multiple of three, it starts with ATG or AUG,
    and it translates to at least five amino acids. These are the filters used in
    Stage1_refactor.ipynb, so the same sample yields the same retained rows.
    """
    seqs, labels = [], []
    for _, row in df.iterrows():
        seq = str(row[seq_col]).strip().upper()
        if not is_in_frame_and_starts_correctly(seq):
            continue
        if len(translate_cds(seq)) < 5:
            continue
        seqs.append(seq)
        if label_col is not None:
            labels.append(row[label_col])
    lengths = np.array([len(s) for s in seqs]).reshape(-1, 1)
    return seqs, (np.array(labels) if label_col is not None else None), lengths


def encoder_input(encoder, seq):
    """Return the string an encoder reads for one retained coding sequence."""
    if encoder.alphabet == "dna":
        return rna_to_dna(seq)
    if encoder.alphabet == "rna":
        return dna_to_rna(seq)
    return translate_cds(seq)


def gc_content(seq):
    """Return the G-or-C fraction of a nonempty uppercase sequence."""
    return (seq.count("G") + seq.count("C")) / len(seq)


def gc3_content(seq):
    """Return the GC fraction at third positions of complete codons."""
    return gc_content(seq[2::3])


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

@torch.no_grad()
def embed(seq, tokenizer, model, max_len, device):
    """Mean-pool one sequence's final hidden state into a NumPy vector."""
    inputs = tokenizer(seq, return_tensors="pt", truncation=True, max_length=max_len).to(device)
    out = model(**inputs)
    token_embeddings = out[0]  # (1, T, d): last_hidden_state for every encoder used here
    return token_embeddings.mean(dim=1).squeeze().float().cpu().numpy()


def count_tokens(seq, tokenizer, max_len):
    """Return (tokens after truncation, tokens without truncation) for one input."""
    full = len(tokenizer(seq)["input_ids"])
    return min(full, max_len), full


def sequences_fingerprint(seqs):
    """Return a short hash identifying an ordered list of sequences."""
    digest = hashlib.sha1("\n".join(seqs).encode()).hexdigest()
    return digest[:16]


def embed_with_cache(encoder, seqs, cache_dir, device, progress_every=200):
    """Embed seqs with one encoder, reusing a saved matrix when it matches.

    The cache file records the checkpoint, revision, token limit, and a fingerprint of
    the ordered input sequences; any mismatch triggers recomputation.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{encoder.key}.npz")
    fingerprint = sequences_fingerprint(seqs)
    expected = {
        "checkpoint": encoder.checkpoint,
        "revision": encoder.revision or "",
        "max_len": encoder.max_len,
        "fingerprint": fingerprint,
    }
    if os.path.exists(path):
        saved = np.load(path, allow_pickle=False)
        if all(str(saved[k]) == str(v) for k, v in expected.items()):
            return saved["embeddings"], True

    tokenizer, model = load_encoder(encoder, device)
    vectors = []
    for i, seq in enumerate(seqs, start=1):
        vectors.append(embed(encoder_input(encoder, seq), tokenizer, model, encoder.max_len, device))
        if progress_every and i % progress_every == 0:
            print(f"    {encoder.key}: {i}/{len(seqs)}")
    del model, tokenizer
    free_memory()
    embeddings = np.vstack(vectors)
    np.savez(path, embeddings=embeddings, device=device, **expected)
    return embeddings, False


@torch.no_grad()
def embed_all_layers(seq, encoder, tokenizer, model, device):
    """Mean-pool every returned hidden state for one sequence.

    Every encoder contributes its embedding-layer output followed by each transformer
    layer. DNABERT-2's own all-layer option fails, so its states are captured with
    forward hooks on the embedding module and each encoder layer.
    """
    inputs = tokenizer(
        encoder_input(encoder, seq), return_tensors="pt", truncation=True, max_length=encoder.max_len
    ).to(device)
    if encoder.loader == "remote_dnabert2":
        captured = []
        modules = [model.embeddings] + list(model.encoder.layer)
        hooks = [m.register_forward_hook(lambda _m, _i, out: captured.append(out)) for m in modules]
        try:
            model(**inputs)
        finally:
            for hook in hooks:
                hook.remove()
        layers = captured
    else:
        layers = model(**inputs, output_hidden_states=True).hidden_states
    return [h.reshape(-1, h.shape[-1]).mean(dim=0).float().cpu().numpy() for h in layers]


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

CODONS = ["".join(t) for t in itertools.product("ACGT", repeat=3)]
AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")


def composition_features(seq):
    """Return GC, GC3, log length, 64 codon frequencies, and 20 amino-acid frequencies."""
    dna = rna_to_dna(seq)
    protein = translate_cds(seq)
    codons = [dna[i:i + 3] for i in range(0, len(dna) - 2, 3)]
    codon_counts = pd.Series(codons).value_counts()
    codon_freq = [codon_counts.get(c, 0) / len(codons) for c in CODONS]
    aa_freq = [protein.count(a) / max(len(protein), 1) for a in AMINO_ACIDS]
    return [gc_content(dna), gc3_content(dna), np.log(len(dna))] + codon_freq + aa_freq


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
# Attention and candidate motifs
# ---------------------------------------------------------------------------

STABILITY_MOTIFS = {"ARE_pentamer": "AUUUA", "ARE_nonamer": "UUAUUUAUU", "m6A_DRACH": "DRACH"}
_IUPAC = {
    "A": "A", "C": "C", "G": "G", "T": "T", "U": "T", "R": "[AG]", "Y": "[CT]", "S": "[GC]",
    "W": "[AT]", "K": "[GT]", "M": "[AC]", "B": "[CGT]", "D": "[AGT]", "H": "[ACT]",
    "V": "[ACG]", "N": "[ACGT]",
}


def scan_sequence_for_motifs(sequence, motifs=STABILITY_MOTIFS):
    """Return (start, end, motif_name) for each consensus match, including overlaps."""
    import re

    seq = sequence.upper().replace("U", "T")
    hits = []
    for name, pattern in motifs.items():
        regex = "".join(_IUPAC[b] for b in pattern.upper())
        hits += [(m.start(), m.start() + len(pattern), name) for m in re.finditer(f"(?={regex})", seq)]
    return hits


@torch.no_grad()
def nucleotide_attention(seq, encoder, tokenizer, model, device, layer=-1):
    """Return last-layer incoming attention, min-max scaled, expanded to nucleotides.

    Heads are averaged, each token's received attention is summed over queries, special
    tokens are dropped, and each token's score is repeated over the nucleotides it spells.
    """
    inputs = tokenizer(
        encoder_input(encoder, seq), return_tensors="pt", truncation=True, max_length=encoder.max_len
    ).to(device)
    attentions = model(**inputs, output_attentions=True).attentions
    layer_att = attentions[layer][0].float().mean(dim=0).cpu().numpy()
    score = layer_att.sum(axis=0)
    score = (score - score.min()) / (score.max() - score.min() + 1e-8)
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    expanded = []
    for s, tok in zip(score, tokens):
        if tok.startswith("<") or tok.startswith("["):
            continue
        expanded.extend([s] * len(tok))
    return np.array(expanded)


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
