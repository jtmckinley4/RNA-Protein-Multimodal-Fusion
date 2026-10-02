"""Sequence checks, translation, composition features, and motif scanning.

Functions here act on single sequence strings and need neither PyTorch nor an encoder.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from Bio.Seq import Seq


def is_in_frame_and_starts_correctly(seq):
    """Check for a length divisible by three and an ATG or AUG start."""
    seq = seq.upper().strip()
    return len(seq) % 3 == 0 and seq.startswith(("ATG", "AUG"))


def translate_cds(seq):
    """Translate complete codons using the standard code, up to the first stop."""
    trimmed_seq = seq[: len(seq) - (len(seq) % 3)]
    return str(Seq(trimmed_seq).translate(to_stop=True))


def rna_to_dna(seq):
    """Return an uppercase sequence with U replaced by T."""
    return seq.upper().replace("U", "T")


def dna_to_rna(seq):
    """Return an uppercase sequence with T replaced by U."""
    return seq.upper().replace("T", "U")


def gc_content(seq):
    """Return the G-or-C fraction of a nonempty uppercase sequence."""
    return (seq.count("G") + seq.count("C")) / len(seq)


def gc3_content(seq):
    """Return the GC fraction at third positions of complete codons."""
    return gc_content(seq[2::3])


# ---------------------------------------------------------------------------
# Composition features
# ---------------------------------------------------------------------------

CODONS = ["".join(t) for t in itertools.product("ACGT", repeat=3)]


AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")


def composition_features(seq):
    """Return GC, GC3, log length, 64 codon frequencies, and 20 amino-acid frequencies."""
    dna = rna_to_dna(seq)
    protein = translate_cds(seq)
    codons = [dna[i:i + 3] for i in range(0, len(dna) - 2, 3)]
    codon_counts = pd.Series(codons).value_counts()
    codon_freq = [codon_counts.get(c, 0) / len(codons) for c in CODONS]
    aa_freq = [protein.count(a) / max(len(protein), 1) for a in AMINO_ACIDS]
    return [gc_content(dna), gc3_content(dna), np.log(len(dna))] + codon_freq + aa_freq


# ---------------------------------------------------------------------------
# Candidate stability motifs
# ---------------------------------------------------------------------------

STABILITY_MOTIFS = {"ARE_pentamer": "AUUUA", "ARE_nonamer": "UUAUUUAUU", "m6A_DRACH": "DRACH"}


_IUPAC = {
    "A": "A", "C": "C", "G": "G", "T": "T", "U": "T", "R": "[AG]", "Y": "[CT]", "S": "[GC]",
    "W": "[AT]", "K": "[GT]", "M": "[AC]", "B": "[CGT]", "D": "[AGT]", "H": "[ACT]",
    "V": "[ACG]", "N": "[ACGT]",
}


def scan_sequence_for_motifs(sequence, motifs=STABILITY_MOTIFS):
    """Return (start, end, motif_name) for each consensus match, including overlaps."""
    import re

    seq = sequence.upper().replace("U", "T")
    hits = []
    for name, pattern in motifs.items():
        regex = "".join(_IUPAC[b] for b in pattern.upper())
        hits += [(m.start(), m.start() + len(pattern), name) for m in re.finditer(f"(?={regex})", seq)]
    return hits
