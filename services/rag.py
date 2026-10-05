import re
from typing import List, Dict


def split_into_chunks(text: str, chunk_size: int = 500) -> List[str]:
    """
    Split document text into smaller chunks.
    """

    if not text:
        return []

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


def tokenize(text: str) -> set:
    """
    Convert text into simple searchable words.
    """

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    stop_words = {
        "the",
        "is",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "what",
        "are",
        "was",
        "were"
    }

    return {
        word
        for word in words
        if word not in stop_words
    }


def calculate_score(query: str, chunk: str) -> int:
    """
    Calculate basic keyword similarity.
    """

    query_words = tokenize(query)
    chunk_words = tokenize(chunk)

    return len(query_words.intersection(chunk_words))


def retrieve(
    query: str,
    document_text: str,
    top_k: int = 3
) -> List[Dict]:
    """
    Retrieve the most relevant document chunks.
    """

    chunks = split_into_chunks(document_text)

    scored_chunks = []

    for chunk in chunks:
        score = calculate_score(query, chunk)

        scored_chunks.append({
            "text": chunk,
            "score": score
        })

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_chunks[:top_k]


def build_context(
    query: str,
    document_text: str,
    top_k: int = 3
) -> str:
    """
    Build the context that will be sent to the AI.
    """

    results = retrieve(
        query,
        document_text,
        top_k
    )

    useful_results = [
        item["text"]
        for item in results
        if item["score"] > 0
    ]

    if not useful_results:
        return ""

    return "\n\n--- Relevant section ---\n\n".join(
        useful_results
    )