import shutil

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from src.config import (
    RAW_DATA_DIR,
    VECTOR_STORE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHROMA_COLLECTION
)

from src.services.embeddings import get_embedding_model


def load_documents():
    documents = []

    for file_path in RAW_DATA_DIR.glob("*.md"):

        content = file_path.read_text(
            encoding="utf-8"
        )

        document = Document(
            page_content=content,
            metadata={
                "source": file_path.name,
                "city": file_path.stem
            }
        )

        documents.append(document)

    return documents


def build_vector_store():
    documents = load_documents()

    if not documents:
        raise ValueError(
            f"No documents found in {RAW_DATA_DIR}"
        )

    # Split documents into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(documents)

    # Get Ollama embedding model
    embedding_model = get_embedding_model()

    # Remove old vector database when rebuilding
    if VECTOR_STORE_DIR.exists():
        shutil.rmtree(VECTOR_STORE_DIR)

    # Create Chroma vector database
    Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=str(VECTOR_STORE_DIR),
        collection_name=CHROMA_COLLECTION
    )

    print(f"Loaded documents: {len(documents)}")
    print(f"Created chunks: {len(chunks)}")
    print("Vector store created successfully.")


if __name__ == "__main__":
    build_vector_store()