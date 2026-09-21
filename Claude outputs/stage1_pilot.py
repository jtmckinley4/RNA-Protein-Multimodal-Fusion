"""
Stage 1 pilot: representation analysis for frozen RNA and protein encoders,
built directly around Mina's proposed downstream task and datasets.

WHAT THIS DOES
Mina's document names the actual datasets and models to use, so this
version is grounded in those specifics rather than generic placeholders.

  Main dataset:    mRNA_Stability (CodonBERT benchmark, ~41,123 sequences,
                    human, mouse, frog, fish).
  Control dataset:  mRFP_Expression (CodonBERT benchmark, 1,459 variants,
                    synonymous codon randomization of one gene, so every
                    variant translates to an IDENTICAL protein).
  RNA encoder:      Nucleotide Transformer. Chosen over CodonBERT or RNA-FM
                    for this first pass specifically because Mina's own
                    model list confirms Nucleotide Transformer has weights
                    on Hugging Face, while CodonBERT and RNA-FM are not
                    confirmed plug-and-play there. Swap in a custom loader
                    (see load_custom_rna_encoder below) if you want to use
                    CodonBERT or RNA-FM's own GitHub checkpoints instead.
  Protein encoder:  ESM-2.

WHAT IT PRODUCES
  1. A check that every sequence is in frame and starts at a start codon
     (Mina's own "checks before starting" list, run as code instead of by hand).
  2. Linear probe results for RNA-only and protein-only embeddings against
     the stability or expression label. This is the Stage 1 preview of the
     "RNA-only vs protein-only" half of Mina's key experiment. The
     RNA-plus-protein and all-three comparisons are Stage 3 and 4 work,
     once an actual fusion module exists, not this stage.
  3. Linear CKA between the RNA and protein embeddings.
  4. A control check on mRFP_Expression: since every variant encodes an
     identical protein, the protein embeddings for all of them should be
     effectively the same vector, while the RNA embeddings should differ.
     If the protein embeddings are NOT effectively identical, something in
     the translation or embedding step is wrong, and that is worth catching
     now rather than after Stage 4 benchmarking.
  5. A UMAP plot of the main dataset's RNA and protein embeddings.

BEFORE RUNNING
- Pull mRNA_Stability and mRFP_Expression from the CodonBERT benchmark repo
  and set MAIN_CSV_PATH and CONTROL_CSV_PATH below.
- Open both CSVs once and set SEQ_COLUMN and LABEL_COLUMN to match their
  actual headers, they are placeholders here.
- pip install torch transformers biopython scikit-learn umap-learn matplotlib pandas
"""

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import umap
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel
from Bio.Seq import Seq

# ---------------------------------------------------------------------------
# Configuration. Edit these to match your actual files and column names.
# ---------------------------------------------------------------------------
MAIN_CSV_PATH = "mRNA_Stability.csv"
CONTROL_CSV_PATH = "mRFP_Expression.csv"
SEQ_COLUMN = "sequence"        # column holding the CDS or mRNA sequence, check the real header
LABEL_COLUMN = "label"         # column holding stability or expression, check the real header
LABEL_IS_CONTINUOUS = True     # True for a regression style label
N_ROWS = 200                   # keep the first pass small and fast

RNA_MODEL_NAME = "InstaDeepAI/nucleotide-transformer-500m-human-ref"
PROTEIN_MODEL_NAME = "facebook/esm2_t12_35M_UR50D"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------------------
# Optional: swap in CodonBERT or RNA-FM's own checkpoints instead of
# Nucleotide Transformer. Mina's model list flags that these are not
# confirmed to be Hugging Face plug-and-play, so this is left as a stub to
# fill in with whatever loading code their GitHub repo actually provides.
# ---------------------------------------------------------------------------
def load_custom_rna_encoder():
    raise NotImplementedError(
        "Fill this in with CodonBERT's or RNA-FM's own repo loading code "
        "if you want to use one of those instead of Nucleotide Transformer."
    )


# ---------------------------------------------------------------------------
# Model loading and embedding
# ---------------------------------------------------------------------------
def load_encoder(name):
    tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
    model = AutoModel.from_pretrained(name, trust_remote_code=True).to(DEVICE).eval()
    return tok, model


@torch.no_grad()
def embed(seq, tok, model, max_len=1024):
    inputs = tok(seq, return_tensors="pt", truncation=True, max_length=max_len).to(DEVICE)
    out = model(**inputs)
    return out.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()


def is_in_frame_and_starts_correctly(seq):
    """Mina's checklist, as code: sequence length is a multiple of 3, and it
    starts with a start codon, so translation to protein will be clean."""
    seq = seq.upper().strip()
    return len(seq) % 3 == 0 and seq.startswith("ATG")


def translate_cds(seq):
    trimmed = seq[: len(seq) - (len(seq) % 3)]
    return str(Seq(trimmed).translate(to_stop=True))


# ---------------------------------------------------------------------------
# Linear probing
# ---------------------------------------------------------------------------
def run_probe(X, y, continuous, name):
    X = StandardScaler().fit_transform(X)
    if continuous:
        scores = cross_val_score(Ridge(), X, y, cv=5, scoring="r2")
        print(f"  Linear probe on {name} embeddings, R^2 (5 fold): {scores.mean():.3f} +/- {scores.std():.3f}")
    else:
        scores = cross_val_score(LogisticRegression(max_iter=2000), X, y, cv=5, scoring="accuracy")
        print(f"  Linear probe on {name} embeddings, accuracy (5 fold): {scores.mean():.3f} +/- {scores.std():.3f}")


# ---------------------------------------------------------------------------
# Linear CKA
# ---------------------------------------------------------------------------
def linear_cka(X, Y):
    X = X - X.mean(axis=0, keepdims=True)
    Y = Y - Y.mean(axis=0, keepdims=True)
    hsic = np.linalg.norm(Y.T @ X, ord="fro") ** 2
    norm_x = np.linalg.norm(X.T @ X, ord="fro")
    norm_y = np.linalg.norm(Y.T @ Y, ord="fro")
    return hsic / (norm_x * norm_y)


# ---------------------------------------------------------------------------
# Embedding a dataframe of sequences into RNA and protein vectors
# ---------------------------------------------------------------------------
def embed_dataset(df, rna_tok, rna_model, prot_tok, prot_model, seq_col, label_col=None):
    rna_embeds, prot_embeds, labels, protein_strings = [], [], [], []
    dropped_out_of_frame = 0

    for _, row in df.iterrows():
        seq = str(row[seq_col]).strip().upper()

        if not is_in_frame_and_starts_correctly(seq):
            dropped_out_of_frame += 1
            continue

        protein_seq = translate_cds(seq)
        if len(protein_seq) < 5:
            continue

        rna_embeds.append(embed(seq, rna_tok, rna_model))
        prot_embeds.append(embed(protein_seq, prot_tok, prot_model))
        protein_strings.append(protein_seq)
        if label_col is not None and label_col in df.columns:
            labels.append(row[label_col])

    if dropped_out_of_frame:
        print(f"  Dropped {dropped_out_of_frame} sequences that were not in frame or did not start with ATG.")

    rna_embeds = np.vstack(rna_embeds) if rna_embeds else np.empty((0,))
    prot_embeds = np.vstack(prot_embeds) if prot_embeds else np.empty((0,))
    labels = np.array(labels) if labels else None
    return rna_embeds, prot_embeds, protein_strings, labels


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading encoders...")
    rna_tok, rna_model = load_encoder(RNA_MODEL_NAME)
    prot_tok, prot_model = load_encoder(PROTEIN_MODEL_NAME)

    # ---- Main dataset: mRNA_Stability ----
    print("\n=== Main dataset: mRNA_Stability ===")
    main_df = pd.read_csv(MAIN_CSV_PATH).head(N_ROWS).dropna(subset=[SEQ_COLUMN])
    rna_embeds, prot_embeds, _, labels = embed_dataset(
        main_df, rna_tok, rna_model, prot_tok, prot_model, SEQ_COLUMN, LABEL_COLUMN
    )
    print(f"Embedded {len(rna_embeds)} sequences.")

    np.savez(
        "stage1_main_embeddings.npz",
        rna=rna_embeds, protein=prot_embeds,
        labels=labels if labels is not None else np.array([]),
    )

    if labels is not None and len(labels) == len(rna_embeds):
        print("\nLinear probing (RNA-only vs protein-only, the Stage 1 preview of Mina's key comparison):")
        run_probe(rna_embeds, labels, LABEL_IS_CONTINUOUS, "RNA")
        run_probe(prot_embeds, labels, LABEL_IS_CONTINUOUS, "protein")
    else:
        print(f"\nNo usable '{LABEL_COLUMN}' column found or length mismatch, skipping linear probing.")

    print("\nLinear CKA, RNA vs protein:", f"{linear_cka(rna_embeds, prot_embeds):.3f}")

    print("\nBuilding UMAP plot of the main dataset...")
    coords_rna = umap.UMAP(random_state=42).fit_transform(rna_embeds)
    coords_prot = umap.UMAP(random_state=42).fit_transform(prot_embeds)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    axes[0].scatter(coords_rna[:, 0], coords_rna[:, 1], s=14, color="#2C5F2D")
    axes[0].set_title("RNA embeddings (UMAP)")
    axes[1].scatter(coords_prot[:, 0], coords_prot[:, 1], s=14, color="#97BC62")
    axes[1].set_title("Protein embeddings (UMAP)")
    plt.tight_layout()
    plt.savefig("stage1_umap.png", dpi=150, bbox_inches="tight")
    print("Saved stage1_umap.png")

    # ---- Control dataset: mRFP_Expression ----
    print("\n=== Control dataset: mRFP_Expression ===")
    print("Every variant here is a synonymous recoding of one gene, so they should")
    print("all translate to the identical protein. This checks that the pipeline")
    print("actually behaves that way before trusting results on the main dataset.")

    control_df = pd.read_csv(CONTROL_CSV_PATH).head(N_ROWS).dropna(subset=[SEQ_COLUMN])
    control_rna, control_prot, control_proteins, _ = embed_dataset(
        control_df, rna_tok, rna_model, prot_tok, prot_model, SEQ_COLUMN
    )

    unique_proteins = set(control_proteins)
    print(f"Unique translated protein sequences across {len(control_proteins)} variants: {len(unique_proteins)}")
    if len(unique_proteins) == 1:
        print("  As expected: every variant encodes the same protein.")
    else:
        print("  Unexpected: variants encode different proteins. Check the frame and start codon on this file.")

    if len(control_prot) > 1:
        protein_spread = np.linalg.norm(control_prot - control_prot.mean(axis=0), axis=1).mean()
        rna_spread = np.linalg.norm(control_rna - control_rna.mean(axis=0), axis=1).mean()
        print(f"  Average distance to centroid, protein embeddings: {protein_spread:.5f} (should be near zero)")
        print(f"  Average distance to centroid, RNA embeddings:     {rna_spread:.5f} (should be clearly nonzero)")


if __name__ == "__main__":
    main()
