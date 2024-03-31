import os
import json
import requests
import openai

DISCORD_WEBHOOK_URL = os.getenv('discord_webhook_url')
RAPIDAPI_KEY = os.getenv('rapidapi_key')
openai.api_key = os.getenv('rapidapi_key')

def getTwitterTrends(woeid):
    url = "https://twitter154.p.rapidapi.com/trends/"
    querystring = {"woeid":woeid}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()

# def createTweetSummaryFromTrend(name_url_tuples):
    # pass

def getDalleImage(name_url_tuples):
    prompt = 'Create a marvel movie poster using these comma separated tags : ' + ','.join(trend[0] for trend in name_url_tuples)
    url = "https://text-to-image7.p.rapidapi.com/"
    querystring = {"prompt":prompt}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "text-to-image7.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()['data'][0]
    # try:
    #     response = openai.Image.create(
    #         prompt=prompt,
    #         n=1,
    #         size="1024x1024"
    #     )
    #     return response['data'][0]['url']
    # except Exception as e:
    #     return str(e)
    
def save_image_from_url(url, file_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return "Image saved successfully."
    else:
        return "Failed to download the image."

def writeTweetsAndImageToDiscord(image_path, tweets):
    with open(image_path, 'rb') as img:
        payload = {
            'file': img
        }
        data = {
            'payload_json': (None, json.dumps({'content': tweets}))
        }
        try :
            response = requests.post(DISCORD_WEBHOOK_URL, files=payload, data=data)
        except Exception as e:
            print('Error sending message to Discord: ' + str(e))

def main():
    # California
    woeid = 2442047
    trends = getTwitterTrends(woeid)
    name_url_tuples = [(trend['name'], trend['url']) for trend in trends[0]['trends']]
    # TODO : Add
    trendAndSummaries = createTweetSummaryFromTrend(name_url_tuples)
    image_url = getDalleImage(name_url_tuples)
    save_image_from_url(image_url, 'image.png')
    # TODO : Remove
    tweets = '\n'.join(trendAndSummary[0] for trendAndSummary in trendAndSummaries)
    writeTweetsAndImageToDiscord('image.png', tweets)
    
main()