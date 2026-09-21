import logging
import time
import requests

from src.config import (
    NOMINATIM_SEARCH_URL,
    OVERPASS_URLS,
    PLACES_SEARCH_RADIUS,
    PLACES_RESULT_LIMIT
)


HEADERS = {
    "User-Agent": "travel-ai-assistant/1.0",
    "Accept": "application/json",
}


logger = logging.getLogger(__name__)


def query_overpass(
    query: str,
    request_timeout: int = 12
):
    """
    Try multiple Overpass servers.

    If one server fails or times out,
    automatically try the next one.
    """

    last_error = None

    for url in OVERPASS_URLS:
        try:
            logger.debug(
                "Trying Overpass server: %s",
                url
            )

            request_start = time.perf_counter()

            response = requests.post(
                url,
                data={"data": query},
                headers=HEADERS,
                timeout=request_timeout
            )

            request_elapsed = (
                time.perf_counter()
                - request_start
            )

            logger.debug(
                "Overpass server %s finished in %.2fs",
                url,
                request_elapsed
            )

            if not response.ok:
                logger.debug(
                    "Overpass response: %s",
                    response.text[:1000]
                )

            response.raise_for_status()

            logger.debug(
                "Overpass request successful: %s",
                url
            )

            return response.json()

        except requests.RequestException as error:
            logger.warning(
                "Overpass failed: %s (%s)",
                url,
                error
            )

            last_error = error

    raise RuntimeError(
        f"All Overpass servers failed: {last_error}"
    )


def get_place_coordinates(
    city: str
):
    """
    Convert a city name to latitude and longitude.
    """

    params = {
        "q": f"{city}, New Zealand",
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "nz"
    }

    response = requests.get(
        NOMINATIM_SEARCH_URL,
        params=params,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError(
            f"Could not find location: {city}"
        )

    return {
        "name": city,
        "latitude": float(
            data[0]["lat"]
        ),
        "longitude": float(
            data[0]["lon"]
        )
    }


def search_restaurants_by_coordinates(
    latitude: float,
    longitude: float,
    cuisine: str | None = None
):
    """
    Search restaurants using coordinates.
    """

    start_time = time.perf_counter()

    if cuisine:
        cuisine_filter = (
            f'["cuisine"~"{cuisine}",i]'
        )
    else:
        cuisine_filter = ""

    query = f"""
    [out:json][timeout:10];

    nwr
      ["amenity"="restaurant"]
      ["name"]
      {cuisine_filter}
      (around:{PLACES_SEARCH_RADIUS},{latitude},{longitude});

    out tags center {PLACES_RESULT_LIMIT};
    """

    data = query_overpass(
        query,
        request_timeout=12
    )

    results = []
    seen_names = set()

    for element in data.get(
        "elements",
        []
    ):
        tags = element.get(
            "tags",
            {}
        )

        name = tags.get(
            "name"
        )

        if (
            not name
            or name in seen_names
        ):
            continue

        seen_names.add(
            name
        )

        results.append(
            {
                "name": name,
                "cuisine": tags.get(
                    "cuisine"
                ),
                "opening_hours": tags.get(
                    "opening_hours"
                ),
                "website": tags.get(
                    "website"
                ),
                "phone": tags.get(
                    "phone"
                )
            }
        )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] Restaurant search: "
        f"{elapsed:.2f}s"
    )

    return results


def search_attractions_by_coordinates(
    latitude: float,
    longitude: float
):
    """
    Search attractions using coordinates.
    """

    start_time = time.perf_counter()

    query = f"""
    [out:json][timeout:10];

    node
      ["tourism"~"^(attraction|museum|viewpoint)$"]
      ["name"]
      (around:2000,{latitude},{longitude});

    out tags {PLACES_RESULT_LIMIT};
    """

    data = query_overpass(
        query,
        request_timeout=12
    )

    results = []
    seen_names = set()

    for element in data.get(
        "elements",
        []
    ):
        tags = element.get(
            "tags",
            {}
        )

        name = tags.get(
            "name"
        )

        if (
            not name
            or name in seen_names
        ):
            continue

        seen_names.add(
            name
        )

        results.append(
            {
                "name": name,
                "type": tags.get(
                    "tourism"
                ),
                "opening_hours": tags.get(
                    "opening_hours"
                ),
                "website": tags.get(
                    "website"
                )
            }
        )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] Attraction search: "
        f"{elapsed:.2f}s"
    )

    return results


def search_restaurants(
    city: str,
    cuisine: str | None = None
):
    """
    Compatibility wrapper for old code.
    """

    location = get_place_coordinates(
        city
    )

    return search_restaurants_by_coordinates(
        latitude=location[
            "latitude"
        ],
        longitude=location[
            "longitude"
        ],
        cuisine=cuisine
    )


def search_attractions(
    city: str
):
    """
    Compatibility wrapper for old code.
    """

    location = get_place_coordinates(
        city
    )

    return search_attractions_by_coordinates(
        latitude=location[
            "latitude"
        ],
        longitude=location[
            "longitude"
        ]
    )