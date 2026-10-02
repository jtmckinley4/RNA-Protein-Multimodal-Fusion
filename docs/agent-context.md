# Research context for agents

Use this page to locate the research material and questions relevant to a task. The [project README](../README.md) owns the project overview and repository map; the [documentation index](README.md) provides a reading route. Working instructions are in [AGENTS.md](../AGENTS.md). [Selected sources](sources.md) retains useful readings and explains what was consulted and why; it complements the papers and contributor reviews.

## Notebook-study context

Chase's current study focus is understanding the Stage 1 pipeline, its results, and its relationship to the literature. This individual learning focus does not define the scope or sequence of the whole project; the [project background](../README.md#project-background) describes the broader research aim. [Stage1_analysis.ipynb](../Code/Stage1_analysis.ipynb) contains the explanation of that pipeline, using the functions in the [mbf package](../Code/mbf/). Associate a result with the notebook version and settings that produced it.

The saved run uses eight frozen encoders, two or three per modality: three DNA encoders read each coding sequence in DNA letters, RNA-FM and mRNA-FM read it in RNA letters, and three ESM-2 models read its translation. The notebook's introduction describes three questions: what simple predictive models can recover from frozen embeddings, how the representation spaces of every encoder pair organize the same examples, and how a selected attention summary of the nucleotide encoders relates to candidate sequence patterns. All three inputs are derived from one sequence, and this constructed relationship matters when interpreting the representations.

## Project scope: DNA and multiple encoders

Mina Basirat set the longer-term goal of fusing several pretrained encoders, with more than one model per modality across DNA, RNA, and protein. Stage1_analysis.ipynb covers DNA, RNA, and protein with two or three encoders per modality. The remaining Stage 1 work, described in the [next steps](../README.md#next-steps-published-benchmarks-and-distinct-modalities), compares against BioLangFusion on the CodonBERT stability data, where all three modality inputs derive from one coding sequence, and against IsoFormer on its GTEx transcript-expression data, where genomic DNA is a distinct input. The Overleaf project "multimodal-bio-fusion" holds the Stage 1 record and this plan. These comparisons are plans, not implemented methods.

## Evidence and unresolved questions

Use the following questions to identify what a task needs to establish, rather than assuming that the documentation has settled them.

- **Dataset version:** Is [mRNA_Stability.csv](../Code/mRNA_Stability.csv) the same version BioLangFusion used? Its 65,356 rows and 29,949 distinct sequences differ from the paper's 41,123 raw and 23,929 used sequences, and the supplied `Split` places 5,392 distinct test sequences in training as well. See the [dataset audit](../README.md#data) and the dataset audit section of Stage1_analysis.ipynb.
- **Modality definition:** When every modality input derives from one coding sequence, what does a difference between DNA, RNA, and protein encoders measure? Compare with a dataset where DNA is a distinct input before generalizing.
- **Dataset meaning:** What does `Value` in [mRNA_Stability.csv](../Code/mRNA_Stability.csv) represent, how was it obtained, and which biological sequence regions are included? The [dataset overview](../README.md#data) identifies the reported source; the CSV header alone does not establish the assay or label interpretation.
- **Evaluation:** Which rows are retained, how are training and test examples selected, and what generalization claim does that split support? Check the producing code and settings rather than inferring the split from a dataset column.
- **Result provenance:** Which data, notebook, model revisions, settings, and saved outputs support a reported result? If notebook prose, outputs, reviews, or slides disagree, identify the versions involved and retain the disagreement until it is resolved.
- **Meaning of alignment:** Distinguish biological sequence correspondence, similarity of representation spaces, and combining representations for prediction. Stage 1's composition control shows that most measured agreement involving the frozen nucleotide embeddings is reproduced by sequence composition alone, while agreement among the protein encoders largely survives it. Julian's [alignment review](../Notes/Reviews/Julian/Alignment_Theory_Paper_Review.md) and [BioLangFusion review](../Notes/Reviews/Julian/BioLangFusion.md) are starting points for reading the [source papers](../Papers/).
- **Further experiments:** What comparison would distinguish the proposed explanation from alternatives? The [meeting slides](../Notes/Mina_Meeting_Slides_2026-09-23.pptx), especially slides 3 and 6, record the contribution and architecture candidates. The [architecture priorities](../README.md#architecture-priorities) reflect the meeting's decision to prioritize Coupled Mamba. Distinguish literature ideas, meeting preferences, and implemented methods. The Stage 1 notebook's exploratory findings alone do not select a fusion method.

## Shared context across sessions

GitHub shares the files and versions contributed to the repository. The shared source index and linked explanations preserve selected learning and evidence across contributors' sessions; private agent memory is not their maintained owner. Separate AI conversations are not part of that shared record unless their relevant content is explicitly recorded here. Carry forward consequential decisions with their rationale, source links, and unresolved qualifications; avoid requiring collaborators to reconstruct an entire chat.

This page holds research context rather than the status of every active task. Keep assignments, pending reviews, and next actions in the relevant task conversation or an explicitly maintained task record. Update this page when the research focus or shared assumptions change.

Context checked against the repository on October 2, 2026. These source pointers do not certify the scientific interpretations.
