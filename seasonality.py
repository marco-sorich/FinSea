import datetime as dt
import os

import seasonality as ssn

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages


import pandas as pd

import seaborn as sns



# select the symbol to analyze

# symbol = '2B7K.DE'    # iShares MSCI World SRI UCITS ETF EUR (Acc)
# symbol = 'EUNL.DE'    # iShares Core MSCI World UCITS ETF USD (Acc)
# symbol = 'EURUSD=X'   # USD/EUR
# symbol = 'GBPUSD=X'   # GBP/USD
# symbol = 'AUDUSD=X'   # AUD/USD
# symbol = '^ATX'       # Austrian Traded Index in EUR
# symbol = 'ALV.DE'     # Allianz SE
# symbol = 'ADS.DE'     # adidas AG
# symbol = 'EBAY'       # eBay Inc.
# symbol = 'AXP'        # American Express Company
# symbol = 'BTC-USD'    # Bitcoin USD
# symbol = 'ETH-USD'    # Ethereum USD
symbol = '^GSPC'      # S&P 500
# symbol = 'AAPL'       # Apple


# set maximum number of years to analyze
max_num_of_years = 5


def printProgress(current: int, total: int) -> None:
    """ Prints the progress of the analysis """
    progress = (current + 1) / total
    print("\r[%-20s] %d%%" % ('=' * int(20 * progress), 100 * progress), end='')
    if current == total-1:
        print()


def pdfLayout(figure: plt.Figure) -> None:
    """ Layouts the figure for PDF export """
    figure.subplots_adjust(top=0.85, bottom=0.15, left=0.1, hspace=0.7, wspace=0.7)


max_progress = 12
cur_progress = 0
printProgress(cur_progress, max_progress)

analyzer = ssn.Analyzer(symbol, max_num_of_years)
analyzer.calc()

cur_progress += 1
printProgress(cur_progress, max_progress)



# Set the figure size to DIN A4 dimensions with a 10mm border
fig_width = 210 + 20  # 210mm + 10mm border on each side
fig_height = 297 + 20  # 297mm + 10mm border on each side

# set number of days for rolling averages for full data plots
rolling_narrow_resolution = 50
rolling_wide_resolution = 200


# configure graphical apperance of plots
sns.set_theme(context='paper', font_scale=0.8, rc={'figure.figsize': (fig_width / 25.4, fig_height / 25.4)}, style='darkgrid')


# Create new PDF file
with PdfPages('myplots.pdf') as pdf:

    # first page - plot overall analysis
    numSubPlots = 3
    figOverall, axs = plt.subplots(numSubPlots, 1)
    pdfLayout(figOverall)
    figOverall.suptitle(f'Overall analysis of {analyzer.ticker.info["longName"]}\n', fontsize=20)

    currentAxis = 0

    # Plot overall closing prices of last x years
    overallDf = pd.DataFrame(data=analyzer.df)
    overallDf[f'{rolling_wide_resolution} days rolling average'] = overallDf['Close'].rolling(rolling_wide_resolution).mean()
    overallDf[f'{rolling_narrow_resolution} days rolling average'] = overallDf['Close'].rolling(rolling_narrow_resolution).mean()
    overallDf.rename(columns={'Close':'Daily closing price'}, inplace=True)
    overallDf = overallDf[analyzer.rangeMaxYrs.min():pd.to_datetime('today')]
    sns.lineplot(data=overallDf, dashes=False, ax=axs[currentAxis], legend='full')
    axs[currentAxis].set_title(f'Daily close prices of last {analyzer.rangeNumOfYears} years')
    axs[currentAxis].set_ylabel(analyzer.ticker.info['currency'])
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    # Plot overall closing prices of last x years with STL trend
    overallDf = pd.DataFrame(data=analyzer.trendDecompDf)
    overallDf = overallDf[analyzer.rangeMaxYrs.min():pd.to_datetime('today')]
    overallDf['Daily closing price'] = analyzer.df[analyzer.rangeMaxYrs.min():pd.to_datetime('today')]['Close']
    sns.lineplot(data=overallDf, dashes=False, ax=axs[currentAxis], legend='full')
    axs[currentAxis].set_title(f'Fitting of daily closing prices to STL trend of last {analyzer.rangeNumOfYears} years')
    axs[currentAxis].set_ylabel(analyzer.ticker.info['currency'])
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    # Plot overall STL residual of last x years with STL trend
    overallDf = pd.DataFrame(data=analyzer.residDecompDf)
    sns.lineplot(data=overallDf, dashes=False, ax=axs[currentAxis], legend='full')
    axs[currentAxis].set_title(f'Residual of STL trend of last {analyzer.rangeNumOfYears} years')
    axs[currentAxis].set_ylabel(analyzer.ticker.info['currency'])
    currentAxis += 1
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    pdf.savefig(figOverall, facecolor='w')

    # Second page - plot annual analysis
    axs = []
    numSubPlots = 5

    figAnnually = plt.figure()
    pdfLayout(figAnnually)
    gs = GridSpec(5, 3, figure=figAnnually)
    figAnnually.suptitle(f'Annual analysis of {analyzer.ticker.info["longName"]}\nof last {analyzer.rangeNumOfYears} years\n', fontsize=20)

    currentAxis = 0

    axs.append(figAnnually.add_subplot(gs[0, :]))   # add plot over full line
    # Plot annual closing prices with confidence band
    sns.lineplot(data=analyzer.annualDf, x='Day', y='Close', ax=axs[currentAxis], sort=True)
    sns.lineplot(data=analyzer.annualDf, x='Day', y='rolling average', ax=axs[currentAxis], sort=True, errorbar=None)
    axs[currentAxis].xaxis.set_major_locator(mdates.MonthLocator())
    axs[currentAxis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_xlabel('Date')
    axs[currentAxis].set_title(f'annually closing prices')
    axs[currentAxis].legend(labels=['Daily Mean', '90% Confidence', 'Mean of Rolling Averages'])
    axs[currentAxis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    axs.append(figAnnually.add_subplot(gs[1, :]))   # add plot over full line
    # Plot annual seasonal prices with confidence band
    sns.lineplot(data=analyzer.annunalSeasonalDecompDf, ax=axs[currentAxis], x='Day', y='value')
    sns.lineplot(data=analyzer.annunalSeasonalDecompDf, x='Day', y='rolling average', ax=axs[currentAxis], sort=True, errorbar=None)
    axs[currentAxis].xaxis.set_major_locator(mdates.MonthLocator())
    axs[currentAxis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_xlabel('Date')
    axs[currentAxis].set_title(f'annually seasonal price changes')
    axs[currentAxis].legend(labels=['Daily Mean', '90% Confidence', 'Mean of Rolling Averages'])
    axs[currentAxis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    axs.append(figAnnually.add_subplot(gs[2, :]))   # add plot over full line
    # Plot annual residual prices with confidence band
    sns.lineplot(data=analyzer.annunalResidDecompDf, ax=axs[currentAxis], x='Day', y='value')
    sns.lineplot(data=analyzer.annunalResidDecompDf, x='Day', y='rolling average', ax=axs[currentAxis], sort=True, errorbar=None)
    axs[currentAxis].xaxis.set_major_locator(mdates.MonthLocator())
    axs[currentAxis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_xlabel('Date')
    axs[currentAxis].set_title(f'Annually non-seasonal price changes')
    axs[currentAxis].legend(labels=['Daily Mean', '90% Confidence', 'Mean of Rolling Averages'])
    axs[currentAxis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    axs.append(figAnnually.add_subplot(gs[3, 0]))
    # Plot quarterly seasonal prices
    sns.boxplot(data=analyzer.quarterlySeasonalDecompDf, x='Quarter', y='value', ax=axs[currentAxis])
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_title(f'Quarterly')
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    axs.append(figAnnually.add_subplot(gs[3, 1:]))
    # Plot monthly seasonal prices
    sns.boxplot(data=analyzer.monthlySeasonalDecompDf, x='Month', y='value', ax=axs[currentAxis])
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_title(f'Monthly')
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    axs.append(figAnnually.add_subplot(gs[4, :-1]))
    # Plot weekly seasonal prices
    sns.boxplot(data=analyzer.weeklySeasonalDecompDf, x='Week', y='value', ax=axs[currentAxis])
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_title(f'Weekly')
    axs[currentAxis].tick_params(axis='x', labelsize=4)
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    axs.append(figAnnually.add_subplot(gs[4, 2]))
    # Plot weekdaily seasonal prices
    sns.boxplot(data=analyzer.weekdailySeasonalDecompDf, x='Weekday', y='value', ax=axs[currentAxis])
    axs[currentAxis].set_ylabel('USD')
    axs[currentAxis].set_title(f'Weekdaily')
    currentAxis += 1
    cur_progress += 1
    printProgress(cur_progress, max_progress)

    pdf.savefig(figAnnually, facecolor='w')


# Close the PDF file
plt.close('all')

# Open the PDF file
os.system('open myplots.pdf')
