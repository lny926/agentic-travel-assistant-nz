from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings

from src.config import (
    EMBEDDING_PROVIDER,
    HF_EMBEDDING_MODEL,
    OLLAMA_EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
)


def get_embedding_model():

    if EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddings(
            model=OLLAMA_EMBEDDING_MODEL,
            base_url=OLLAMA_BASE_URL,
        )

    return HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        },
    )