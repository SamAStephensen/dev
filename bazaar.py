import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

class MarketIngest:

    def __init__(self, data_folder='/data/stocks'):
        self.data_folder = data_folder
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def get_data(self, ticker, start_date="1900-01-01", end_date=datetime.today().strftime('%Y-%m-%d')):
        """
        Get historical data for a stock ticker from Yahoo Finance and store it in a Parquet file for the specified date range.
        """
        print(f"Fetching historical data for {ticker} from {start_date} to {end_date}...")
        data = yf.download(ticker, start=start_date, end=end_date)
        
        # Ensure data is not empty
        if data.empty:
            print(f"No data found for {ticker} in the given date range.")
            return

        # Save historical data to Parquet file
        file_path = os.path.join(self.data_folder, f"{ticker}.parquet")
        data.to_parquet(file_path, engine='pyarrow', index=False)
        print(f"Data for {ticker} from {start_date} to {end_date} saved to {file_path}")


    def find_file(self, ticker):
        """
        Check if file exists for specified ticker.
        """
        file_path = os.path.join(self.data_folder, f"{ticker}.parquet")
        path = os.path.exists(file_path)
        if not path:
            print(f"File for {ticker} not found. Fetching historical data...")
          
        return path
        
    def get_last_date(self, ticker):
        """
        Get the most recent date from the stock data file for the given ticker.
        """
        # Read Parquet file
        
        file_path = os.path.join(self.data_folder, f"{ticker}.parquet")
        data = pd.read_parquet(file_path, engine='pyarrow')
        
        if not data.empty:
            # Get the most recent date from the file
            most_recent_date = data['Date'].max()
            print(f"The most recent date for {ticker} is {most_recent_date}")
            return most_recent_date
        else:
            print(f"No data available for {ticker}")
            return None

    def update_data(self, ticker):
        """
        Get the current day's stock data for a ticker and append it to the Parquet file.
        """
        if find_file:
            current_date = datetime.today().strftime('%Y-%m-%d')
            last_date = self.get_last_date(ticker) 
            print(f"Fetching current day's data for {ticker}...")
            self.get_data(ticker, last_date, current_date)

# Example usage
if __name__ == "__main__":
    tickers = ['AAPL', 'GOOGL', 'AMZN']
    
    pipeline = MarketIngest(data_folder='/data/stocks')

    # Fetch historical data for all tickers (for a given date range)
    for ticker in tickers:
        pipeline.get_historical_data(ticker, start_date="2020-01-01", end_date="2021-01-01")

    # Get most recent date for a specific stock and perform updates
    for ticker in tickers:
        pipeline.get_most_recent_date(ticker)

    # Get current day's data and append to the Parquet file
    for ticker in tickers:
        pipeline.get_current_day_data(ticker)
