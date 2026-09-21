import requests
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.config import (
    OPEN_METEO_GEOCODING_URL,
    OPEN_METEO_FORECAST_URL,
    WEATHER_FORECAST_DAYS,
)


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Moderate rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorm"
}


def get_coordinates(city: str):
    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
        "countryCode": "NZ",
    }

    response = requests.get(
        OPEN_METEO_GEOCODING_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results")

    if not results:
        raise ValueError(
            f"Could not find location: {city}"
        )

    location = results[0]

    return {
        "name": location["name"],
        "country": location.get("country"),
        "latitude": location["latitude"],
        "longitude": location["longitude"]
    }


def get_weather(city: str):
    location = get_coordinates(city)

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max"
        ],
        "timezone": "auto",
        "forecast_days": WEATHER_FORECAST_DAYS
    }

    response = requests.get(
        OPEN_METEO_FORECAST_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return {
        "location": location,
        "daily": data["daily"]
    }


def get_weather_range(
    city: str,
    start_date: str,
    end_date: str
):
    weather = get_weather(city)

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start > end:
        raise ValueError(
            "Start date cannot be later than end date."
        )

    today = datetime.now(
        ZoneInfo("Pacific/Auckland")
    ).date()

    last_forecast_date = (
        today + timedelta(days=15)
    )

    if start < today:
        raise ValueError(
            "This weather tool currently supports future forecasts only."
        )

    if end > last_forecast_date:
        raise ValueError(
            f"Weather forecasts are currently available only until "
            f"{last_forecast_date}."
        )

    daily = weather["daily"]

    results = []

    for index, date_string in enumerate(daily["time"]):
        current_date = date.fromisoformat(
            date_string
        )

        if start <= current_date <= end:

            weather_code = daily[
                "weather_code"
            ][index]

            results.append(
                {
                    "date": date_string,
                    "condition": WEATHER_CODES.get(
                        weather_code,
                        "Unknown"
                    ),
                    "max_temperature": daily[
                        "temperature_2m_max"
                    ][index],
                    "min_temperature": daily[
                        "temperature_2m_min"
                    ][index],
                    "precipitation_probability": daily[
                        "precipitation_probability_max"
                    ][index]
                }
            )

    return {
        "location": weather["location"]["name"],
        "country": weather["location"]["country"],
        "forecast": results
    }