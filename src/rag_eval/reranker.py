import torch

from sentence_transformers import (
    CrossEncoder
)


RERANK_MODEL_NAME = (
    "BAAI/bge-reranker-base"
)


_reranker_model = None


def get_reranker():
    """
    Load the reranker only once.
    """

    global _reranker_model

    if _reranker_model is not None:
        return _reranker_model

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"[RERANK] Loading model on {device}"
    )

    _reranker_model = CrossEncoder(
        RERANK_MODEL_NAME,
        device=device,
        max_length=512
    )

    return _reranker_model


def rerank_documents(
    question: str,
    documents: list,
    top_k: int = 5
):
    """
    Rerank retrieved documents using
    a local cross-encoder model.
    """

    if not documents:
        return []

    model = get_reranker()

    pairs = [
        [
            question,
            document.page_content
        ]
        for document in documents
    ]

    scores = model.predict(
        pairs,
        batch_size=8,
        show_progress_bar=False
    )

    scored_documents = []

    for document, score in zip(
        documents,
        scores
    ):
        scored_documents.append(
            (
                document,
                float(score)
            )
        )

    scored_documents.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return scored_documents[:top_k]