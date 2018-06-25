"""Library for accessing the local datastore.
"""


import datetime
import os
import pathlib
import shelve

import sh
from sh import at
from sh import atrm

import fetcher


class Error(Exception):
  """Base error class."""


class EntryExistsError(Error):
  """Entry already exists."""


class EntryDoesNotExistError(Error):
  """Entry does not exists."""


class Datastore(object):
  """The local datastore of all program information."""

  DEFAULT_DIRECTORY = os.path.join(str(pathlib.Path.home()), '.stock_tracker')

  def __init__(self, base=DEFAULT_DIRECTORY):
    if not os.path.exists(base):
      os.makedirs(base)
    databases = ('history',
                 'watchlist',
                 'picklist',
                 'positions')

    # set database filename attr
    for db in databases:
      setattr(self, '_{}_file'.format(db), os.path.join(base, db))

    # define getters that return dict copies of the databases
    for db in databases:
      setattr(self, 'get_{}'.format(db), self.__make_getter(db))

  def __make_getter(self, db):
    """Makes a getter method for a specific database."""
    filename = getattr(self, '_{}_file'.format(db))
    def fn():
      with shelve.open(filename) as db:
        return dict(db)
    return fn

  def _add_history_record(self, ticker, *args):
    record = (now_tuple(),) + args
    with shelve.open(self._history_file) as history:
      if ticker not in history:
        history[ticker] = [record]
      else:
        history[ticker] += [record]

  def _remove_from_picklist_in_future(self, ticker, hours):
    """Use the system 'at' command to run 'unpick' at a future time."""
    job_id = None
    script = os.path.abspath(__file__)
    cmd = '{} unpick {}'.format(script, ticker)
    when = 'now + {} hours'.format(hours)
    for line in at(when, _in=cmd, _iter=True, _err_to_out=True):
      if job_id is None and 'job' in line:
        words = line.split()
        job_id = int(words[words.index('job') + 1]) # next word after 'job'
    return job_id

  def _cancel_future_removal_from_picklist(self, at_job_id):
    try:
      atrm(at_job_id)
    except sh.ErrorReturnCode_1 as e:
      if 'Cannot find jobid' in str(e.stderr):
        return
      raise

  def _add_position(self, sale_type, ticker, shares, price):
    with shelve.open(self._positions_file) as positions:
      p = positions.setdefault(ticker, {'transactions': []})
      p['transactions'].append((now_tuple(), sale_type, shares, price))
      positions[ticker] = p
    self._add_history_record(ticker, sale_type, shares, price)

  def _calc_position_summary(self, ticker, pos):
    trans = pos['transactions']
    buy_trans = [t for t in trans if t[1] == 'buy']
    sell_trans = [t for t in trans if t[1] == 'sell']
    bought = sum(t[2] for t in buy_trans)
    sold = sum(t[2] for t in sell_trans)
    holding = bought - sold
    avg = sum(t[3] for t in buy_trans)/len(buy_trans)
    return {'holding': holding,
            'average_cost': avg,
            'bought': bought,
            'sold': sold,
            'last_update': trans[0][0]}

  def update_position(self, ticker, **kwargs):
    with shelve.open(self._positions_file, writeback=True) as positions:
      if ticker not in positions:
        raise EntryDoesNotExistError('No position for {}'.format(ticker))
      positions[ticker].update(kwargs)

  def add_buy(self, ticker, shares, price, **attrs):
    self._add_position('buy', ticker, shares, price)
    if attrs:
      self.update_position(ticker, **attrs)

  def add_sell(self, ticker, shares, price):
    self._add_position('sell', ticker, shares, price)

  def get_position_summary(self, ticker):
    with shelve.open(self._positions_file) as positions:
      return self._calc_position_summary(ticker, positions[ticker])

  def get_all_position_summaries(self):
    summaries = {}
    with shelve.open(self._positions_file) as positions:
      for ticker, pos in positions.items():
        summaries[ticker] = self._calc_position_summary(ticker, pos)
        summaries[ticker].update({'stoploss': pos.get('stoploss'),
                                  'takeprofit': pos.get('takeprofit')})
    return summaries

  def add_to_watchlist(self, ticker, note):
    with shelve.open(self._watchlist_file) as watchlist:
      if ticker in watchlist:
        raise EntryExistsError('{} already in watchlist'.format(ticker))
      watchlist[ticker] = {'note': note,
                           'timestamp': now_tuple(),
                           'prices': fetcher.get_OHLCV(ticker)}
    self._add_history_record(ticker, 'watch', note)

  def remove_from_watchlist(self, ticker):
    with shelve.open(self._watchlist_file) as watchlist:
      if ticker not in watchlist:
        raise EntryDoesNotExistError('{} not in watchlist'.format(ticker))
      del watchlist[ticker]
    self._add_history_record(ticker, 'unwatch')

  def add_to_picklist(self, ticker, note):
    with shelve.open(self._picklist_file) as picklist:
      if ticker in picklist:
        raise EntryExistsError('{} already in picklist'.format(ticker))
      at_job_id = self._remove_from_picklist_in_future(ticker, 24)
      picklist[ticker] = {'note': note,
                          'at_job_id': at_job_id,
                          'timestamp': now_tuple(),
                          'prices': fetcher.get_OHLCV(ticker)}
    self._add_history_record(ticker, 'pick', note)

  def remove_from_picklist(self, ticker):
    with shelve.open(self._picklist_file) as picklist:
      if ticker not in picklist:
        raise EntryDoesNotExistError('{} not in picklist'.format(ticker))
      self._cancel_future_removal_from_picklist(picklist[ticker]['at_job_id'])
      del picklist[ticker]
    self._add_history_record(ticker, 'unpick')


def now_tuple():
  """Get the current datetime as a time-tuple."""
  return tuple(datetime.datetime.now().utctimetuple())


