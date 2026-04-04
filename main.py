#!/usr/bin/env python3
"""
Coinbase Data Downloader for LEAN
Main entry point for the console application
"""

import argparse
import logging
import sys
from pathlib import Path

from coinbase_downloader import CoinbaseDownloader
from data_handler import DataHandler
from utils import GRANULARITY_SECONDS, parse_datetime, validate_symbol_format


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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


def download_data(symbols: list, start_datetime: str, end_datetime: str, output_dir: str, granularity: str, keep_csv: bool = False) -> None:
    """Download historical data for specified symbols."""
    logger = logging.getLogger(__name__)
    
    try:
        # Parse datetime parameters
        start_dt = parse_datetime(start_datetime)
        end_dt = parse_datetime(end_datetime)
        
        if start_dt >= end_dt:
            logger.error("Start datetime must be before end datetime")
            sys.exit(1)
        
        invalid_formats = [symbol for symbol in symbols if not validate_symbol_format(symbol)]
        if invalid_formats:
            raise ValueError(f"Invalid symbol format(s): {', '.join(invalid_formats)}")
        
        granularity_seconds = GRANULARITY_SECONDS[granularity]
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloader = CoinbaseDownloader()
        available_symbols = downloader.get_available_symbols()
        unknown_symbols = [symbol for symbol in symbols if symbol not in available_symbols]
        if unknown_symbols:
            raise ValueError(f"Unknown symbol(s): {', '.join(unknown_symbols)}")
        
        data_handler = DataHandler()
        
        logger.info(f"Starting download for {len(symbols)} symbol(s)")
        logger.info(f"Date range: {start_dt} to {end_dt}")
        logger.info(f"Granularity: {granularity} ({granularity_seconds} seconds)")
        logger.info(f"Keep CSV files: {keep_csv}")
        
        for symbol in symbols:
            try:
                logger.info(f"Downloading data for {symbol}...")
                
                # Download data
                quotes = downloader.get_historical_data(
                    symbol=symbol,
                    start_time=start_dt,
                    end_time=end_dt,
                    granularity=granularity_seconds
                )
                
                # Save to compressed ZIP files with new folder structure
                data_handler.save_quotes_by_day(quotes, output_path, granularity, keep_csv=keep_csv)
                
                logger.info(f"✓ {symbol}: {len(quotes)} quotes saved")
                print(f"✓ {symbol}: Saved {len(quotes)} quotes to ZIP file(s)")
                
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
        description='Download quote data from Coinbase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List all available symbols
  python main.py list-symbols
  
  # Download data for a single symbol (default minute granularity)
  python main.py download ETH-EUR --start 20240101-00:00:00 --end 20240131-23:59:59
  
  # Download data for multiple symbols with hour granularity
  python main.py download BTC-USD ETH-EUR --start 20240101-00:00:00 --end 20240131-23:59:59 --output ./data --granularity HOUR
  
  # Download daily data for a symbol
  python main.py download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59 --granularity DAILY
  
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
        help='Download historical quote data'
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
    download_parser.add_argument(
        '--granularity',
        choices=['MINUTE', 'HOUR', 'DAILY'],
        default='MINUTE',
        help='Granularity of quote data (default: MINUTE)'
    )
    download_parser.add_argument(
        '--keep-csv',
        action='store_true',
        help='Keep CSV files after compression (default: delete them)'
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
                output_dir=args.output,
                granularity=args.granularity,
                keep_csv=args.keep_csv
            )
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
