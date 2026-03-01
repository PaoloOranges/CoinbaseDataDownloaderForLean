#!/usr/bin/env python3
"""
Coinbase Data Downloader for LEAN
Main entry point for the console application
"""

import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path

from coinbase_downloader import CoinbaseDownloader
from data_handler import DataHandler


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_datetime(datetime_str: str) -> datetime:
    """Parse datetime string in format yyyyMMdd-hh:mm:ss."""
    try:
        return datetime.strptime(datetime_str, '%Y%m%d-%H:%M:%S')
    except ValueError:
        raise ValueError(
            f"Invalid datetime format: {datetime_str}. "
            f"Expected format: yyyyMMdd-hh:mm:ss (e.g., 20240101-09:30:00)"
        )


def list_symbols() -> None:
    """List all available symbols on Coinbase."""
    logger = logging.getLogger(__name__)
    logger.info("Fetching available symbols...")
    
    try:
        downloader = CoinbaseDownloader()
        symbols = downloader.get_available_symbols()
        
        if not symbols:
            print("No symbols found.")
            return
        
        print(f"\nAvailable Coinbase symbols ({len(symbols)} total):\n")
        for symbol in sorted(symbols):
            print(f"  {symbol}")
        print()
        
    except Exception as e:
        logger.error(f"Failed to fetch symbols: {e}")
        sys.exit(1)


def download_data(symbols: list, start_datetime: str, end_datetime: str, output_dir: str) -> None:
    """Download historical data for specified symbols."""
    logger = logging.getLogger(__name__)
    
    try:
        # Parse datetime parameters
        start_dt = parse_datetime(start_datetime)
        end_dt = parse_datetime(end_datetime)
        
        if start_dt >= end_dt:
            logger.error("Start datetime must be before end datetime")
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloader = CoinbaseDownloader()
        data_handler = DataHandler()
        
        logger.info(f"Starting download for {len(symbols)} symbol(s)")
        logger.info(f"Date range: {start_dt} to {end_dt}")
        
        for symbol in symbols:
            try:
                logger.info(f"Downloading data for {symbol}...")
                
                # Download data
                trades, quotes = downloader.get_historical_data(
                    symbol=symbol,
                    start_time=start_dt,
                    end_time=end_dt
                )
                
                # Save to CSV files
                trade_csv = output_path / f"{symbol}_trades_{start_dt.strftime('%Y%m%d_%H%M%S')}_to_{end_dt.strftime('%Y%m%d_%H%M%S')}.csv"
                quote_csv = output_path / f"{symbol}_quotes_{start_dt.strftime('%Y%m%d_%H%M%S')}_to_{end_dt.strftime('%Y%m%d_%H%M%S')}.csv"
                
                data_handler.save_trades_to_csv(trades, trade_csv)
                data_handler.save_quotes_to_csv(quotes, quote_csv)
                
                logger.info(f"✓ {symbol}: {len(trades)} trades and {len(quotes)} quotes saved")
                print(f"✓ {symbol}: Saved {len(trades)} trades to {trade_csv.name}")
                print(f"           Saved {len(quotes)} quotes to {quote_csv.name}")
                
            except Exception as e:
                logger.error(f"Failed to download data for {symbol}: {e}")
                print(f"✗ {symbol}: Error - {e}")
        
        logger.info("Download complete!")
        
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Download operation failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download trade and quote data from Coinbase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List all available symbols
  python main.py list-symbols
  
  # Download data for a single symbol
  python main.py download ETH-EUR --start 20240101-00:00:00 --end 20240131-23:59:59
  
  # Download data for multiple symbols
  python main.py download BTC-USD ETH-EUR --start 20240101-00:00:00 --end 20240131-23:59:59 --output ./data
  
  # Use verbose logging
  python main.py -v download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59
        '''
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True
    
    # List symbols command
    subparsers.add_parser(
        'list-symbols',
        help='List all available symbols on Coinbase'
    )
    
    # Download command
    download_parser = subparsers.add_parser(
        'download',
        help='Download historical trade and quote data'
    )
    download_parser.add_argument(
        'symbols',
        nargs='+',
        help='Symbol(s) to download (e.g., BTC-USD, ETH-EUR)'
    )
    download_parser.add_argument(
        '--start',
        required=True,
        help='Start datetime in format yyyyMMdd-hh:mm:ss (e.g., 20240101-09:30:00)'
    )
    download_parser.add_argument(
        '--end',
        required=True,
        help='End datetime in format yyyyMMdd-hh:mm:ss (e.g., 20240131-23:59:59)'
    )
    download_parser.add_argument(
        '--output',
        default='./data',
        help='Output directory for CSV files (default: ./data)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'list-symbols':
            list_symbols()
        elif args.command == 'download':
            download_data(
                symbols=args.symbols,
                start_datetime=args.start,
                end_datetime=args.end,
                output_dir=args.output
            )
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
