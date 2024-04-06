import os
import sys
import requests
from datetime import datetime

RAW = 'raw_images'
FINISHED = 'finished_images'
DATE_FORMAT = '%m_%d_%Y'

def save_image_from_url(url):
    baseDir = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
    imagePath = os.path.join(baseDir, RAW)
    filePath = f"{imagePath}/{datetime.now().strftime(DATE_FORMAT)}.png"
    response = requests.get(url)
    if response.status_code == 200:
        with open(filePath, 'wb') as file:
            file.write(response.content)
        return filePath
    else:
        raise Exception('Failed to download image')