# this file processes the api call for Open Weather API
# requires you to have installed requests, dotenv in your virtual env to get this to work

import requests
from dotenv import load_dotenv
import os

# grabs the api key from the .env file and stores it in api_key
load_dotenv()
api_key= os.getenv('API_KEY')

# first we use Geocoding version of API to get latitude and longitude based on passed in parameters
def get_lat_lon(city_name, state_code, country_code, API_key):
    # make call with passed in params, then get response and then convert it to readable json
    resp = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={city_name},{state_code},{country_code}&appid={API_key}').json()
    
    # the dictionary is the first element of response, store it in data
    data = resp[0]
    lat, lon = data.get('lat'), data.get('lon')
    return lat, lon

# TESTING LAT LONG METHOD
print(get_lat_lon('Boston', 'MA', 'United States', api_key))