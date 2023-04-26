""" 
reference https://github.com/lucaoh21/Spotify-Discover-2.0/blob/master/functions.py 

All Spotify API calls
"""

from flask import render_template, redirect, request
from app import app
import config
import base64
import os
import random as rand
import string as string
import requests
import time
import logging

"""
Creates a state key for the authorization request
"""
def createStateKey(size):
	#https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
	return ''.join(rand.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))

"""
Requests an access token from Spotify API
"""
def getToken(code):
    token_url = "https://accounts.spotify.com/api/token"
    
    authorization = app.config['AUTHORIZATION']
    redirect_uri = app.config['REDIRECT_URI']

    headers = {'Authorization': authorization, 
             'Accept': 'application/json', 
             'Content-Type': 'application/x-www-form-urlencoded'}
    body = {'code': code, 'redirect_uri': redirect_uri, 
          'grant_type': 'authorization_code'}
          
    post_response = requests.post(token_url,headers=headers,data=body)

    if post_response.status_code == 200:
        pr = post_response.json()
        return pr['access_token'], pr['refresh_token'], pr['expires_in']
    
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
Makes a GET request with the proper headers. If the request fails because the access token has expired, the
check token function is called to update the access token.
"""
def makeGetRequest(session, url, params={}):
	headers = {"Authorization": "Bearer {}".format(session['token'])}
	response = requests.get(url, headers=headers, params=params)

	# 200 code indicates request was successful
	if response.cod== 200:
		return response.json()

	# if a 401 error occurs, update the access token
	elif response.cod == 401 and checkTokenStatus(session) != None:
		return makeGetRequest(session, url, params)

	else:
		logging.error('makeGetRequest:' + str(response.status_code))
		return None


"""
Makes a PUT request with the proper headers. If the request fails because the access token has expired, the
check token function is called to update the access token.
"""
def makePutRequest(session, url, params={}, data={}):
	headers = {"Authorization": "Bearer {}".format(session['token']), 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
	response = requests.put(url, headers=headers, params=params, data=data)

	# if request succeeds or specific errors occured, status code is returned
	if response.status_code == 204 or response.status_code == 403 or response.status_code == 404 or response.status_code == 500:
		return response.status_code

	# if a 401 error occurs, update the access token
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return makePutRequest(session, url, data)
	else:
		logging.error('makePutRequest:' + str(response.status_code))
		return None

"""
Makes a POST request with the proper headers. If the request fails because the access token has expired, the
check token function is called to update the access token. If the requests fails
due to inactive devices or forbidden requests the status code is returned.
"""
def makePostRequest(session, url, data):
	headers = {"Authorization": "Bearer {}".format(session['token']), 'Accept': 'application/json', 'Content-Type': 'application/json'}
	response = requests.post(url, headers=headers, data=data)

	# both 201 and 204 indicate success, however only 201 responses have body information
	if response.status_code == 201:
		return response.json()
	if response.status_code == 204:
		return response

	# if a 401 error occurs, update the access token
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return makePostRequest(session, url, data)

	elif response.status_code == 403 or response.status_code == 404:
		return response.status_code

	else:
		logging.error('makePostRequest:' + str(response.status_code))
		return None

"""
Makes a DELETE request with the proper headers. If the request succeeds, the json parsed
response is returned. If the request fails because the access token has expired, the
check token function is called to update the access token.
"""
def makeDeleteRequest(session, url, data):
	headers = {"Authorization": "Bearer {}".format(session['token']), 'Accept': 'application/json', 'Content-Type': 'application/json'}
	response = requests.delete(url, headers=headers, data=data)

	# 200 code indicates request was successful
	if response.status_code == 200:
		return response.json()

	# if a 401 error occurs, update the access token
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return makeDeleteRequest(session, url, data)
	else:
		logging.error('makeDeleteRequest:' + str(response.status_code))
		return None

"""
Get user information (username, user ID, and user location)
"""
def getUserInformation(session):
    url = 'https://api.spotify.com/v1/me'
    payload = makeGetRequest(session, url)

    if payload == None:
        return None

    return payload

"""
Get user top tracks
"""
def getUserTopTracks(session):
	type = 'tracks'
	time_range = 'short_term'	#top tracks of the past 4 weeks
	limit = '20'
	url = f'https://api.spotify.com/v1/me/top/{type}/{time_range}/{limit}'

	payload = makeGetRequest(session, url)

	if payload == None:
		return None

	return payload

"""
Get user top artists
"""
def getUserTopArtists(session):
	type = 'artists'
	time_range = 'short_term'	#top artists of the past 4 weeks
	limit = '20'
	url = f'https://api.spotify.com/v1/me/top/{type}/{time_range}/{limit}'

	payload = makeGetRequest(session, url)
	if payload == None:
		return None
		
	return payload


