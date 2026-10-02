"""Embeddings from frozen encoders: pooled vectors, per-layer vectors, and attention.

embed_with_cache saves one matrix per encoder and reuses it only when the checkpoint,
revision, token limit, and input sequences all match.
"""

from __future__ import annotations

import hashlib
import os

import numpy as np
import torch

from .encoders import encoder_input, free_memory, load_encoder


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
def nucleotide_attention(seq, encoder, tokenizer, model, device, layer=-1):
    """Return last-layer incoming attention, min-max scaled, expanded to nucleotides.

    Heads are averaged, each token's received attention is summed over queries, special
    tokens are dropped, and each token's score is repeated over the nucleotides it spells.
    """
    inputs = tokenizer(
        encoder_input(encoder, seq), return_tensors="pt", truncation=True, max_length=encoder.max_len
    ).to(device)
    attentions = model(**inputs, output_attentions=True).attentions
    layer_att = attentions[layer][0].float().mean(dim=0).cpu().numpy()
    score = layer_att.sum(axis=0)
    score = (score - score.min()) / (score.max() - score.min() + 1e-8)
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    expanded = []
    for s, tok in zip(score, tokens):
        if tok.startswith("<") or tok.startswith("["):
            continue
        expanded.extend([s] * len(tok))
    return np.array(expanded)
