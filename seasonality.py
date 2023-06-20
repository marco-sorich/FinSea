# %%

import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
from statsmodels.tsa.seasonal import seasonal_decompose
from pandas_datareader import data as pdr

from statsmodels.tsa.seasonal import MSTL




# select the symbol to analyze

# symbol = '2B7K.DE'    # iShares MSCI World SRI UCITS ETF EUR (Acc)
symbol = 'EUNL.DE'    # iShares Core MSCI World UCITS ETF USD (Acc)
# symbol = 'EURUSD=X'   # USD/EUR
# symbol = 'GBPUSD=X'   # GBP/USD
# symbol = 'AUDUSD=X'   # AUD/USD
# symbol = '^ATX'       # Austrian Traded Index in EUR
# symbol = 'ALV.DE'     # Allianz SE
# symbol = 'ADS.DE'     # adidas AG
# symbol = 'EBAY'       # eBay Inc.
# symbol = 'AXP'        # American Express Company



# should data be downloaded from internet (and saved to csv)
# or read from csv
download_symbol = False



# select which seasonal decomposition routine to use
use_STL = True 




# set maximum number of years to analyze
max_num_of_years = 5







if download_symbol:
    yf.pdr_override()  # <== that's all it takes :-)
    df = pdr.get_data_yahoo(tickers=[symbol], interval="1d")[['Close']]
    df.to_csv(f'{symbol}.csv')
else:
    df = pd.read_csv(f'{symbol}.csv', parse_dates=['Date'], index_col=['Date'])





df

# %%

rolling_resolution = 200

df.index = pd.to_datetime(df.index)
df = df.asfreq('d')                 # set correct frequency
df = df.fillna(method='ffill')      # fill up missing values

resultDf = pd.DataFrame()
numOfYears = 0
for year in sorted(list(set(df.index.year)), reverse=True)[1:-1]:
    numOfYears += 1
    if numOfYears > max_num_of_years:
        break
    curYearValues = df[str(year) + '-01-01':str(year) + '-12-31']['Close'].values
    if curYearValues.size == 366:
        curYearValues = np.delete(curYearValues, 59)  # remove Feb. 29 of leap year
    resultDf[str(year)] = curYearValues

resultMean = resultDf.mean(axis=1)
resultMin = resultDf.min(axis=1)
resultMax = resultDf.max(axis=1)
resultDf['mean'] = resultMean
resultDf['min'] = resultMin
resultDf['max'] = resultMax

lastYear = dt.date.today().year-1
range = pd.date_range(str(lastYear) + '-01-01', str(lastYear) + '-12-31', freq='D')
resultDf['date'] = range
resultDf = resultDf.set_index('date')

# resultDf.index = resultDf.index.strftime('%d. %b')

resultDf

# %%


if not use_STL:
    decompose = seasonal_decompose(df['Close'], model='additive', period=365)
else:
    decompose = MSTL(df['Close'], periods=365)
    decompose = decompose.fit()

numOfYears = 0
for year in sorted(list(set(decompose.seasonal.index.year)), reverse=True)[1:-1]:
    numOfYears += 1
    if numOfYears > max_num_of_years:
        break
    curYearValues = decompose.seasonal[str(year) + '-01-01':str(year) + '-12-31'].values
    if curYearValues.size == 366:
        curYearValues = np.delete(curYearValues, 59)  # remove Feb. 29 of leap year
    resultDf['seasonal-' + str(year)] = curYearValues


resultDf

# %%

plt.figure(figsize=(20, 15), layout='constrained')
plt.suptitle('Analysis of ' + symbol, fontsize=23)

plt.subplot(411)
plt.title('Closing price', fontsize=17)
df['Close'].plot(legend=True, label='close price')
df['Close'].rolling(rolling_resolution).mean().plot(legend=True, label=str(rolling_resolution) + '-day moving average')

plt.subplot(412)
plt.title('Seasonality last years', fontsize=17)
plt.axvline(mdates.date2num(dt.datetime(lastYear, dt.date.today().month, dt.date.today().day)), linestyle='dashed')
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d. %b"))
for col in resultDf.columns:
    if col.startswith('seasonal-'):
        resultDf[col].plot(legend=True)

plt.subplot(413)
plt.title('Seasonality/Residual overall', fontsize=17)
decompose.seasonal.plot(legend=True)
decompose.resid.plot(legend=True)

plt.subplot(414)
plt.title('Trend', fontsize=17)
decompose.trend.plot()


# %%
