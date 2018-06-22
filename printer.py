"""Library for printing things to screen.
"""


import colors


class TabularPrinter(object):
  """Prints data as an ASCII table."""

  def __init__(self, headers):
    self.headers = headers

  def _calc_max_widths(self, rows, price_columns):
    """Calculate max widths of each column."""
    num_cols = len(self.headers)
    widths = [len(h) for h in self.headers]
    for row in rows:
      if len(row) != num_cols:
        raise ValueError('headers and row lengths must be the same')
      for i, val in enumerate(row):
        if i+1 in price_columns:
          length = len('{:.2f}'.format(val))
        else:
          length = len(colors.StripColor(str(val)))
        if length > widths[i]:
          widths[i] = length
    return widths

  def _collate(self, row, widths):
    """Collate the row value along with its width to get format() args."""
    return [t for tup in zip(row, widths) for t in tup]

  def _mkformat(self, sep, price_columns):
    """Create a format string with given separator."""
    columns = ['{:<{}}']*len(self.headers)
    for c in price_columns:
      columns[c -1] = '{:<{}.2f}'
    return sep.join(columns)

  def _print_headers(self, widths, indent):
    space_fmt = self._mkformat('   ', [])
    bar_fmt = self._mkformat('-|-', [])
    dashes = ('-'*widths[i] for i,_ in enumerate(self.headers))
    print(' '*indent, end='')
    print(space_fmt.format(*self._collate(self.headers, widths)))
    print(' '*indent, end='')
    print(bar_fmt.format(*self._collate(dashes, widths)))

  def _print_rows(self, widths, rows, price_columns, indent):
    fmt = self._mkformat('   ', price_columns)
    for row in rows:
      print(' '*indent, end='')
      print(fmt.format(*self._collate(row, widths)))

  def print(self, rows, price_columns=[], indent=0):
    if not rows:
      return
    widths = self._calc_max_widths(rows, price_columns)
    self._print_headers(widths, indent)
    self._print_rows(widths, rows, price_columns, indent)
