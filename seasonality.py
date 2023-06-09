import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
from statsmodels.tsa.seasonal import seasonal_decompose
from pandas_datareader import data as pdr







symbol='2B7K.DE'   # iShares MSCI World SRI UCITS ETF EUR (Acc)
#symbol='EUNL.DE'    # iShares Core MSCI World UCITS ETF USD (Acc)

yf.pdr_override() # <== that's all it takes :-)
df = pdr.get_data_yahoo(tickers=[symbol], interval="1d")[['Close']]
df.head()








rolling_resolution = 100

plt.figure(figsize=(20,8))
plt.xlabel('Data', fontsize=17)
plt.ylabel('Price', fontsize=17)
plt.title('Daily closing price', fontsize=17)
#plt.grid(b=True, which='major', color='b', linestyle='-')

df['Close'].plot(legend=True, label='close price')
df['Close'].rolling(rolling_resolution).mean().plot(legend=True, label=str(rolling_resolution) + '-day moving average')
#df[symbol].plot(legend=True, label='20-day VWAP')

plt.show()









df.index = pd.to_datetime(df.index)
df = df.asfreq('d')                 # set correct frequency
df = df.fillna(method='ffill')      # fill up missing values


resultDf = pd.DataFrame()
for year in list(set(df.index.year))[1:-1]:
    curYearValues = df[str(year) + '-01-01':str(year) + '-12-31']['Close'].values
    if curYearValues.size == 365:                     # take a regular complete year
        resultDf[str(year)] = curYearValues
    elif curYearValues.size == 366:
        curYearValues = np.delete(curYearValues, 59)  # remove Feb. 29 of leap year
        resultDf[str(year)] = curYearValues

resultMean = resultDf.mean(axis=1)
resultMin = resultDf.min(axis=1)
resultMax = resultDf.max(axis=1)
resultDf['mean'] = resultMean
resultDf['min'] = resultMin
resultDf['max'] = resultMax


fig, ax = plt.subplots(figsize=(20,10))
ax.plot(resultDf.index, resultDf['mean'], '-')
ax.fill_between(resultDf.index, resultDf['min'], resultDf['max'], alpha=0.2)
ax.axvline(dt.date.today().timetuple().tm_yday, linestyle='dashed')
     







decompose = seasonal_decompose(df['Close'], model='additive', period=365)

lastYear=dt.date.today().year-1
resultDf['seasonal'] = decompose.seasonal[str(year) + '-01-01':str(year) + '-12-31'].values

resultDf







plt.figure(figsize=(20,12), layout='constrained')

plt.subplot(311)
plt.xlabel('Date', fontsize=17)
plt.title('Seasonality', fontsize=17)
plt.axvline(mdates.date2num(dt.datetime(year, dt.date.today().month, dt.date.today().day)), linestyle='dashed')
decompose.seasonal[str(year) + '-01-01':str(year) + '-12-31'].plot()

plt.subplot(312)
plt.xlabel('Date', fontsize=17)
plt.title('Trend', fontsize=17)
decompose.trend.plot()

plt.subplot(313)
plt.xlabel('Date', fontsize=17)
plt.title('Residual', fontsize=17)
decompose.resid.plot()

