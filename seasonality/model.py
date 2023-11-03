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


# Prepare new dataframe in wide form for annual data distribution
def _df_to_wide_form(
        input_df: pd.DataFrame,
        range: pd.date_range,
        freq: str = 'd',
        col_name: str = 'Day',
        col_content: str = '%m-%d',
        with_fill: bool = True,
        drop_leap: bool = True):

    """Normalizes given dataframe to a new wide form dataframe over one year.

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
    wideDf = pd.DataFrame(data=input_df)

    # set correct frequency for better comparison
    wideDf = wideDf.asfreq(freq)

    # fill up missing values for better comparison
    wideDf = wideDf.ffill() if with_fill else wideDf

    # Drop Feb. 29th of leap years for better comparison
    wideDf = wideDf[~((wideDf.index.month == 2) & (wideDf.index.day == 29))] if drop_leap else wideDf

    # Create year and month columns
    wideDf['Year'], wideDf[col_name] = wideDf.index.year, wideDf.index.strftime(col_content)

    # crop dataframe to last full years
    wideDf = wideDf[range.min():range.max()]

    # remove date index and return to numbered index
    wideDf = wideDf.reset_index()

    # remove date column which was left over from removing date index
    wideDf = wideDf.drop('Date', axis=1)

    return wideDf


class Model:
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
    """

    def __init__(self, symbol: str, years: dt.datetime, robust: bool = False, annual_rolling_days: int = 30):
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
            Number of days for integrated rolling mean for annual daily wide form data
        """
        self.symbol = symbol
        self.years = years
        self.robust = robust
        self.annual_rolling_days = annual_rolling_days
        self._overall_daily_prices = pd.DataFrame()
        self._overall_daily_seasonal = pd.DataFrame()
        self._overall_daily_trend = pd.DataFrame()
        self._overall_daily_residual = pd.DataFrame()
        self._annual_daily_prices = pd.DataFrame()

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
            self._overall_daily_prices = pdr.get_data_yahoo(tickers=[self.symbol], interval="1d")
            self._overall_daily_prices.to_csv(history_filename)
        else:
            self._overall_daily_prices = pd.read_csv(history_filename, parse_dates=['Date'], index_col=['Date'])

        self._overall_daily_prices = self._overall_daily_prices[['Close']]

        # for (k, v) in ticker.info.items():
        #    D(f'* {k}: {v}')

        # set correct frequency
        self._overall_daily_prices = self._overall_daily_prices.asfreq('B')

        # fill up missing values
        self._overall_daily_prices = self._overall_daily_prices.ffill()

        # prepare range of max 5 years or smaller if dataframe is smaller
        first_day = pd.to_datetime(str((self._overall_daily_prices.index.year.min() + 1 if ((self._overall_daily_prices.index.year.max() - 1) - (self._overall_daily_prices.index.year.min() + 1)) < self.years else self._overall_daily_prices.index.year.max() - self.years)) + '-01-01')
        last_day = pd.to_datetime(str(self._overall_daily_prices.index.year.max() - 1) + '-12-31')
        self.range_max_yrs = pd.date_range(first_day, last_day, freq='D')

        # get actual number of calculated years for dataframe
        self.range_num_of_years = self.range_max_yrs.max().year - self.range_max_yrs.min().year + 1

        # save information for backtrader
        backtest_info = {
            'history_filename': history_filename,
            'self.range_max_yrs': self.range_max_yrs,
        }
        pickle.dump(backtest_info, open(pickle_filename, 'wb'))

        self._annual_daily_prices = _df_to_wide_form(self._overall_daily_prices, self.range_max_yrs)

        # set to multiindex: 1st level 'Day', 2nd level 'Year'
        self._annual_daily_prices = self._annual_daily_prices.set_index(['Year', 'Day'])

        # reorder by index level 'Day'
        self._annual_daily_prices = self._annual_daily_prices.sort_index(level='Year')

        decomp_df = pd.DataFrame(data=self._overall_daily_prices)

        # crop dataframe to max 5 last full years
        decomp_df = decomp_df[self.range_max_yrs.min():pd.to_datetime('today')]

        # decompose seasonal trend and residual via LOESS regression
        decompose_result = STL(decomp_df['Close'], period=365, robust=self.robust, seasonal=7, seasonal_deg=1, trend_deg=1, low_pass_deg=1, seasonal_jump=1, trend_jump=1, low_pass_jump=1).fit()
        self._overall_daily_seasonal['value'] = decompose_result.seasonal
        self._overall_daily_trend['value'] = decompose_result.trend
        self._overall_daily_residual['value'] = decompose_result.resid

    def get_overall_daily_prices(self) -> pd.DataFrame:
        """Returns the original dataframe as downloaded from internet."""
        return self._overall_daily_prices

    def get_overall_daily_trend(self) -> pd.DataFrame:
        """Returns the decomposed trend dataframe right out of the STL fit() function."""
        return self._overall_daily_trend

    def get_overall_daily_seasonal(self) -> pd.DataFrame:
        """Returns the decomposed seasonal dataframe right out of the STL fit() function."""
        return self._overall_daily_seasonal

    def get_overall_daily_residual(self) -> pd.DataFrame:
        """Returns the decomposed residual dataframe right out of the STL fit() function."""
        return self._overall_daily_residual

    def get_annual_daily_prices(self) -> pd.DataFrame:
        """Returns the original annual dataframe converted to wide form."""
        return self._annual_daily_prices

    def get_annual_daily_seasonal(self) -> pd.DataFrame:
        """Returns the decomposed annual daily seasonal dataframe in wide form."""
        # prepare annual dataframes with multiindex
        return _df_to_wide_form(self._overall_daily_seasonal, self.range_max_yrs)

    def get_annual_daily_residual(self) -> pd.DataFrame:
        """Returns the decomposed annual daily residual dataframe in wide form."""
        # prepare annual dataframes with multiindex
        return _df_to_wide_form(self._overall_daily_residual, self.range_max_yrs)

    def get_monthly_seasonal(self) -> pd.DataFrame:
        """Returns the decomposed annual monthly seasonal dataframe."""
        # prepare annual dataframes with multiindex including the rolling average
        return _df_to_wide_form(self._overall_daily_seasonal.resample('M').mean(), self.range_max_yrs, freq='M', col_name='Month', col_content='%b', with_fill=False, drop_leap=False)

    def get_weekdaily_seasonal(self) -> pd.DataFrame:
        """Returns the decomposed weekdaily seasonal dataframe."""
        # prepare annual dataframes with multiindex including the rolling average
        return _df_to_wide_form(self._overall_daily_seasonal, self.range_max_yrs, freq='B', col_name='Weekday', col_content='%a', with_fill=False, drop_leap=False)

    def get_annual_quarterly_seasonal(self) -> pd.DataFrame:
        """Returns the decomposed annual quarterly seasonal dataframe."""
        # prepare annual dataframes with multiindex including the rolling average
        return _df_to_wide_form(self._overall_daily_seasonal.resample('Q').mean(), self.range_max_yrs, freq='Q', col_name='Quarter', col_content='%b', with_fill=False, drop_leap=False)

    def get_annual_weekly_seasonal(self) -> pd.DataFrame:
        """Returns the decomposed annual weekly seasonal dataframe."""
        # prepare annual dataframes with multiindex including the rolling average
        return _df_to_wide_form(self._overall_daily_seasonal.resample('W').mean(), self.range_max_yrs, freq='W', col_name='Week', col_content='%V', with_fill=False, drop_leap=False)
