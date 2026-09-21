# 1. Paper Information

**Title:** BioLangFusion: Multimodal Fusion of DNA, mRNA, and Protein Language Models
**Authors:** Mollaysa et al.
**Year / Venue:** 2025, ICML 2025 Workshop on Multi-modal Foundation Models and LLMs for Life Sciences
**Paper Type:** Method
**Biological Domain:** Central-dogma molecular biology (DNA, mRNA, protein)
**Primary Sequence Representation(s):** Mixed (nucleotide, codon-resolved mRNA, amino acid)

**One-sentence summary:** The paper proposes three lightweight, training-free fusion schemes that align frozen DNA, RNA, and protein language-model embeddings to a shared codon resolution and combine them, improving molecular property prediction over any single modality.

# 2. Problem and Motivation

Pretrained DNA, RNA, and protein language models are trained separately and tokenize at different granularities, so they cannot be combined directly even though the sequences they model are causally linked by the central dogma. The paper addresses how to fuse these frozen embeddings cheaply, without retraining or architectural changes to the base models. It explicitly deals with three representations simultaneously: DNA (6-mer tokens), mRNA (single-nucleotide tokens), and protein (amino-acid/codon tokens), unified at codon resolution (Sec. 2.1).

# 3. Input Representation and Tokenization

Each modality keeps its own pretrained tokenizer: Nucleotide Transformer v2 for DNA (6-mers), RNA-FM for mRNA (single nucleotides), ESM-2 for protein (amino acids, i.e. 3-mers of nucleotide). For an mRNA of length $T$:

$$E_{DNA}\in\mathbb{R}^{T/6\times d_{DNA}},\quad E_{RNA}\in\mathbb{R}^{T\times d_{RNA}},\quad E_{Prot}\in\mathbb{R}^{T/3\times d_{Prot}}$$

with $d_{DNA}=4107$, $d_{RNA}=640$, $d_{Prot}=320$ (Table 3). No special tokens, reading-frame or strand handling are specified beyond using start/stop codons to map an mRNA to its DNA/protein counterparts; max input length is 1000 tokens (RNA truncated beyond this, Table 2).

**Mixed-representation handling.** The protein frame ($T'=T/3$) is the reference resolution. DNA is upsampled and RNA downsampled onto it:

$$\tilde{E}_{DNA}=\mathrm{TConv}_{k=2,s=2}(E_{DNA})\in\mathbb{R}^{T'\times d_{DNA}},\quad \tilde{E}_{RNA}=\mathrm{AvgPool}_{k=3,s=3}(E_{RNA})\in\mathbb{R}^{T'\times d_{RNA}}$$

so position $t$ denotes the same codon in all three modalities. Vocabularies are separate (one per pretrained model); the model does not use an explicit modality/type token — the modality identity is implicit in which embedding stream a vector arrives on.

# 4. Model Architecture

**Backbone:** none learned end-to-end for representation — three frozen pretrained encoders (Transformer-based) feed a downstream fusion head plus a TextCNN prediction head.
**Representation-specific components:** separate frozen encoders per modality; a shared codon-resolution grid (not a shared latent space); modality-specific learnable MLP projections; one of three fusion mechanisms.

Three fusion heads, all after alignment (Sec. 2.2):
(1) Concatenation: $Z_{concat}(t)=\mathrm{MLP}(\tilde{E}_{DNA}[t])\,\|\,\tilde{E}_{RNA}[t]\,\|\,E_{Prot}[t]$.
(2) MIL with entropy regularization: gated (tanh/sigmoid) attention produces one weight per modality per sequence from mean-pooled summaries; fused vector is the attention-weighted sum, trained with an added negative-entropy loss term to discourage near-uniform weights.
(3) Cross-modal multi-head attention: the three projected streams are concatenated along the sequence axis into one context of length $3T'$; each modality queries this joint context; outputs are averaged with a residual connection and layer-normalized.

Flow: $x_{DNA},x_{RNA},x_{Prot}\to E_{DNA},E_{RNA},E_{Prot}\to$ codon-resolution alignment $\to$ {concat | MIL-attention | cross-attention} $\to$ TextCNN head $\to y$.

# 5. Training Strategy

Base encoders stay frozen; only the fusion head and prediction head are trained. Objective is task-specific supervised loss (regression/classification) on five downstream datasets — not an explicit cross-modal alignment loss beyond the entropy regularizer in method (2). No joint pretraining; training is single-stage on the fusion+prediction modules only.

# 6. Evaluation and Main Findings

Five tasks: CoV-Vac, Fungal, E. coli expression, mRNA stability, Ab1 (Table with per-task metrics). All three fusion methods beat single-modality baselines. MIL with entropy regularization is best/tied-best on 4/5 datasets; cross-attention wins on E. coli protein abundance. Ablation: removing the codon-alignment step (projecting and concatenating without resampling) measurably underperforms the aligned version, and removing the entropy term hurts MIL performance — direct evidence the alignment step and the entropy regularizer both matter.

# 7. Architectural Strengths and Limitations

**Strengths**
- No retraining of pretrained FMs needed — cheap, modular (Sec. 1).
- Ablation isolates the value of codon-resolution alignment itself.
- Attention-pooling adapts modality weighting per sequence rather than fixing it.

**Limitations**
- Alignment is purely positional/resolution matching, not learned semantic alignment — our inference.
- Codon-grid alignment assumes a clean reading frame throughout; no mechanism for non-coding regions.
- Separate frozen encoders cannot interact during pretraining, limiting deep cross-modal learning.

# 8. Relevance to OIL and Our Research

**Direct relevance:** Medium. BioLangFusion's fusion mechanisms transfer directly to OIL's CDS regions, which are already codon-resolved, but the paper's alignment method assumes every position maps to a codon — a condition OIL's intergenic sequences do not satisfy.

**What can be transferred to OIL?**
Our inference: the entropy-regularized attention-pooling head could fuse a CDS codon-resolution stream with an IGS nucleotide-resolution stream:

$$h_{fused}=\sum_m \alpha_m \cdot \mathrm{Proj}_m(\tilde{E}_m),\quad \alpha=\mathrm{softmax}(\text{gated attention})$$

Cross-modal multi-head attention (method 3) is likewise reusable between a codon encoder and a nucleotide encoder.

**What would need to change?** The fixed 3:1/6:1 resampling ratio assumes codon structure everywhere; IGS has none, so alignment needs a boundary/type indicator marking CDS vs. IGS spans instead of uniform resampling.

**Key architectural takeaway:** For our nucleotide–codon model, the most useful idea from this paper is the entropy-regularized attention-pooling fusion head, adapted to fuse a codon-resolution CDS stream with a nucleotide-resolution IGS stream once a boundary-aware alignment (rather than uniform resampling) is defined.

# 9. Final Verdict for Literature Review

**Category:** Direct nucleotide–codon modeling; Multimodal / multi-encoder architecture; Representation alignment
**Priority for our project:** High
**Reason:** It is the most directly analogous fusion-of-frozen-encoders approach to OIL's CDS+IGS setting, and its ablations give concrete evidence for what alignment choices matter.

## Compact Comparison Record

| Input | Tokenization | Backbone | Interaction | Objective | OIL relevance |
|---|---|---|---|---|---|
| DNA (6-mer) + mRNA (nt) + protein (aa/codon) | Separate pretrained tokenizers per modality | 3 frozen pretrained Transformers + fusion head + TextCNN | Codon-grid resampling then concat / MIL-attention / cross-attention | Downstream supervised loss + entropy regularizer (MIL) | Medium direct; High architectural (fusion head reusable)|
