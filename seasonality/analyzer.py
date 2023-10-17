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
def _df_to_long_form(
        input_df: pd.DataFrame,
        range: pd.date_range,
        freq: str = 'd',
        col_name: str = 'Day',
        col_content: str = '%m-%d',
        with_fill: bool = True,
        drop_leap: bool = True):

    """Normalizes given dataframe to a new long form dataframe over one year.

    This routine takes a dataframe with expected data over several years and
    creates a new target dataframe with over one year with multiple values
    for each `freq` (e.g. day) of several years.

    Parameters:
    -----------
        input_df: pd.DataFrame
        Input dataframe with data spanning over several years

        range: pd.date_range
        Date range to which the input dataframe should be cropped

        freq: str, optional
        Target frequency of the new dataframe in pandas `asfreq` format (default is 'd' for day)

        col_name: str, optional
        Name of the 'freq' column in the new target dataframe (default is 'Day')

        col_content: str, optional
        Content of the column according to `strftime` conversion format (default is '%m-%d' for "<MM>-<DD>")

        with_fill: bool, optional
        Should missing values be filled with `fillna` (default is True)

        drop_leap: bool, optional
        Should leap days be dropped (default is True)
    """

    # Create new dataframe
    longDf = pd.DataFrame(data=input_df)

    # set correct frequency for better comparison
    longDf = longDf.asfreq(freq)

    # fill up missing values for better comparison
    longDf = longDf.fillna(method='ffill') if with_fill else longDf

    # Drop Feb. 29th of leap years for better comparison
    longDf = longDf[~((longDf.index.month == 2) & (longDf.index.day == 29))] if drop_leap else longDf

    # Create year and month columns
    longDf['Year'], longDf[col_name] = longDf.index.year, longDf.index.strftime(col_content)

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

        range_max_yrs: pd.date_range
        Actual range of years. Might be identical of value given by constructor or less, if less data is available only.

        range_num_of_years: int
        Number of years from range_max_yrs

        


        Full history data that was available for download:

        df: pd.DataFrame
        Original history data as it is downloaded. This is not cropped to given range of years.

        

        
        Decomposed data spanning over `range_num_of_years` years (leapdays cropped):

        sasonalDecompDf: pd.DataFrame
        Seasonal values splitted from trend.

        trend_decomp_df: pd.DataFrame
        Trend values without seasonality.

        resid_decomp_df: pd.DataFrame
        Residual values which is neither trend nor seasonality.

        

        Annual data over one full year, each year of 'range_num_of_years' is in a separate column:

        annual_df: pd.DataFrame
        Original data over whole year.

        annunal_seasonal_decomp_df: pd.DataFrame
        Decomposed annual daily seasonal values.

        annunal_resid_decomp_df: pd.DataFrame
        Decomposed annual daily residual values.

        

        Same data over different other timeframes:

        quarterly_seasonal_decomp_df: pd.DataFrame
        Decomposed annual quarterly seasonal values over whole year holding `range_num_of_years` values per day.

        weekly_seasonal_decomp_df: pd.DataFrame
        Decomposed annual weekly seasonal values over whole year holding `range_num_of_years` values per day.

        monthly_seasonal_decomp_df: pd.DataFrame
        Decomposed annual monthly seasonal values over whole year holding `range_num_of_years` values per day.

        weekdaily_seasonal_decomp_df: pd.DataFrame
        Decomposed weekdaily seasonal values over whole year holding `range_num_of_years` values per day.
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
        history_filename = f'{dirname}{os.path.sep}{self.symbol}_{dt.date.today()}.csv'
        cache_filename = f"{dirname}{os.path.sep}yfinance.cache"
        pickle_filename = f"{dirname}{os.path.sep}lastAnalysis.pkl"

        os.makedirs(dirname, exist_ok=True)

        session = CachedLimiterSession(
            limiter=Limiter(RequestRate(2, Duration.SECOND * 5),
                            bucket_class=MemoryQueueBucket),
            backend=SQLiteCache(cache_filename),
        )
        self.ticker = yf.Ticker(self.symbol, session=session)

        if not os.path.isfile(history_filename):
            yf.pdr_override()  # <== that's all it takes :-)
            self.df = pdr.get_data_yahoo(tickers=[self.symbol], interval="1d")
            self.df.to_csv(history_filename)
        else:
            self.df = pd.read_csv(history_filename, parse_dates=['Date'], index_col=['Date'])

        self.df = self.df[['Close']]

        # for (k, v) in ticker.info.items():
        #    D(f'* {k}: {v}')

        # set correct frequency
        self.df = self.df.asfreq('B')

        # fill up missing values
        self.df = self.df.fillna(method='ffill')

        # prepare range of max 5 years or smaller if dataframe is smaller
        first_day = pd.to_datetime(str((self.df.index.year.min() + 1 if ((self.df.index.year.max() - 1) - (self.df.index.year.min() + 1)) < self.years else self.df.index.year.max() - self.years)) + '-01-01')
        last_day = pd.to_datetime(str(self.df.index.year.max() - 1) + '-12-31')
        self.range_max_yrs = pd.date_range(first_day, last_day, freq='D')

        # get actual number of calculated years for dataframe
        self.range_num_of_years = self.range_max_yrs.max().year - self.range_max_yrs.min().year + 1

        # save information for backtrader
        backtest_info = {
            'history_filename': history_filename,
            'self.range_max_yrs': self.range_max_yrs,
        }
        pickle.dump(backtest_info, open(pickle_filename, 'wb'))

        self.annual_df = _df_to_long_form(self.df.assign(**{'rolling average': self.df['Close'].rolling(self.annual_rolling_days).mean()}), self.range_max_yrs)

        # set to multiindex: 1st level 'Day', 2nd level 'Year'
        self.annual_df = self.annual_df.set_index(['Year', 'Day'])

        # reorder by index level 'Day'
        self.annual_df = self.annual_df.sort_index(level='Year')

        decomp_df = pd.DataFrame(data=self.df)

        # crop dataframe to max 5 last full years
        decomp_df = decomp_df[self.range_max_yrs.min():pd.to_datetime('today')]

        # prepare the 3 dataframes for seasonal, trend and residual
        self.seasonal_decomp_df = pd.DataFrame()
        self.trend_decomp_df = pd.DataFrame()
        self.resid_decomp_df = pd.DataFrame()

        # simplest form of STL
        decompose_simple_stl = STL(decomp_df['Close'], period=365, robust=self.robust)
        decompose_simple_res = decompose_simple_stl.fit()

        self.seasonal_decomp_df['value'] = decompose_simple_res.seasonal
        self.trend_decomp_df['value'] = decompose_simple_res.trend
        self.resid_decomp_df['value'] = decompose_simple_res.resid

        # prepare annual dataframes with multiindex including the rolling averages
        self.annunal_seasonal_decomp_df = _df_to_long_form(self.seasonal_decomp_df.assign(**{'rolling average': self.seasonal_decomp_df['value'].rolling(self.annual_rolling_days).mean()}), self.range_max_yrs)
        # annunalTrendDecompDf = _df_to_long_form(self.trend_decomp_df.assign(**{'rolling average': self.trend_decomp_df['value'].rolling(self.annual_rolling_days).mean()}), self.range_max_yrs)
        self.annunal_resid_decomp_df = _df_to_long_form(self.resid_decomp_df.assign(**{'rolling average': self.resid_decomp_df['value'].rolling(self.annual_rolling_days).mean()}), self.range_max_yrs)

        # prepare other dataframes for categorial plots
        self.monthly_seasonal_decomp_df = _df_to_long_form(self.seasonal_decomp_df.resample('M').mean(), self.range_max_yrs, freq='M', col_name='Month', col_content='%b', with_fill=False, drop_leap=False)
        self.weekdaily_seasonal_decomp_df = _df_to_long_form(self.seasonal_decomp_df, self.range_max_yrs, freq='B', col_name='Weekday', col_content='%a', with_fill=False, drop_leap=False)
        self.quarterly_seasonal_decomp_df = _df_to_long_form(self.seasonal_decomp_df.resample('Q').mean(), self.range_max_yrs, freq='Q', col_name='Quarter', col_content='%b', with_fill=False, drop_leap=False)
        self.weekly_seasonal_decomp_df = _df_to_long_form(self.seasonal_decomp_df.resample('W').mean(), self.range_max_yrs, freq='W', col_name='Week', col_content='%V', with_fill=False, drop_leap=False)
