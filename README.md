# RNA-Protein-Multimodal-Fusion

A research project in the [Complex Adaptive Systems Laboratory](https://complexity.cecs.ucf.edu/directors-welcome/) at the University of Central Florida, studying how to choose and combine pretrained biological foundation models.

## Project background

The aim is to develop methods for choosing which biological modalities and pretrained models to combine, and for deciding when and how fusion is useful for a target task. Those choices should be grounded in the biological question and the wet-lab work the predictions could inform. The [meeting slides](Notes/Mina_Meeting_Slides_2026-09-23.pptx), particularly slide 3, frame the contribution as a method for deciding whether and how to fuse.

The current investigation uses frozen Nucleotide Transformer and ESM-2 encoders to study nucleotide and translated protein representations, beginning with mRNA stability prediction and a synonymous-recoding control. Frozen means that the encoder weights are not updated during these analyses. This is an initial case study within the broader methodology; the choice of future tasks, model combinations, and evaluation criteria remains part of the research.

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
| [docs/](docs/README.md) | Shared explanations and reading routes connecting biology, methods, and evidence to the notebook. |
| [Reviews/](Reviews/) | Individual paper reviews and interpretations, organized by contributor. |
| [Notes/](Notes/) | Meeting notes, project planning, and slide decks. |
| [Papers/](Papers/) | Reference papers informing the research. |

Keep individual paper notes in contributor folders, such as [Reviews/Julian/](Reviews/Julian/) and `Reviews/Chase/`, so interpretations remain attributable. Obsidian supports personal study; explanations needed to understand the project belong in the shared documentation.

Agents working in this repository should start with [AGENTS.md](AGENTS.md).

## Stage 1 analysis

[Stage1.ipynb](Code/Stage1.ipynb) contains the original representation analysis. [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) is a developing refactor with expanded explanations. Keep results associated with the notebook and version that produced them.

The notebooks contain analyses that:

1. Check sequence length and start codons, translate nucleotide sequences, and generate paired embeddings.
2. Probe prediction from each representation separately and from concatenated embeddings, with sequence-feature controls.
3. Compare representation geometry using linear CKA and additional neighborhood, correlation, and retrieval diagnostics; visualize embeddings with UMAP.
4. Examine the mRFP expression dataset as a synonymous-recoding control.
5. Explore nucleotide attention, candidate sequence patterns, and relationships between representation similarity and prediction error.

The concatenated-embedding probe uses a linear model, distinct from the concatenation + MLP reference baseline. These analyses can inform experiment design; their outputs alone do not establish which fusion method to use or validate a wet-lab application.

## Data

The input datasets are included in `Code/`:

- [mRFP_Expression.csv](Code/mRFP_Expression.csv): 1,459 rows containing 1,455 distinct sequence strings, from synonymous codon randomization of one gene.
- [mRNA_Stability.csv](Code/mRNA_Stability.csv): 65,356 rows containing 29,949 distinct sequence strings.

These counts describe the included CSVs before notebook filtering or subsampling. The CSVs were sourced from the fine-tuning benchmark data in [Sanofi-Public/CodonBERT](https://github.com/Sanofi-Public/CodonBERT/tree/master/benchmarks/CodonBERT/data/fine-tune). Their inclusion supplies the notebook inputs; interpreting a prediction still requires checking the source assay, labels, and retained sequence regions.

## Generated files

Keep routine model caches and regenerable intermediate outputs local and ignore their specific paths. Retain source datasets and notebooks in Git. Share selected results deliberately, with the producing notebook or code version, input identities, model revisions, and relevant settings so that others can interpret them. Avoid blanket ignore rules for scientific file formats.

When code adds or changes an output, update this inventory and its handling. Add or adjust specific paths in [.gitignore](.gitignore) for outputs kept local. Preserve an identified copy of any result needed as evidence before rerunning code that overwrites it. Paths below assume the working directory specified in Setup.

| Generated file | Producer | Purpose | Handling |
| --- | --- | --- | --- |
| `Code/stage1_main_embeddings.npz` | `Stage1.ipynb` and `Stage1_refactor.ipynb` | Snapshot of RNA embeddings, protein embeddings, and labels; subsequent analyses use the in-memory arrays. | Local and ignored; either notebook overwrites the same path. |

## Setup

### Notebook dependencies

Use your existing Python environment for the project. Install PyTorch using the [official installation selector](https://pytorch.org/get-started/locally/) for your operating system and CPU or CUDA configuration. Install the remaining notebook dependencies in that environment:

```sh
python -m pip install numpy pandas scipy scikit-learn umap-learn matplotlib biopython transformers ipykernel
```

Open notebooks with VS Code's Python and Jupyter extensions and [select the environment containing these packages as the kernel](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management). Use `Code/` as the kernel's working directory because the notebooks use relative CSV and output paths.

The notebooks use CUDA when available and otherwise run on CPU. The first run downloads `InstaDeepAI/nucleotide-transformer-500m-human-ref` and `facebook/esm2_t12_35M_UR50D`, unless they are already cached. Hugging Face normally stores these downloads in the [user's cache](https://huggingface.co/docs/transformers/installation#cache-directory); the notebooks do not configure the repository's `.model-cache/` directory.

This dependency list covers the imports in both notebooks. A fresh-environment run has not been verified, and the repository does not yet pin package versions or model revisions for reproducibility.

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
