from typing import (
    Annotated,
    TypedDict
)

from langchain_core.messages import (
    BaseMessage
)

from langgraph.graph.message import (
    add_messages
)


class TravelState(
    TypedDict,
    total=False
):
    # Conversation
    question: str

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]

    # Trip information
    destination: str | None
    origin: str | None
    start_date: str | None
    end_date: str | None
    duration_days: int | None
    budget: float | None
    interests: list[str]

    # Requested services
    services: list[str]

    # Places
    place_type: str | None
    cuisine: str | None

    # Analytics
    regions: list[str]
    analytics_operation: str | None
    analytics_start_date: str | None
    analytics_end_date: str | None
    visitor_type: str | None
    visitor_origin: str | None
    product: str | None
    top_n: int | None

    # Tool results
    weather_result: dict | None
    places_result: dict | None
    places_errors: dict | None

    rag_result: (
        list[dict]
        | dict
        | None
    )

    analytics_result: dict | None

    # Final response
    answer: str
    sources: list[str]