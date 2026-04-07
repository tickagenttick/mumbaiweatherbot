import os
import logging
import requests
from flask import Flask, request, jsonify
from rapidfuzz import process

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# WMO Weather Code descriptions
# https://open-meteo.com/en/docs#weathervariables
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

# Supported cities: name → (latitude, longitude, timezone)
CITIES = {
    "mumbai":     (19.076,  72.8777, "Asia/Kolkata"),
    "delhi":      (28.6139, 77.2090, "Asia/Kolkata"),
    "bangalore":  (12.9716, 77.5946, "Asia/Kolkata"),
    "chennai":    (13.0827, 80.2707, "Asia/Kolkata"),
    "kolkata":    (22.5726, 88.3639, "Asia/Kolkata"),
    "hyderabad":  (17.3850, 78.4867, "Asia/Kolkata"),
    "pune":       (18.5204, 73.8567, "Asia/Kolkata"),
    "dubai":      (25.2048, 55.2708, "Asia/Dubai"),
    "london":     (51.5074, -0.1278, "Europe/London"),
    "new york":   (40.7128, -74.0060, "America/New_York"),
}


def extract_city(text):
    """Extract and fuzzy-match a city name from the user's message.
    Returns (city_name, (lat, lon, timezone)) or (None, None) if no match.
    """
    text = text.lower()
    if "weather" not in text:
        return None, None
    city_guess = text.replace("weather", "").strip(" ?!,.")
    if not city_guess:
        return None, None
    result = process.extractOne(city_guess, CITIES.keys())
    if result and result[1] >= 75:
        city = result[0]
        return city, CITIES[city]
    return None, None


def get_weather(city, lat, lon, timezone):
    """Fetch current weather for a city from Open-Meteo and return a formatted string."""
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weathercode,windspeed_10m,relative_humidity_2m",
            "timezone": timezone,
        },
        timeout=10,
    )
    resp.raise_for_status()
    current = resp.json()["current"]

    temp = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    humidity = current["relative_humidity_2m"]
    wind = current["windspeed_10m"]
    condition = WMO_CODES.get(current["weathercode"], "Unknown")

    return (
        f"{city.title()} Weather\n"
        f"Condition: {condition}\n"
        f"Temp: {temp}°C (feels like {feels_like}°C)\n"
        f"Humidity: {humidity}%\n"
        f"Wind: {wind} km/h"
    )


def send_message(chat_id, text):
    resp = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )
    logging.info(f"Telegram sendMessage response: {resp.status_code} {resp.text}")


@app.route("/")
def index():
    return "Weather Bot is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    # Validate Telegram secret token if configured
    if WEBHOOK_SECRET:
        incoming = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if incoming != WEBHOOK_SECRET:
            logging.warning("Rejected request with invalid secret token")
            return jsonify(error="Forbidden"), 403

    update = request.get_json(silent=True)
    if not update:
        return jsonify(ok=True)

    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    logging.info(f"Received message: '{text}' from chat_id: {chat_id}")

    city, city_data = extract_city(text)
    if chat_id and city:
        lat, lon, tz = city_data
        logging.info(f"Matched city: {city} (score >= 75)")
        try:
            weather_text = get_weather(city, lat, lon, tz)
        except Exception as e:
            logging.error(f"Weather fetch failed: {e}")
            weather_text = "Sorry, could not fetch weather right now. Try again in a moment."
        send_message(chat_id, weather_text)

    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(port=5000)
