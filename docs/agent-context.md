# Research context for agents

Use this page to locate the research material and questions relevant to a task. The [project README](../README.md) owns the project overview and repository map; the [documentation index](README.md) provides a reading route. Working instructions are in [AGENTS.md](../AGENTS.md). [Selected sources](sources.md) retains useful readings and explains what was consulted and why; it complements the papers and contributor reviews.

## Notebook-study context

Chase's current study focus is understanding the Stage 1 pipeline, its results, and its relationship to the literature. This individual learning focus does not define the scope or sequence of the whole project; the [project background](../README.md#project-background) describes the broader research aim. [Stage1_refactor.ipynb](../Code/Stage1_refactor.ipynb) contains the developing explanation of that pipeline. [Stage1.ipynb](../Code/Stage1.ipynb) is the original notebook named in the project overview. These are distinct artifacts; associate a result with the notebook and version that produced it.

The refactor's introduction describes three questions: what simple predictive models can recover from frozen embeddings, how the two representation spaces organize the same examples, and how a selected nucleotide attention summary relates to candidate sequence patterns. It also describes the protein input as a translation of the nucleotide input. This constructed relationship matters when interpreting the two representations.

## Evidence and unresolved questions

Use the following questions to identify what a task needs to establish, rather than assuming that the documentation has settled them.

- **Dataset meaning:** What does `Value` in [mRNA_Stability.csv](../Code/mRNA_Stability.csv) represent, how was it obtained, and which biological sequence regions are included? The [dataset overview](../README.md#data) identifies the reported source; the CSV header alone does not establish the assay or label interpretation.
- **Evaluation:** Which rows are retained, how are training and test examples selected, and what generalization claim does that split support? Check the producing code and settings rather than inferring the split from a dataset column.
- **Result provenance:** Which data, notebook, model revisions, settings, and saved outputs support a reported result? If notebook prose, outputs, reviews, or slides disagree, identify the versions involved and retain the disagreement until it is resolved.
- **Meaning of alignment:** Distinguish biological sequence correspondence, similarity of representation spaces, and combining representations for prediction. Julian's [alignment review](../Reviews/Julian/Alignment_Theory_Paper_Review.md) and [BioLangFusion review](../Reviews/Julian/BioLangFusion.md) are starting points for reading the [source papers](../Papers/).
- **Further experiments:** What comparison would distinguish the proposed explanation from alternatives? The [meeting slides](../Notes/Mina_Meeting_Slides_2026-09-23.pptx), especially slides 3 and 6, record the contribution and architecture candidates. The [architecture priorities](../README.md#architecture-priorities) reflect the meeting's decision to prioritize Coupled Mamba. Distinguish literature ideas, meeting preferences, and implemented methods. The refactor's exploratory findings alone do not select a fusion method.

## Shared context across sessions

GitHub shares the files and versions contributed to the repository. The shared source index and linked explanations preserve selected learning and evidence across contributors' sessions; private agent memory is not their maintained owner. Separate AI conversations are not part of that shared record unless their relevant content is explicitly recorded here. Carry forward consequential decisions with their rationale, source links, and unresolved qualifications; avoid requiring collaborators to reconstruct an entire chat.

This page holds research context rather than the status of every active task. Keep assignments, pending reviews, and next actions in the relevant task conversation or an explicitly maintained task record. Update this page when the research focus or shared assumptions change.

Context checked against the repository on September 25, 2026. These source pointers do not certify the scientific interpretations.
