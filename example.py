"""
Example usage script demonstrating programmatic usage of the Coinbase downloader
Run this file to see the library in action
"""

from datetime import datetime

from coinbase_downloader import CoinbaseDownloader
from data_handler import DataHandler


def example_list_symbols():
    """Example: List all available symbols."""
    print("=" * 60)
    print("EXAMPLE 1: List Available Symbols")
    print("=" * 60)
    
    downloader = CoinbaseDownloader()
    symbols = downloader.get_available_symbols()
    
    print(f"\nFound {len(symbols)} symbols. First 20:")
    for symbol in sorted(symbols)[:20]:
        print(f"  - {symbol}")
    print()


def example_download_data():
    """Example: Download data for a symbol."""
    print("=" * 60)
    print("EXAMPLE 2: Download Quote Data")
    print("=" * 60)
    
    downloader = CoinbaseDownloader()
    data_handler = DataHandler()
    
    # Download data for BTC-USD from Jan 1 to Jan 7, 2024
    symbol = 'BTC-USD'
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    end_time = datetime(2024, 1, 7, 23, 59, 59)
    
    print(f"\nDownloading data for {symbol}")
    print(f"Time range: {start_time} to {end_time}")
    
    try:
        quotes = downloader.get_historical_data(symbol, start_time, end_time, granularity=3600)  # 1 hour granularity
        
        print(f"✓ Downloaded {len(quotes)} quotes (1-hour granularity)")
        
        # Save to CSV
        quotes_file = f"{symbol}_quotes.csv"
        
        data_handler.save_quotes_to_csv(quotes, quotes_file)
        
        print(f"✓ Saved to {quotes_file}")
        
        # Display sample data
        if quotes:
            print("\nSample quote data (first 3):")
            for quote in quotes[:3]:
                print(f"  {quote['time']}: O={quote['open']}, H={quote['high']}, "
                      f"L={quote['low']}, C={quote['close']}, V={quote['volume']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()


def example_load_data():
    """Example: Load previously downloaded data."""
    print("=" * 60)
    print("EXAMPLE 3: Load Data from CSV")
    print("=" * 60)
    
    data_handler = DataHandler()
    
    try:
        # Try to load previously saved data
        trades = data_handler.load_trades_from_csv("BTC-USD_trades.csv")
        quotes = data_handler.load_quotes_from_csv("BTC-USD_quotes.csv")
        
        print(f"\n✓ Loaded {len(trades)} trades and {len(quotes)} quotes")
        
    except FileNotFoundError:
        print("\n⚠ No saved CSV files found. Run EXAMPLE 2 first to generate them.")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Coinbase Data Downloader - Example Usage")
    print("=" * 60 + "\n")
    
    # Run examples
    example_list_symbols()
    # Uncomment below to actually download data (will make API calls)
    # example_download_data()
    # example_load_data()
    
    print("=" * 60)
    print("To download data, call example_download_data() in the script")
    print("or use: python main.py download BTC-USD --start 20240101-00:00:00 --end 20240107-23:59:59")
    print("=" * 60)
