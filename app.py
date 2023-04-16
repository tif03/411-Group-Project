""" 
Main file with all routes
reference https://github.com/lucaoh21/Spotify-Discover-2.0/blob/master/functions.py 
"""

from flask import Flask, render_template, request, session, redirect
from weather import main as getweather
from spotify import createStateKey, getToken, getUserInformation
import os
from dotenv import load_dotenv
import base64
from requests import post, get
from logging import error, info
import json
import random
import time

load_dotenv()

app = Flask("411-Group-Project")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    client_id = app.config['CLIENT_ID']
    client_secret = app.config['CLIENT_SECRET']
    redirect_uri = app.config['REDIRECT_URI']
    scope = app.config['SCOPE']
    
    state_key = createStateKey(15)
    session['state_key'] = state_key

    authorize_url = "https://accounts.spotify.com/authorize?"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state_key,
    }

    result = post(authorize_url, headers=params)
    json_result = json.loads(result.content)
    return json_result

""" Called after user authorized application through Spotify API page, stores user info 
redirects in a session and redirects user back to page initially visited """
@app.route('/callback')
def callback():
    if request.arg.get('state') != session['state_key']:
        return render_template('index.html', error = 'State failed.')

    if request.args.get('error'):
        return render_template('index.html', error = 'SPotify error.')

    else:
        code = request.arg.get('code')
        session.pop('state key', None)

        payload = getToken(code)
        if payload != None:
            session['token'] = payload[0]
            session['refresh_token'] = payload[1]
            session['token_expiration'] = time.time() + payload[2]

        else:
            return render_template('index.html', error = 'Failed access token.')

    current_user = getUserInformation(session)
    session['user_id'] = current_user['id']
    info('new user:' + session['user_id'])

    return redirect(session['previous_url'])

""" 
Grabs the current weather report -- prompt the user to press a button "get weather and playlist"
@app.route('/currweather', methods = ['GET'])
"""

if __name__ == "__main__":
    app.run()
