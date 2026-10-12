import sys
from pathlib import Path

import pytest

from coinbase_downloader.cli import main as cli_main
from coinbase_downloader.utils.utils import GRANULARITY_SECONDS, parse_symbols_file, validate_binance_symbol


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


def test_parse_symbols_file_binance(tmp_path):
    content = """
    BTCUSDT, ethusdt
    # a comment line should be ignored
    ADAUSDT;SOLUSDT

    """
    p = tmp_path / "symbols.txt"
    p.write_text(content, encoding='utf-8')

    symbols = parse_symbols_file(str(p), exchange='binance')
    assert symbols == ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]


def test_binance_symbol_validation():
    assert validate_binance_symbol("BTCUSDT")
    assert validate_binance_symbol("ETHUSDT")
    assert not validate_binance_symbol("BTC-USD")
    assert not validate_binance_symbol("BTC")


def test_main_download_calls_download_data_for_each_granularity(monkeypatch, tmp_path):
    calls = []

    def fake_download_data(*args, **kwargs):
        calls.append(kwargs.get('granularity'))

    monkeypatch.setattr(cli_main, 'download_data', fake_download_data)
    monkeypatch.setattr(cli_main, 'setup_logging', lambda *a, **k: None)

    test_args = ['prog', 'download', '--output', str(tmp_path)]
    monkeypatch.setattr(sys, 'argv', test_args)

    cli_main.main()

    expected = sorted(GRANULARITY_SECONDS.keys())
    assert calls == expected


@pytest.mark.parametrize("granularity", ["MINUTE", "HOUR", "DAILY"])
def test_main_download_with_specific_granularity(monkeypatch, tmp_path, granularity):
    calls = []

    def fake_download_data(*args, **kwargs):
        calls.append(kwargs.get('granularity'))

    monkeypatch.setattr(cli_main, 'download_data', fake_download_data)
    monkeypatch.setattr(cli_main, 'setup_logging', lambda *a, **k: None)

    test_args = ['prog', 'download', '--output', str(tmp_path), '--granularity', granularity]
    monkeypatch.setattr(sys, 'argv', test_args)

    cli_main.main()

    assert calls == [granularity]


def test_main_download_supports_binance_exchange(monkeypatch, tmp_path):
    calls = []

    def fake_download_data(*args, **kwargs):
        calls.append(kwargs.get('exchange'))

    monkeypatch.setattr(cli_main, 'download_data', fake_download_data)
    monkeypatch.setattr(cli_main, 'setup_logging', lambda *a, **k: None)

    test_args = ['prog', 'download', '--output', str(tmp_path), '--exchange', 'binance']
    monkeypatch.setattr(sys, 'argv', test_args)

    cli_main.main()

    assert calls and all(call == 'binance' for call in calls)
