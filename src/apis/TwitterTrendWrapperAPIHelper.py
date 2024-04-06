import os
import requests

RAPIDAPI_KEY = os.getenv('rapidapi_key')

def getTwitterTrends(woeid):
    url = "https://twitter154.p.rapidapi.com/trends/"
    querystring = {"woeid":woeid}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()