import os
import logging
import requests
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

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


def get_mumbai_weather():
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 19.076,
            "longitude": 72.8777,
            "current": "temperature_2m,apparent_temperature,weathercode,windspeed_10m,relative_humidity_2m",
            "timezone": "Asia/Kolkata",
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
        f"Mumbai Weather\n"
        f"Condition: {condition}\n"
        f"Temp: {temp}°C (feels like {feels_like}°C)\n"
        f"Humidity: {humidity}%\n"
        f"Wind: {wind} km/h"
    )


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )


@app.route("/")
def index():
    return "Mumbai Weather Bot is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True)
    if not update:
        return jsonify(ok=True)

    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    logging.info(f"Received message: '{text}' from chat_id: {chat_id}")

    if chat_id and "mumbai weather" in text.lower():
        try:
            weather_text = get_mumbai_weather()
        except Exception:
            weather_text = "Sorry, could not fetch weather right now. Try again in a moment."
        send_message(chat_id, weather_text)

    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(port=5000)
