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

from coinbase_downloader.downloader.binance_downloader import BinanceDownloader
from coinbase_downloader.downloader.coinbase_downloader import CoinbaseDownloader
from coinbase_downloader.handlers.data_handler import DataHandler
from coinbase_downloader.utils.utils import (
    GRANULARITY_SECONDS,
    parse_datetime,
    parse_iso_datetime,
    parse_symbols_file,
)


def get_downloader(exchange: str = 'coinbase'):
    """Return the configured exchange downloader."""
    normalized = (exchange or 'coinbase').lower()
    if normalized == 'coinbase':
        return CoinbaseDownloader()
    if normalized == 'binance':
        return BinanceDownloader()
    raise ValueError(f"Unsupported exchange: {exchange}")


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


def list_symbols(exchange: str = 'coinbase') -> None:
    """List all available symbols on the selected market."""
    logger = logging.getLogger(__name__)
    logger.info("Fetching available symbols...")

    try:
        downloader = get_downloader(exchange)
        symbols = downloader.get_available_symbols()

        if not symbols:
            print("No symbols found.")
            return

        exchange_name = (exchange or 'coinbase').capitalize()
        print(f"\nAvailable {exchange_name} symbols ({len(symbols)} total):\n")
        for symbol in sorted(symbols):
            print(f"  {symbol}")
        print()

    except Exception as e:
        logger.error(f"Failed to fetch symbols: {e}")
        sys.exit(1)


def download_data(output_dir: str, symbols_file: str, symbols: list, granularity: str, keep_csv: bool = False, start_time: str = None, end_time: str = None, exchange: str = 'coinbase') -> None:
    """Download historical data for specified symbols."""
    logger = logging.getLogger(__name__)

    try:
        downloader = get_downloader(exchange)
        resolved_symbols_file = symbols_file or downloader.default_symbols_file
        if not symbols:
            symbols = parse_symbols_file(resolved_symbols_file, exchange=exchange)
            if not symbols:
                raise ValueError(f"No symbols found in {resolved_symbols_file}")

        invalid_formats = [symbol for symbol in symbols if not downloader.validate_symbol(symbol)]
        if invalid_formats:
            raise ValueError(f"Invalid symbol format(s): {', '.join(invalid_formats)}")

        granularity_seconds = downloader.granularity_map[granularity]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        available_symbols = downloader.get_available_symbols()
        unknown_symbols = [symbol for symbol in symbols if symbol not in available_symbols]
        if unknown_symbols:
            raise ValueError(f"Unknown symbol(s): {', '.join(unknown_symbols)}")

        data_handler = DataHandler()
        data_dir = Path(resolved_symbols_file).parent if resolved_symbols_file else Path(output_dir)
        timestamps = data_handler.load_timestamps(data_dir, downloader.timestamps_filename)

        logger.info(f"Starting download for {len(symbols)} symbol(s)")
        logger.info(f"Granularity: {granularity} ({granularity_seconds} seconds)")
        logger.info(f"Keep CSV files: {keep_csv}")

        from datetime import datetime, timedelta, timezone

        for symbol in symbols:
            try:
                if start_time:
                    start_dt = parse_datetime(start_time)
                else:
                    last_timestamp_str = timestamps.get(symbol, {}).get(granularity)
                    if last_timestamp_str:
                        start_dt = parse_iso_datetime(last_timestamp_str) + timedelta(seconds=granularity_seconds)
                    else:
                        start_dt = datetime.now(tz=timezone.utc) - timedelta(days=730)

                if end_time:
                    end_dt = parse_datetime(end_time)
                else:
                    end_dt = (datetime.now(tz=timezone.utc).replace(hour=23, minute=59, second=59) - timedelta(days=1))

                if start_dt >= end_dt:
                    logger.info(f"✓ {symbol}: No new data to download")
                    continue

                logger.info(f"Downloading data for {symbol} from {start_dt} to {end_dt}...")

                quotes, max_timestamp = downloader.get_historical_data(
                    symbol=symbol,
                    start_time=start_dt,
                    end_time=end_dt,
                    granularity=granularity_seconds
                )

                if quotes:
                    data_handler.save_quotes_by_day(quotes, output_path, granularity, keep_csv=keep_csv)

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

        data_handler.save_timestamps(data_dir, timestamps, downloader.timestamps_filename)

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
        description='Download quote data from Coinbase or Binance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List Coinbase symbols (default exchange)
  python main.py list-symbols

  # List Binance symbols separately
  python main.py list-symbols --exchange binance
  
  # Download Coinbase symbols from the default Coinbase symbols file
  python main.py download --output ./data

  # Download Binance symbols from the default Binance symbols file
  python main.py download --exchange binance --output ./data
  
  # Download specific Coinbase symbols
  python main.py download --symbols BTC-USD ETH-EUR --output ./data

  # Use one BASE-QUOTE symbols file with either exchange
  python main.py download --exchange coinbase --symbols-file shared-symbols.txt --output ./data
  python main.py download --exchange binance --symbols-file shared-symbols.txt --output ./data
  
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
    parser.add_argument(
        '--exchange',
        choices=['coinbase', 'binance'],
        default='coinbase',
        help='Exchange to query or download from; each command uses one exchange (default: coinbase)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True
    
    # List symbols command
    list_symbols_parser = subparsers.add_parser(
        'list-symbols',
        help='List all available symbols on the selected exchange'
    )
    list_symbols_parser.add_argument(
        '--exchange',
        choices=['coinbase', 'binance'],
        default='coinbase',
        help='Exchange whose symbols to list (one exchange per command; default: coinbase)'
    )
    
    # Download command
    download_parser = subparsers.add_parser(
        'download',
        help='Download historical quote data'
    )
    download_parser.add_argument(
        '--exchange',
        choices=['coinbase', 'binance'],
        default='coinbase',
        help='Exchange to download from (default: coinbase)'
    )
    download_parser.add_argument(
        '--symbols',
        nargs='*',
        help='Exchange-native symbol(s) to download. Use --symbols-file for shared BASE-QUOTE symbols'
    )
    download_parser.add_argument(
        '--symbols-file',
        default=None,
        help='Symbols file (BASE-QUOTE works for both exchanges; Binance symbols are converted). Defaults to an exchange-specific file'
    )
    download_parser.add_argument(
        '--output',
        required=True,
        help='Output directory for CSV files'
    )
    download_parser.add_argument(
        '--granularity',
        choices=['MINUTE', 'HOUR', 'DAILY'],
        default=None,
        help='Granularity of quote data. If omitted, downloads for all granularities (MINUTE, HOUR, DAILY)'
    )
    download_parser.add_argument(
        '--keep-csv',
        action='store_true',
        help='Keep CSV files after compression (default: delete them)'
    )
    download_parser.add_argument(
        '--start-time',
        help='Start time for download in YYYYmmDD-HH:MM:SS format (e.g., 20240101-00:00:00). If not provided, uses timestamp file or defaults to 2 years ago'
    )
    download_parser.add_argument(
        '--end-time',
        help='End time for download in YYYYmmDD-HH:MM:SS format (e.g., 20241231-23:59:59). If not provided, uses current time'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, getattr(args, 'output', None))
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'list-symbols':
            list_symbols(exchange=args.exchange)
        elif args.command == 'download':
            granularity = sorted(GRANULARITY_SECONDS.keys())
            if args.granularity is not None:
                granularity = [args.granularity]

            for g in granularity:
                print(f"==> Running download for granularity: {g}")
                download_data(
                    output_dir=args.output,
                    symbols_file=args.symbols_file,
                    symbols=args.symbols or [],
                    granularity=g,
                    keep_csv=args.keep_csv,
                    start_time=getattr(args, 'start_time', None),
                    end_time=getattr(args, 'end_time', None),
                    exchange=args.exchange,
                )
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
