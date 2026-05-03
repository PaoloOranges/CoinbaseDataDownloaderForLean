import sys
from pathlib import Path

import pytest

from coinbase_downloader.cli import main as cli_main
from coinbase_downloader.utils.utils import GRANULARITY_SECONDS, parse_symbols_file


def test_parse_symbols_file_csv_and_lines(tmp_path):
    content = """
    BTC-USD, eth-eur
    # a comment line should be ignored
    XRP-USD;LTC-USD

    """
    p = tmp_path / "symbols.txt"
    p.write_text(content, encoding='utf-8')

    symbols = parse_symbols_file(str(p))
    assert symbols == ["BTC-USD", "ETH-EUR", "XRP-USD", "LTC-USD"]


def test_main_download_calls_download_data_for_each_granularity(monkeypatch, tmp_path):
    calls = []

    def fake_download_data(*args, **kwargs):
        # CLI calls download_data with granularity as a keyword
        calls.append(kwargs.get('granularity'))

    # Patch out network/file-creating helpers
    monkeypatch.setattr(cli_main, 'download_data', fake_download_data)
    monkeypatch.setattr(cli_main, 'setup_logging', lambda *a, **k: None)

    test_args = ['prog', 'download', '--output', str(tmp_path)]
    monkeypatch.setattr(sys, 'argv', test_args)

    # Run CLI main which should call our fake_download_data for each granularity
    cli_main.main()

    expected = sorted(GRANULARITY_SECONDS.keys())
    assert calls == expected


@pytest.mark.parametrize("granularity", ["MINUTE", "HOUR", "DAILY"])
def test_main_download_with_specific_granularity(monkeypatch, tmp_path, granularity):
    calls = []

    def fake_download_data(*args, **kwargs):
        calls.append(kwargs.get('granularity'))

    # Patch out network/file-creating helpers
    monkeypatch.setattr(cli_main, 'download_data', fake_download_data)
    monkeypatch.setattr(cli_main, 'setup_logging', lambda *a, **k: None)

    test_args = ['prog', 'download', '--output', str(tmp_path), '--granularity', granularity]
    monkeypatch.setattr(sys, 'argv', test_args)

    # Run CLI main which should call our fake_download_data only for the specified granularity
    cli_main.main()

    assert calls == [granularity]
