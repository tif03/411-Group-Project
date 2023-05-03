
# this file processes the api call for Open Weather API
# requires you to have installed requests, dotenv in your virtual env to get this to work
from app import app
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter
from ipregistry import IpregistryClient
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
LOCATION_API_KEY = os.getenv("LOCATION_API_KEY")
IP_API_KEY = os.getenv("IP_API_KEY")

def get_current_location():
    client = IpregistryClient(IP_API_KEY)
    ip_info = client.lookup()
    return ip_info.location["latitude"], ip_info.location["longitude"]


def find_long_lat():
    try:
        latitude, longitude = get_current_location()
        geolocator = Nominatim(user_agent="weather_app")
        geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)
        location = geocode((latitude, longitude))
        city = location.raw["address"].get("city") or location.raw["address"].get("town") or location.raw["address"].get("village") or location.raw["address"].get("hamlet")
        country_code = location.raw["address"]["country_code"].upper()
        description, fehTemperature, celTemperature = report_weather(city, country_code)
        return city, country_code, description, fehTemperature, celTemperature

    except (GeocoderTimedOut, GeocoderServiceError) as ex:
        print("Oops! Unable to retrieve your location :(")
        return None, None, None, None, None


def report_weather(city, country_code):
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country_code}&appid={API_KEY}"
    try:
        response = requests.get(weather_url)
        data = response.json()
        description = format_description(data["weather"][0]["description"])
        fehTemperature = kelvin_to_fahrenheit(data["main"]["temp"])
        celTemperature = kelvin_to_celsius(data["main"]["temp"])

        return description, fehTemperature, celTemperature
    except Exception as ex:
        print("Oops! Unable to retrieve your location :(")
        return None, None, None


def format_description(description):
    descriptions_list = {
        'clear sky': 'clear',
        'few clouds': 'slightly cloudy',
        'scattered clouds': 'partly cloudy',
        'broken clouds': 'mostly cloudy',
        'overcast clouds': 'cloudy',
        'shower rain': 'showery',
        'light rain': 'lightly rainy',
        'moderate rain': 'moderately rainy',
        'rain': 'rainy',
        'thunderstorm': 'stormy',
        'snow': 'snowy',
        'mist': 'misty',
    }

    return descriptions_list.get(description, description)

def kelvin_to_fahrenheit(temperature):
    return (temperature - 273.15) * 9/5 + 32

def kelvin_to_celsius(temperature):
    return temperature - 273.15

if __name__ == "__main__":
    find_long_lat()