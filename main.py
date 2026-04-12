#!/usr/bin/env python3
"""
Wrapper script for backward compatibility.
Delegates to coinbase_downloader.cli.main
"""

from coinbase_downloader.cli.main import main

if __name__ == '__main__':
    main()
