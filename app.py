from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import string as string
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import weather
from flask_sqlalchemy import SQLAlchemy
from datetime import date


app = Flask("411-Group-Project")
app.config.from_pyfile('config.py')

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'YOUR_SECRET_KEY'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

# ~~~~~~~~~~~~~~~~~~~~~DATABASE SETUP~~~~~~~~~~~~~~~~~~~~~~~~~~~~
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_playlists.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# instantiate database object
db = SQLAlchemy(app)

# simple model for playlists (table in database)
class Playlists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String(50), nullable=False)
    playlist_id = db.Column(db.String(50), nullable=False)
    weather_description = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Playlist('{self.spotify_user_id}', '{self.playlist_id}', '{self.weather_description})"



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ROUTES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# our landing page, displays a button which routes the user to login
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


# this route generates playlist Weatherify with songs based on the user's top tracks & playlists
# also stores the playlist id and user id in database
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


    # gets weather and corresponding valence score bounds (valence score = mood of songs we'll put in the playlist)
    weather_data = get_weather()
    weather_description = weather_data["description"]
    lowerbound, upperbound = get_lower_upper_bound(weather_description)

    #today's date
    today = date.today()
    date_of_creation = today.strftime("%m/%d/%y")

    # first we check if a playlist with same name already exists
    #current_playlists =  sp.current_user_playlists()['items']
    #existing_playlist_id = None
    #for playlist in current_playlists:
    #    if(playlist['name'] == 'Weatherify'):
    #        existing_playlist_id = playlist['id']
    
    # create a playlist called Weatherify if playlist doesn't exist already, and save its playlist id in existing_playlist_id
    #if existing_playlist_id == None:
        
    new_playlist_title = date_of_creation + ' - ' + weather_description + ' playlist'
    new_playlist_id = sp.user_playlist_create(current_user_id, new_playlist_title, public=True, collaborative=False, description='A playlist generated from the current weather at your location')['id']
    
    #get top tracks
    top_tracks = sp.current_user_top_tracks(limit=2, offset=0, time_range='medium_term')['items']
    top_artists = sp.current_user_top_artists(limit=2, offset=0, time_range='medium_term')['items']

    top_tracks_uri = []
    top_artists_uri = []

    for song in top_tracks:
        song_uri= song['uri']
        top_tracks_uri.append(song_uri)
    for artist in top_artists:
        artist_uri= artist['uri']
        top_artists_uri.append(artist_uri)

    #valance, energy, dancability min_dancability=lowerbound, max_dancability=upperbound, min_energy=lowerbound, max_energy=upperbound,
    recommended_songs = sp.recommendations(seed_tracks=top_tracks_uri, seed_artists=top_artists_uri, min_dancability=lowerbound, max_dancability=upperbound, min_energy=lowerbound, max_energy=upperbound, min_valance=lowerbound, max_valance=upperbound)['tracks']
    recommended_tracks_uri = []
    for song in recommended_songs:
        uri = song['uri']
        recommended_tracks_uri.append(uri)
    
    sp.user_playlist_add_tracks(current_user_id, new_playlist_id, recommended_tracks_uri, None)
    

    #loop over the songs in our generated playlist to compile final list to pass to front end
    final_playlist = []
    for song in sp.playlist(new_playlist_id)['tracks']['items']:
        song_and_artist = song['track']['name'] + " - " + song['track']['artists'][0]['name']
        final_playlist.append(song_and_artist)

    # store the playlist id and user id in the database
    new_playlist = Playlists(spotify_user_id=current_user_id, playlist_id=new_playlist_id, weather_description = weather_description)
    db.session.add(new_playlist)
    db.session.commit()

    # send them to the done html page and display their generated playlist
    return render_template("done.html", final_playlist=final_playlist, new_playlist_title=new_playlist_title)


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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~WEATHER FUNCTIONS AND ROUTES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_weather():
    city, country_code, description, fehTemperature, celTemperature = weather.find_long_lat()
    return {
        "city": city,
        "country_code": country_code,
        "description": description,
        "fehTemperature": fehTemperature,
        "celTemperature": celTemperature
    }
@app.route('/weather')
def weather_route():
    weather_data = get_weather()
    return jsonify(weather_data)

def get_lower_upper_bound(description):
    lowerbound, upperbound = 0.0, 0.0

    if description == ['stormy', 'snowy']:
        lowerbound, upperbound = 0.0, 0.25
    elif description in ['misty', 'cloudy', 'rainy', 'moderately rainy', 'lightly rainy', 'showery']:
        lowerbound, upperbound = 0.25, 0.5
    elif description == 'clear':
        lowerbound, upperbound = 0.75, 1.0
    else:
        lowerbound, upperbound = 0.5, 0.75
    return lowerbound, upperbound


if __name__ == "__main__":
    # need for database to correctly load
    with app.app_context():
        db.create_all()
    app.run(debug=True)