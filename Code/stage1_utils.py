"""Compatibility module for notebooks that import stage1_utils.

The shared functions now live in the mbf package (Code/mbf/). This module re-exports
them under their previous names so that Stage1_multimodel.ipynb runs unchanged. New
code should import from mbf.
"""

from mbf.analysis import (  # noqa: F401
    attention_motif_overlap,
    cca_retrieval,
    composition_share,
    compute_rsa,
    linear_cka,
    mantel_p_value,
    mutual_knn_alignment,
    pair_table,
    pairwise_matrix,
    plot_matrices,
    probe_scores,
    probe_table,
    residualize,
)
from mbf.datasets import retained_rows  # noqa: F401
from mbf.embeddings import (  # noqa: F401
    count_tokens,
    embed,
    embed_all_layers,
    embed_with_cache,
    nucleotide_attention,
    sequences_fingerprint,
)
from mbf.encoders import (  # noqa: F401
    ENCODERS,
    Encoder,
    apply_transformers5_compat,
    encoder_input,
    free_memory,
    load_encoder,
    select_device,
)
from mbf.sequences import (  # noqa: F401
    AMINO_ACIDS,
    CODONS,
    STABILITY_MOTIFS,
    composition_features,
    dna_to_rna,
    gc3_content,
    gc_content,
    is_in_frame_and_starts_correctly,
    rna_to_dna,
    scan_sequence_for_motifs,
    translate_cds,
)
