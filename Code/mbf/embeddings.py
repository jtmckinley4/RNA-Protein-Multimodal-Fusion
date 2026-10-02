"""Embeddings from frozen encoders: pooled vectors, per-layer vectors, and attention.

embed_with_cache saves one matrix per encoder and reuses it only when the checkpoint,
revision, token limit, and input sequences all match.
"""

from __future__ import annotations

import hashlib
import os

import numpy as np
import torch

from .analysis import aggregate_attention, attention_motif_overlap, expand_token_attention_to_nucleotides
from .encoders import encoder_input, free_memory, load_encoder
from .sequences import scan_sequence_for_motifs


@torch.no_grad()
def embed(seq, tokenizer, model, max_len, device):
    """Mean-pool one sequence's final hidden state into a NumPy vector."""
    inputs = tokenizer(seq, return_tensors="pt", truncation=True, max_length=max_len).to(device)
    out = model(**inputs)
    token_embeddings = out[0]  # (1, T, d): last_hidden_state for every encoder used here
    return token_embeddings.mean(dim=1).squeeze().float().cpu().numpy()


def count_tokens(seq, tokenizer, max_len):
    """Return (tokens after truncation, tokens without truncation) for one input."""
    full = len(tokenizer(seq)["input_ids"])
    return min(full, max_len), full


def sequences_fingerprint(seqs):
    """Return a short hash identifying an ordered list of sequences."""
    digest = hashlib.sha1("\n".join(seqs).encode()).hexdigest()
    return digest[:16]


def embed_with_cache(encoder, seqs, cache_dir, device, progress_every=200):
    """Embed seqs with one encoder, reusing a saved matrix when it matches.

    The cache file records the checkpoint, revision, token limit, and a fingerprint of
    the ordered input sequences; any mismatch triggers recomputation.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{encoder.key}.npz")
    fingerprint = sequences_fingerprint(seqs)
    expected = {
        "checkpoint": encoder.checkpoint,
        "revision": encoder.revision or "",
        "max_len": encoder.max_len,
        "fingerprint": fingerprint,
    }
    if os.path.exists(path):
        saved = np.load(path, allow_pickle=False)
        if all(str(saved[k]) == str(v) for k, v in expected.items()):
            return saved["embeddings"], True

    tokenizer, model = load_encoder(encoder, device)
    vectors = []
    for i, seq in enumerate(seqs, start=1):
        vectors.append(embed(encoder_input(encoder, seq), tokenizer, model, encoder.max_len, device))
        if progress_every and i % progress_every == 0:
            print(f"    {encoder.key}: {i}/{len(seqs)}")
    del model, tokenizer
    free_memory()
    embeddings = np.vstack(vectors)
    np.savez(path, embeddings=embeddings, device=device, **expected)
    return embeddings, False


@torch.no_grad()
def embed_all_layers(seq, encoder, tokenizer, model, device):
    """Mean-pool every returned hidden state for one sequence.

    Every encoder contributes its embedding-layer output followed by each transformer
    layer. DNABERT-2's own all-layer option fails, so its states are captured with
    forward hooks on the embedding module and each encoder layer.
    """
    inputs = tokenizer(
        encoder_input(encoder, seq), return_tensors="pt", truncation=True, max_length=encoder.max_len
    ).to(device)
    if encoder.loader == "remote_dnabert2":
        captured = []
        modules = [model.embeddings] + list(model.encoder.layer)
        hooks = [m.register_forward_hook(lambda _m, _i, out: captured.append(out)) for m in modules]
        try:
            model(**inputs)
        finally:
            for hook in hooks:
                hook.remove()
        layers = captured
    else:
        layers = model(**inputs, output_hidden_states=True).hidden_states
    return [h.reshape(-1, h.shape[-1]).mean(dim=0).float().cpu().numpy() for h in layers]


@torch.no_grad()
def attention_maps(text, tokenizer, model, device, max_len, layers=None):
    """Return self-attention arrays and token strings for one input string.

    Each array has shape (heads, query_tokens, key_tokens). layers selects which layers
    to return, all by default; converting only the needed layers saves memory for long
    inputs. The model must be loaded with eager attention so that it returns weights.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_len).to(device)
    attentions = model(**inputs, output_attentions=True).attentions
    chosen = range(len(attentions)) if layers is None else layers
    arrays = [attentions[i][0].float().cpu().numpy() for i in chosen]
    return arrays, tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])


def nucleotide_attention(seq, encoder, tokenizer, model, device, layer=-1):
    """Return one layer's incoming attention, min-max scaled and expanded to nucleotides."""
    arrays, tokens = attention_maps(
        encoder_input(encoder, seq), tokenizer, model, device, encoder.max_len, layers=[layer]
    )
    return expand_token_attention_to_nucleotides(aggregate_attention(arrays, layer=0), tokens)


def embed_layers(encoder, seqs, device):
    """Return one (n, d) matrix per hidden state for the given retained sequences.

    The encoder is loaded, applied to each sequence with embed_all_layers, and released.
    """
    tokenizer, model = load_encoder(encoder, device)
    per_sequence = [embed_all_layers(s, encoder, tokenizer, model, device) for s in seqs]
    del model, tokenizer
    free_memory()
    return [np.vstack([states[k] for states in per_sequence]) for k in range(len(per_sequence[0]))]


def attention_motif_tests(encoder, seqs, device, layer=-1):
    """Run attention_motif_overlap on each sequence for one nucleotide encoder.

    Returns the usable results (sequences with an available pooled comparison). The
    encoder is loaded with eager attention and released afterwards.
    """
    tokenizer, model = load_encoder(encoder, device, eager_attention=True)
    results = []
    for seq in seqs:
        attention = nucleotide_attention(seq, encoder, tokenizer, model, device, layer=layer)
        result = attention_motif_overlap(attention, scan_sequence_for_motifs(seq))
        if result is not None:
            results.append(result)
    del model, tokenizer
    free_memory()
    return results
