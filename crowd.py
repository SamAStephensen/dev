import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

def fetch_news(ticker, api_key):
    # Define the News API URL with parameters
    url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={api_key}"

    # Make a request to the News API
    response = requests.get(url)
    news_data = response.json()
    print(news_data)
    print('hello')
    # Extract articles from the response
    articles = news_data['articles']

    return articles

def analyze_sentiment(articles):
    # Initialize VADER sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()

    # List to store article sentiment data
    sentiment_data = []

    for article in articles:
        # Get the article title and description
        title = article['title']
        description = article['description']
        date = article['publishedAt']

        # Combine the title and description for sentiment analysis
        text = f"{title}. {description}"

        # Get sentiment score from VADER
        sentiment_score = analyzer.polarity_scores(text)

        # Store the sentiment data
        sentiment_data.append({
            'Date': date,
            'Sentiment': sentiment_score['compound'],
            'Title': title,
            'URL': article['url']
        })

    return sentiment_data

def fetch_and_analyze(ticker, api_key):
    # Fetch the latest news articles about the ticker
    articles = fetch_news(ticker, api_key)

    # Analyze the sentiment of the fetched articles
    sentiment_data = analyze_sentiment(articles)

    # Convert the sentiment data into a DataFrame
    sentiment_df = pd.DataFrame(sentiment_data)

    # Display the sentiment DataFrame
    print(sentiment_df)            
    max_date = sentiment_df['Date'].max()
    min_date = sentiment_df['Date'].min()
    print(max_date)
    print(min_date)
    return sentiment_df

# Example usage
api_key = '0ff5bb13046c4a61ac76ec61e16575f6'  # Replace with your actual NewsAPI key
ticker = 'AAPL'  # Example ticker symbol

sentiment_df = fetch_and_analyze(ticker, api_key)
