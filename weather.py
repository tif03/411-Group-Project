# this file processes the api call for Open Weather API
# requires you to have installed requests, dotenv in your virtual env to get this to work

import requests
from dotenv import load_dotenv
import os
from dataclasses import dataclass

# define a class object that allows us to retreive and store info from the current weather api call in a organized way
# WeatherData object has 4 attributes
@dataclass
class WeatherData:
    main: str
    description: str
    icon: str
    temperature: float


# grabs the api key from the .env file and stores it in api_key
load_dotenv()
api_key= os.getenv('API_KEY')

# first we use Geocoding version of API to get latitude and longitude based on passed in parameters
def get_lat_lon(city_name, state_code, country_code, API_key):
    # make call with passed in params, then get response and then convert it to readable json
    resp = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={city_name},{state_code},{country_code}&appid={API_key}').json()
    print(resp)
    # the dictionary is the first element of response, store it in data
    data = resp[0]
    lat, lon = data.get('lat'), data.get('lon')
    return lat, lon

def get_current_weather(lat, lon, API_key):
    resp = requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_key}&units=imperial').json()

    # create data oject of our defined type weatherdata so we can easily grab the data we want
    data = WeatherData(
        main=resp.get('weather')[0].get('main'),
        description=resp.get('weather')[0].get('description'),
        icon=resp.get('weather')[0].get('icon'),
        temperature=resp.get('main').get('temp')
    )

    return data

def main(city_name, state_name, country_name):
    lat, lon = get_lat_lon(city_name, state_name, country_name, api_key)
    weather_data = get_current_weather(lat, lon, api_key)
    return weather_data

#testing
if __name__ == "__main__":
    lat, lon = get_lat_lon('Boston', 'MA', 'United States', api_key)
    print(get_current_weather(lat, lon, api_key))
