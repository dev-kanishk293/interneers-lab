from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

try:
    from langsmith import traceable
except Exception:  # pragma: no cover
    def traceable(*_args: Any, **_kwargs: Any):  # type: ignore[no-redef]
        def decorator(func):
            return func

        return decorator


PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_DIR = PROJECT_BACKEND_ROOT / "public"
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_COLLECTION_NAME = "expert_knowledge"


@dataclass(frozen=True)
class RetrievedChunk:
    content: str
    source: str
    score: float


def _load_text_splitter(chunk_size: int = 320, chunk_overlap: int = 60):
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def _load_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "RAG retrieval requires `sentence-transformers`. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from exc

    return SentenceTransformer(model_name)


@lru_cache(maxsize=4)
def _cached_model(model_name: str):
    return _load_sentence_transformer(model_name)


def _read_documents(docs_dir: Path = DEFAULT_DOCS_DIR) -> List[Dict[str, str]]:
    documents: List[Dict[str, str]] = []
    for path in sorted(docs_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents.append({"source": path.name, "text": text})
    return documents


def load_sample_documents(docs_dir: Path = DEFAULT_DOCS_DIR) -> List[Dict[str, str]]:
    """Return the uploaded/sample knowledge-base documents."""
    return _read_documents(docs_dir)


def build_vector_store(
    *,
    docs_dir: Path = DEFAULT_DOCS_DIR,
    model_name: str = DEFAULT_MODEL_NAME,
    chunk_size: int = 320,
    chunk_overlap: int = 60,
):
    try:
        import chromadb
        from chromadb.config import Settings
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "RAG retrieval requires `chromadb`. Install dependencies with: "
            "pip install -r requirements.txt"
        ) from exc

    splitter = _load_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    model = _cached_model(model_name)

    texts: List[str] = []
    metadatas: List[Dict[str, str]] = []
    ids: List[str] = []

    for document in _read_documents(docs_dir):
        chunks = splitter.split_text(document["text"])
        for chunk_index, chunk in enumerate(chunks):
            clean_chunk = chunk.strip()
            if not clean_chunk:
                continue
            texts.append(clean_chunk)
            metadatas.append(
                {"source": document["source"], "chunk_index": str(chunk_index)}
            )
            ids.append(f"{document['source']}:{chunk_index}:{uuid4().hex[:8]}")

    client = chromadb.EphemeralClient(
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.create_collection(
        name=f"{DEFAULT_COLLECTION_NAME}_{uuid4().hex[:8]}",
        metadata={"hnsw:space": "cosine"},
    )

    if texts:
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    return collection


@lru_cache(maxsize=1)
def _cached_vector_store():
    return build_vector_store()


@traceable(name="retrieve_relevant_chunks")
def retrieve_relevant_chunks(query: str, top_k: int = 3) -> List[RetrievedChunk]:
    query = (query or "").strip()
    if not query:
        return []

    collection = _cached_vector_store()
    model = _cached_model(DEFAULT_MODEL_NAME)
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, int(top_k)),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks: List[RetrievedChunk] = []
    for content, metadata, distance in zip(documents, metadatas, distances):
        chunks.append(
            RetrievedChunk(
                content=str(content),
                source=str((metadata or {}).get("source", "unknown")),
                score=1.0 - float(distance),
            )
        )
    return chunks


def _format_context(chunks: Sequence[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"Source: {chunk.source}\n{chunk.content}" for chunk in chunks
    )


def _generate_with_gemini(question: str, chunks: Sequence[RetrievedChunk]) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
    except Exception:
        return None

    prompt = f"""
Answer the question using only the context below. If the context does not contain
the answer, say you do not know.

Context:
{_format_context(chunks)}

Question: {question}
Answer:
""".strip()

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
    )
    return (response.text or "").strip() or None


@traceable(name="ask_the_expert")
def ask_the_expert(question: str, top_k: int = 3) -> Dict[str, Any]:
    chunks = retrieve_relevant_chunks(question, top_k=top_k)
    if not chunks:
        return {
            "answer": "I could not find anything relevant in the uploaded documents.",
            "sources": [],
        }

    generated = _generate_with_gemini(question, chunks)
    if generated:
        answer = generated
    else:
        answer = f"Based on {chunks[0].source}: {chunks[0].content}"

    return {
        "answer": answer,
        "sources": [
            {"source": chunk.source, "score": round(chunk.score, 4)}
            for chunk in chunks
        ],
    }
