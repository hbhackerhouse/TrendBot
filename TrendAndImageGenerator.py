import os
import time
from datetime import datetime
import json
import requests
import openai
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import chromedriver_binary
from bs4 import BeautifulSoup

env = os.getenv('environment')
DISCORD_WEBHOOK_URL = os.getenv('discord_webhook_url')
RAPIDAPI_KEY = os.getenv('rapidapi_key')
openai.api_key = os.getenv('openai_key')
TWITTER_USERNAME = os.getenv('twitter_username')
TWITTER_PASSWORD = os.getenv('twitter_password')

def getTwitterTrends(woeid):
    url = "https://twitter154.p.rapidapi.com/trends/"
    querystring = {"woeid":woeid}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()

def scrapeTweetsFromTrendURL(url):
    # Step 1: Set up the Selenium web driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("user-data-dir=selenium") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    if (env and env == 'PROD'):
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--window-size=1280,720")
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)

    # Step 2: Get the webpage
    # driver.get(url)
    # cookieFilePath = os.getcwd()+'/TrendBot/cookie.json'
    # with open(cookieFilePath, 'r') as cookiesFile:
    #     data = json.load(cookiesFile)
    #     for cookie in data:
    #         driver.add_cookie(cookie)
    
    # driver.refresh()
    # # xsrf_token = '7f9f4ce16574d989762c8ad9c63be843ac042d4f9522f1e197b74f1ea2e989a2a20f5be9e5b0e740f53d512ee3d9921f503ea0903520ae6c327f1876661f1e8f65798b7ce05f47c803e15e85a7115cd9'
    # # driver.add_cookie({'name': 'XSRF-TOKEN', 'value': xsrf_token})
    driver.delete_all_cookies()

    loginUrl = "https://twitter.com/i/flow/login"
    driver.get(loginUrl)

    username = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
    username.send_keys(TWITTER_USERNAME)
    username.send_keys(Keys.ENTER)

    password = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
    password.send_keys(TWITTER_PASSWORD)
    password.send_keys(Keys.ENTER)

    time.sleep(10)

    driver.get(url)

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='tweetText']"))
        )
    except Exception as e:
        print("Element not found")
        driver.quit()
        return []

    # Step 3: Get the page source
    page_source = driver.page_source

    # Step 4: Parse the webpage content
    soup = BeautifulSoup(page_source, 'html.parser')

    # Step 5: Find the specific div and get all anchor tags inside it
    divs = soup.find_all('div', {'data-test-id': 'tweetText'}, limit=10)

    # Step 5: Extract and concatenate text from span tags within each div
    tweets = []
    for div in divs:
        spans = div.find_all('span')
        tweet_text = ' '.join(span.get_text() for span in spans)
        tweets.append(tweet_text)

    print(tweets)

    # Step 7: Close the web driver
    driver.quit()

    return tweets

def createSummariesFromTrend(name_url_tuples):
    trendAndSummaries = []
    for trendAndUrl in name_url_tuples:
        trend = trendAndUrl[0]
        url = trendAndUrl[1]
        
        tweets = scrapeTweetsFromTrendURL(url) 
        aggregated_tweets = "\n".join(tweets)
        prompt = f"Summarize the tweets about '{trend}' into one sentence with no dashses. Here are the tweets: \n{aggregated_tweets}"

        response = openai.Completion.create(
            engine="gpt-3.5-turbo-0125",  # GPT-3.5
            prompt=prompt,
            max_tokens=60  # Length
        )
        trendAndSummaries.append(trend + ' - ' + response.choices[0].text.strip())

    return trendAndSummaries

def generatePrompt(trendAndSummaries):
    return 'Create a marvel-like movie poster with no words using these comma separated tags as subjects.' \
        + ','.join(trendAndSummary.split('-')[0] for trendAndSummary in trendAndSummaries)

def getDalleImageURL(prompt):
    # url = "https://text-to-image7.p.rapidapi.com/"
    # querystring = {"prompt":prompt}
    # headers = {
    #     "X-RapidAPI-Key": RAPIDAPI_KEY,
    #     "X-RapidAPI-Host": "text-to-image7.p.rapidapi.com"
    # }

    # response = requests.get(url, headers=headers, params=querystring)

    # return response.json()['data'][0]
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response['data'][0]['url']
    except Exception as e:
        return str(e)
    
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
    # Get Twitter trends around California
    # woeid = 2442047
    # trends = getTwitterTrends(woeid)
    # name_url_tuples = [(trend['name'], trend['url']) for trend in trends[0]['trends']]
    name_url_tuples = [('Colorado', 'http://twitter.com/search?q=Colorado'), ('Baylor', 'http://twitter.com/search?q=Baylor'), ('Elite 8', 'http://twitter.com/search?q=%22Elite+8%22'), ('Arte', 'http://twitter.com/search?q=Arte'), ('Dylan Cease', 'http://twitter.com/search?q=%22Dylan+Cease%22'), ('#LAFC', 'http://twitter.com/search?q=%23LAFC'), ('Martinez', 'http://twitter.com/search?q=Martinez'), ('Elite Eight', 'http://twitter.com/search?q=%22Elite+Eight%22'), ('Matt Chapman', 'http://twitter.com/search?q=%22Matt+Chapman%22'), ('Paige', 'http://twitter.com/search?q=Paige'), ('UCLA', 'http://twitter.com/search?q=UCLA'), ('Manchester United', 'http://twitter.com/search?q=%22Manchester+United%22'), ('Malik', 'http://twitter.com/search?q=Malik'), ('White House', 'http://twitter.com/search?q=%22White+House%22'), ...]
    # TODO : Get a summary of each trend
    trendAndSummaries = createSummariesFromTrend(name_url_tuples)
    # Craft a prompt and create a movie poster image for all the trends
    prompt = generatePrompt(trendAndSummaries)
    imageOutputFilePath = f"/raw_images/{datetime.now().strftime('%m_%d_%Y')}.png"
    image_url = getDalleImageURL(prompt)
    save_image_from_url(image_url, imageOutputFilePath)
    # Post the image and trend with their summaries delimited by a '-' to the Discord
    tweets = '\n'.join(trendAndSummaries)
    writeTweetsAndImageToDiscord(imageOutputFilePath, tweets)
    
main()