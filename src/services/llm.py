import os

from langchain_openai import ChatOpenAI

from src.config import (
    LLM_MODEL,
    DEEPSEEK_BASE_URL
)


def get_llm():
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set.")

    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )