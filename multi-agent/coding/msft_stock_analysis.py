# filename: msft_stock_analysis.py
import pandas as pd
import yfinance as yf
from datetime import datetime

# Ensure we're working with the current date as the `yfinance` library might not return future data.
current_year = datetime.now().year
if current_year > 2024:
    end_year = '2025'
else:
    raise ValueError("Historical data for the year 2024 is not available yet.")

# Download Microsoft stock data for 2024
msft = yf.Ticker("MSFT")
msft_data = msft.history(start="2024-01-01", end=end_year)

# Filter days where the stock was higher than $370
days_higher_than_370 = msft_data[msft_data['Close'] > 370]

# Print the result
print(days_higher_than_370.index.strftime('%Y-%m-%d'))