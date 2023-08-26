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
def _dfToLongForm(inputDf, range, freq='d', colName='Day', colContent='%m-%d', withFill=True, dropLeap=True):
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

    # crop dataframe to max 5 last full years
    longDf = longDf[range.min():range.max()]

    # remove date index and return to numbered index
    longDf = longDf.reset_index()

    # remove date column which was left over from removing date index
    longDf = longDf.drop('Date', axis=1)

    return longDf


class Analyzer:

    # external variables
    # ticker - accessing static information about selected symbol
    # df - original history data as pandas dataframe as it is downloaded
    # rangeMax5yrs - pandas date_range of last max_num_of_years years or less if no more symbol history data is available
    # rangeNumOfYears - number of years from rangeMax5yrs
    # sasonalDecompDf - pandas dataframe containing decomposed seasonal
    # trendDecompDf - pandas dataframe containing decomposed trend
    # residDecompDf - pandas dataframe containing decomposed residual
    # annualDf - long form pandas dataframe containing original data of rangeMax5yrs date range
    # annunalSeasonalDecompDf - long form pandas dataframe containing decomposed seasonal data of rangeMax5yrs date range
    # annunalResidDecompDf - long form pandas dataframe containing decomposed residual data of rangeMax5yrs date range
    # quarterlySeasonalDecompDf - long form pandas dataframe containing quarterly decomposed seasonal data of rangeMax5yrs date range
    # weeklySeasonalDecompDf - long form pandas dataframe containing weekly decomposed seasonal data of rangeMax5yrs date range
    # weekdailySeasonalDecompDf - long form pandas dataframe containing weekdaily decomposed seasonal data of rangeMax5yrs date range
    # monthlySeasonalDecompDf - long form pandas dataframe containing monthly decomposed seasonal data of rangeMax5yrs date range

    def __init__(self, symbol, years, robust=False):
        self.symbol = symbol
        self.years = years
        self.robust = robust

        # set number of day of rolling averages for annual data plots
        self.annual_rolling_days = 20

    def calc(self):
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
        self.rangeMax5yrs = pd.date_range(firstDay, lastDay, freq='D')

        # get actual number of calculated years for dataframe
        self.rangeNumOfYears = self.rangeMax5yrs.max().year - self.rangeMax5yrs.min().year + 1

        # save information for backtrader
        backtestInfo = {
            'historyFilename': historyFilename,
            'self.rangeMax5yrs': self.rangeMax5yrs,
        }
        pickle.dump(backtestInfo, open(pickleFilename, 'wb'))

        self.annualDf = _dfToLongForm(self.df.assign(**{'rolling average': self.df['Close'].rolling(self.annual_rolling_days).mean()}), self.rangeMax5yrs)

        # set to multiindex: 1st level 'Day', 2nd level 'Year'
        self.annualDf = self.annualDf.set_index(['Year', 'Day'])

        # reorder by index level 'Day'
        self.annualDf = self.annualDf.sort_index(level='Year')

        decompDf = pd.DataFrame(data=self.df)

        # crop dataframe to max 5 last full years
        decompDf = decompDf[self.rangeMax5yrs.min():pd.to_datetime('today')]

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
        self.annunalSeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.assign(**{'rolling average': self.seasonalDecompDf['value'].rolling(self.annual_rolling_days).mean()}), self.rangeMax5yrs)
        # annunalTrendDecompDf = _dfToLongForm(self.trendDecompDf.assign(**{'rolling average': self.trendDecompDf['value'].rolling(self.annual_rolling_days).mean()}), self.rangeMax5yrs)
        self.annunalResidDecompDf = _dfToLongForm(self.residDecompDf.assign(**{'rolling average': self.residDecompDf['value'].rolling(self.annual_rolling_days).mean()}), self.rangeMax5yrs)

        # prepare other dataframes for categorial plots
        self.monthlySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('M').mean(), self.rangeMax5yrs, freq='M', colName='Month', colContent='%B', withFill=False, dropLeap=False)
        self.weekdailySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf, self.rangeMax5yrs, freq='B', colName='Weekday', colContent='%A', withFill=False, dropLeap=False)
        self.quarterlySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('Q').mean(), self.rangeMax5yrs, freq='Q', colName='Quarter', colContent='%B', withFill=False, dropLeap=False)
        self.quarterlySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('Q').mean(), self.rangeMax5yrs, freq='Q', colName='Quarter', colContent='%B', withFill=False, dropLeap=False)
        self.weeklySeasonalDecompDf = _dfToLongForm(self.seasonalDecompDf.resample('W').mean(), self.rangeMax5yrs, freq='W', colName='Week', colContent='%V', withFill=False, dropLeap=False)
