import json
import time

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from langchain_core.messages import (
    AIMessage
)

from src.graph.state import TravelState

from src.services.llm import get_llm

from src.rag.retriever import (
    retrieve_context
)

from src.tools.weather import (
    get_weather_range
)

from src.tools.places import (
    get_place_coordinates,
    search_restaurants_by_coordinates,
    search_attractions_by_coordinates
)

from src.tools.analytics import (
    run_analytics
)


llm = get_llm()


def execute_weather_service(
    state: TravelState
):
    start_time = time.perf_counter()

    destination = state.get(
        "destination"
    )

    start_date = state.get(
        "start_date"
    )

    end_date = state.get(
        "end_date"
    )

    result = {}

    if not (
        destination
        and start_date
        and end_date
    ):
        result["weather_result"] = {
            "error": (
                "Missing destination "
                "or date information."
            )
        }

        return result

    try:
        weather_data = get_weather_range(
            destination,
            start_date,
            end_date
        )

        result[
            "weather_result"
        ] = weather_data

        result["sources"] = [
            "Open-Meteo"
        ]

    except Exception as error:
        result["weather_result"] = {
            "error": str(error)
        }

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] Weather: "
        f"{elapsed:.2f}s"
    )

    return result


def execute_places_service(
    state: TravelState
):
    start_time = time.perf_counter()

    destination = state.get(
        "destination"
    )

    place_type = state.get(
        "place_type"
    )

    cuisine = state.get(
        "cuisine"
    )

    result = {}

    if not destination:
        result["places_result"] = {
            "error": "Missing destination."
        }

        return result

    # Resolve city coordinates once
    try:
        location_start = (
            time.perf_counter()
        )

        location = get_place_coordinates(
            destination
        )

        latitude = location[
            "latitude"
        ]

        longitude = location[
            "longitude"
        ]

        location_elapsed = (
            time.perf_counter()
            - location_start
        )

        print(
            f"[TIMING] Places geocoding: "
            f"{location_elapsed:.2f}s"
        )

    except Exception as error:
        result["places_result"] = {
            "error": (
                "Could not resolve "
                f"destination: {error}"
            )
        }

        return result

    places_data = {}
    places_errors = {}

    tasks = {}

    if place_type in [
        "restaurant",
        "both"
    ]:
        tasks[
            "restaurants"
        ] = True

    if place_type in [
        "attraction",
        "both"
    ]:
        tasks[
            "attractions"
        ] = True

    if not tasks:
        result["places_result"] = {
            "error": (
                "Missing or invalid "
                "place type."
            )
        }

        return result

    # Restaurant and attraction searches
    # run in parallel
    with ThreadPoolExecutor(
        max_workers=len(tasks)
    ) as executor:

        futures = {}

        if "restaurants" in tasks:
            future = executor.submit(
                search_restaurants_by_coordinates,
                latitude,
                longitude,
                cuisine
            )

            futures[
                future
            ] = "restaurants"

        if "attractions" in tasks:
            future = executor.submit(
                search_attractions_by_coordinates,
                latitude,
                longitude
            )

            futures[
                future
            ] = "attractions"

        for future in as_completed(
            futures
        ):
            service_name = futures[
                future
            ]

            try:
                data = future.result()

                places_data[
                    service_name
                ] = data

            except Exception as error:
                places_errors[
                    service_name
                ] = str(error)

    if places_data:
        result[
            "places_result"
        ] = places_data

        result["sources"] = [
            "OpenStreetMap"
        ]

        if places_errors:
            result[
                "places_errors"
            ] = places_errors

    elif places_errors:
        result["places_result"] = {
            "error": places_errors
        }

    else:
        result["places_result"] = {
            "error": (
                "No place data "
                "was returned."
            )
        }

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] Places: "
        f"{elapsed:.2f}s"
    )

    return result


def execute_rag_service(
    state: TravelState
):
    start_time = time.perf_counter()

    result = {}

    try:
        rag_data = retrieve_context(
            state["question"]
        )

        result[
            "rag_result"
        ] = rag_data

        sources = []

        for item in rag_data:
            source = item.get(
                "source"
            )

            if (
                source
                and source not in sources
            ):
                sources.append(
                    source
                )

        if sources:
            result[
                "sources"
            ] = sources

    except Exception as error:
        result["rag_result"] = {
            "error": str(error)
        }

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] RAG: "
        f"{elapsed:.2f}s"
    )

    return result


def execute_analytics_service(
    state: TravelState
):
    start_time = time.perf_counter()

    result = {}

    try:
        operation = state.get(
            "analytics_operation"
        )

        if not operation:
            raise ValueError(
                "Missing analytics operation."
            )

        analytics_data = run_analytics(
            operation=operation,

            regions=state.get(
                "regions",
                []
            ),

            start_date=state.get(
                "analytics_start_date"
            ),

            end_date=state.get(
                "analytics_end_date"
            ),

            visitor_type=state.get(
                "visitor_type"
            ),

            visitor_origin=state.get(
                "visitor_origin"
            ),

            product=state.get(
                "product"
            ),

            top_n=state.get(
                "top_n"
            )
        )

        result[
            "analytics_result"
        ] = analytics_data

        result["sources"] = [
            (
                "MBIE Monthly Regional "
                "Tourism Estimates (MRTE)"
            )
        ]

    except Exception as error:
        result[
            "analytics_result"
        ] = {
            "error": str(error)
        }

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] Analytics: "
        f"{elapsed:.2f}s"
    )

    return result


def execute_services_node(
    state: TravelState
):
    total_start = time.perf_counter()

    services = state.get(
        "services",
        []
    )

    result = {
        "sources": [],

        "weather_result": None,

        "places_result": None,

        "places_errors": None,

        "rag_result": None,

        "analytics_result": None
    }

    service_functions = {
        "weather": (
            execute_weather_service
        ),

        "places": (
            execute_places_service
        ),

        "rag": (
            execute_rag_service
        ),

        "analytics": (
            execute_analytics_service
        )
    }

    selected_services = [
        service
        for service in services
        if service in service_functions
    ]

    if not selected_services:
        return result

    # Run independent services in parallel
    with ThreadPoolExecutor(
        max_workers=len(
            selected_services
        )
    ) as executor:

        futures = {
            executor.submit(
                service_functions[
                    service
                ],
                state
            ): service

            for service
            in selected_services
        }

        for future in as_completed(
            futures
        ):
            service = futures[
                future
            ]

            try:
                service_result = (
                    future.result()
                )

            except Exception as error:
                service_result = {
                    f"{service}_result": {
                        "error": str(error)
                    }
                }

            # Merge service results
            for key, value in (
                service_result.items()
            ):
                if key == "sources":
                    for source in value:
                        if (
                            source
                            not in result[
                                "sources"
                            ]
                        ):
                            result[
                                "sources"
                            ].append(
                                source
                            )

                else:
                    result[
                        key
                    ] = value

    elapsed = (
        time.perf_counter()
        - total_start
    )

    print(
        f"[TIMING] All tools: "
        f"{elapsed:.2f}s"
    )

    return result


def final_synthesizer_node(
    state: TravelState
):
    question = state[
        "question"
    ]

    selected_services = state.get(
        "services",
        []
    )

    request_context = {
        "destination": state.get(
            "destination"
        ),
        "origin": state.get(
            "origin"
        ),
        "start_date": state.get(
            "start_date"
        ),
        "end_date": state.get(
            "end_date"
        ),
        "duration_days": state.get(
            "duration_days"
        ),
        "analytics_start_date": state.get(
            "analytics_start_date"
        ),
        "analytics_end_date": state.get(
            "analytics_end_date"
        ),
    }

    weather_result = state.get(
        "weather_result"
    )

    places_result = state.get(
        "places_result"
    )

    places_errors = state.get(
        "places_errors"
    )

    rag_result = state.get(
        "rag_result"
    )

    analytics_result = state.get(
        "analytics_result"
    )

    sources = state.get(
        "sources",
        []
    )

    tool_data = {
        "request_context": (
            request_context
        ),
        "weather": (
            weather_result
        ),
        "places": (
            places_result
        ),
        "places_errors": (
            places_errors
        ),
        "rag": (
            rag_result
        ),
        "analytics": (
            analytics_result
        )
    }

    prompt = f"""
You are a helpful New Zealand travel assistant.

Answer the user's current question using the selected services,
available information, and stable general knowledge when permitted
by the instructions below.

User question:
{question}

Selected services:
{json.dumps(
    selected_services,
    ensure_ascii=False
)}

Available information:
{json.dumps(
    tool_data,
    ensure_ascii=False,
    indent=2
)}

Instructions:

1. Answer every part of the user's CURRENT question.

2. When multiple information sources are available, combine them
   into a useful answer rather than treating them as unrelated
   sections when integration would be helpful.

3. Explain why a recommendation fits the user's situation when
   the available information supports that reasoning.

4. If weather information is available together with places,
   use the weather to evaluate which places may be more suitable.

5. Viewpoints may be more weather-dependent because visibility
   matters.

6. Grounding depends on the selected services:

   If "general" is included in selected_services:
   - You may use your own general knowledge to answer stable,
     non-time-sensitive factual questions.
   - General knowledge may be used for facts such as geography,
     well-known locations, general destination knowledge,
     definitions, and other stable information.
   - Do not use general knowledge to invent or guess information
     that may change over time.

   If "general" is NOT included in selected_services:
   - Ground factual claims in the available tool and reference data.
   - Do not introduce unsupported factual details.

7. Even when "general" is selected, do NOT rely on general knowledge
   for time-sensitive or frequently changing information, including:
   - current weather
   - opening hours
   - current prices
   - current availability
   - restaurant operating status
   - current events
   - temporary closures
   - live transport information

   For these questions, rely on the available current data.
   If reliable current data is unavailable, clearly say that the
   current information could not be confirmed.

8. Never infer characteristics of a place from its name.
   Do not assume that a place is:
   - indoor
   - sheltered
   - waterfront
   - family-friendly
   - scenic
   - free
   - expensive
   unless this information is explicitly provided or is a stable,
   well-established fact allowed under the "general" service.

9. An explicitly identified museum may generally be considered
   less visibility-dependent than a viewpoint, but do not claim
   that a specific location is indoor unless that information is
   available or it is an unambiguous, stable fact.

10. If the available place information is not detailed enough to
    evaluate suitability, clearly say so only when that limitation
    is relevant to the user's question.

11. Separate facts from recommendations.

    Recommendations may be reasoned from:
    - weather
    - explicit place types
    - retrieved travel knowledge
    - stable general knowledge when "general" is selected

    Do not introduce unsupported current or time-sensitive facts.

12. Do not mention missing information unless it is relevant to
    something the user actually asked for.

13. Retrieved travel-reference passages are reference material.
    Synthesize the useful information instead of copying passages
    verbatim.

14. Trip/weather dates and analytics reporting dates are separate.

15. Never use analytics_start_date or analytics_end_date to
    interpret the user's travel dates.

16. Treat start_date and end_date in request_context as the FINAL
    resolved trip/weather dates produced by the planner.

    If the user used a relative expression such as:
    - tomorrow
    - the day after
    - next week
    - then
    - that day

    DO NOT resolve or shift the date again.

    For example, if the current user asks "What about the day after?"
    and request_context.start_date is "2026-09-18", then answer for
    2026-09-18 directly. Do NOT interpret it as the day after
    2026-09-18.

17. Never mention internal implementation details such as:
    - RAG
    - tool results
    - APIs
    - vector databases
    - LangGraph
    - internal services
    - routing decisions

18. If a data source fails, describe the limitation naturally
    without exposing the internal implementation.

19. Do not say that a place is closed on days that are absent from
    its opening-hours data.

    Missing opening-hour information does not prove that the place
    is closed.

20. If the user did not request weather information, do not
    complain that weather data is unavailable or unnecessarily
    discuss missing weather data.

21. When weather data exists for the same date as
    request_context.start_date or end_date, treat that weather data
    as the answer to the user's resolved date request.

    Do not claim that weather data is missing merely because the
    original user wording used a relative date expression.

22. If the user asks a stable general-knowledge question and
    "general" is selected, answer it directly and naturally.

    Do not say:
    - "the available information does not contain this"
    - "the reference material does not mention this"
    - "I cannot determine this from the provided information"

    when the answer can reasonably be provided from stable general
    knowledge.

23. If both "general" and one or more data-backed services are
    selected, use general knowledge only to complement the supplied
    data.

    Current or time-sensitive facts from supplied data take priority
    over general knowledge.

24. Answer only the user's current request.

    Do not volunteer limitations about unrelated services.

    Examples:
    - If the user asks only about weather, do not mention missing
      place information.
    - If the user asks only about restaurants, do not mention
      missing weather information.
    - If the user asks only a general geography question, do not
      discuss missing RAG or place data.
"""

    print(
        "\n[LLM CALL] "
        "Final Synthesizer"
    )

    response = llm.invoke(
        prompt
    )

    return {
        "answer": response.content,
        "sources": sources,

        "messages": [
            AIMessage(
                content=response.content
            )
        ]
    }