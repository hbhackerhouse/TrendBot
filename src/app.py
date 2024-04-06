from apis import TwitterTrendWrapperAPIHelper, OpenAiAPIHelper
from tools import TwitterScraper, DiscordHook, ImageHelper
from Trend import Trend
from Job import Job

# LA
WOEID = 2442047

def main():
    trends = TwitterTrendWrapperAPIHelper.getTwitterTrends(WOEID)
    trendObjects = [Trend(topic=trend['name'], url=trend['url']) for trend in trends[0]['trends'][:5]]

    # For each trend get their related tweets and generate a summary
    for trend in trendObjects:
        relatedTweets = TwitterScraper.scrapeTweetsFromTrendURL(trend.url)
        trend.summary = OpenAiAPIHelper.createSummaryFromTrendTweets(relatedTweets, trend.topic)
    
    # Generate image from all the trend topics
    allTopicsFromAllTrends = [trend.topic for trend in trendObjects]
    imagePrompt = OpenAiAPIHelper.generatePrompt(allTopicsFromAllTrends)
    imageURL = OpenAiAPIHelper.getDalleImageURL(imagePrompt)
    outputImagePath = ImageHelper.save_image_from_url(imageURL)

    # TODO : Generate Song

    discordMessage = f'{outputImagePath}\n'
    for trend in trendObjects:
        discordMessage = f'{discordMessage}\n{trend.topic} - {trend.summary}'
    DiscordHook.writeTopicsandTweetsAndImageToDiscord(discordMessage, outputImagePath)

    job = Job(trendObjects, imagePrompt, outputImagePath)

    # TODO : Discord Listener -> Post to Twitter on 2 reactions
    
main()