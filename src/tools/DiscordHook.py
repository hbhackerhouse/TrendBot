import os
import requests
import traceback

DISCORD_WEBHOOK_URL = os.getenv('discord_webhook_url')

def writeTweetsAndImageToDiscord(discordMessage, outputImagePath):
    try :
        # Prepare the data to be sent
        data = {'content': discordMessage}

        # If there's an image, prepare the file data
        files = {}
        if outputImagePath:
            files = {
                'file': (os.path.basename(outputImagePath), open(outputImagePath, 'rb'))
            }

        # Make the POST request to the Discord webhook
        response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)
    except Exception as e:
        print('Error sending message to Discord: ' + traceback.format_exc())
