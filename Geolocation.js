const API_KEY = "f18b28d8ac2c5d60b45b17e9d0a42ed2";
const LOCATION_API_KEY = "pk.96d197d5b545c6078cd1fa0ac71e2050"

function findLongLat() {
  const status = document.querySelector("#status");

  async function success(position) {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    const {city, country} = await findCityCountry(latitude, longitude);
    reportWeather(city, country);
  }

  function error() {
    status.textContent = "Oops! Unable to retrieve your location :(";
  }

  if (!navigator.geolocation) {
    status.textContent = "Geolocation is not supported by your browser :(";
  } else {
    status.textContent = "Locating your weather…";
    navigator.geolocation.getCurrentPosition(success, error);
  }
}

async function findCityCountry(latitude, longitude) {
  const locationURL = `https://us1.locationiq.com/v1/reverse.php?key=${LOCATION_API_KEY}&lat=${latitude}&lon=${longitude}&format=json`;
  try {
    const response = await fetch(locationURL);
    const data = await response.json();
    return {
      city: data.address.city || data.address.town || data.address.village || data.address.hamlet,
      country: data.address.country_code.toUpperCase()
    };
  } catch (error) {
    console.error("Error: ", error);
    return {city: null, country: null};
  }
}


async function reportWeather(city, country) {
  const status = document.querySelector("#status");
  const weatherURL = `https://api.openweathermap.org/data/2.5/weather?q=${city},${country}&appid=${API_KEY}`;

  try {
    const response = await fetch(weatherURL);
    const data = await response.json();
    const description = formatDescription(data.weather[0].description);
    const Ftemperature = kelvinToFahrenheit(data.main.temp);
    const Ctemperature = kelvinToCelsius(data.main.temp);

    status.textContent = `The temperature in ${city}, ${country} is ${Ftemperature.toFixed(0)} °F / ${Ctemperature.toFixed(0)} °C with ${description} weather`;
  } catch (error) {
    status.textContent = "Oops! Unable to retrieve your location :(";
  }
}

function formatDescription(description) {
  const descriptionsList = {
    'clear sky': 'clear',
    'few clouds': 'slightly cloudy',
    'scattered clouds': 'partly cloudy',
    'broken clouds': 'mostly cloudy',
    'shower rain': 'Showery',
    'light rain': 'lightly rainy',
    'moderate rain': 'moderately rainy',
    'rain': 'Rain',
    'thunderstorm': 'Thunderstorm',
    'snow': 'Snow',
    'mist': 'Mist',
  };

  return descriptionsList[description] || description;
}

function kelvinToFahrenheit(temperature) {
  return (temperature - 273.15) * 9/5 + 32;
}

function kelvinToCelsius(temperature) {
  return temperature - 273.15;
}

document.querySelector("#find-me").addEventListener("click", findLongLat);