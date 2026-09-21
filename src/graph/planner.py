import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.services.llm import get_llm
from src.graph.state import TravelState


llm = get_llm()


VALID_SERVICES = {
    "rag",
    "weather",
    "places",
    "analytics",
    "general"
}


VALID_PLACE_TYPES = {
    "restaurant",
    "attraction",
    "both"
}


VALID_ANALYTICS_OPERATIONS = {
    "total",
    "compare",
    "rank",
    "top",
    "trend"
}


def clean_json_response(content: str) -> str:
    content = content.strip()

    if content.startswith("```"):
        content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    return content


def plan_request(
    question: str,
    conversation_history: str = ""
):
    today = datetime.now(
        ZoneInfo("Pacific/Auckland")
    ).date()

    tomorrow = today + timedelta(days=1)

    day_after_tomorrow = (
            today + timedelta(days=2)
    )

    next_week_start = (
            today + timedelta(days=7)
    )

    next_week_end = (
            next_week_start
            + timedelta(days=6)
    )

    history_text = (
        conversation_history.strip()
        if conversation_history.strip()
        else "No previous conversation."
    )

    prompt = f"""
You are the planning component of a New Zealand travel assistant.

Your job is to understand the user's CURRENT request, use previous
conversation context when necessary, extract structured information,
and decide which services are required.

Today's date in New Zealand is:
{today}

Conversation context rules:

- The conversation history may contain previous user requests and
  assistant responses.

- Use conversation history when the current request contains omitted
  or relative information.

- Examples of follow-up expressions include:
  "there"
  "that city"
  "what about tomorrow?"
  "what about the day after?"
  "and restaurants?"
  "how about attractions?"
  "what about the weather?"

- If the current request refers to a previously discussed destination,
  reuse that destination when appropriate.

- If the current request refers to a previously discussed date,
  resolve the new date relative to that previous date when appropriate.

- If the current request is a follow-up to a previous weather question,
  you may reuse the previous destination and weather intent.

- If the current request asks for restaurants or attractions "there",
  reuse the previously discussed destination.

- The CURRENT user request always has priority over conversation history.

- If the current request explicitly provides a new destination, date,
  cuisine, region, or other value, use the new value instead of the
  previous one.

- Do NOT automatically repeat services from previous turns.
  Select only the services needed for the CURRENT request.

- Do NOT carry analytics filters, cuisine, place type, or other
  constraints into a new request unless the user clearly refers to
  them or they are needed to resolve the follow-up.

- Conversation history is context, not a new request.

Available services:

general
- Stable general knowledge
- Geography
- Where a suburb, city, region, or landmark is located
- General definitions
- Stable facts that do not require live data
- Questions that can be answered from general world knowledge

rag
- Curated travel-reference knowledge
- Destination travel guidance from the local knowledge base
- Travel advice contained in the reference material
- Transport information contained in the reference material
- Destination-specific information that should come from the
  local travel documents

weather
- Actual current or future weather conditions
- Weather forecasts for a real date or time period
- Weather-based planning when the user wants actual forecast data

- Do NOT select weather when the user only describes a
  hypothetical condition such as:
  "on a rainy day"
  "if it rains"
  "when the weather is bad"
  "on a sunny day"

  unless the user also asks about an actual date or forecast.

places
- Restaurants
- Attractions
- Museums
- Viewpoints
- Places to eat
- Places to visit
- Things to do that require real place search

analytics
- Tourism statistics
- Visitor spending
- Tourism trends
- Regional tourism comparisons


You may select MULTIPLE services.

Do not force the request into only one service.


Extract ALL of the following fields:

destination
origin

start_date
end_date

duration_days
budget
interests

regions

services

place_type
cuisine

analytics_operation
analytics_start_date
analytics_end_date
visitor_type
visitor_origin
product
top_n


Rules:

1. destination is the user's travel destination.

2. origin is where the traveller is travelling from.

3. destination and origin should use standard English place names.

4. start_date and end_date refer to the TRIP or WEATHER period.

5. analytics_start_date and analytics_end_date refer ONLY to the
   tourism analytics reporting period.

6. Never overwrite trip/weather dates with analytics dates.

7. Dates must use YYYY-MM-DD format.

8. Resolve relative dates using today's date.

9. If a value is unknown, return null.

10. interests must always be a JSON list.

11. regions must always be a JSON list.

12. services must always be a JSON list.

13. services may contain only:
    general
    rag
    weather
    places
    analytics

14. place_type may only be:
    restaurant
    attraction
    both
    null

15. If the user asks for restaurants, food, dining or places to eat:
    place_type = restaurant

16. If the user asks for attractions, sightseeing, museums,
    viewpoints or places to visit:
    place_type = attraction

17. If both restaurants and attractions are requested:
    place_type = both

18. cuisine should contain a lowercase cuisine type when the user
    explicitly requests a cuisine.

Examples:
Chinese food -> "chinese"
Italian food -> "italian"
Japanese food -> "japanese"

Otherwise cuisine = null.

19. If the user asks for recommendations based on ACTUAL
    current or future weather, select weather together with
    the other required service when appropriate.

    Do NOT select weather only because the user describes
    a hypothetical weather condition.

    Example:
    "What should a family do in Auckland on a rainy day?"
    -> ["rag"]

    "What should a family do in Auckland if it rains tomorrow?"
    -> ["weather", "rag"]

20. If the user is planning a future trip and trip dates are known
    or can be resolved, weather is usually relevant.

    For example:
    "I'm planning a trip to Queenstown next week. What should I know?"
    should normally select:
    ["rag", "weather"]

    Do not require the user to explicitly say the word "weather"
    when weather is clearly useful for a dated future trip.

    Do not automatically select places unless the user asks for
    restaurants, attractions, things to do, or place recommendations.

21. Do not select analytics unless tourism statistics or tourism
    spending data are requested.

22. Do not select services simply because they exist.


Analytics rules:

23. analytics_operation may only be:
    total
    compare
    rank
    top
    trend
    null

24. Use "total" when the user asks how much was spent in a region
    or by a visitor group.

25. Use "compare" when the user asks to compare specific regions.

26. Use "rank" when the user asks to rank regions.

27. Use "top" when the user asks for the top N regions.

28. Use "trend" when the user asks how tourism spending changes
    over time.

29. For analytics queries, put the analysed regions in "regions".

30. Do not combine multiple analytics regions into destination.

31. If analytics concern the same city as the user's trip:
    destination may contain the travel destination
    AND regions may contain the analytics region.

32. visitor_type should be exactly:
    "International"
    "New Zealand"
    null

33. visitor_origin is the visitor's origin market or country,
    such as "Australia".

34. Do NOT confuse visitor_origin with the traveller's trip origin.

35. product should use the closest matching MRTE category when
    explicitly requested.

General service rules:

36. Use "general" for stable, general-knowledge questions
that do not require live data or the local knowledge base.

Examples:
- "Which part of Auckland is Botany in?"
- "Is Queenstown in the South Island?"
- "What is Auckland known for?"
- "What is the difference between the North Island and South Island?"

Do NOT use "rag" only because a question mentions
Auckland or Queenstown.

Use "rag" when the user asks for information that
should come from the travel knowledge base or when
destination-specific reference material is useful.

Do NOT use "general" for information that may change,
such as:
- opening hours
- current prices
- weather
- restaurant availability
- current events

Available MRTE product categories include:

Accommodation
Cultural and recreational services
Food and beverage serving services
Other passenger transport
Retail sales - alcohol, food, and beverages
Retail sales - fuel and other automotive products
Retail sales - other

36. top_n should contain an integer only when required by a top-N
    request. Otherwise return null.


Example 1:

User:
What will the weather be tomorrow in Auckland?

Output:
{{
    "destination": "Auckland",
    "origin": null,
    "start_date": "{tomorrow}",
    "end_date": "{tomorrow}",
    "duration_days": null,
    "budget": null,
    "interests": [],
    "regions": [],
    "services": ["weather"],
    "place_type": null,
    "cuisine": null,
    "analytics_operation": null,
    "analytics_start_date": null,
    "analytics_end_date": null,
    "visitor_type": null,
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}


Example 2:

User:
Recommend Chinese restaurants in Auckland.

Output:
{{
    "destination": "Auckland",
    "origin": null,
    "start_date": null,
    "end_date": null,
    "duration_days": null,
    "budget": null,
    "interests": ["Chinese food"],
    "regions": [],
    "services": ["places"],
    "place_type": "restaurant",
    "cuisine": "chinese",
    "analytics_operation": null,
    "analytics_start_date": null,
    "analytics_end_date": null,
    "visitor_type": null,
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}


Example 3:

User:
Compare tourism spending between Auckland and Otago in July 2026.

Output:
{{
    "destination": null,
    "origin": null,
    "start_date": null,
    "end_date": null,
    "duration_days": null,
    "budget": null,
    "interests": [],
    "regions": ["Auckland", "Otago"],
    "services": ["analytics"],
    "place_type": null,
    "cuisine": null,
    "analytics_operation": "compare",
    "analytics_start_date": "2026-07-01",
    "analytics_end_date": "2026-07-31",
    "visitor_type": null,
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}


Example 4:

User:
How much did international visitors spend in Auckland in July 2026?

Output:
{{
    "destination": null,
    "origin": null,
    "start_date": null,
    "end_date": null,
    "duration_days": null,
    "budget": null,
    "interests": [],
    "regions": ["Auckland"],
    "services": ["analytics"],
    "place_type": null,
    "cuisine": null,
    "analytics_operation": "total",
    "analytics_start_date": "2026-07-01",
    "analytics_end_date": "2026-07-31",
    "visitor_type": "International",
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}


Example 5:

User:
I'm planning a trip to Auckland next week. Check the weather,
recommend attractions and restaurants, and show Auckland tourism
spending in July 2026.

Output:
{{
    "destination": "Auckland",
    "origin": null,
    "start_date": "{next_week_start}",
    "end_date": "{next_week_end}",
    "duration_days": 7,
    "budget": null,
    "interests": [],
    "regions": ["Auckland"],
    "services": ["rag", "weather", "places", "analytics"],
    "place_type": "both",
    "cuisine": null,
    "analytics_operation": "total",
    "analytics_start_date": "2026-07-01",
    "analytics_end_date": "2026-07-31",
    "visitor_type": null,
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}

Example 6:

Conversation history:
User:
What will the weather be tomorrow in Auckland?

Assistant:
The Auckland weather forecast for {tomorrow} is available.

Current user request:
What about the day after?

Output:
{{
    "destination": "Auckland",
    "origin": null,
    "start_date": "{day_after_tomorrow}",
    "end_date": "{day_after_tomorrow}",
    "duration_days": null,
    "budget": null,
    "interests": [],
    "regions": [],
    "services": ["weather"],
    "place_type": null,
    "cuisine": null,
    "analytics_operation": null,
    "analytics_start_date": null,
    "analytics_end_date": null,
    "visitor_type": null,
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}

Example 7:

Conversation history:
User:
What is the weather in Auckland tomorrow?

Assistant:
The forecast for Auckland tomorrow is available.

Current user request:
Can you recommend some restaurants there?

Output:
{{
    "destination": "Auckland",
    "origin": null,
    "start_date": null,
    "end_date": null,
    "duration_days": null,
    "budget": null,
    "interests": [],
    "regions": [],
    "services": ["places"],
    "place_type": "restaurant",
    "cuisine": null,
    "analytics_operation": null,
    "analytics_start_date": null,
    "analytics_end_date": null,
    "visitor_type": null,
    "visitor_origin": null,
    "product": null,
    "top_n": null
}}

Return ONLY valid JSON.

Conversation history:
{history_text}

Current user request:
{question}

Important:
The current user request is the request that must be planned.
Conversation history exists only to resolve context and references.

Return ONLY valid JSON.
"""

    print("\n[LLM CALL] Planner")
    response = llm.invoke(prompt)

    content = clean_json_response(
        response.content
    )

    try:
        plan = json.loads(content)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Planner returned invalid JSON: {content}"
        ) from error

    # -------------------------
    # Validate services
    # -------------------------

    services = plan.get("services")

    if not isinstance(services, list):
        services = []

    plan["services"] = [
        str(service).lower()
        for service in services
        if str(service).lower()
        in VALID_SERVICES
    ]

    # -------------------------
    # Validate interests
    # -------------------------

    if not isinstance(
        plan.get("interests"),
        list
    ):
        plan["interests"] = []

    # -------------------------
    # Validate regions
    # -------------------------

    if not isinstance(
        plan.get("regions"),
        list
    ):
        plan["regions"] = []

    plan["regions"] = [
        str(region).strip()
        for region in plan["regions"]
        if str(region).strip()
    ]

    # -------------------------
    # Validate place type
    # -------------------------

    place_type = plan.get(
        "place_type"
    )

    if isinstance(place_type, str):
        place_type = (
            place_type
            .strip()
            .lower()
        )

    if place_type not in VALID_PLACE_TYPES:
        place_type = None

    plan["place_type"] = place_type

    # -------------------------
    # Validate cuisine
    # -------------------------

    cuisine = plan.get("cuisine")

    if isinstance(cuisine, str):
        cuisine = cuisine.strip().lower()

        if cuisine in [
            "",
            "null",
            "none"
        ]:
            cuisine = None

    else:
        cuisine = None

    plan["cuisine"] = cuisine

    # -------------------------
    # Validate analytics operation
    # -------------------------

    analytics_operation = plan.get(
        "analytics_operation"
    )

    if isinstance(
        analytics_operation,
        str
    ):
        analytics_operation = (
            analytics_operation
            .strip()
            .lower()
        )

    if (
        analytics_operation
        not in VALID_ANALYTICS_OPERATIONS
    ):
        analytics_operation = None

    plan["analytics_operation"] = (
        analytics_operation
    )

    # -------------------------
    # Validate visitor type
    # -------------------------

    visitor_type = plan.get(
        "visitor_type"
    )

    if isinstance(visitor_type, str):
        normalized = (
            visitor_type
            .strip()
            .casefold()
        )

        visitor_type_map = {
            "international": (
                "International"
            ),
            "new zealand": (
                "New Zealand"
            ),
            "nz": (
                "New Zealand"
            ),
            "domestic": (
                "New Zealand"
            )
        }

        visitor_type = (
            visitor_type_map.get(
                normalized
            )
        )

    else:
        visitor_type = None

    plan["visitor_type"] = (
        visitor_type
    )

    # -------------------------
    # Validate visitor origin
    # -------------------------

    visitor_origin = plan.get(
        "visitor_origin"
    )

    if isinstance(visitor_origin, str):
        visitor_origin = (
            visitor_origin.strip()
            or None
        )
    else:
        visitor_origin = None

    plan["visitor_origin"] = (
        visitor_origin
    )

    # -------------------------
    # Validate product
    # -------------------------

    product = plan.get("product")

    if isinstance(product, str):
        product = (
            product.strip()
            or None
        )
    else:
        product = None

    plan["product"] = product

    # -------------------------
    # Validate top_n
    # -------------------------

    top_n = plan.get("top_n")

    if (
        isinstance(top_n, str)
        and top_n.isdigit()
    ):
        top_n = int(top_n)

    if (
        not isinstance(top_n, int)
        or isinstance(top_n, bool)
        or top_n <= 0
    ):
        top_n = None

    plan["top_n"] = top_n

    # -------------------------
    # Service guardrails
    # -------------------------

    question_lower = question.lower()

    direct_weather_keywords = [
        "weather",
        "forecast",
        "temperature",
        "will it rain",
        "is it raining",
        "will it snow",
        "is it snowing"
    ]

    weather_condition_keywords = [
        "rain",
        "rainy",
        "raining",
        "snow",
        "snowy",
        "snowing"
    ]

    hypothetical_weather_phrases = [
        "rainy day",
        "if it rains",
        "if it is raining",
        "if it's raining",
        "when it rains",
        "bad weather",
        "sunny day",
        "if it snows",
        "when it snows"
    ]

    time_keywords = [
        "today",
        "tomorrow",
        "tonight",
        "day after tomorrow",
        "this weekend",
        "next week",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"
    ]

    restaurant_keywords = [
        "restaurant",
        "restaurants",
        "where to eat",
        "place to eat",
        "places to eat",
        "food options",
        "dining"
    ]

    attraction_keywords = [
        "attraction",
        "attractions",
        "place to go",
        "places to go",
        "where to go",
        "things to do",
        "sightseeing",
        "museum",
        "museums",
        "viewpoint",
        "viewpoints"
    ]

    analytics_keywords = [
        "tourism spending",
        "visitor spending",
        "tourism statistics",
        "tourism trend",
        "tourism trends",
        "rank regions",
        "top regions"
    ]

    has_hypothetical_weather = any(
        phrase in question_lower
        for phrase in hypothetical_weather_phrases
    )

    has_weather_time = (
            bool(plan.get("start_date"))
            or any(
        keyword in question_lower
        for keyword in time_keywords
    )
    )

    has_direct_weather_request = any(
        keyword in question_lower
        for keyword in direct_weather_keywords
    )

    has_weather_condition = any(
        keyword in question_lower
        for keyword in weather_condition_keywords
    )

    # Hypothetical weather condition only.
    # Example:
    # "What should I do on a rainy day?"
    if (
            has_hypothetical_weather
            and not has_weather_time
    ):

        plan["services"] = [
            service
            for service in plan["services"]
            if service != "weather"
        ]


    # Actual weather request.
    else:

        if (
                has_direct_weather_request
                or (
                has_weather_condition
                and has_weather_time
        )
        ):

            if "weather" not in plan["services"]:
                plan["services"].append(
                    "weather"
                )

    has_restaurant_request = any(
        keyword in question_lower
        for keyword in restaurant_keywords
    )

    has_attraction_request = any(
        keyword in question_lower
        for keyword in attraction_keywords
    )

    if (
        has_restaurant_request
        or has_attraction_request
    ):
        if "places" not in plan["services"]:
            plan["services"].append(
                "places"
            )

    if (
        has_restaurant_request
        and has_attraction_request
    ):
        plan["place_type"] = "both"

    elif has_restaurant_request:
        plan["place_type"] = (
            "restaurant"
        )

    elif has_attraction_request:
        plan["place_type"] = (
            "attraction"
        )

    if any(
        keyword in question_lower
        for keyword in analytics_keywords
    ):
        if "analytics" not in plan["services"]:
            plan["services"].append(
                "analytics"
            )

    # -------------------------
    # Future trip weather guardrail
    # -------------------------

    trip_keywords = [
        "trip",
        "travel",
        "travelling",
        "traveling",
        "visit",
        "visiting",
        "holiday",
        "vacation",
        "planning",

        "旅行",
        "旅游",
        "出行",
        "行程"
    ]

    has_trip_request = any(
        keyword in question_lower
        for keyword in trip_keywords
    )

    if (
            has_trip_request
            and plan.get("destination")
            and plan.get("start_date")
            and plan.get("end_date")
    ):
        try:
            trip_start = datetime.strptime(
                plan["start_date"],
                "%Y-%m-%d"
            ).date()

            trip_end = datetime.strptime(
                plan["end_date"],
                "%Y-%m-%d"
            ).date()

            forecast_limit = (
                    today + timedelta(days=15)
            )

            if (
                    today <= trip_start
                    and trip_end <= forecast_limit
            ):
                if (
                        "weather"
                        not in plan["services"]
                ):
                    plan["services"].append(
                        "weather"
                    )

        except ValueError:
            pass

    # -------------------------
    # Analytics operation fallback
    # -------------------------

    if (
        "analytics"
        in plan["services"]
        and not plan.get(
            "analytics_operation"
        )
    ):
        if "compare" in question_lower:
            plan[
                "analytics_operation"
            ] = "compare"

        elif "trend" in question_lower:
            plan[
                "analytics_operation"
            ] = "trend"

        elif "rank" in question_lower:
            plan[
                "analytics_operation"
            ] = "rank"

        elif (
            "top " in question_lower
            or "top-" in question_lower
        ):
            plan[
                "analytics_operation"
            ] = "top"

        else:
            plan[
                "analytics_operation"
            ] = "total"

    return plan


def planner_node(
    state: TravelState
):
    question = state[
        "question"
    ]

    conversation_history = (
        format_conversation_history(
            state.get(
                "messages",
                []
            )
        )
    )

    plan = plan_request(
        question=question,
        conversation_history=(
            conversation_history
        )
    )

    return {
        "destination": plan.get(
            "destination"
        ),

        "origin": plan.get(
            "origin"
        ),

        "start_date": plan.get(
            "start_date"
        ),

        "end_date": plan.get(
            "end_date"
        ),

        "duration_days": plan.get(
            "duration_days"
        ),

        "budget": plan.get(
            "budget"
        ),

        "interests": plan.get(
            "interests",
            []
        ),

        "regions": plan.get(
            "regions",
            []
        ),

        "services": plan.get(
            "services",
            []
        ),

        "place_type": plan.get(
            "place_type"
        ),

        "cuisine": plan.get(
            "cuisine"
        ),

        "analytics_operation": plan.get(
            "analytics_operation"
        ),

        "analytics_start_date": plan.get(
            "analytics_start_date"
        ),

        "analytics_end_date": plan.get(
            "analytics_end_date"
        ),

        "visitor_type": plan.get(
            "visitor_type"
        ),

        "visitor_origin": plan.get(
            "visitor_origin"
        ),

        "product": plan.get(
            "product"
        ),

        "top_n": plan.get(
            "top_n"
        )
    }

def format_conversation_history(
    messages,
    max_messages: int = 6
):
    if not messages:
        return "No previous conversation."

    # Exclude the current user message
    previous_messages = (
        messages[:-1]
    )

    if not previous_messages:
        return "No previous conversation."

    previous_messages = (
        previous_messages[
            -max_messages:
        ]
    )

    history = []

    for message in previous_messages:
        message_type = getattr(
            message,
            "type",
            ""
        )

        content = str(
            getattr(
                message,
                "content",
                ""
            )
        )

        # Avoid sending extremely long
        # previous answers to the planner
        if len(content) > 1500:
            content = (
                content[:1500]
                + "..."
            )

        if message_type == "human":
            role = "User"

        elif message_type == "ai":
            role = "Assistant"

        else:
            role = "Message"

        history.append(
            f"{role}: {content}"
        )

    return "\n".join(
        history
    )