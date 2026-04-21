from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np


def _product_to_text(product: Dict[str, Any]) -> str:
    name = str(product.get("name") or "").strip()
    description = str(product.get("description") or "").strip()
    category = str(product.get("category") or "").strip()
    brand = str(product.get("brand") or "").strip()

    parts = [name, description]
    if category:
        parts.append(f"Category: {category}")
    if brand:
        parts.append(f"Brand: {brand}")
    return ". ".join([part for part in parts if part])


def _require_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "Semantic search requires `sentence-transformers`. "
            "Install it with: pip install -r backend/python/requirements.txt"
        ) from exc
    return SentenceTransformer


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    SentenceTransformer = _require_sentence_transformers()
    return SentenceTransformer(model_name)


@dataclass(frozen=True)
class SemanticSearchResult:
    product: Dict[str, Any]
    score: float


class SemanticSearchIndex:
    def __init__(
        self,
        products: Sequence[Dict[str, Any]],
        *,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name
        self.products: List[Dict[str, Any]] = list(products)
        self._texts = [_product_to_text(product) for product in self.products]

        self._model = _load_model(model_name)
        self._embeddings = self._model.encode(
            self._texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        if not isinstance(self._embeddings, np.ndarray):
            self._embeddings = np.asarray(self._embeddings)

        if self._embeddings.ndim != 2:
            raise ValueError("Unexpected embedding shape from model.encode().")

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_score: Optional[float] = None,
    ) -> List[SemanticSearchResult]:
        query = (query or "").strip()
        if not query:
            return []

        query_embedding = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if isinstance(query_embedding, np.ndarray):
            query_vector = query_embedding[0]
        else:
            query_vector = np.asarray(query_embedding)[0]

        scores = self._embeddings @ query_vector
        if scores.ndim != 1:
            scores = np.asarray(scores).reshape(-1)

        if top_k <= 0:
            top_k = 1

        ranked_indices = np.argsort(-scores)[: min(top_k, len(self.products))]
        results: List[SemanticSearchResult] = []
        for idx in ranked_indices.tolist():
            score = float(scores[idx])
            if min_score is not None and score < float(min_score):
                continue
            results.append(SemanticSearchResult(product=self.products[idx], score=score))
        return results


def semantic_search(
    products: Sequence[Dict[str, Any]],
    query: str,
    *,
    top_k: int = 10,
    model_name: str = "all-mpnet-base-v2",
    min_score: Optional[float] = None,
) -> List[SemanticSearchResult]:
    return SemanticSearchIndex(products, model_name=model_name).search(
        query, top_k=top_k, min_score=min_score
    )


def keyword_search(
    products: Iterable[Dict[str, Any]],
    query: str,
    *,
    fields: Sequence[str] = ("name", "description", "category", "brand"),
) -> List[Dict[str, Any]]:
    query = (query or "").strip().lower()
    if not query:
        return list(products)

    hits: List[Dict[str, Any]] = []
    for product in products:
        haystack = " ".join(str(product.get(field) or "") for field in fields).lower()
        if query in haystack:
            hits.append(product)
    return hits
