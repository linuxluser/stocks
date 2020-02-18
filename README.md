# stocks
Scripts For Stock Analysis and Tracking.

## Five Energies Method

One of the most useful scripts is `Energies`, which provides terminal, line-by-line output of the "five energies" of each ticker according to [Trend Trading For Dummies](https://www.amazon.com/dp/1118871286), a book written by Barry Burns of [Top Dog Trading](https://www.topdogtrading.com).

In this method, you look at only **five** signals to make your buy or sell decision of a particular security. **If at least three of the five signals are in your favor, you have high-probabilty trade**. The one caveat is that the **trend signal must always be in your favor** or the trade will not be high-probabilty.

The five energeies are:
*  Trend
*  Momentum
*  Cycle
*  Support/Resistance
*  Scale

If this is interesting to you, be sure to watch [the video presented by Barry Burns](https://www.youtube.com/watch?v=BFMgnarSMuw) on how to use these energies for precisely entering and exiting positions.

## Installation

### 1. Install dependencies

```bash
$ sudo apt install at python3-pip
$ sudo pip3 install beautifulsoup4 npyscreen numpy pandas==0.21.0 pandas-datareader==0.5.0 requests scipy sh
```

### 2. Get scripts (Clone this repository)

```bash
$ git clone https://github.com/linuxluser/stocks.git
$ cd stocks
$ ./Energies FB AMZN NFLX GOOGL
```
