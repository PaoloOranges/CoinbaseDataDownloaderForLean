#!/usr/bin/env python3
"""
Coinbase Data Downloader for LEAN
Main entry point for the console application
"""

import argparse
import logging
import logging.handlers
import sys
from pathlib import Path

from coinbase_downloader import CoinbaseDownloader
from data_handler import DataHandler
from utils import (
    GRANULARITY_SECONDS,
    parse_datetime,
    parse_iso_datetime,
    parse_symbols_file,
    validate_symbol_format,
)


def setup_logging(verbose: bool = False, output_dir: str = None) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if output_dir:
        log_file = Path(output_dir) / "coinbase_downloader.log"
        handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when='midnight', interval=1, backupCount=7
        )
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)


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


def download_data(output_dir: str, symbols_file: str, symbols: list, granularity: str, keep_csv: bool = False) -> None:
    """Download historical data for specified symbols."""
    logger = logging.getLogger(__name__)
    
    try:
        # Load symbols
        if not symbols:
            symbols = parse_symbols_file(symbols_file)
            if not symbols:
                raise ValueError(f"No symbols found in {symbols_file}")
        
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
        data_dir = Path(symbols_file).parent
        timestamps = data_handler.load_timestamps(data_dir)
        
        logger.info(f"Starting download for {len(symbols)} symbol(s)")
        logger.info(f"Granularity: {granularity} ({granularity_seconds} seconds)")
        logger.info(f"Keep CSV files: {keep_csv}")
        
        from datetime import datetime, timedelta
        
        for symbol in symbols:
            try:
                last_timestamp_str = timestamps.get(symbol, {}).get(granularity)
                if last_timestamp_str:
                    start_dt = parse_iso_datetime(last_timestamp_str) + timedelta(seconds=granularity_seconds)
                else:
                    # Default to 1 year ago if no timestamp
                    start_dt = datetime.now() - timedelta(days=730)
                
                end_dt = datetime.now()
                
                if start_dt >= end_dt:
                    logger.info(f"✓ {symbol}: No new data to download")
                    continue
                
                logger.info(f"Downloading data for {symbol} from {start_dt} to {end_dt}...")
                
                # Download data
                quotes, max_timestamp = downloader.get_historical_data(
                    symbol=symbol,
                    start_time=start_dt,
                    end_time=end_dt,
                    granularity=granularity_seconds
                )
                
                if quotes:
                    # Save to compressed ZIP files with new folder structure
                    data_handler.save_quotes_by_day(quotes, output_path, granularity, keep_csv=keep_csv)
                    
                    # Update timestamp
                    if max_timestamp:
                        timestamps.setdefault(symbol, {})[granularity] = max_timestamp
                    
                    logger.info(f"✓ {symbol}: {len(quotes)} quotes saved")
                    print(f"✓ {symbol}: Saved {len(quotes)} quotes to ZIP file(s)")
                else:
                    logger.info(f"✓ {symbol}: No new quotes")
                    print(f"✓ {symbol}: No new quotes")
                
            except Exception as e:
                logger.error(f"Failed to download data for {symbol}: {e}")
                print(f"✗ {symbol}: Error - {e}")
        
        # Save updated timestamps
        data_handler.save_timestamps(data_dir, timestamps)
        
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
  
  # Download data for symbols from file (default)
  python main.py download --output ./data
  
  # Download data for specific symbols
  python main.py download --symbols BTC-USD ETH-EUR --output ./data
  
  # Download data for symbols from custom file
  python main.py download --symbols-file my-symbols.txt --output ./data --granularity HOUR
  
  # Use verbose logging
  python main.py -v download --output ./data
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
        '--symbols',
        nargs='*',
        help='Symbol(s) to download (e.g., BTC-USD, ETH-EUR). If not provided, read from symbols-file'
    )
    download_parser.add_argument(
        '--symbols-file',
        default='data/coinbase-download-symbols.txt',
        help='File containing symbols to download (default: data/coinbase-download-symbols.txt)'
    )
    download_parser.add_argument(
        '--output',
        required=True,
        help='Output directory for CSV files'
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
    setup_logging(args.verbose, getattr(args, 'output', None))
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'list-symbols':
            list_symbols()
        elif args.command == 'download':
            download_data(
                output_dir=args.output,
                symbols_file=args.symbols_file,
                symbols=args.symbols or [],
                granularity=args.granularity,
                keep_csv=args.keep_csv
            )
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
