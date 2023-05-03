from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import string as string
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import weather


app = Flask("411-Group-Project")
app.config.from_pyfile('config.py')

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'YOUR_SECRET_KEY'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

#*******************************COMMENTING OUT WEATHER CODE FOR NOW ***********************************************
# @app.route("/login")
# def login():
    # client_id = app.config['CLIENT_ID']
    # client_secret = app.config['CLIENT_SECRET']
    # redirect_uri = app.config['REDIRECT_URI']
    # scope = app.config['SCOPE']
    
    # # when the user clicks the button to send in the form, they make a post request
    # if request.method == 'POST':
    #     city = request.form['cityName']
    #     state = request.form['stateName']
    #     country = request.form['countryName']
        
    #     # we will call our get_weather method we created, save result in data
    #     data = get_weather(city, state, country)
    #     weather=data.description

        #we set the valence score based on the weather description

    # return redirect(url_for('login'))
    # ******************TEMPORARILY COMMENTING THIS OUT UNTIL WE FIGURE OUT HOW TO CONNECT WEATHER STUFF TO SPOTIFY STUFF***********************************
	# we then pass in data as a parameter to the front end so we can display it there
    # return render_template("index.html", data=data)

#our landing page, displays a button which routes the user to login
@app.route('/')
def home():
    return render_template('index.html')


# route to handle logging in
@app.route('/login')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)

# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the save_discover_weekly route
    return redirect(url_for('make_playlist',_external=True))


# ******************************USES PLACEHOLDER VALENCE SCORE BOUNDS, WE NEED TO PASS IT IN SOMEHOW **********************************************
# this route should generate the playlist Weatherify, and populate it with songs based on the user's top tracks
@app.route('/makePlaylist')
def make_playlist():
    try: 
        # get token info from session
        token_info = get_token()
    except:
        # if no token info, redirect user to login route
        print('User not logged in')
        return redirect("/login")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # current user method returns a dictionary response, so we need to just grab the user id from it
    current_user_id = sp.current_user()['id']


    #*******************************WEATHER FUNCTIONS******************************************************************
    weather_data = get_weather()
    description = weather_data["description"]
    lowerbound, upperbound = get_lower_upper_bound(description)

    return lowerbound
    # return render_template("done.html")



def create_spotify_oauth():
    # grabs the api key from the .env file and stores it in api_key
    return SpotifyOAuth(
        client_id = app.config['CLIENT_ID'],
        client_secret = app.config['CLIENT_SECRET'],
        redirect_uri = url_for('redirect_page', _external=True),
        scope=app.config['SCOPE']
    )

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

## weather routes
@app.route('/weather')
def get_weather():
    city, country_code, description, fehTemperature, celTemperature = weather.find_long_lat()
    return jsonify(city=city, country_code=country_code, description=description, fehTemperature=fehTemperature, celTemperature=celTemperature)

def get_lower_upper_bound(description):
    lowerbound, upperbound = 0.0, 0.0

    if description == 'stormy':
        lowerbound, upperbound = 0.0, 0.25
    elif description in ['snowy', 'rainy', 'moderately rainy', 'lightly rainy', 'showery']:
        lowerbound, upperbound = 0.25, 0.5
    elif description == 'clear':
        lowerbound, upperbound = 0.75, 1.0
    else:
        lowerbound, upperbound = 0.5, 0.75
    return lowerbound, upperbound




app.run(debug=True)

# if __name__ == "__main__":
#     app.run()