# Multimodal Biology

A research project in the [Complex Adaptive Systems Laboratory](https://complexity.cecs.ucf.edu/directors-welcome/) at the University of Central Florida, studying how to choose and combine pretrained DNA, RNA, and protein foundation models. The team's manuscript is the Overleaf project [Multimodal Biology](https://www.overleaf.com/project/6ab8535fb63c8540bed7e56f), which records the Stage 1 methods, metric definitions, and results.

## Project background

The aim is to develop methods for choosing which biological modalities and pretrained models to combine, and for deciding when and how fusion is useful for a target task. The longer-term goal set with Mina Basirat is to fuse several pretrained encoders, with more than one model per modality (for example, several DNA, RNA, and protein models), and to compare those combinations. Those choices should be grounded in the biological question and the wet-lab work the predictions could inform. The [meeting slides](Notes/Mina_Meeting_Slides_2026-09-23.pptx), particularly slide 3, frame the contribution as a method for deciding whether and how to fuse.

The current investigation uses frozen Nucleotide Transformer and ESM-2 encoders to study nucleotide and translated protein representations, beginning with mRNA stability prediction and a synonymous-recoding control. Frozen means that the encoder weights are not updated during these analyses. The Nucleotide Transformer checkpoint used so far (`nucleotide-transformer-500m-human-ref`) was pretrained on the human reference genome, so it is a DNA language model reading the coding sequence in DNA letters; Stage 1 has therefore compared a DNA-model representation with a protein-model representation. The notebooks' `rna_*` variable names refer to this nucleotide branch. This is an initial case study within the broader methodology; the choice of future tasks, model combinations, and evaluation criteria remains part of the research.

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

[Stage1.ipynb](Code/Stage1.ipynb) contains the original representation analysis. [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) is a developing refactor with expanded explanations. The refactor's final section, Multi-encoder extension, repeats the analysis on the same sample for several DNA, RNA, and protein encoders; that section has not yet been run with the real checkpoints. Keep results associated with the notebook and version that produced them.

The notebooks contain analyses that:

1. Check sequence length and start codons, translate nucleotide sequences, and generate paired embeddings.
2. Probe prediction from each representation separately and from concatenated embeddings, with sequence-feature controls.
3. Compare representation geometry using linear CKA and additional neighborhood, correlation, and retrieval diagnostics; visualize embeddings with UMAP.
4. Examine the mRFP expression dataset as a synonymous-recoding control.
5. Explore nucleotide attention, candidate sequence patterns, and relationships between representation similarity and prediction error.

The concatenated-embedding probe uses a linear model, distinct from the concatenation + MLP reference baseline. These analyses can inform experiment design; their outputs alone do not establish which fusion method to use or validate a wet-lab application.

### Planned extension: DNA and multiple encoders

The next Stage 1 work adds the DNA modality and more than one encoder per modality, and compares against published fusion studies on their own datasets to define what alignment means. The Overleaf section "Stage 1 Extension: Benchmarks and the DNA Modality" holds the full plan; nothing in it has been run yet.

| Setting | Dataset | How DNA enters | Published comparison |
| --- | --- | --- | --- |
| A: derived modalities | CodonBERT mRNA stability (the current CSV) | A DNA encoder reads the coding sequence in DNA letters, an RNA encoder reads it in RNA letters, and a protein encoder reads its translation. | [BioLangFusion](Papers/BioLangFusion.pdf), Table 1: best fusion Spearman 0.563 versus 0.553 for the best single encoder. |
| B: distinct modalities | [IsoFormer GTEx transcript expression](https://huggingface.co/datasets/InstaDeepAI/multi_omics_transcript_expression) | Genomic DNA centered on the transcription start site, alongside the full transcript and the protein. | [IsoFormer](Papers/Multi-Modal-Transfer-Learning.pdf), Table 2: three modalities reach R² 0.43 versus 0.36 for RNA alone. |

In Setting A all three inputs derive from one coding sequence, so differences between encoders come from pretraining corpora and tokenization rather than new biological information. The stability CSV has no gene or transcript identifiers, so genomic context around each gene is not available without a separate mapping step. Setting B supplies DNA that carries promoter and regulatory context absent from the protein.

The Multi-encoder extension section of [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) implements Setting A. It embeds every sequence with each encoder, then computes decodability probes per encoder; CKA, mutual k-NN, RSA with a permutation test, and held-out CCA with retrieval for every encoder pair, including pairs within one modality; the same comparisons after regressing out sequence composition; and synergy for pairs and triples. Candidate encoders are Nucleotide Transformer (500M human-ref and v2 100M multi-species) and DNABERT-2 for DNA; RNA-FM, an mRNA-trained model such as CodonBERT, and Nucleotide Transformer as an RNA encoder; and ESM-2 at 8M, 35M, and 150M for protein. Starred entries in the Overleaf plan's encoder table match the checkpoints used by BioLangFusion and IsoFormer.

## Data

The input datasets are included in `Code/`:

- [mRFP_Expression.csv](Code/mRFP_Expression.csv): 1,459 rows containing 1,455 distinct sequence strings, from synonymous codon randomization of one gene.
- [mRNA_Stability.csv](Code/mRNA_Stability.csv): 65,356 rows containing 29,949 distinct sequence strings.

These counts describe the included CSVs before notebook filtering or subsampling.

An audit of `mRNA_Stability.csv` on September 29, 2026 recorded the following properties, which matter for comparisons with published results:

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
| `Code/stage1_multi_encoder_cache/*.npz` | `Stage1_refactor.ipynb`, Multi-encoder extension | Per-encoder embeddings of the main sample and the mRFP control for encoders other than the two Stage 1 encoders; file names include a hash of the inputs, checkpoint, and token limit. | Local and ignored; delete to force re-embedding. |
| `Code/stage1_multi_encoder_results/` | `Stage1_refactor.ipynb`, Multi-encoder extension | Small CSV tables (encoder status, probes, pairwise alignment with and without composition control, synergy, control spread) and `run_info.json` with package versions and device. | Not ignored; commit a run's folder deliberately when its results are reported. |
| `Code/stage1_main_embeddings.npz` | `Stage1.ipynb` and `Stage1_refactor.ipynb` | Snapshot of nucleotide (DNA-model) embeddings, stored under the key `rna`, protein embeddings, and labels; subsequent analyses use the in-memory arrays. | Local and ignored; either notebook overwrites the same path. |

## Setup

### Notebook dependencies

Use your existing Python environment for the project. Install PyTorch using the [official installation selector](https://pytorch.org/get-started/locally/) for your operating system and CPU or CUDA configuration. Install the remaining notebook dependencies in that environment:

```sh
python -m pip install numpy pandas scipy scikit-learn umap-learn matplotlib biopython transformers ipykernel
```

Open notebooks with VS Code's Python and Jupyter extensions and [select the environment containing these packages as the kernel](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management). Use `Code/` as the kernel's working directory because the notebooks use relative CSV and output paths.

The notebooks use CUDA when available and otherwise run on CPU. The first run downloads `InstaDeepAI/nucleotide-transformer-500m-human-ref` and `facebook/esm2_t12_35M_UR50D`, unless they are already cached. Hugging Face normally stores these downloads in the [user's cache](https://huggingface.co/docs/transformers/installation#cache-directory); the notebooks do not configure the repository's `.model-cache/` directory.

The Multi-encoder extension section of [Stage1_refactor.ipynb](Code/Stage1_refactor.ipynb) also needs `multimolecule` for the RNA encoders and `einops` for DNABERT-2. `multimolecule` 0.2.1 imports with `transformers` 5.14.1 and 5.15.1 but not 5.16 or later, so install `python -m pip install "transformers==5.15.1" multimolecule einops` before running that section. Its encoders are downloaded from Hugging Face on first use; a checkpoint that fails to load is recorded in the section's status table and skipped.

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
