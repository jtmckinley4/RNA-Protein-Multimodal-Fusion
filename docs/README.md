# Research documentation

This directory brings together the team's maintained research plans, bibliography, and explanations connecting biological questions, analyses, and evidence behind the Multimodal Biology analyses of DNA, RNA, and protein foundation models. It supports code development, experiment planning, and manuscript writing in the [Multimodal Biology Overleaf project](https://www.overleaf.com/project/6ab8535fb63c8540bed7e56f).

## Find relevant material

Use the following starting points to connect a research question to the analysis and its evidence.

| Question | Starting point |
| --- | --- |
| What are we proposing to investigate? | The [Research Canvas](Research_Canvas.pptx). |
| What is the project schedule? | The [Gantt presentation](Research_Project_Plan_Gantt.pptx) and [editable Gantt workbook](Research_Project_Plan_Gantt.xlsx). |
| Where is the annotated bibliography? | The [team bibliography](Annotated_Bibliography.docx). |
| What biological question motivates the analysis? | The [project overview](../README.md) and the introduction to [Stage1_refactor.ipynb](../Code/Stage1_refactor.ipynb). |
| What do the sequences and labels represent? | The [dataset overview](../README.md#data), [mRNA stability data](../Code/mRNA_Stability.csv), and the notebook's loading and preprocessing sections. Check what a row and its label mean, how the label was obtained, and which examples enter the analysis. |
| Where are the Stage 1 methods, metric definitions, and results written up? | The [Multimodal Biology Overleaf project](https://www.overleaf.com/project/6ab8535fb63c8540bed7e56f), which records what each Stage 1 metric measures and how each number was obtained. |
| What did Stage 1 find? | The [Stage 1 results](../README.md#stage-1-results) summary in the project README, and the result notes after each output in [Stage1_refactor.ipynb](../Code/Stage1_refactor.ipynb). |
| How will additional encoders and published benchmarks be compared? | The [next steps](../README.md#next-steps-multiple-encoders-and-published-benchmarks) in the project README and the corresponding section of the Overleaf project. |
| Which readings are worth returning to? | [Selected sources and readings](sources.md), with reasons to retain them and the scope of what was read. |
| Why use this method? | Julian's [BioLangFusion review](../Notes/Reviews/Julian/BioLangFusion.md) and [alignment paper review](../Notes/Reviews/Julian/Alignment_Theory_Paper_Review.md), read alongside the corresponding [papers](../Papers/). |
| How is the method implemented? | The relevant sections of [Stage1_refactor.ipynb](../Code/Stage1_refactor.ipynb) and [Stage1.ipynb](../Code/Stage1.ipynb). Identify the notebook and version associated with the result being discussed. |
| What does the result establish? | Its producing notebook cells, outputs, baselines, evaluation split, and interpretation. Check whether the evidence supports the claim and retain unresolved discrepancies between versions. |

Start with the biological question and dataset meaning, then follow the method into its implementation and interpretation. The notebook and paper reviews provide the initial route while the supporting biological and methodological explanations develop.
