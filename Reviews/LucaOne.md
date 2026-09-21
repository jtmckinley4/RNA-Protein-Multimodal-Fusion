# 1. Paper Information

**Title:** LucaOne: generalized biological foundation model with unified nucleic acid and protein language
**Authors:** He, Fang, Shan, Pan, Wei, et al.
**Year / Venue:** 2025, Nature Machine Intelligence
**Paper Type:** Model
**Biological Domain:** General-purpose (spans nucleic acid and protein biology; ~170,000 species)
**Primary Sequence Representation(s):** Mixed (nucleotide + amino acid, single shared model)

**One-sentence summary:** LucaOne trains one 1.8B-parameter transformer from scratch on a shared 39-token vocabulary spanning nucleotides and amino acids, showing that a central-dogma correspondence between DNA and protein emerges from joint pretraining without any explicit cross-modal supervision.

# 2. Problem and Motivation

The paper addresses whether cross-modal biological structure (the DNA→RNA→protein correspondence) can be learned implicitly by a single model trained jointly on both sequence types, rather than fused after separate pretraining. It explicitly and centrally handles two representations together in one vocabulary: nucleic acid (DNA/RNA nucleotides) and protein (amino acids), with no separate encoders (Methods, "Vocabulary").

# 3. Input Representation and Tokenization

Character-level tokenization over a single shared 39-token vocabulary: 4 standard nucleotides plus 'N' for unknown, 20 standard amino acids (excluding B, J, O, U, Z) plus 'X' for unknown, 5 special tokens ([PAD],[UNK],[CLS],[SEP],[MASK]), plus a few misc. symbols. Digits substitute for A/T/C/G/N internally to avoid collision with amino-acid letters. [CLS]/[SEP] mark sequence start/end. Max length 1,280 tokens. Reading-frame/strand handling: Not specified — no codon grouping; each nucleic-acid or protein unit is one token.

$$x=(t_1,\ldots,t_L),\quad t_i\in V,\quad |V|=39,\quad L\le 1280$$

**Mixed-representation handling.** Nucleotide and amino-acid tokens are concatenated into the *same* sequence and embedded through the *same* shared vocabulary/embedding table — the strongest form of mixing among the surveyed papers. A token-type embedding added at every position tells the model which alphabet it is reading:

$$e_i = \mathrm{Emb}(t_i) + \mathrm{TypeEmb}(m_i) + \mathrm{RoPE}(i),\quad m_i\in\{0,1\}\ (0=\text{nucleic acid},\,1=\text{protein})$$

No separate per-modality vocabularies or conversion between representations — one model, one vocabulary, one embedding table for both.

# 4. Model Architecture

**Backbone:** decoder-agnostic Transformer encoder, BERT-style, 20 layers, embedding dimension 2,560, 40 attention heads, pre-layer normalization (instead of post-LN) for training stability, rotary position embeddings (RoPE) instead of absolute positional encoding, 1.8B parameters total.
**Representation-specific components:** one shared encoder (no separate nucleotide/protein towers); a token-type embedding is the only representation-specific mechanism; no cross-attention, fusion layer, or shared-latent-space machinery is needed because the encoder itself is shared.

Flow: mixed nucleotide/codon-adjacent and amino-acid tokens $\to$ shared embedding + token-type embedding + RoPE $\to$ 20-layer Transformer (pre-LN) $\to$ task-specific heads (masked-token prediction, span classification, structure regression, etc.).

# 5. Training Strategy

Ten pretraining tasks across four levels, jointly weighted in one loss: two MLM objectives (Gene-Mask, Prot-Mask; weight 1.0), span-level region classification (weight 0.2), sequence-level taxonomy/keyword prediction (weight 0.2/1.0), and structure-level Cα-coordinate regression (weight 1.0):

$$\mathcal{L}=\mathcal{L}_{Gene\text{-}Mask}+\mathcal{L}_{Prot\text{-}Mask}+\mathcal{L}_{keyword}+\mathcal{L}_{structure}+0.2\sum_k\mathcal{L}_{aux,k}$$

Training is joint, single-stage: all tasks train simultaneously on mixed-modality batches. Data: NCBI RefSeq (169,861 species) plus UniProt/UniRef50/ColabFoldDB. 8 A100 GPUs, 120 days; checkpoints at 36.95B and 116.62B tokens seen.

# 6. Evaluation and Main Findings

Central experiment: a few-shot DNA–protein matching task (4:3:25 train/val/test) compares one-hot encoding, a random transformer, concatenated DNABert2+ESM2-3B embeddings, and LucaOne, plus single-modality LucaOne-Gene/LucaOne-Prot ablations. LucaOne substantially outperforms both — core evidence that joint mixed-modality pretraining, not scale alone, produces the emergent DNA–protein correspondence. Across seven downstream tasks (LucaTasks), it is best or competitive on five of seven, including the cross-modality ncRPI task, and hits perfect accuracy on InfA. Failure case: accuracy drops on Ciona intestinalis (atypical codon usage/GC content), recovered by adding urochordate training data — a data-coverage, not architectural, gap.

# 7. Architectural Strengths and Limitations

**Strengths**
- Single shared vocabulary removes the alignment problem entirely — tokens live in the same space by construction.
- Emergent cross-modal correspondence demonstrated without explicit paired-alignment supervision.
- One architecture scales to many downstream tasks without per-modality redesign.

**Limitations**
- Very high computational cost (1.8B parameters, 120 GPU-days) vs. fusing existing frozen encoders.
- No codon-level grouping — nucleotides are individual tokens, so codon structure isn't built into tokenization — our inference.
- Accuracy degrades with exon count and on species with underrepresented codon usage.

# 8. Relevance to OIL and Our Research

**Direct relevance:** High. LucaOne is the clearest existing precedent for OIL's core requirement — a single model handling both codon-resolvable and raw-nucleotide regions — because it already mixes two token granularities (nucleotide, amino acid) in one vocabulary with a type embedding, rather than fusing separate encoders.

**What can be transferred to OIL?**
Our inference: the shared-vocabulary-plus-type-embedding pattern generalizes directly to a codon/nucleotide split instead of nucleotide/amino-acid:

$$e_i=\mathrm{Emb}(t_i)+\mathrm{TypeEmb}(m_i)+\mathrm{RoPE}(i),\quad m_i\in\{\text{CDS-codon},\,\text{IGS-nucleotide}\}$$

with $t_i$ drawn from a vocabulary containing both codon tokens (for CDS) and single-nucleotide tokens (for IGS). RoPE and pre-LN are also reusable as general stability choices.

**What would need to change?** LucaOne mixes single-character tokens only; OIL needs single-nucleotide (IGS) and codon-level (CDS) tokens of different granularities in the same stream, which LucaOne's design doesn't itself address — this needs an explicit boundary marker or length-aware position indexing so RoPE stays meaningful across a resolution change.

**Key architectural takeaway:** For our nucleotide–codon model, the most useful idea from this paper is a single shared model with a mixed vocabulary and a type embedding, extended so the type embedding also signals a token's resolution (codon vs. nucleotide), not just its molecule class.

# 9. Final Verdict for Literature Review

**Category:** Direct nucleotide–codon modeling; Nucleotide–amino-acid mixed modeling; Multi-resolution modeling; Dataset / corpus paper
**Priority for our project:** High
**Reason:** It is the strongest existing precedent for a single joint model over mixed biological token types and directly informs the "single model, mixed vocabulary" architectural option for OIL.

## Compact Comparison Record

| Input | Tokenization | Backbone | Interaction | Objective | OIL relevance |
|-.-|---|---|---|---|---|
| Nucleotides + amino acids, single stream | Shared 39-token character-level vocabulary + token-type embedding | Single 20-layer Transformer, pre-LN, RoPE, 1.8B params | Implicit, via shared self-attention (no explicit fusion module) | 10 joint pretraining tasks (MLM + span/seq/structure) | High direct; High architectural |
