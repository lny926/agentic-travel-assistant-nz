from langchain_chroma import Chroma

from src.config import (
    DISSERTATION_VECTOR_STORE_DIR,
    DISSERTATION_CHROMA_COLLECTION,
    DISSERTATION_RETRIEVAL_K
)

from src.services.embeddings import (
    get_embedding_model
)

from src.rag_eval.reranker import (
    rerank_documents
)


# Number of candidates retrieved
# before reranking.
INITIAL_RETRIEVAL_K = 12


def get_dissertation_vector_store():
    """
    Load the isolated dissertation
    Chroma database.
    """

    embedding_model = (
        get_embedding_model()
    )

    return Chroma(
        collection_name=(
            DISSERTATION_CHROMA_COLLECTION
        ),
        embedding_function=(
            embedding_model
        ),
        persist_directory=str(
            DISSERTATION_VECTOR_STORE_DIR
        )
    )


# =========================================================
# Original vector retrieval
# =========================================================

def retrieve_dissertation_documents(
    question: str
):
    """
    Original vector-only retrieval.

    This is kept for comparison with
    the reranked version.
    """

    vector_store = (
        get_dissertation_vector_store()
    )

    documents = (
        vector_store.similarity_search(
            query=question,
            k=DISSERTATION_RETRIEVAL_K
        )
    )

    return documents


# =========================================================
# Reranked retrieval
# =========================================================

def retrieve_dissertation_documents_reranked(
    question: str
):
    """
    Retrieve more candidates from Chroma,
    then rerank them locally.
    """

    vector_store = (
        get_dissertation_vector_store()
    )

    # Stage 1:
    # High-recall vector search
    candidates = (
        vector_store.similarity_search(
            query=question,
            k=INITIAL_RETRIEVAL_K
        )
    )

    # Stage 2:
    # Cross-encoder reranking
    reranked_results = (
        rerank_documents(
            question=question,
            documents=candidates,
            top_k=DISSERTATION_RETRIEVAL_K
        )
    )

    return reranked_results


# =========================================================
# Original context
# =========================================================

def retrieve_dissertation_context(
    question: str
):
    """
    Original vector-only retrieval.
    """

    documents = (
        retrieve_dissertation_documents(
            question
        )
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
                ),

                "page": (
                    document.metadata.get(
                        "page"
                    )
                ),

                "knowledge_base": (
                    "dissertation"
                )
            }
        )

    return results


# =========================================================
# Reranked context
# =========================================================

def retrieve_dissertation_context_reranked(
    question: str
):
    """
    Vector retrieval + local reranking.
    """

    reranked_documents = (
        retrieve_dissertation_documents_reranked(
            question
        )
    )

    results = []

    for document, rerank_score in (
        reranked_documents
    ):

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
                ),

                "page": (
                    document.metadata.get(
                        "page"
                    )
                ),

                "rerank_score": (
                    rerank_score
                ),

                "knowledge_base": (
                    "dissertation"
                )
            }
        )

    return results