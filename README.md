# multimodal-bio-fusion

A research project in the [Complex Adaptive Systems Laboratory](https://complexity.cecs.ucf.edu/directors-welcome/) at the University of Central Florida, studying how to choose and combine pretrained DNA, RNA, and protein foundation models. The team's manuscript is the Overleaf project [multimodal-bio-fusion](https://www.overleaf.com/project/6ab8535fb63c8540bed7e56f), which records the Stage 1 methods, metric definitions, and results.

## Project background

The aim is to develop methods for choosing which biological modalities and pretrained models to combine, and for deciding when and how fusion is useful for a target task. The longer-term goal set with Mina Basirat is to fuse several pretrained encoders, with more than one model per modality (for example, several DNA, RNA, and protein models), and to compare those combinations. Those choices should be grounded in the biological question and the wet-lab work the predictions could inform. The [meeting slides](Notes/Mina_Meeting_Slides_2026-09-23.pptx), particularly slide 3, frame the contribution as a method for deciding whether and how to fuse.

Stage 1 studies DNA, RNA, and translated protein representations from frozen encoders, beginning with mRNA stability prediction and a synonymous-recoding control. Frozen means that the encoder weights are not updated during these analyses. [Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb) compares eight encoders, two or three per modality. Nucleotide Transformer 500M human-ref, Nucleotide Transformer v2 100M multi-species, and DNABERT-2 read each coding sequence in DNA letters; RNA-FM (pretrained on non-coding RNA) and mRNA-FM (pretrained on messenger RNA coding sequences) read the same sequence in RNA letters; and ESM-2 8M, 35M, and 150M read its translation. The notebook runs on any dataset and set of encoders registered in the `mbf` package. A dataset in which DNA is a distinct input, such as IsoFormer's GTEx transcript-expression data, is the next addition. The choice of future tasks, model combinations, and evaluation criteria remains part of the research.

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
| [Code/mbf/](Code/mbf/) | The Python package the notebooks share: sequence utilities, encoder and dataset registries, fold assignments, embedding, and analysis functions. |
| [docs/](docs/README.md) | Team research plans, bibliography, and shared explanations connecting biology, methods, and evidence to the notebook. |
| [Notes/Reviews/](Notes/Reviews/) | Individual paper reviews and interpretations, organized by contributor. |
| [Notes/](Notes/) | Working notes, meeting records, and discussion slides. |
| [Papers/](Papers/) | Reference papers informing the research. |

Keep individual paper notes in contributor folders, such as [Notes/Reviews/Julian/](Notes/Reviews/Julian/) and `Notes/Reviews/Chase/`, so interpretations remain attributable. Obsidian supports personal study; explanations needed to understand the project belong in the shared documentation.

Agents working in this repository should start with [AGENTS.md](AGENTS.md).

## Stage 1 analysis

[Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb) holds the Stage 1 analyses, with explanations and an interpretation after each result. Its settings choose a dataset from `mbf.datasets` and encoders from `mbf.encoders`, and it displays the source of the `mbf` functions beside their explanations. The saved run uses eight encoders on 981 retained mRNA stability sequences. Keep results associated with the notebook version and settings that produced them.

The notebook:

1. Checks sequence length and start codons, translates nucleotide sequences, generates matched embeddings from every encoder, and audits the full stability file against the version used by BioLangFusion.
2. Probes prediction of stability, GC content, GC3, and a base-pairing proxy from each embedding, compares stability prediction with a sequence-length baseline, and probes stability from concatenated embeddings.
3. Compares representation geometry for every encoder pair using linear CKA, layer-wise CKA, neighborhood overlap, and CCA retrieval, repeats CKA and retrieval after removing sequence composition, and visualizes embeddings with UMAP.
4. Examines the mRFP expression dataset as a synonymous-recoding control.
5. Explores nucleotide-encoder attention at candidate sequence patterns, relationships between representation alignment and prediction error, and representational similarity with a Mantel permutation test.

Probes use ridge regression over five folds that keep identical sequences together. A hash of each sequence pins the fold assignment, so it does not depend on the machine, and each probe is repeated over ten further fold assignments to show how much the partition moves the result. The concatenated-embedding probe uses a linear model, distinct from the concatenation + MLP reference baseline. These analyses can inform experiment design; their outputs alone do not establish which fusion method to use or validate a wet-lab application.

### Stage 1 results

The main results from the saved run of [Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb), with 981 retained sequences. Probe scores are mean $R^2$ over the five pinned folds, with the fold standard deviation, and the mean over ten further fold assignments. The notebook's result notes give the full tables and interpretations, and its Summary section draws them together.

| Encoder | Modality | Stability $R^2$, pinned (fold SD) | Stability $R^2$, ten further assignments | GC3 $R^2$ | Share of embedding variance explained by composition |
| --- | --- | --- | --- | --- | --- |
| Nucleotide Transformer 500M human-ref | DNA | 0.032 (0.043) | 0.046 | 0.968 | 0.618 |
| Nucleotide Transformer v2 100M multi-species | DNA | 0.080 (0.032) | 0.074 | 0.986 | 0.804 |
| DNABERT-2 | DNA | 0.054 (0.031) | 0.057 | 0.948 | 0.610 |
| RNA-FM | RNA | 0.052 (0.032) | 0.046 | 0.917 | 0.677 |
| mRNA-FM | RNA | 0.127 (0.032) | 0.110 | 0.946 | 0.296 |
| ESM-2 8M | Protein | 0.127 (0.044) | 0.131 | 0.379 | 0.479 |
| ESM-2 35M | Protein | 0.114 (0.049) | 0.123 | 0.387 | 0.446 |
| ESM-2 150M | Protein | 0.144 (0.035) | 0.142 | 0.436 | 0.437 |

| Encoder pairs | Linear CKA | CKA after composition control | CCA Recall@1 (chance 0.0034) | Recall@1 after composition control |
| --- | --- | --- | --- | --- |
| Within DNA | 0.270 to 0.608 | 0.038 to 0.113 | 0.702 to 0.783 | 0.058 to 0.122 |
| Within RNA (RNA-FM and mRNA-FM) | 0.126 | 0.055 | 0.322 | 0.047 |
| Within protein | 0.553 to 0.744 | 0.376 to 0.643 | 0.936 to 0.973 | 0.671 to 0.868 |
| DNA with RNA-FM | 0.171 to 0.613 | 0.044 to 0.164 | 0.549 to 0.614 | 0.092 to 0.112 |
| DNA with mRNA-FM | 0.030 to 0.087 | 0.012 to 0.031 | 0.393 to 0.492 | 0.034 to 0.044 |
| DNA or RNA-FM with protein | 0.067 to 0.255 | 0.013 to 0.085 | 0.217 to 0.580 | 0.017 to 0.054 |
| mRNA-FM with protein | 0.037 to 0.046 | 0.021 to 0.028 | 0.458 to 0.492 | 0.078 to 0.102 |

- The protein encoders carry the most linearly accessible stability signal. mRNA-FM, which reads one token per codon, comes close, while the other nucleotide encoders reach 0.03 to 0.08, and sequence length alone predicts almost nothing ($R^2$ 0.003).
- Every nucleotide encoder retains synonymous codon information that the protein encoders cannot, shown by the GC3 probes.
- Concatenating mRNA-FM with a protein encoder improves on the better of the two under all ten further fold assignments, by about 0.01 to 0.02. Larger concatenations do not improve on the best single encoder.
- Most agreement involving a nucleotide encoder comes from shared sequence composition: removing letter, codon, and amino-acid frequencies cuts CKA by 38% to 90%. Agreement among the protein encoders survives the control, and mRNA-FM keeps the most correspondence with the protein encoders, retrieving its protein partner at about 23 to 30 times chance.
- The synonymous-recoding control behaves as expected. Nucleotide Transformer 500M and RNA-FM do not attend more to candidate stability patterns; the apparent associations for Nucleotide Transformer v2 and mRNA-FM need positional and codon-composition controls before they can be interpreted.

### Next steps: published benchmarks and distinct modalities

The remaining Stage 1 work compares against published fusion studies on the same inputs to define what alignment means. The saved run of [Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb) covers Setting A below. Setting B needs a GTEx entry in the dataset registry, [datasets.py](Code/mbf/datasets.py), and notebook support for rows that carry separate DNA, transcript, and protein sequences. The Overleaf section "Next Step: Multiple Encoders per Modality and Published Benchmarks" holds the plan.

| Setting | Dataset | How DNA enters | Published comparison |
| --- | --- | --- | --- |
| A: derived modalities | CodonBERT mRNA stability (the current CSV) | A DNA encoder reads the coding sequence in DNA letters, an RNA encoder reads it in RNA letters, and a protein encoder reads its translation. This is the Stage 1 setup. | [BioLangFusion](Papers/BioLangFusion.pdf), Table 1: best fusion Spearman 0.563 versus 0.553 for the best single encoder. |
| B: distinct modalities | [IsoFormer GTEx transcript expression](https://huggingface.co/datasets/InstaDeepAI/multi_omics_transcript_expression) | Genomic DNA centered on the transcription start site, alongside the full transcript and the protein. | [IsoFormer](Papers/Multi-Modal-Transfer-Learning.pdf), Table 2: three modalities reach R² 0.43 versus 0.36 for RNA alone. |

In Setting A all three inputs derive from one coding sequence, so differences between encoders come from pretraining corpora and tokenization rather than new biological information. The stability CSV has no gene or transcript identifiers, so genomic context around each gene is not available without a separate mapping step. Setting B supplies DNA that carries promoter and regulatory context absent from the protein.

The eight encoders include BioLangFusion's three, Nucleotide Transformer v2 100M multi-species, RNA-FM, and ESM-2 8M, and IsoFormer's protein encoder, ESM-2 150M. Nucleotide Transformer v2 and DNABERT-2 load custom model code written for `transformers` 4; the encoder registry, [encoders.py](Code/mbf/encoders.py), applies the small compatibility adjustments they need under `transformers` 5 and pins both to a fixed checkpoint revision. Trained fusion architectures, including BioLangFusion's fusion heads and IsoFormer's cross-attention, need token-level embeddings and belong to the fusion stage.

## Data

The input datasets are included in `Code/`:

- [mRFP_Expression.csv](Code/mRFP_Expression.csv): 1,459 rows containing 1,455 distinct sequence strings, from synonymous codon randomization of one gene.
- [mRNA_Stability.csv](Code/mRNA_Stability.csv): 65,356 rows containing 29,949 distinct sequence strings.

These counts describe the included CSVs before notebook filtering or subsampling.

The dataset audit in [Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb) records the following properties of `mRNA_Stability.csv`, which matter for comparisons with published results:

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
| `Code/stage1_embeddings/<dataset>_n<rows>_seed<seed>/` | `Stage1_analysis.ipynb` | One embedding matrix per encoder for one dataset sample, saved with its checkpoint, revision, token limit, and a fingerprint of the ordered input sequences. The notebook reuses a matrix only when all of these match. | Local and ignored; delete an encoder's file to recompute it. |

## Setup

### Notebook dependencies

Use your existing Python environment for the project. Install PyTorch using the [official installation selector](https://pytorch.org/get-started/locally/) for your operating system and CPU or CUDA configuration. Install the remaining notebook dependencies in that environment:

```sh
python -m pip install numpy pandas scipy scikit-learn umap-learn matplotlib "transformers==5.15.1" multimolecule einops ipykernel
```

Open notebooks with VS Code's Python and Jupyter extensions and [select the environment containing these packages as the kernel](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management). Use `Code/` as the kernel's working directory because the notebooks use relative CSV and output paths.

[Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb) uses a CUDA GPU when available, then an Apple Silicon GPU through PyTorch's MPS backend, and otherwise the CPU. `multimolecule` provides RNA-FM and mRNA-FM. Version 0.2.1 imports with `transformers` 5.14.1 and 5.15.1 but not 5.16 or later, which is why `transformers` is pinned. If `import multimolecule` fails in an Anaconda environment with an older `datasets` or `huggingface_hub`, upgrade `datasets` and `fsspec` and reinstall `huggingface_hub`.

The first run of [Stage1_analysis.ipynb](Code/Stage1_analysis.ipynb) downloads the eight encoders' checkpoints, about 5 GB in total, unless they are already cached; [encoders.py](Code/mbf/encoders.py) lists their Hugging Face identifiers. DNABERT-2's model code requires `einops`. Hugging Face normally stores these downloads in the [user's cache](https://huggingface.co/docs/transformers/installation#cache-directory); the notebooks do not configure the repository's `.model-cache/` directory.

This dependency list covers the imports in the Stage 1 notebook and the `mbf` package. A fresh-environment run has not been verified. The repository does not yet pin package versions, and only Nucleotide Transformer v2 and DNABERT-2 have pinned model revisions.

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
