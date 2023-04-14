from flask import Flask, render_template, request
from weather import main as get_weather

from flask import Flask, render_template
from dotenv import load_dotenv
import os
import base64
from requests import post, get
from logging import error
import json
import random

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")



app = Flask("411-Group-Project")

@app.route("/")
def home():
    return render_template("index.html")

def generateRandomString(length):
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choice(letters) for i in range(length))


@app.route("/login")
def login():
    redirect_uri = app.config['REDIRECT_URI']
    state = generateRandomString(16)
    scope = 'ugs-image-upload playlist-modify-private playlist-modify-public user-top-read'
    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    url = "https://accounts.spotify.com/authorize?"
    result = post(url, headers=params)
    json_result = json.loads(result.content)
    return json_result

def getToken(code):
    authorization = app.config['AUTHORIZATION']
    redirect_uri = app.config['REDIRECT_URI']

    auth_string = client_id + ":" + client_secret
    auth_bytes =  auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {'Authorization': authorization, 
             'Accept': 'application/json', 
             'Content-Type': 'application/x-www-form-urlencoded'}
    body = {'code': code, 'redirect_uri': redirect_uri, 
          'grant_type': 'authorization_code'}
    post_response = post(url,headers=headers,data=body)
    if post_response.status_code == 200:
        pr = post_response.json()
        return pr['access_token'], pr['refresh_token'], pr['expires_in']
    else:
        error('getToken:' + str(post_response.status_code))
        return None

def makeGetRequest(session, url, params={}):
  headers = {"Authorization": "Bearer {}".format(session['token'])}
  response = get(url, headers=headers, params=params)
  if response.status_code == 200:
    return response.json()
  elif response.status_code == 401 and checkTokenStatus(session) != None:
    return makeGetRequest(session, url, params)
  else:
    error('makeGetRequest:' + str(response.status_code))
    return None

if __name__ == "__main__":
    app.run()