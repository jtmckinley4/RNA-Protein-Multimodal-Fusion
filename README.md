# multimodal-bio-fusion

A research project in the [Complex Adaptive Systems Laboratory](https://complexity.cecs.ucf.edu/directors-welcome/) at the University of Central Florida, studying how to choose and combine pretrained DNA, RNA, and protein foundation models. The team's manuscript is the Overleaf project [Multimodal Biology](https://www.overleaf.com/project/6ab8535fb63c8540bed7e56f), which records the Stage 1 methods, metric definitions, and results.

## Project background

The aim is to develop methods for choosing which biological modalities and pretrained models to combine, and for deciding when and how fusion is useful for a target task. The longer-term goal set with Mina Basirat is to fuse several pretrained encoders, with more than one model per modality (for example, several DNA, RNA, and protein models), and to compare those combinations. Those choices should be grounded in the biological question and the wet-lab work the predictions could inform. The [meeting slides](Notes/Mina_Meeting_Slides_2026-09-23.pptx), particularly slide 3, frame the contribution as a method for deciding whether and how to fuse.

The current investigation uses one frozen encoder per modality to study DNA, RNA, and translated protein representations, beginning with mRNA stability prediction and a synonymous-recoding control. Frozen means that the encoder weights are not updated during these analyses. In [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb), Nucleotide Transformer 500M human-ref (pretrained on the human reference genome) reads each coding sequence in DNA letters, RNA-FM (pretrained on non-coding RNA) reads the same sequence in RNA letters, and ESM-2 35M reads its translation. The original [Stage1.ipynb](Code/Stage1.ipynb) compares only the Nucleotide Transformer and ESM-2 branches, and its `rna_*` variable names refer to the Nucleotide Transformer branch. This is an initial case study within the broader methodology; the choice of future tasks, model combinations, and evaluation criteria remains part of the research.

### Architecture priorities

| Priority | Architecture |
| --- | --- |
| 1 | Coupled Mamba |
| 2 | Isoformer-style cross-attention |
| Fallbacks | Cross-Mamba / BiMamba; mixture-of-experts fusion |

Coupled Mamba's priority was agreed at the September 23, 2026 online meeting. The [meeting slides](Notes/Mina_Meeting_Slides_2026-09-23.pptx), slide 6, list the primary and fallback architectures. Concatenation + MLP is the reference baseline in the research design.

## Repo structure

| Location | Contents |
| --- | --- |
| [Code/](Code/) | Analysis notebooks and input datasets; local runs also produce intermediate outputs here. |
| [docs/](docs/README.md) | Team research plans, bibliography, and shared explanations connecting biology, methods, and evidence to the notebook. |
| [Notes/Reviews/](Notes/Reviews/) | Individual paper reviews and interpretations, organized by contributor. |
| [Notes/](Notes/) | Working notes, meeting records, and discussion slides. |
| [Papers/](Papers/) | Reference papers informing the research. |

Keep individual paper notes in contributor folders, such as [Notes/Reviews/Julian/](Notes/Reviews/Julian/) and `Notes/Reviews/Chase/`, so interpretations remain attributable. Obsidian supports personal study; explanations needed to understand the project belong in the shared documentation.

Agents working in this repository should start with [AGENTS.md](AGENTS.md).

## Stage 1 analysis

[Stage1.ipynb](Code/Stage1.ipynb) contains the original representation analysis. [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) is the current Stage 1 notebook, with expanded explanations and an interpretation after each result. It runs every track on DNA, RNA, and protein embeddings of the same 981 retained sequences and compares the three modality pairs. Keep results associated with the notebook and version that produced them.

The notebooks contain analyses that:

1. Check sequence length and start codons, translate nucleotide sequences, generate matched DNA, RNA, and protein embeddings, and audit the full stability file against the version used by BioLangFusion.
2. Probe prediction from each representation separately and from concatenated embeddings, with sequence-feature controls.
3. Compare representation geometry using linear CKA and additional neighborhood, correlation, and retrieval diagnostics, repeat CKA and retrieval after removing sequence composition, and visualize embeddings with UMAP.
4. Examine the mRFP expression dataset as a synonymous-recoding control.
5. Explore DNA-encoder and RNA-encoder attention, candidate sequence patterns, relationships between representation similarity and prediction error, and representational similarity with a Mantel permutation test.

The concatenated-embedding probe uses a linear model, distinct from the concatenation + MLP reference baseline. These analyses can inform experiment design; their outputs alone do not establish which fusion method to use or validate a wet-lab application.

### Stage 1 results

The main results from [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb), with 981 retained sequences and five grouped folds. The notebook's result notes give the full tables and interpretations.

| Analysis | DNA | RNA | Protein |
| --- | --- | --- | --- |
| Stability probe, mean $R^2$ (fold SD) | 0.015 (0.072) | 0.028 (0.065) | 0.103 (0.034) |
| GC content, mean $R^2$ | 0.986 | 0.950 | 0.678 |
| GC3, mean $R^2$ | 0.969 | 0.919 | 0.380 |
| Share of embedding variance explained by composition | 0.618 | 0.677 | 0.446 |

| Pair | Linear CKA | CKA after composition control | CCA Recall@1 (chance 0.0034) | Recall@1 after composition control | RSA (Mantel $p$) |
| --- | --- | --- | --- | --- | --- |
| DNA-RNA | 0.530 | 0.101 | 0.549 | 0.112 | 0.548 (0.002) |
| DNA-protein | 0.128 | 0.027 | 0.366 | 0.024 | 0.234 (0.002) |
| RNA-protein | 0.199 | 0.055 | 0.224 | 0.054 | 0.238 (0.002) |

- Only the protein embedding carries a consistent linear stability signal, and concatenating modalities does not improve on it (best combination 0.103).
- The DNA and RNA embeddings retain synonymous codon information that the protein embedding cannot, shown by the GC3 probes.
- Most agreement between modalities comes from shared sequence composition: removing letter, codon, and amino-acid frequencies cuts CKA by 72% to 81% and retrieval to between 7 and 33 times chance.
- The synonymous-recoding control behaves as expected, and neither nucleotide encoder attends more to candidate stability motifs.

### Next steps: multiple encoders and published benchmarks

Stage 1 now covers the DNA modality with one encoder per modality. The next work adds more than one encoder per modality and compares against published fusion studies on the same inputs to define what alignment means. The Overleaf section "Stage 1 Extension: Benchmarks and the DNA Modality" holds the plan; it will be implemented in a separate notebook.

| Setting | Dataset | How DNA enters | Published comparison |
| --- | --- | --- | --- |
| A: derived modalities | CodonBERT mRNA stability (the current CSV) | A DNA encoder reads the coding sequence in DNA letters, an RNA encoder reads it in RNA letters, and a protein encoder reads its translation. This is the Stage 1 setup. | [BioLangFusion](Papers/BioLangFusion.pdf), Table 1: best fusion Spearman 0.563 versus 0.553 for the best single encoder. |
| B: distinct modalities | [IsoFormer GTEx transcript expression](https://huggingface.co/datasets/InstaDeepAI/multi_omics_transcript_expression) | Genomic DNA centered on the transcription start site, alongside the full transcript and the protein. | [IsoFormer](Papers/Multi-Modal-Transfer-Learning.pdf), Table 2: three modalities reach R² 0.43 versus 0.36 for RNA alone. |

In Setting A all three inputs derive from one coding sequence, so differences between encoders come from pretraining corpora and tokenization rather than new biological information. The stability CSV has no gene or transcript identifiers, so genomic context around each gene is not available without a separate mapping step. Setting B supplies DNA that carries promoter and regulatory context absent from the protein.

Candidate additional encoders are Nucleotide Transformer v2 100M multi-species (BioLangFusion's DNA encoder) and DNABERT-2 for DNA, mRNA-FM for RNA, and ESM-2 8M (BioLangFusion) and 150M (IsoFormer) for protein. Nucleotide Transformer v2 and DNABERT-2 load custom model code written for `transformers` 4, which needs small compatibility adjustments under `transformers` 5. Trained fusion architectures, including BioLangFusion's fusion heads and IsoFormer's cross-attention, need token-level embeddings and belong to the fusion stage.

## Data

The input datasets are included in `Code/`:

- [mRFP_Expression.csv](Code/mRFP_Expression.csv): 1,459 rows containing 1,455 distinct sequence strings, from synonymous codon randomization of one gene.
- [mRNA_Stability.csv](Code/mRNA_Stability.csv): 65,356 rows containing 29,949 distinct sequence strings.

These counts describe the included CSVs before notebook filtering or subsampling.

The Dataset audit cell in [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) records the following properties of `mRNA_Stability.csv`, which matter for comparisons with published results:

- The `Split` column assigns 45,749 rows to train, 9,803 to validation, and 9,804 to test. Of the 8,283 distinct test sequences, 5,392 also occur in training.
- 12,844 sequences occur more than once, and 12,775 of those carry differing `Value` labels; the median standard deviation of labels within one sequence is 0.49.
- 37% of rows are at most 1,000 nucleotides, so single-nucleotide encoders with a limit near 1,000 tokens see truncated input for most sequences.
- [BioLangFusion](Papers/BioLangFusion.pdf), Appendix A.2, reports 41,123 raw and 23,929 used mRNA stability sequences with the CodonBERT splits. Whether this file is the same version, and which filtering produced 23,929, is unresolved.

Comparisons with published numbers should therefore use the official split, while leakage-free estimates need a deduplicated, sequence-disjoint split. The CSVs were sourced from the fine-tuning benchmark data in [Sanofi-Public/CodonBERT](https://github.com/Sanofi-Public/CodonBERT/tree/master/benchmarks/CodonBERT/data/fine-tune). Their inclusion supplies the notebook inputs; interpreting a prediction still requires checking the source assay, labels, and retained sequence regions.

## Generated files

Keep routine model caches and regenerable intermediate outputs local and ignore their specific paths. Retain source datasets and notebooks in Git. Share selected results deliberately, with the producing notebook or code version, input identities, model revisions, and relevant settings so that others can interpret them. Avoid blanket ignore rules for scientific file formats.

When code adds or changes an output, update this inventory and its handling. Add or adjust specific paths in [.gitignore](.gitignore) for outputs kept local. Preserve an identified copy of any result needed as evidence before rerunning code that overwrites it. Paths below assume the working directory specified in Setup.

| Generated file | Producer | Purpose | Handling |
| --- | --- | --- | --- |
| `Code/stage1_main_embeddings.npz` | `Stage1.ipynb` and `Stage1_refactor.ipynb` | Snapshot of embeddings and labels; subsequent analyses use the in-memory arrays. `Stage1_refactor.ipynb` stores the keys `dna`, `rna` (RNA-FM), `protein`, and `labels`; `Stage1.ipynb` stores its Nucleotide Transformer embeddings under `rna`, with `protein` and `labels`. | Local and ignored; either notebook overwrites the same path. |

## Setup

### Notebook dependencies

Use your existing Python environment for the project. Install PyTorch using the [official installation selector](https://pytorch.org/get-started/locally/) for your operating system and CPU or CUDA configuration. Install the remaining notebook dependencies in that environment:

```sh
python -m pip install numpy pandas scipy scikit-learn umap-learn matplotlib biopython "transformers==5.15.1" multimolecule ipykernel
```

Open notebooks with VS Code's Python and Jupyter extensions and [select the environment containing these packages as the kernel](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management). Use `Code/` as the kernel's working directory because the notebooks use relative CSV and output paths.

The notebooks use CUDA when available and otherwise run on CPU. `multimolecule` provides RNA-FM. Version 0.2.1 imports with `transformers` 5.14.1 and 5.15.1 but not 5.16 or later, which is why `transformers` is pinned. If `import multimolecule` fails in an Anaconda environment with an older `datasets` or `huggingface_hub`, upgrade `datasets` and `fsspec` and reinstall `huggingface_hub`.

The first run of [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) downloads `InstaDeepAI/nucleotide-transformer-500m-human-ref`, `multimolecule/rnafm`, and `facebook/esm2_t12_35M_UR50D`, unless they are already cached. Hugging Face normally stores these downloads in the [user's cache](https://huggingface.co/docs/transformers/installation#cache-directory); the notebooks do not configure the repository's `.model-cache/` directory.

This dependency list covers the imports in the Stage 1 notebooks. A fresh-environment run has not been verified, and the repository does not yet pin package versions or model revisions for reproducibility.

### Viewing project files in VS Code

These optional extensions provide convenient access to the documents and datasets in this repository.

| Files | Extension | Use |
| --- | --- | --- |
| `.pptx`, `.docx`, `.xlsx` | [Office Viewer for VS Code](https://marketplace.visualstudio.com/items?itemName=imfing.office-viewer-vscode) | Preview slides, documents, and spreadsheets. |
| `.pdf` | [PDF Viewer](https://marketplace.visualstudio.com/items?itemName=mathematic.vscode-pdf) | Read papers inside VS Code. |
| `.csv` | [Spreadsheet Viewer](https://marketplace.visualstudio.com/items?itemName=GrapeCity.gc-excelviewer) | Browse data in a grid, sort columns, and filter rows. |

For CSV files, choose **Open Preview** from the file's context menu. To display numeric values as stored, set `csv-preview.formatValues` to `never`; the default preview formats numbers to two significant digits.

## Contributors

- Julian McKinley ([@jtmckinley4](https://github.com/jtmckinley4))
- Chase Di Maria Breisinger ([@Lqvy](https://github.com/Lqvy))
