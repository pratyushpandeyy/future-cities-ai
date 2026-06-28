import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.models.schemas import (
    KnowledgeChunk,
    KnowledgeSource,
    RAGQueryRequest,
    RAGQueryResponse,
)


KNOWLEDGE_SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge"
    / "climate_advisor_seed.json"
)
KNOWLEDGE_INDEX_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge"
    / "climate_knowledge_index.json"
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "or",
    "should",
    "the",
    "to",
    "with",
}


@dataclass(frozen=True)
class VectorizedChunk:
    chunk: KnowledgeChunk
    terms: set[str]
    vector: dict[str, float]


def retrieve_climate_knowledge(payload: RAGQueryRequest) -> RAGQueryResponse:
    index = load_vector_index()
    query_terms = query_tokens(payload)
    query_vector = build_query_vector(query_terms)
    scored_chunks = [
        score_vectorized_chunk(
            vectorized_chunk=vectorized_chunk,
            query_terms=query_terms,
            query_vector=query_vector,
            payload=payload,
        )
        for vectorized_chunk in index
    ]
    ranked_chunks = sorted(
        (chunk for chunk in scored_chunks if chunk.relevance_score > 0),
        key=lambda chunk: chunk.relevance_score,
        reverse=True,
    )
    selected = ranked_chunks[: payload.max_chunks] or scored_chunks[: payload.max_chunks]

    return RAGQueryResponse(
        query_text=payload.query_text,
        retrieval_mode="local_tfidf_vector_rag_v1",
        chunks=selected,
        grounding_summary=grounding_summary(selected),
    )


@lru_cache(maxsize=1)
def load_knowledge_chunks() -> list[KnowledgeChunk]:
    knowledge_path = active_knowledge_path()

    if not knowledge_path.exists():
        return []

    raw_chunks = json.loads(knowledge_path.read_text(encoding="utf-8"))
    return [
        KnowledgeChunk(
            chunk_id=str(item["chunk_id"]),
            title=str(item["title"]),
            text=str(item["text"]),
            source=KnowledgeSource(**item["source"]),
            tags=[str(tag) for tag in item.get("tags", [])],
            relevance_score=0.0,
        )
        for item in raw_chunks
    ]


def active_knowledge_path() -> Path:
    if KNOWLEDGE_INDEX_PATH.exists():
        return KNOWLEDGE_INDEX_PATH

    return KNOWLEDGE_SEED_PATH


@lru_cache(maxsize=1)
def load_vector_index() -> list[VectorizedChunk]:
    chunks = load_knowledge_chunks()

    if not chunks:
        return []

    chunk_terms = [
        tokenize(" ".join([chunk.title, chunk.text, " ".join(chunk.tags)]))
        for chunk in chunks
    ]
    document_frequency = build_document_frequency(chunk_terms)
    document_count = len(chunks)

    return [
        VectorizedChunk(
            chunk=chunk,
            terms=terms,
            vector=tfidf_vector(
                terms=terms,
                document_frequency=document_frequency,
                document_count=document_count,
            ),
        )
        for chunk, terms in zip(chunks, chunk_terms, strict=True)
    ]


def build_document_frequency(term_sets: list[set[str]]) -> dict[str, int]:
    document_frequency: dict[str, int] = {}

    for terms in term_sets:
        for term in terms:
            document_frequency[term] = document_frequency.get(term, 0) + 1

    return document_frequency


def tfidf_vector(
    terms: set[str],
    document_frequency: dict[str, int],
    document_count: int,
) -> dict[str, float]:
    vector = {}

    for term in terms:
        inverse_document_frequency = math.log(
            (1 + document_count) / (1 + document_frequency.get(term, 0)),
        ) + 1
        vector[term] = inverse_document_frequency

    return normalize_vector(vector)


def build_query_vector(query_terms: set[str]) -> dict[str, float]:
    if not query_terms:
        return {}

    return normalize_vector({term: 1.0 for term in query_terms})


def normalize_vector(vector: dict[str, float]) -> dict[str, float]:
    magnitude = math.sqrt(sum(value * value for value in vector.values()))

    if magnitude == 0:
        return vector

    return {term: value / magnitude for term, value in vector.items()}


def query_tokens(payload: RAGQueryRequest) -> set[str]:
    text_parts = [
        payload.query_text,
        payload.location or "",
        payload.climate_region_type or "",
        payload.season or "",
        " ".join(payload.risks),
    ]
    return tokenize(" ".join(text_parts))


def tokenize(text: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", text.lower())
        if token not in STOPWORDS
    }

    expanded = set(tokens)
    if "asthma" in tokens or "respiratory" in tokens:
        expanded.update({"health", "air", "heat", "respiratory"})
    if "monsoon" in tokens:
        expanded.update({"flood", "rainfall", "drainage"})
    if "relocate" in tokens or "relocation" in tokens or "instead" in tokens:
        expanded.update({"relocation", "tradeoffs", "migration"})
    if "green" in tokens or "vegetation" in tokens:
        expanded.update({"green", "vegetation", "resilience"})

    return expanded


def score_vectorized_chunk(
    vectorized_chunk: VectorizedChunk,
    query_terms: set[str],
    query_vector: dict[str, float],
    payload: RAGQueryRequest,
) -> KnowledgeChunk:
    chunk = vectorized_chunk.chunk
    vector_score = cosine_similarity(query_vector, vectorized_chunk.vector)
    tag_overlap = query_terms.intersection({tag.lower() for tag in chunk.tags})
    score = vector_score + (0.08 * len(tag_overlap))

    if payload.climate_region_type and payload.climate_region_type in vectorized_chunk.terms:
        score += 0.05
    if payload.season and payload.season.lower() in vectorized_chunk.terms:
        score += 0.05

    normalized = round(score, 4)

    return chunk.model_copy(update={"relevance_score": normalized})


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0

    return sum(value * right.get(term, 0.0) for term, value in left.items())


def grounding_summary(chunks: list[KnowledgeChunk]) -> str:
    if not chunks:
        return "No climate knowledge chunks were available for retrieval."

    sources = []
    for chunk in chunks:
        source_name = f"{chunk.source.publisher}: {chunk.source.title}"
        if source_name not in sources:
            sources.append(source_name)

    return "Retrieved local RAG evidence from " + "; ".join(sources[:3]) + "."
