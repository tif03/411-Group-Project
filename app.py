from flask import Flask, render_template, request, session, make_response, redirect
from weather import main as get_weather
import random as rand
import string as string
import requests
import time
import logging
from dotenv import load_dotenv
import os

app = Flask("411-Group-Project")


# we need to pass in what methods are allowed to be called from this route, by default only get is allowed
@app.route("/", methods=['GET', 'POST'])
def home():
    #initialize data to none so even if its a get method render template can still have something declared for data
    data = None
    
    # when the user clicks the button to send in the form, they make a post request
    if request.method == 'POST':
        city = request.form['cityName']
        state = request.form['stateName']
        country = request.form['countryName']
        
        # we will call our get_weather method we created, save result in data
        data = get_weather(city, state, country)
    
    # we then pass in data as a parameter to the front end so we can display it there
    return render_template("index.html", data=data)


# these are the spotify routes

"""
Called by the backend when a user has not authorized the application to
access their Spotify account. Attempts to authorize a new user by redirecting
them to the Spotify authorization page.
"""
@app.route('/authorize')
def authorize():
    # grabs the secrets etc from the .env file and stores it in api_key
    #this is broken for some reason maybe i should change it to the config thing in the original
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    redirect_uri = os.getenv('REDIRECT_URI')
    scope = os.getenv('SCOPE')
	
    
    # state key used to protect against cross-site forgery attacks
    state_key = createStateKey(15)
    session['state_key'] = state_key

	# redirect user to Spotify authorization page
    authorize_url = 'https://accounts.spotify.com/en/authorize?'
    parameters = 'response_type=code&client_id=' + client_id + '&redirect_uri=' + redirect_uri + '&scope=' + scope + '&state=' + state_key
    response = make_response(redirect(authorize_url + parameters))

    return response


"""
Called after a new user has authorized the application through the Spotift API page.
Stores user information in a session and redirects user back to the page they initally
attempted to visit.
"""
@app.route('/callback')
def callback():
	# make sure the response came from Spotify
	if request.args.get('state') != session['state_key']:
		return render_template('index.html', error='State failed.')
	if request.args.get('error'):
		return render_template('index.html', error='Spotify error.')
	else:
		code = request.args.get('code')
		session.pop('state_key', None)

		# get access token to make requests on behalf of the user
		payload = getToken(code)
		if payload != None:
			session['token'] = payload[0]
			session['refresh_token'] = payload[1]
			session['token_expiration'] = time.time() + payload[2]
		else:
			return render_template('index.html', error='Failed to access token.')

	current_user = getUserInformation(session)
	session['user_id'] = current_user['id']
	logging.info('new user:' + session['user_id'])

	return redirect(session['previous_url'])










# these are the Spotify functions 
"""
Creates a state key for the authorization request
"""
def createStateKey(size):
	#https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
	return ''.join(rand.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))



"""
Requests an access token from the Spotify API. Only called if no refresh token for the
current user exists.
Returns: either [access token, refresh token, expiration time] or None if request failed
"""
def getToken(code):
	token_url = 'https://accounts.spotify.com/api/token'
	authorization = app.config['AUTHORIZATION']
	redirect_uri = app.config['REDIRECT_URI']

	headers = {'Authorization': authorization, 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
	body = {'code': code, 'redirect_uri': redirect_uri, 'grant_type': 'authorization_code'}
	post_response = requests.post(token_url, headers=headers, data=body)

	# 200 code indicates access token was properly granted
	if post_response.status_code == 200:
		json = post_response.json()
		return json['access_token'], json['refresh_token'], json['expires_in']
	else:
		logging.error('getToken:' + str(post_response.status_code))
		return None


"""
Requests an access token from the Spotify API with a refresh token. Only called if an access
token and refresh token were previously acquired.
Returns: either [access token, expiration time] or None if request failed
"""
def refreshToken(refresh_token):
	token_url = 'https://accounts.spotify.com/api/token'
	authorization = app.config['AUTHORIZATION']

	headers = {'Authorization': authorization, 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
	body = {'refresh_token': refresh_token, 'grant_type': 'refresh_token'}
	post_response = requests.post(token_url, headers=headers, data=body)

	# 200 code indicates access token was properly granted
	if post_response.status_code == 200:
		return post_response.json()['access_token'], post_response.json()['expires_in']
	else:
		logging.error('refreshToken:' + str(post_response.status_code))
		return None

"""
Determines whether new access token has to be requested because time has expired on the 
old token. If the access token has expired, the token refresh function is called. 
Returns: None if error occured or 'Success' string if access token is okay
"""
def checkTokenStatus(session):
	if time.time() > session['token_expiration']:
		payload = refreshToken(session['refresh_token'])

		if payload != None:
			session['token'] = payload[0]
			session['token_expiration'] = time.time() + payload[1]
		else:
			logging.error('checkTokenStatus')
			return None

	return "Success"


"""
REQUESTS: Functions to make GET, POST, PUT, and DELETE requests with the correct
authorization headers.
"""

"""
Makes a GET request with the proper headers. If the request succeeds, the json parsed
response is returned. If the request fails because the access token has expired, the
check token function is called to update the access token.
Returns: Parsed json response if request succeeds or None if request fails
"""
def makeGetRequest(session, url, params={}):
	headers = {"Authorization": "Bearer {}".format(session['token'])}
	response = requests.get(url, headers=headers, params=params)

	# 200 code indicates request was successful
	if response.status_code == 200:
		return response.json()

	# if a 401 error occurs, update the access token
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return makeGetRequest(session, url, params)
	else:
		logging.error('makeGetRequest:' + str(response.status_code))
		return None



"""
PERSONAL USER INFORMATION: Functions that get information specific to the user.
"""

"""
Gets user information such as username, user ID, and user location.
Returns: Json response of user information
"""
def getUserInformation(session):
	url = 'https://api.spotify.com/v1/me'
	payload = makeGetRequest(session, url)

	if payload == None:
		return None

	return payload









if __name__ == "__main__":
    app.run()