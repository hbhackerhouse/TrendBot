import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import chromedriver_binary
from bs4 import BeautifulSoup

ENV = os.getenv('environment')
TWITTER_USERNAME = os.getenv('twitter_username')
TWITTER_PASSWORD = os.getenv('twitter_password')

def scrapeTweetsFromTrendURL(trendURL):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("user-data-dir=selenium") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    if (ENV and ENV == 'PROD'):
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

    loginUrl = "https://twitter.com/i/flow/login"
    driver.get(loginUrl)

    username = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
    username.send_keys(TWITTER_USERNAME)
    username.send_keys(Keys.ENTER)

    password = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
    password.send_keys(TWITTER_PASSWORD)
    password.send_keys(Keys.ENTER)

    time.sleep(10)

    driver.get(trendURL)

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