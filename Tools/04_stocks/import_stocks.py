import sys
import os

project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# set up warnings
from common.bootstrap import setup_warnings
setup_warnings()

from common.settings import setup_logger
logger = setup_logger(name=__name__)
logger.info('Path added to sys.path: {}'.format(project_root))

import gc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas_datareader import data as pdr
import yfinance as yf
import datetime
import time


class DataSourceError(Exception):
    pass

class JapanStockModel(object):
    """
    (.venv) 04_stocks$ pip install pandas matplotlib pandas-datareader yfinance
    """
    def __init__(self, _ticker_symbol, _start, _end=str(datetime.date.today())):
        self.train = None
        self.ticker_symbol = _ticker_symbol
        self.start = _start
        self.end = _end
        self._duration = 30

    @staticmethod
    def fetch_by_yfinance(ticker: int, start: str, end: str) -> pd.DataFrame:
        symbol = f"{ticker}.T"
        try:
            time.sleep(1.0)  # レート制限回避のため控えめに
            df = yf.download(symbol, start=start, end=end, progress=False, threads=False)
        except Exception as e:
            raise DataSourceError(f"yfinance failed: {symbol}: {e}")

        if df.empty:
            raise DataSourceError(f"yfinance returned empty dataframe: {symbol}")

        if "Close" not in df.columns:
            raise DataSourceError(
                f"yfinance missing Close column: {symbol}, columns={list(df.columns)}"
            )
        return df

    @staticmethod
    def fetch_japan_stock_by_pdr_stooq(
            _ticker_symbol: int, _start: str, _end: str) -> pd.DataFrame:
        """
        2025.05 ~ yfinace cannot response our request.
                          then, change to pandas_datareader by stooq
        https://stooq.com/
        """
        logger.info('fetch_japan_stock_by_pdr_stooq: ticker=%s, start=%s, end=%s', _ticker_symbol, _start, _end)
        ticker_symbol_dr = f"{_ticker_symbol}.JP"
        try:
            df = pdr.DataReader(ticker_symbol_dr, "stooq", start=_start, end=_end)
        except Exception as e:
            logger.warning("Failed to download %s: %s", ticker_symbol_dr, e)
            return pd.DataFrame()

        if df.empty:
            logger.warning("Downloaded empty dataframe: %s", ticker_symbol_dr)
            return pd.DataFrame()

        logger.info("Downloaded %s rows for %s", len(df), ticker_symbol_dr)
        return df

    @staticmethod
    def fetch_by_stooq(ticker: int, start: str, end: str) -> pd.DataFrame:
        symbol = f"{ticker}.JP"
        try:
            df = pdr.DataReader(symbol, "stooq", start=start, end=end)
        except Exception as e:
            raise DataSourceError(f"stooq failed: {symbol}: {e}")

        if df.empty:
            raise DataSourceError(f"stooq returned empty dataframe: {symbol}")

        if "Close" not in df.columns:
            raise DataSourceError(
                f"stooq missing Close column: {symbol}, columns={list(df.columns)}"
            )
        return df.sort_index()

    def fetch_stock_dataframe(self, ticker: int, start: str, end: str) -> pd.DataFrame:
        errors = []

        for fetcher in (self.fetch_by_stooq, self.fetch_by_yfinance):
            try:
                return fetcher(ticker, start, end)
            except DataSourceError as e:
                errors.append(str(e))

        raise DataSourceError(" | ".join(errors))

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    def import_data(self):
        # self.train, self.test, self.sample = self._import_csv()
        # self.train = self.fetch_japan_stock_by_pdr_stooq(
        #     self.ticker_symbol, self.start, self.end)
        self.train = self.fetch_stock_dataframe(
            self.ticker_symbol, self.start, self.end)
        if self.train.empty:
            raise ValueError(f"No stock data found for ticker={self.ticker_symbol}")

        if 'Close' not in self.train.columns:
            raise ValueError(
                f"Close column not found for ticker={self.ticker_symbol}. columns={list(self.train.columns)}"
            )

    def plot_stock(self):
        self.train['Close'].plot(figsize=(12, 6), color='green')
        plt.show()


def fetch_stock_dataframe(
        company_code, start='2010-01-01', end=str(datetime.date.today()), span=30):
    if company_code is None:
        return None

    dataset = JapanStockModel(company_code, start, end)
    dataset.duration = span
    dataset.import_data()

    if dataset.train is None or dataset.train.empty:
        return pd.DataFrame(columns=['year', 'value'])

    if 'Close' not in dataset.train.columns:
        raise ValueError(f"Close column not found: columns={list(dataset.train.columns)}")

    d_year = dataset.train.index.to_list()
    data = np.array(dataset.train['Close']).ravel()

    df = pd.DataFrame({
        'year': d_year,
        'value': data,
    })

    del dataset
    return df


def main_no_prediction():
    """
    Test this clas.

    fetch GMO stock and plot graph.
    """
    ticker_symbols = {'GMO': 7177,
                      'JapanCeramic': 6929,
                      'MHI': 7011,
                      'Zaoh': 9986,
                      'mirai': 7931}
    start = '2000-01-01'
    end = str(datetime.date.today())
    span = 365

    machin_learning = JapanStockModel(ticker_symbols['GMO'], start, end)
    # machin_learning = JapanStockModel(7203, '2023-01-01', '2023-12-01')
    machin_learning.duration = span
    machin_learning.import_data()
    machin_learning.plot_stock()


def main():
    # ticker = 7203  # Toyota
    ticker = 9986  # Zaoh
    start = '1990-01-01'
    end = str(datetime.date.today())
    span = 365
    data = fetch_stock_dataframe(ticker, start, end, span)
    logger.info(data)


if __name__ == '__main__':
    # main_no_prediction()
    main()

    gc.collect()
    logger.info({'action': 'garbage collection', 'gc': gc.get_stats()[2]})