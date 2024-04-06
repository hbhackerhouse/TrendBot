import os
import requests
from openai import OpenAI

OPEN_AI = OpenAI(
    api_key=os.environ.get("openai_key")
)

def createSummaryFromTrendTweets(relatedTweets, trendTropic):
    try:
        aggregatedTweets = "\n".join(relatedTweets)
        prompt = f"Summarize the tweets about '{trendTropic}' into one sentence with no dashes. Here are the tweets separated by new line characters\
            and may not be related to each other. If they are not related only keep the one's that appear the most often: \n{aggregatedTweets}"

        response = OPEN_AI.chat.completions.create(
            model="gpt-3.5-turbo-0125",  # GPT-3.5
            messages=[{"role": "system", "content": prompt}],
            max_tokens=60  # Length
        )
        
        return response.choices[0].message.content
    except Exception as e:
        pass

def generatePrompt(allTopicsFromAllTrends):
    return 'Create a music album cover using these topics:' + ','.join(allTopicsFromAllTrends)

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
        pass