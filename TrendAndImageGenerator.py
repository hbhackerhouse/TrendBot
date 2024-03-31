import os
import time
from datetime import datetime
import json
import requests
from openai import OpenAI
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
OPEN_AI = OpenAI(
    api_key=os.environ.get("openai_key")
)
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
    # # xsrf_token = '7f9f4ce16574d989762c8ad9c63be843ac042d4f9522f1e197b74f1ea2e989a2a20f5be9e5b0e740f53d512ee3d9921f503ea0903520ae6c327f1876661f1e8f65798b7ce05f47c803e15e85a7115cd9'
    # # driver.add_cookie({'name': 'XSRF-TOKEN', 'value': xsrf_token})
    # driver.delete_all_cookies()

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
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid=\"tweetText\"]"))
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
    divs = soup.find_all('div', attrs={"data-testid": "tweetText"}, limit=5)

    # Step 5: Extract and concatenate text from span tags within each div
    tweets = []
    for div in divs:
        spans = div.find_all('span')
        tweet_text = ' '.join(span.get_text() for span in spans)
        tweets.append(tweet_text)

    # Step 7: Close the web driver
    driver.quit()

    return tweets

def createSummariesFromTrend(name_url_tuples):
    trendAndSummaries = []
    for trendAndUrl in name_url_tuples:
        try:
            trend = trendAndUrl[0]
            url = trendAndUrl[1]
            
            tweets = scrapeTweetsFromTrendURL(url) 
            aggregated_tweets = "\n".join(tweets)
            prompt = f"Summarize the tweets about '{trend}' into one sentence with no dashes. Here are the tweets separated by new line characters\
                and may not be related to each other. If they are not related only keep the one's that appear the most often: \n{aggregated_tweets}"

            response = OPEN_AI.chat.completions.create(
                model="gpt-3.5-turbo-0125",  # GPT-3.5
                messages=[{"role": "system", "content": prompt}],
                max_tokens=60  # Length
            )
            trendAndSummaries.append(trend + ' - ' + response.choices[0].message.content)
        except Exception as e:
            continue

    return trendAndSummaries

def generatePrompt(trendAndSummaries):
    return 'Create a music album cover using these topics:' \
        + ','.join(trendAndSummary.split('-')[0].strip() for trendAndSummary in trendAndSummaries)

def getDalleImageURL(prompt):
    try:
        response = OPEN_AI.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            quality="standard",
            size="1024x1024"
        )
        return response.data[0].url
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

def writeTweetsAndImageToDiscord(tweetsAndLink):
    # with open(image_path, 'rb') as img:
    #     payload = {
    #         'file': img
    #     }
    # data = {
    #     'payload_json': (None, json.dumps({'content': tweets}))
    # }
    data = {
        'content' : tweetsAndLink
    }
    try :
        # response = requests.post(DISCORD_WEBHOOK_URL, files=payload, data=data)
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        print('Error sending message to Discord: ' + str(e))

def main():
    # Get Twitter trends around California
    # woeid = 2442047
    # trends = getTwitterTrends(woeid)
    # trends = trends[:5]
    # name_url_tuples = [(trend['name'], trend['url']) for trend in trends[0]['trends']]
    # name_url_tuples = [('Colorado', 'http://twitter.com/search?q=Colorado'), ('Baylor', 'http://twitter.com/search?q=Baylor'), ('Elite 8', 'http://twitter.com/search?q=%22Elite+8%22'), ('Arte', 'http://twitter.com/search?q=Arte'), ('Dylan Cease', 'http://twitter.com/search?q=%22Dylan+Cease%22'), ('#LAFC', 'http://twitter.com/search?q=%23LAFC'), ('Martinez', 'http://twitter.com/search?q=Martinez'), ('Elite Eight', 'http://twitter.com/search?q=%22Elite+Eight%22'), ('Matt Chapman', 'http://twitter.com/search?q=%22Matt+Chapman%22'), ('Paige', 'http://twitter.com/search?q=Paige'), ('UCLA', 'http://twitter.com/search?q=UCLA'), ('Manchester United', 'http://twitter.com/search?q=%22Manchester+United%22'), ('Malik', 'http://twitter.com/search?q=Malik'), ('White House', 'http://twitter.com/search?q=%22White+House%22'), ...]
    # Get a summary of each trend
    # trendAndSummaries = createSummariesFromTrend(name_url_tuples)
    # Craft a prompt and create a movie poster image for all the trends
    trendAndSummaries = ["Colorado - There are impressive athletic achievements taking place in Colorado, including a triple home run on the 11th pitch and a 2-run homer by Rockies players, alongside recognition of a basketball player's successful collegiate career with Colorado.", 
                         'Baylor - A recent article suggested that the future of the Baylor program may be "withering away" without Kim Mulkey, but the current coach, Nicki Collen, disagrees, stating that nothing is withering in Waco.', 
                         "Elite 8 - The Elite 8 features a rematch of last year's National Championship game, with extra motivation for Dan Hurley and each team's starting lineup based on their college origins.", 
                         'Arte - Arte is being celebrated as a powerful medium of expression in various forms.', 
                         'White House - There are tweets mentioning controversy, opposition to Trump returning to the White House, and accusations of the White House promoting Satanism, along with a confrontation with a protestor outside the White House.']
    # prompt = generatePrompt(trendAndSummaries)
    
    # image_url = getDalleImageURL(prompt)
    image_url = 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-M8YrltJT88gss1cJU7sD2Dsh/user-nbhw1QvMdBN1yM0H6Z5dTXb5/img-S6eF1oSPmt4dnmg1khozJoct.png?st=2024-03-31T05%3A11%3A46Z&se=2024-03-31T07%3A11%3A46Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-03-31T00%3A32%3A28Z&ske=2024-04-01T00%3A32%3A28Z&sks=b&skv=2021-08-06&sig=RapTvP68Dq87H92tyQ1vol88Kzu5tVh/wnIKqaY2suc%3D'
    imageOutputFilePath = f"{os.getcwd()}/TrendBot/raw_images/{datetime.now().strftime('%m_%d_%Y')}.png"
    save_image_from_url(image_url, imageOutputFilePath)
    # Post the image and trend with their summaries delimited by a '-' to the Discord
    tweetsAndLink = '\n'.join(trendAndSummaries) + '\n' + image_url
    writeTweetsAndImageToDiscord(tweetsAndLink)
    
main()