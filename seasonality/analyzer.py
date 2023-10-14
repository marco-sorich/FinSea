"""
Analyzer module to perform the analysis for seasonality behaviour of financial symbols.

Classes:
--------
    Analyzer
    Performs the analyzer calculation and fills some pandas dataframes with resuls.
"""

import os
import datetime as dt
import pickle


import pandas as pd
from pandas_datareader import data as pdr

import yfinance as yf

from statsmodels.tsa.seasonal import STL

from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


# Prepare new dataframe in long form for annual data distribution
def _dfToLongForm(
        inputDf: pd.DataFrame,
        range: pd.date_range,
        freq: str = 'd',
        colName: str = 'Day',
        colContent: str = '%m-%d',
        withFill: bool = True,
        dropLeap: bool = True):

    """Normalizes given dataframe to a new long form dataframe over one year.

    This routine takes a dataframe with expected data over several years and
    creates a new target dataframe with over one year with multiple values
    for each `freq` (e.g. day) of several years.

    Parameters:
    -----------
        inputDf: pd.DataFrame
        Input dataframe with data spanning over several years

        range: pd.date_range
        Date range to which the input dataframe should be cropped

        freq: str, optional
        Target frequency of the new dataframe in pandas `asfreq` format (default is 'd' for day)

        colName: str, optional
        Name of the 'freq' column in the new target dataframe (default is 'Day')

        colContent: str, optional
        Content of the column according to `strftime` conversion format (default is '%m-%d' for "<MM>-<DD>")

        withFill: bool, optional
        Should missing values be filled with `fillna` (default is True)

        dropLeap: bool, optional
        Should leap days be dropped (default is True)
    """

    # Create new dataframe
    longDf = pd.DataFrame(data=inputDf)

    # set correct frequency for better comparison
    longDf = longDf.asfreq(freq)

    # fill up missing values for better comparison
    longDf = longDf.fillna(method='ffill') if withFill else longDf

    # Drop Feb. 29th of leap years for better comparison
    longDf = longDf[~((longDf.index.month == 2) & (longDf.index.day == 29))] if dropLeap else longDf

    # Create year and month columns
    longDf['Year'], longDf[colName] = longDf.index.year, longDf.index.strftime(colContent)

    # crop dataframe to last full years
    longDf = longDf[range.min():range.max()]

    # remove date index and return to numbered index
    longDf = longDf.reset_index()

    # remove date column which was left over from removing date index
    longDf = longDf.drop('Date', axis=1)

    return longDf


class Analyzer:
    """ Analyzes a given financial symbol for seasonality, trend and residual behviour

    This class analyzes the given financial symbol over the given range of years,
    selectively with simple or robust STL. This produces a bunch of dataframes containing
    the original values and the analyzed values of seasonality, trend and residual.

    Methods:
    --------
        calc()
        Calculates the given symbol and fills all the attibutes with values as described.

    Attributes:
    -----------
        ticker: yf.Ticker
        Static information about selected symbol.

        rangeMaxYrs: pd.date_range
        Actual range of years. Might be identical of value given by constructor or less, if less data is available only.

        rangeNumOfYears: int
        Number of years from rangeMaxYrs

        


        Full history data that was available for download:

        df: pd.DataFrame
        Original history data as it is downloaded. This is not cropped to given range of years.

        

        
        Decomposed data spanning over `rangeNumOfYears` years:

        sasonalDecompDf: pd.DataFrame
        Seasonal values splitted from trend.

        trendDecompDf: pd.DataFrame
        Trend values without seasonality.

        residDecompDf: pd.DataFrame
        Residual values which is neither trend nor seasonality.

        

        Annual data over one full year, each year of 'rangeNumOfYears' is in a separate column:

        annualDf: pd.DataFrame
        Original data over whole year.

        annunalSeasonalDecompDf: pd.DataFrame
        Decomposed annual daily seasonal values.

        annunalResidDecompDf: pd.DataFrame
        Decomposed annual daily residual values.

        

        Same data over different other timeframes:

        quarterlySeasonalDecompDf: pd.DataFrame
        Decomposed annual quarterly seasonal values over whole year holding `rangeNumOfYears` values per day.

        weeklySeasonalDecompDf: pd.DataFrame
        Decomposed annual weekly seasonal values over whole year holding `rangeNumOfYears` values per day.

        monthlySeasonalDecompDf: pd.DataFrame
        Decomposed annual monthly seasonal values over whole year holding `rangeNumOfYears` values per day.

        weekdailySeasonalDecompDf: pd.DataFrame
        Decomposed weekdaily seasonal values over whole year holding `rangeNumOfYears` values per day.
    """

    def __init__(self, symbol: str, years: dt.datetime, robust: bool = False, annual_rolling_days: int = 200):
        """Constructor

        Parameters:
        -----------
            symbol: str
            Symbol to analyze in unique identifier string from Yahoo Finance

            years: dt.datetime
            Range of years to analyze backwards from now on

            robust: bool, optional
            Use robust or simple STL decomposition (default is simple)

            annual_rolling_days: int, optional
            Number of days for integrated rolling mean for annual daily long form data
        """
        self.symbol = symbol
        self.years = years
        self.robust = robust
        self.annual_rolling_days = annual_rolling_days

    def calc(self):
        """Performs the calculation to fill all the attributes."""
        dirname = '.downloads'
        historyFilename = f'{dirname}{os.path.sep}{self.symbol}_{dt.date.today()}.csv'
        cacheFilename = f"{dirname}{os.path.sep}yfinance.cache"
        pickleFilename = f"{dirname}{os.path.sep}lastAnalysis.pkl"

        os.makedirs(dirname, exist_ok=True)

        session = CachedLimiterSession(
            limiter=Limiter(RequestRate(2, Duration.SECOND * 5),
                            bucket_class=MemoryQueueBucket),
            backend=SQLiteCache(cacheFilename),
        )
        self.ticker = yf.Ticker(self.symbol, session=session)

        if not os.path.isfile(historyFilename):
            yf.pdr_override()  # <== that's all it takes :-)
            self.df = pdr.get_data_yahoo(tickers=[self.symbol], interval="1d")
            self.df.to_csv(historyFilename)
        else:
            self.df = pd.read_csv(historyFilename, parse_dates=['Date'], index_col=['Date'])

        self.df = self.df[['Close']]

        # for (k, v) in ticker.info.items():
        #    D(f'* {k}: {v}')

        # set correct frequency
        self.df = self.df.asfreq('B')

        # fill up missing values
        self.df = self.df.fillna(method='ffill')

        # prepare range of max 5 years or smaller if dataframe is smaller
        firstDay = pd.to_datetime(str((self.df.index.year.min() + 1 if ((self.df.index.year.max() - 1) - (self.df.index.year.min() + 1)) < self.years else self.df.index.year.max() - self.years)) + '-01-01')
        lastDay = pd.to_datetime(str(self.df.index.year.max() - 1) + '-12-31')
        self.rangeMaxYrs = pd.date_range(firstDay, lastDay, freq='D')

        # get actual number of calculated years for dataframe
        self.rangeNumOfYears = self.rangeMaxYrs.max().year - self.rangeMaxYrs.min().year + 1

        # save information for backtrader
        backtestInfo = {
            'historyFilename': historyFilename,
            'self.rangeMaxYrs': self.rangeMaxYrs,
        }
        pickle.dump(backtestInfo, open(pickleFilename, 'wb'))

        self.annualDf = _dfToLongForm(self.df.assign(**{'rolling average': self.df['Close'].rolling(self.annual_rolling_days).mean()}), self.rangeMaxYrs)

        # set to multiindex: 1st level 'Day', 2nd level 'Year'
        self.annualDf = self.annualDf.set_index(['Year', 'Day'])

        # reorder by index level 'Day'
        self.annualDf = self.annualDf.sort_index(level='Year')

        decompDf = pd.DataFrame(data=self.df)

        # crop dataframe to max 5 last full years
        decompDf = decompDf[self.rangeMaxYrs.min():pd.to_datetime('today')]

        # prepare the 3 dataframes for seasonal, trend and residual
        self.seasonalDecompDf = pd.DataFrame()
        self.trendDecompDf = pd.DataFrame()
        self.residDecompDf = pd.DataFrame()

        # simplest form of STL
        decomposeSimpleStl = STL(decompDf['Close'], period=365, robust=self.robust)
        decomposeSimpleRes = decomposeSimpleStl.fit()

        self.seasonalDecompDf['value'] = decomposeSimpleRes.seasonal
        self.trendDecompDf['value'] = decomposeSimpleRes.trend
        self.residDecompDf['value'] = decomposeSimpleRes.resid

        # prepare annual dataframes with multiindex including the rolling averages
        self.annunalSeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.assign(**{'rolling average': self.seasonalDecompDf['value'].rolling(self.annual_rolling_days).mean()}), self.rangeMaxYrs)
        # annunalTrendDecompDf = _dfToLongForm(self.trendDecompDf.assign(**{'rolling average': self.trendDecompDf['value'].rolling(self.annual_rolling_days).mean()}), self.rangeMaxYrs)
        self.annunalResidDecompDf = _dfToLongForm(self.residDecompDf.assign(**{'rolling average': self.residDecompDf['value'].rolling(self.annual_rolling_days).mean()}), self.rangeMaxYrs)

        # prepare other dataframes for categorial plots
        self.monthlySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('M').mean(), self.rangeMaxYrs, freq='M', colName='Month', colContent='%B', withFill=False, dropLeap=False)
        self.weekdailySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf, self.rangeMaxYrs, freq='B', colName='Weekday', colContent='%A', withFill=False, dropLeap=False)
        self.quarterlySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('Q').mean(), self.rangeMaxYrs, freq='Q', colName='Quarter', colContent='%B', withFill=False, dropLeap=False)
        self.weeklySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('W').mean(), self.rangeMaxYrs, freq='W', colName='Week', colContent='%V', withFill=False, dropLeap=False)
