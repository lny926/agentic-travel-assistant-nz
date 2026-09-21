from langchain_chroma import Chroma

from src.config import (
    VECTOR_STORE_DIR,
    CHROMA_COLLECTION,
    RETRIEVAL_K,
    SUPPORTED_CITIES,
    USE_RERANKER,
    RERANK_CANDIDATE_K
)

from src.services.embeddings import (
    get_embedding_model
)

from src.rag.reranker import (
    rerank_documents
)


def get_vector_store():
    """
    Load the existing travel vector store.
    """

    embedding_model = (
        get_embedding_model()
    )

    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embedding_model,
        persist_directory=str(
            VECTOR_STORE_DIR
        )
    )


def detect_city(
    question: str
):
    """
    Detect a supported city from
    the user question.
    """

    question = question.lower()

    for city in SUPPORTED_CITIES:

        if city.lower() in question:
            return city

    return None


def retrieve_candidates(
    question: str,
    k: int
):
    """
    Retrieve candidate documents from
    Chroma before optional reranking.
    """

    vector_store = (
        get_vector_store()
    )

    city = detect_city(
        question
    )

    if city:

        documents = (
            vector_store.similarity_search(
                query=question,
                k=k,
                filter={
                    "city": city
                }
            )
        )

    else:

        documents = (
            vector_store.similarity_search(
                query=question,
                k=k
            )
        )

    return documents


def retrieve_documents(
    question: str
):
    """
    Retrieve travel documents.

    If reranking is enabled:
        Chroma Top N
        -> local reranker
        -> final Top K

    Otherwise:
        Chroma Top K only
    """

    # =====================================================
    # Vector search only
    # =====================================================

    if not USE_RERANKER:

        return retrieve_candidates(
            question=question,
            k=RETRIEVAL_K
        )

    # =====================================================
    # Stage 1: high-recall retrieval
    # =====================================================

    candidates = retrieve_candidates(
        question=question,
        k=RERANK_CANDIDATE_K
    )

    # =====================================================
    # Stage 2: reranking
    # =====================================================

    reranked_results = (
        rerank_documents(
            question=question,
            documents=candidates,
            top_k=RETRIEVAL_K
        )
    )

    # Keep the same return format
    # as the old retriever.
    documents = [
        document
        for document, score
        in reranked_results
    ]

    return documents


def retrieve_context(
    question: str
):
    """
    Return travel knowledge context
    for the LangGraph RAG service.
    """

    documents = retrieve_documents(
        question
    )

    results = []

    for document in documents:

        results.append(
            {
                "content": (
                    document.page_content
                ),

                "source": (
                    document.metadata.get(
                        "source",
                        "unknown"
                    )
                )
            }
        )

    return results