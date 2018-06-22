
"""Utility for easily adding color to output.

The color values must be the same number of characters long so that way they
are known to LINE_FORMAT's various padding lengths.
"""


# Length of the string of each color code
COLOR_CODE_LENGTH = 6

# Escape code used for each terminal color
ESCAPE_CODE = '\033'

# Terminal color constants
RESET      = '\033[000m'
BOLD       = '\033[001m'
UNDERLINE  = '\033[004m'
BLACK      = '\033[030m'
RED        = '\033[031m'
GREEN      = '\033[032m'
YELLOW     = '\033[033m'
BLUE       = '\033[034m'
MAGENTA    = '\033[035m'
CYAN       = '\033[036m'
LT_GRAY    = '\033[037m'
DK_GRAY    = '\033[038m'
LT_RED     = '\033[091m'
LT_GREEN   = '\033[092m'
LT_YELLOW  = '\033[093m'
LT_BLUE    = '\033[094m'
LT_MAGENTA = '\033[095m'
LT_CYAN    = '\033[096m'
BG_RED     = '\033[041m'
BG_GREEN   = '\033[042m'
BG_YELLOW  = '\033[043m'
BG_BLUE    = '\033[044m'
BG_MAGENTA = '\033[045m'
BG_CYAN    = '\033[046m'
BG_WHITE   = '\033[107m'


def Paint(S, color):
  return '{}{}{}'.format(color, S, RESET)


def PaintForegroundBackground(S, fg_color, bg_color):
  return '{}{}{}{}'.format(fg_color, bg_color, S, RESET)


# Just text
PaintBold = lambda S: Paint(S, BOLD)
PaintUnderline = lambda S: Paint(S, UNDERLINE)
PaintRed = lambda S: Paint(S, RED)
PaintGreen = lambda S: Paint(S, GREEN)
PaintYellow = lambda S: Paint(S, YELLOW)
PaintBlue = lambda S: Paint(S, BLUE)
PaintMagenta = lambda S: Paint(S, MAGENTA)
PaintCyan = lambda S: Paint(S, CYAN)
PaintLightGray = lambda S: Paint(S, LT_GRAY)
PaintLightRed = lambda S: Paint(S, LT_RED)
PaintLightGreen = lambda S: Paint(S, LT_GREEN)
PaintLightYellow = lambda S: Paint(S, LT_YELLOW)
PaintLightBlue = lambda S: Paint(S, LT_BLUE)
PaintLightMagenta = lambda S: Paint(S, LT_MAGENTA)
PaintLightCyan = lambda S: Paint(S, LT_CYAN)


# Just background
PaintBackgroundRed = lambda S: Paint(S, BG_RED)
PaintBackgroundGreen = lambda S: Paint(S, BG_GREEN)
PaintBackgroundYellow = lambda S: Paint(S, BG_YELLOW)
PaintBackgroundBlue = lambda S: Paint(S, BG_BLUE)
PaintBackgroundMagenta = lambda S: Paint(S, BG_MAGENTA)
PaintBackgroundCyan = lambda S: Paint(S, BG_CYAN)


# Text/background combos
PaintBlackOnWhite = lambda S: PaintForegroundBackground(S, BLACK, BG_WHITE)


def StripColor(S):
  index = S.find(ESCAPE_CODE)
  while index != -1:
    color = S[index:index+COLOR_CODE_LENGTH]
    S = S.replace(color, '')
    index = S.find(ESCAPE_CODE)
  return S
