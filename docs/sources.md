# Selected sources and readings

Use these readings to revisit useful explanations, evidence, and guidance for the project. The [core papers](../Papers/) and [individual reviews](../Reviews/) remain the starting points for the project's biological literature. Add useful research readings here as they arise; group them by the question they help answer.

A citation that already serves a specific claim can stay in its owning page. This index gives reusable readings a route beyond that single use. Selection and annotation guidance lives in the [shared-documentation workflow](../.agents/skills/rna-fusion-shared-documentation/SKILL.md).

## Writing for different reader needs

### Diataxis: Start here

[Diataxis in five minutes](https://diataxis.fr/start-here/), by Daniele Procida, distinguishes tutorials, how-to guides, reference, and explanation.

**Why retain it:** It helps decide whether a page should teach a concept, answer a lookup question, or guide an action. It informed the separation of README navigation from fuller explanations in the shared workflow.

**Reading scope and limits:** The introductory page was read. It offers a way to choose a document's purpose; it does not mandate this repository's folders, Markdown formatting, or scientific conclusions.

## Mathematics in notebook Markdown

### Jupyter and MathJax: LaTeX syntax and delimiters

[Jupyter Notebook 7.0.2: Markdown cells, LaTeX equations](https://jupyter-notebook.readthedocs.io/en/v7.0.2/examples/Notebook/Working%20With%20Markdown%20Cells.html#latex-equations) describes mathematical expressions in Markdown cells, including single-dollar inline syntax. [MathJax 4.0: TeX and LaTeX math delimiters](https://docs.mathjax.org/en/latest/input/tex/delimiters.html) describes double-dollar display delimiters and the configuration dependence of single-dollar inline delimiters.

**Why retain them:** They explain the distinction between mathematical syntax and the delimiters used by a viewer. They support the syntax discussion in the [notebook presentation reference](../.agents/skills/rna-fusion-markdown-formatting/references/notebooks.md). The choice to retain `$...$` inline and separate-line `$$` blocks follows the notebook's existing source and Chase's requested convention. The heading definitions, notation/interpretation sequence, and cell-placement rules were developed through project feedback; the vendor documentation does not establish those editorial choices.

**Reading scope and limits:** Jupyter's LaTeX-equations section and MathJax's delimiter page were read on September 25, 2026. Jupyter documents a configured application; single-dollar inline math is not a default of standalone MathJax. These references establish syntax capabilities, not identical rendering in every editor or proof that this checkout was visually tested. The remote pages were not archived.

## Working with repository-aware agents

### Claude Code: Repository instructions and memory

[How Claude remembers your project](https://code.claude.com/docs/en/memory), especially [file loading](https://code.claude.com/docs/en/memory#how-claude-md-files-load) and [sharing one instruction file](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools).

**Why retain it:** It explains startup and nested instruction loading, imports, and the distinction between project instructions and local auto memory. The import mechanism supports this repository's [CLAUDE.md](../CLAUDE.md), which loads [AGENTS.md](../AGENTS.md).

**Reading scope and limits:** The relevant loading, AGENTS.md, import, and memory sections were read. Direct AGENTS.md discovery depends on version and configuration; the explicit import avoids relying on that fallback. Windows symlink limitations also informed the choice of an ordinary file. Instructions guide behavior rather than enforce permissions.

### Claude Code: Skills and name conflicts

[Extend Claude with skills](https://code.claude.com/docs/en/skills), especially [skill locations](https://code.claude.com/docs/en/skills#choose-where-skills-load) and [same-name resolution](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name).

**Why retain it:** It documents project skills under `.claude/skills/`, selection through descriptions, explicit invocation, and supporting-file links. It informed the small [Claude entry point](../.claude/skills/rna-fusion-shared-documentation/SKILL.md) that reads the maintained repository workflow.

**Reading scope and limits:** Discovery, naming, invocation, and supporting-file sections were read. A personal skill can take precedence over a project skill with the same name, which motivates the distinctive project name and explicit path. The two-entry-point arrangement is this project's design, not a vendor-provided integration recipe.

### Claude Code: Repository access and the Desktop Code surface

[How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works#what-claude-can-access) and [Desktop shared configuration](https://code.claude.com/docs/en/desktop#shared-configuration).

**Why retain them:** They distinguish the model from the application that can search and read the checkout. They help a collaborator determine whether their Claude session can use the repository instructions and skills.

**Reading scope and limits:** Repository-access and shared-configuration sections were read. The Desktop Code surface shares configuration with the CLI; this does not establish equivalent discovery in an ordinary Claude chat.

### Codex: Repository instructions

[Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), especially instruction discovery and project instructions.

**Why retain it:** It explains how global and repository guidance is assembled. It supports using the root AGENTS.md as the shared starting point while keeping this project's writing conventions explicitly scoped.

**Reading scope and limits:** Discovery and project-layering sections were read. This is Codex behavior, not a universal precedence rule for every agent application.

### Codex: Repository skills

[Build skills](https://learn.chatgpt.com/docs/build-skills), especially local skill locations and invocation.

**Why retain it:** It documents `.agents/skills/` discovery and loading the full skill only when relevant. It informed the location of the [maintained workflow](../.agents/skills/rna-fusion-shared-documentation/SKILL.md).

**Reading scope and limits:** Discovery, invocation, and local locations were read. Same-named skills are not merged, so a personal installation should not be assumed to replace or reproduce the repository workflow.

## Checking a teammate's setup

In a fresh session opened on this checkout, ask the agent to identify the repository instructions and the source path of the skill relevant to the task: shared documentation or Markdown formatting. In Claude Code, `/context` lists loaded memory files; `/rna-fusion-shared-documentation` and `/rna-fusion-markdown-formatting` explicitly invoke their respective entry points. If discovery differs, either workflow can still be read through its repository path when the application has file access.

Web sections above were checked on September 25, 2026; the remote pages were not archived. File and link checks can validate this repository's structure. Actual skill discovery and behavior must also be checked in the teammate's application.
