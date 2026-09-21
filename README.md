# Genomics Multimodal Fusion

Research pipeline for aligning and fusing separately pretrained DNA, RNA, and protein foundation models, developed as part of an MSDA (AI Track) capstone project at the University of Central Florida.

## Project background

The goal is to test whether combining frozen, off-the-shelf genomic and protein language models captures more useful biological signal than any single modality alone. The first pass uses Nucleotide Transformer as the RNA encoder and ESM-2 as the protein encoder, with Coupled-Mamba under consideration as a fusion architecture for later stages.

This work is advised by Mina Basirat (postdoc researcher, Prof. Ivan Garibay's lab, UCF) and builds on related work in the lab on codon-resolved genomic language modeling.

## Repo structure

- `Code/` — the main analysis notebook (`Genomics_MultiModal_Fusion_P1.ipynb`) and supporting datasets.
- `Notes/` — meeting notes, project notes, and slide decks.
- `Papers/` — reference papers informing the modeling approach.
- `Reviews/` — structured reviews and summaries of each reference paper.

## Current status: Stage 1

`Code/Genomics_MultiModal_Fusion_P1.ipynb` runs the first-pass representation analysis:

1. Validates that every sequence is in frame and starts at a start codon.
2. Runs linear probes on RNA-only and protein-only embeddings against stability/expression labels.
3. Computes linear CKA between the RNA and protein embeddings.
4. Runs a control check on the mRFP_Expression dataset (synonymous codon variants that all translate to an identical protein).
5. Produces a UMAP visualization of the embeddings.

RNA-plus-protein fusion and full benchmarking come in later stages, once a fusion module exists.

## Data

Two large data files are intentionally excluded from this repo via `.gitignore` and need to be added locally before running the pipeline:

- `Code/mRNA_Stability.csv` (CodonBERT benchmark, ~41,123 sequences)
- `Code/stage1_main_embeddings.npz` (generated embeddings)

Get `mRNA_Stability.csv` and `mRFP_Expression.csv` from the CodonBERT benchmark repo, place them in `Code/`, and set the correct paths in the notebook's configuration cell.

## Setup

```
pip install torch transformers biopython scikit-learn umap-learn matplotlib pandas
```

## Contributors

- Julian McKinley ([@jtmckinley4](https://github.com/jtmckinley4))
- [@Lqvy](https://github.com/Lqvy)
