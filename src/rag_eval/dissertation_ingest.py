import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from src.config import (
    DISSERTATION_SOURCE_DIR,
    DISSERTATION_VECTOR_STORE_DIR,
    DISSERTATION_CHROMA_COLLECTION,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

from src.services.embeddings import (
    get_embedding_model
)


def load_dissertation():
    """
    Load dissertation PDF files only.

    This function is completely separate
    from the travel knowledge base.
    """

    documents = []

    pdf_files = list(
        DISSERTATION_SOURCE_DIR.glob(
            "*.pdf"
        )
    )

    if not pdf_files:
        raise ValueError(
            "No dissertation PDF found in "
            f"{DISSERTATION_SOURCE_DIR}"
        )

    for pdf_path in pdf_files:

        loader = PyPDFLoader(
            str(pdf_path)
        )

        pages = loader.load()

        for page in pages:

            page.metadata[
                "source"
            ] = pdf_path.name

            page.metadata[
                "knowledge_base"
            ] = "dissertation"

        documents.extend(
            pages
        )

    return documents


def build_dissertation_vector_store():
    """
    Build an isolated vector store for
    dissertation RAG evaluation.

    This does NOT modify the travel
    vector database.
    """

    documents = (
        load_dissertation()
    )

    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                " ",
                ""
            ]
        )
    )

    chunks = splitter.split_documents(
        documents
    )

    embedding_model = (
        get_embedding_model()
    )

    # IMPORTANT:
    # Only remove the dissertation DB.
    # Never touch VECTOR_STORE_DIR.
    if (
        DISSERTATION_VECTOR_STORE_DIR
        .exists()
    ):
        shutil.rmtree(
            DISSERTATION_VECTOR_STORE_DIR
        )

    DISSERTATION_VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=str(
            DISSERTATION_VECTOR_STORE_DIR
        ),
        collection_name=(
            DISSERTATION_CHROMA_COLLECTION
        )
    )

    print(
        "Dissertation RAG database built."
    )

    print(
        f"Loaded pages: "
        f"{len(documents)}"
    )

    print(
        f"Created chunks: "
        f"{len(chunks)}"
    )

    print(
        "Vector store:"
    )

    print(
        DISSERTATION_VECTOR_STORE_DIR
    )


if __name__ == "__main__":

    build_dissertation_vector_store()