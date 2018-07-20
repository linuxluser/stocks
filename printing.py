"""Library for printing things to screen.
"""


import sys

import colors


class TabularPrinter(object):
  """Prints data as an ASCII table."""

  def __init__(self, headers, widths=None):
    self.headers = headers
    self.widths = widths
    if widths and len(self.headers) != len(self.widths):
      raise ValueError('argument "widths" must be a list of same length as headers')

  def _calc_max_widths(self, rows):
    """Calculate max widths of each column."""
    num_cols = len(self.headers)
    widths = [len(h) for h in self.headers]
    for row in rows:
      if len(row) != num_cols:
        raise ValueError('headers and row lengths must be the same')
      for i, val in enumerate(row):
        length = len(colors.StripColor(str(val)))
        if length > widths[i]:
          widths[i] = length
    return widths

  def _collate(self, row, widths):
    """Collate the row value along with its width to get format() args."""
    fmt_args = []
    for val, width in zip(row, widths):
      width += colors.ColorCharacterCount(str(val))
      fmt_args.extend((val, width))
    return fmt_args

  def _mkformat(self, sep):
    """Create a format string with given separator."""
    columns = ['{:<{}}']*len(self.headers)
    return sep.join(columns)

  def _underline_headers(self):
    return [colors.PaintUnderline(h) for h in self.headers]

  def _print_rows(self, widths, rows, indent):
    fmt = self._mkformat('  ')
    for row in rows:
      print(' '*indent, end='')
      print(fmt.format(*self._collate(row, widths)))

  def _print_first_column(self, rows, indent):
    for row in rows:
      print(' '*indent, end='')
      print(colors.StripColor(row[0]))

  def print(self, rows, indent=0, detect_pipe=True):
    if not rows:
      return
    if detect_pipe and not sys.stdout.isatty():
      self._print_first_column(rows, indent)
      return
    widths = self.widths
    if not widths:
      widths = self._calc_max_widths(rows)
    underlined_headers = iter(colors.PaintUnderline(h) for h in self.headers)
    self._print_rows(widths, (underlined_headers,), indent)
    self._print_rows(widths, rows, indent)
