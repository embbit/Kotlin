"""Local embedding model wrapper (fastembed)."""

from __future__ import annotations

from functools import lru_cache

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
E5_PREFIX_MODELS = {"intfloat/multilingual-e5-large"}


def _prefix(text: str, *, query: bool, model_name: str) -> str:
    if model_name in E5_PREFIX_MODELS:
        return ("query: " if query else "passage: ") + text
    return text


@lru_cache(maxsize=1)
def get_embedder(model_name: str = DEFAULT_MODEL):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=model_name)


def embed_passages(texts: list[str], model_name: str = DEFAULT_MODEL) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedder(model_name)
    prefixed = [_prefix(t, query=False, model_name=model_name) for t in texts]
    return [vec.tolist() for vec in model.embed(prefixed)]


def embed_query(text: str, model_name: str = DEFAULT_MODEL) -> list[float]:
    model = get_embedder(model_name)
    q = _prefix(text, query=True, model_name=model_name)
    return next(model.embed([q])).tolist()
