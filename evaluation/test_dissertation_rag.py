from src.rag_eval.dissertation_retriever import (
    retrieve_dissertation_context,
    retrieve_dissertation_context_reranked
)


question = (
    "Which dispatching strategies "
    "were evaluated in the final study?"
)


print(
    "\n"
    "========================================"
)

print(
    "QUESTION"
)

print(
    "========================================"
)

print(
    question
)


# =========================================================
# Vector-only retrieval
# =========================================================

print(
    "\n\n"
    "========================================"
)

print(
    "VECTOR SEARCH ONLY"
)

print(
    "========================================"
)


vector_results = (
    retrieve_dissertation_context(
        question
    )
)


for index, result in enumerate(
    vector_results,
    start=1
):

    print(
        f"\n----- Result {index} -----"
    )

    print(
        "Page:",
        result["page"]
    )

    print()

    print(
        result["content"][:600]
    )


# =========================================================
# Vector search + rerank
# =========================================================

print(
    "\n\n"
    "========================================"
)

print(
    "VECTOR SEARCH + RERANK"
)

print(
    "========================================"
)


reranked_results = (
    retrieve_dissertation_context_reranked(
        question
    )
)


for index, result in enumerate(
    reranked_results,
    start=1
):

    print(
        f"\n----- Result {index} -----"
    )

    print(
        "Page:",
        result["page"]
    )

    print(
        "Rerank score:",
        round(
            result["rerank_score"],
            4
        )
    )

    print()

    print(
        result["content"][:600]
    )