# 1. Paper Information

**Title:** Central Dogma Transformer
**Authors:** Ota (independent researcher)
**Year / Venue:** Preprint (arXiv 2601.01089)
**Paper Type:** Model
**Biological Domain:** Gene regulation (enhancer–gene effect prediction, CRISPRi)
**Primary Sequence Representation(s):** Mixed (DNA, RNA gene-level, protein), all as frozen pre-computed embeddings, not raw tokens

**One-sentence summary:** CDT enforces one-directional DNA→RNA→protein cross-attention over frozen foundation-model embeddings, mirroring transcription/translation so attention weights are directly interpretable as regulatory hypotheses, validated by a CTCF/Hi-C case study.

# 2. Problem and Motivation

The paper addresses how to combine DNA, RNA, and protein information for gene-regulation prediction while keeping the model's internal computation interpretable as biological causality, not just accurate. It explicitly uses three representations: DNA (Enformer embeddings over a 114 kb window), RNA (scGPT gene-token embeddings), and protein (ESM-C/ProteomeLM embeddings) (Table, Sec. "Frozen foundation models").

# 3. Input Representation and Tokenization

CDT does not tokenize raw sequence itself; it consumes pre-computed frozen embeddings: Enformer gives DNA embeddings over 896 positional bins spanning a 114 kb window (128 bp/bin), 3072-dim; scGPT gives 512-dim gene-level embeddings via vocabulary lookup; ESM-C/ProteomeLM give 768-dim protein embeddings. Reading-frame/strand handling: Not specified — CDT centers DNA windows on the enhancer rather than the TSS. No special tokens or boundary markers are described; modality identity is structural (dedicated encoder per stream).

**Mixed-representation handling.** The three modalities are processed by separate frozen encoders, never converted into a shared vocabulary. They are connected only through learned cross-attention layers after self-attention, not through positional resampling: DNA keeps 896 positions, RNA/protein keep per-gene/per-protein token counts, and cross-attention directly relates differently-shaped representations via query/key/value projections rather than forcing a shared length.

# 4. Model Architecture

**Backbone:** Transformer self-attention + directional cross-attention over frozen embeddings (~60M trainable parameters on top of ~712M frozen).
**Representation-specific components:** separate encoders per modality; one-directional cross-attention (not bidirectional/symmetric); a "Virtual Cell Embedder" (VCE) fusion/pooling layer; no shared latent space or type embeddings — direction of information flow substitutes for them.

Each modality first passes self-attention (DNA: 2 layers/896 bins; RNA/protein: 1 layer each). Cross-attention is strictly directional:

$$\text{DNA}\to\text{RNA}:\ Q=\text{genes},\ K,V=\text{DNA positions}\ \Rightarrow\ \text{attn}\in\mathbb{R}^{n_{genes}\times 896}$$
$$\text{RNA}\to\text{Protein}:\ Q=\text{proteins},\ K,V=\text{RNA}_{fused}\ \Rightarrow\ \text{attn}\in\mathbb{R}^{n_{proteins}\times n_{genes}}$$

so protein-layer attention indirectly carries DNA context. A learned query per modality attention-pools each cross-informed representation into a 768-dim summary; the three summaries (2304-dim) are concatenated and passed through a small feed-forward network (GELU) to produce the Virtual Cell Embedding, fed to an MLP head predicting a scalar effect size (Huber loss).

Flow: $x_{DNA}\to E_{DNA}\to$ self-attn $\to$ DNA$\to$RNA cross-attn $\to$ RNA$_{fused}\to$ RNA$\to$Protein cross-attn $\to$ Protein$_{fused}\to$ VCE pooling $\to$ concat $\to$ FFN $\to$ effect-size head.

# 5. Training Strategy

Objective: Huber-loss regression on CRISPRi enhancer effect sizes; no masked-language-modeling or generative pretraining — CDT trains only its ~60M parameters (projections, self/cross-attention, VCE, task head) on top of frozen foundation-model embeddings, computed once and cached. Training is single-task, single-stage (not multi-task or alternating). Data: Gasperini et al. K562 CRISPRi screen, 4,605 training / 996 validation enhancer–gene pairs, split at the enhancer level (Sec. "Task and data").

# 6. Evaluation and Main Findings

Main result: Pearson $r=0.503$ predicting CRISPRi effect sizes on held-out pairs; an independent K562 replicate (STING-seq) correlates with Gasperini's at only $r=0.797$, a ceiling CDT reaches ~63% of. Key qualitative finding: a case study on the FNDC5 enhancer–gene pair (726 kb apart) where gradient analysis (not attention) identified a CTCF site as most prediction-critical, independently confirmed by Hi-C contact data as a physical loop anchor — attention and gradient top-20 positions overlapped only ~10% across 100 samples, showing the two methods answer different questions.

# 7. Architectural Strengths and Limitations

**Strengths**
- Directional cross-attention gives every attention weight one unambiguous interpretation by construction.
- Cheap to train (~60M trainable params) by freezing large foundation models and caching embeddings.
- Case study shows sequence-only training recovers 3D chromatin-contact structure never explicitly supervised.

**Limitations**
- Static, non-cell-specific RNA/protein tokens (v1) make cross-modal attention nearly uniform across samples (correlation >0.99), limiting cell-state specificity.
- 114 kb DNA window can miss one anchor of a chromatin loop pair, as in the FNDC5 case.
- Single cell line/dataset with a visible train/validation gap; generalization unproven.

# 8. Relevance to OIL and Our Research

**Direct relevance:** Low–Medium. CDT never operates on raw nucleotide/codon tokens — it fuses pre-computed embeddings at gene/region granularity — so its tokenization choices don't transfer, but its directional-fusion principle is architecturally relevant.

**What can be transferred to OIL?**
Our inference: the one-directional cross-attention pattern maps naturally onto CDS→IGS (or IGS→CDS) information flow if there is a biologically motivated direction to enforce, e.g. regulatory IGS context informing CDS translation:

$$\text{IGS}\to\text{CDS}:\ Q=\text{codon positions},\ K,V=\text{IGS nucleotide positions}$$

The Virtual-Cell-Embedder-style attention pooling is also a reusable way to compress a variable-length stream into a fixed summary before fusing with the other stream.

**What would need to change?** CDT assumes frozen, pre-computed, gene/region-level embeddings rather than raw token sequences; adapting it to OIL would require operating directly on codon/nucleotide token embeddings within a single trainable model instead of caching external foundation-model outputs, and defining what "direction" of causality (if any) applies between CDS and IGS.

**Key architectural takeaway:** For our nucleotide–codon model, the most useful idea from this paper is enforcing a directional (rather than symmetric) cross-attention between representation types when there is a plausible causal or regulatory direction to encode, trading some flexibility for interpretability.

# 9. Final Verdict for Literature Review

**Category:** Genomic-context modeling; Representation alignment; Multimodal / multi-encoder architecture
**Priority for our project:** Medium
**Reason:** The directional-attention idea and its interpretability case study are conceptually valuable, but the paper's reliance on pre-computed gene-level embeddings limits direct architectural reuse for raw codon/nucleotide sequences.

## Compact Comparison Record

| Input | Tokenization | Backbone | Interaction | Objective | OIL relevance |
|---|---|---|---|---|---|
| Frozen DNA (Enformer bins) + RNA (scGPT gene tokens) + protein (ESM-C) embeddings | Not raw-tokenized; pre-computed per-modality embeddings | Self-attention per modality + directional cross-attention + VCE pooling | One-directional DNA→RNA→protein cross-attention | Huber-loss regression on CRISPRi effect size | Low direct; Medium architectural (directional fusion pattern) |
