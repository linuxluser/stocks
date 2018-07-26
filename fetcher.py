
"""A library for fetching remote stock data as a pandas.Dataframe.
"""


import datetime
import os
import time

import pandas as pd
import pandas_datareader as pdr
from pandas_datareader._utils import RemoteDataError


# Time offset
UTC_OFFSET = -7  # PST timezone


class DataSource(object):
  """Holds data-source-specific constants."""

  SOURCE = 'yahoo'
  CLOSE  = 'Close'
  OPEN   = 'Open'
  HIGH   = 'High'
  LOW    = 'Low'
  VOLUME = 'Volume'


class DataFetcher(object):
  """Fetches stock data and caches it locally.

  DataFetcher tries to be smart by only fetching if there is no local data or if
  the market is still open. If the market is closed, DataFetcher will not attempt
  to fetch any more data about a stock (unless it does not have any or it is from
  another day).
  """

  def __init__(self):
    self.tmp_dir = '/tmp/_stock_fetcher_cache_'
    if not os.path.exists(self.tmp_dir):
      os.mkdir(self.tmp_dir)

  def _MinutesInMarket(self, dt):
    """Provide the number of minutes this datetime object falls within market hours.

    0 if it falls outside of market hours.
    """
    # Batteries NOT included: we have to make our own class to represent the timezone
    class TZInfo(datetime.tzinfo):
      utcoffset = lambda self, dt: datetime.timedelta(hours=UTC_OFFSET)
      dst = lambda self, dt: datetime.timedelta(0)
      tzname = lambda self, dt: '{:+03d}00'.format(UTC_OFFSET)

    # Use our custom tzinfo class if none exists for dt
    if dt.tzinfo == None:
      dt = dt.replace(tzinfo=TZInfo())

    # Convert to UTC
    utc_dt = dt.astimezone(datetime.timezone.utc)

    # Closed on weekends
    saturday, sunday = 5, 6
    if utc_dt.weekday() in (saturday, sunday):
      return 0, 0

    open_time = datetime.time(14, 30)  # NYSE in UTC
    closed_time = datetime.time(21, 00)  # NYSE in UTC
    t = utc_dt.time()
    if t < open_time or t > closed_time:
      return 0, 0

    open_m = (open_time.hour * 60) + open_time.minute
    closed_m = (closed_time.hour * 60) + closed_time.minute
    t_m = (t.hour * 60) + t.minute
    since_open_m = t_m - open_m
    before_close_m = closed_m - t_m
    return since_open_m, before_close_m

  def _IsMarketClosed(self, ticker):
    since, before = self._MinutesInMarket(datetime.datetime.now(datetime.timezone.utc))
    return since == before == 0

  def _FileTimeDuringMarketOpen(self, file_time):
    since, before = self._MinutesInMarket(datetime.datetime.fromtimestamp(file_time))
    return (since, before) != (0, 0)

  def _FileTimeIsToday(self, file_time):
    t = datetime.datetime.now()
    f = datetime.datetime.fromtimestamp(file_time)
    return (t.day, t.month, t.year) == (f.day, f.month, f.year)

  def _IsDataFileStale(self, ticker, data_file):
    if not os.path.exists(data_file):
      return True
    file_time = os.path.getmtime(data_file)
    if self._IsMarketClosed(ticker):
      if not self._FileTimeIsToday(file_time):
        return True
      return self._FileTimeDuringMarketOpen(file_time)
    else:
      file_age = time.time() - file_time
      return file_age > 300

  def FetchData(self, ticker):
    data_file = os.path.join(self.tmp_dir, ticker)
    if self._IsDataFileStale(ticker, data_file):
      df = None
      while df is None:
        try:
          df = pdr.data.DataReader(ticker, DataSource.SOURCE)
        except RemoteDataError:
          time.sleep(0.5)
      df.to_pickle(data_file)
    else:
      df = pd.read_pickle(data_file)
    return df


def get_OHLCV(ticker):
  """Convenience function to get the open, high, low, close and volume of today."""
  df = DataFetcher().FetchData(ticker).tail(1)
  return {'open': float(df[DataSource.OPEN]),
          'high': float(df[DataSource.HIGH]),
          'low': float(df[DataSource.LOW]),
          'close': float(df[DataSource.CLOSE]),
          'volume': float(df[DataSource.VOLUME])}
