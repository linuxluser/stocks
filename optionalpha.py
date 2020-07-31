"""A library for working with optionalpha.com.

The optionalpha.com watch list is updated daily so we can cache a daily version locally for a speedup.

"""


import datetime
import getpass
from html.parser import HTMLParser
import os
import pathlib
import pickle
import requests
import time
import yaml


LOGIN_URL = 'https://optionalpha.com/wp-login.php'
WATCHLIST_URL = 'https://optionalpha.com/members/watch-list'
COOKIEJAR_PATH = os.path.join(pathlib.Path.home(), '.oawl_cookies')
CACHE_PATH = os.path.join(pathlib.Path.home(), '.oawl_cache')

# Time constants
ONE_DAY = 24 * 60 * 60
TM_WEEKENDS = (5, 6, 0)  # Saturday, Sunday and Monday
WL_CREATION_OFFSET = 23 * 60 * 60  # 6pm EST


class WatchlistItem(object):

  def __init__(self, ticker, price, rank, earnings_date, expected_ranges):
    self.ticker = ticker
    self.price = price
    self.rank = rank
    self.earnings_date = earnings_date
    self.expected_ranges = expected_ranges


class WatchListParser(HTMLParser):

  def __init__(self):
    super().__init__()
    self.__in_oagrid_item_li = False  # main "card" element
    self.__oagrid_item_li_counter = 0
    self.__in_name_h1 = False
    self.__in_stockprice_span = False
    self.__in_earningcornercontainer_div = False
    self.__in_ranges_div = False
    self.__in_ranges_h3 = False
    self.__in_ranges_h4 = False
    self.__in_popup_date_div = False
    self.__expected_ranges_key = ''
    self.watch_list = []
    self._reset_current_data()

  def _reset_current_data(self):
    self.current_data = {
        'ticker': None,
        'price': None,
        'rank': None,
        'earnings_date': None,
        'expected_ranges': {
            'day': (None, None),
            'week': (None, None),
            'month': (None, None),
        },
    }

  def handle_starttag(self, tag, attrs):
    if tag == 'li':
      attrs = dict(attrs)
      if 'class' in attrs and 'oagrid-item' in attrs['class']:
        self.__oagrid_item_li_counter += 1  # count number of <li>
        self.__in_oagrid_item_li = True

        ##### SAVE
        # Save current data as WatchListItem and clear it for new data
        if self.__oagrid_item_li_counter > 1:
          self.watch_list.append(WatchlistItem(**self.current_data))
          self._reset_current_data()

    elif tag == 'h1':
      attrs = dict(attrs)
      if 'class' in attrs and attrs['class'] == 'name':
        self.__in_name_h1 = True
    elif tag == 'span':
      attrs = dict(attrs)
      if 'class' in attrs and attrs['class'] == 'stockprice':
        self.__in_stockprice_span = True
    elif tag == 'div':
      attrs = dict(attrs)
      if 'class' not in attrs:
        return
      if attrs['class'] == 'ranges':
        self.__in_ranges_div = True
      if attrs['class'] == 'earningcornercontainer':
        self.__in_earningcornercontainer_div = True
      elif attrs['class'] == 'popup-date' and self.__in_earningcornercontainer_div:
        self.__in_popup_date_div = True
        self.__in_earningcornercontainer_div = False
      elif attrs['class'] == 'bar-percentage':
        self.current_data['rank'] = int(attrs['data-percentage'])
    if self.__in_ranges_div:
      if tag == 'h4':
        self.__in_ranges_h4 = True
      elif tag == 'h3':
        self.__in_ranges_h3 = True

  def handle_endtag(self, tag):
    if self.__in_oagrid_item_li and tag == 'li':
      self.__in_oagrid_item_li = False
    if self.__in_name_h1 and tag == 'h1':
      self.__in_name_h1 = False
    if self.__in_stockprice_span and tag == 'span':
      self.__in_stockprice_span = False
    if self.__in_popup_date_div and tag == 'div':
      self.__in_popup_date_div = False
    if self.__in_ranges_div and tag == 'div':
      self.__in_ranges_div = False
      self.__in_ranges_h4 = False
      self.__in_ranges_h3 = False
    if self.__in_ranges_h4 and tag == 'h4':
      self.__in_ranges_h4 = False
    if self.__in_ranges_h3 and tag == 'h3':
      self.__in_ranges_h3 = False

  def handle_data(self, data):
    if self.__in_name_h1:
      self.current_data['ticker'] = data.strip()
    elif self.__in_stockprice_span:
      self.current_data['price'] = float(data.strip())
    elif self.__in_popup_date_div:
      data = data.strip()
      if data:
        month, day, year = map(int, data.split('/', 2))
        self.current_data['earnings_date'] = datetime.date(year, month, day)
    elif self.__in_ranges_h4:
      if '1 day' in data.lower():
        self.__expected_ranges_key = 'day'
      elif '1 week' in data.lower():
        self.__expected_ranges_key = 'week'
      elif '1 month' in data.lower():
        self.__expected_ranges_key = 'month'
    elif self.__in_ranges_h3:
      # TODO: Better locale-aware currency parsing
      lower, upper = data.split('-')
      lower = float(lower.replace('$', '').replace(',', '').strip())
      upper = float(upper.replace('$', '').replace(',', '').strip())
      key = self.__expected_ranges_key
      self.current_data['expected_ranges'][key] = (lower, upper)

class WatchListFetcher(object):

  def __init__(self, session):
    self.session = session

  def FetchWatchListPage(self):
    page = self.session.get(WATCHLIST_URL)
    return page.text


def WatchListToYAML(watch_list):
  D = {}
  for item in watch_list:
    D[item.ticker] = {
        'price': item.price,
        'rank': item.rank,
        'earnings_date': item.earnings_date,
        'expected_ranges': item.expected_ranges,
    }
  return yaml.safe_dump({'WatchList': D}, explicit_start=True, default_flow_style=False)


def YAMLToWatchList(S):
  watch_list = []
  obj = yaml.safe_load(S)
  for ticker,v in obj['WatchList'].items():
    item = WatchlistItem(ticker=ticker,
                         price=v.get('price'),
                         rank=v.get('rank'),
                         earnings_date=v.get('earnings_date'),
                         expected_ranges=v.get('expected_ranges'))
    watch_list.append(item)
  watch_list.sort(key=lambda x: (x.rank, x.ticker))
  return watch_list


def GetOptionAlphaSession():
  if os.path.exists(COOKIEJAR_PATH):
    with open(COOKIEJAR_PATH, 'rb') as f:
      session = pickle.load(f)
    # TODO: check for expired session
  else:
    session = requests.Session()
    login = input('   Login: ')
    password = getpass.getpass('Password: ')
    session.post(LOGIN_URL, data={'log': login, 'pwd': password})
    with open(COOKIEJAR_PATH, 'wb') as f:
      pickle.dump(session, f)
  return session


def _IsCacheExpired():
  if not os.path.exists(CACHE_PATH):
    return True
  now = time.time() + WL_CREATION_OFFSET
  now_struct = time.gmtime(now)
  mtime = os.path.getmtime(CACHE_PATH) + WL_CREATION_OFFSET
  mtime_struct = time.gmtime(mtime)
  age = now - mtime
  if age > ONE_DAY:
    if now_struct.tm_wday in TM_WEEKENDS:
      if age < (ONE_DAY * 3):
        return False
    return True
  return False


def _LoadFromCache():
  with open(CACHE_PATH) as f:
    return YAMLToWatchList(f.read())


def _SaveToCache(watch_list):
  with open(CACHE_PATH, 'w') as f:
    f.write(WatchListToYAML(watch_list))


def GetWatchList(live=False):
  if live or _IsCacheExpired():
    fetcher = WatchListFetcher(GetOptionAlphaSession())
    page = fetcher.FetchWatchListPage()
    parser = WatchListParser()
    parser.feed(page)
    watch_list = sorted(parser.watch_list, key=lambda x: (x.rank, x.ticker))
    _SaveToCache(watch_list)
  else:
    watch_list = _LoadFromCache()
  return watch_list
