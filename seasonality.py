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


def print_progress(current: int, total: int) -> None:
    """ Prints the progress of the analysis """
    progress = (current + 1) / total
    print("\r[%-20s] %d%%" % ('=' * int(20 * progress), 100 * progress), end='')
    if current == total - 1:
        print()


def pdf_layout(figure: plt.Figure) -> None:
    """ Layouts the figure for PDF export """
    figure.subplots_adjust(top=0.85, bottom=0.15, left=0.1, hspace=0.7, wspace=0.7)


def create_pdf(analyzer: ssn.Analyzer, file_path: str) -> None:
    """ Creates a PDF file with the analysis results """

    max_progress = 14
    cur_progress = 0; print_progress(cur_progress, max_progress)

    # Set the figure size to DIN A4 dimensions with a 10mm border
    fig_width = 210 + 20  # 210mm + 10mm border on each side
    fig_height = 297 + 20  # 297mm + 10mm border on each side

    # set number of days for rolling averages for full data plots
    rolling_narrow_resolution = 50
    rolling_wide_resolution = 200

    # configure graphical apperance of plots
    sns.set_theme(context='paper', font_scale=0.8, rc={'figure.figsize': (fig_width / 25.4, fig_height / 25.4)}, style='darkgrid')

    # Create new PDF file
    with PdfPages(file_path) as pdf:

        # first page - plot overall analysis
        num_subplots = 3
        fig_overall, axs = plt.subplots(num_subplots, 1)
        pdf_layout(fig_overall)
        fig_overall.suptitle(f'Overall analysis of {analyzer.ticker.info["longName"]}\n', fontsize=20)

        current_axis = 0

        # Plot overall closing prices of last x years
        overall_df = pd.DataFrame(data=analyzer.get_original())
        overall_df[f'{rolling_wide_resolution} days rolling average'] = overall_df['Close'].rolling(rolling_wide_resolution).mean()
        overall_df[f'{rolling_narrow_resolution} days rolling average'] = overall_df['Close'].rolling(rolling_narrow_resolution).mean()
        overall_df.rename(columns={'Close': 'Daily closing price'}, inplace=True)
        overall_df = overall_df[analyzer.range_max_yrs.min():pd.to_datetime('today')]
        sns.lineplot(data=overall_df, dashes=False, ax=axs[current_axis], legend='full')
        axs[current_axis].set_title(f'Daily close prices of last {analyzer.range_num_of_years} years')
        axs[current_axis].set_ylabel(analyzer.ticker.info['currency'])
        current_axis += 1
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        # Plot overall trend of last x years with STL trend
        overall_df = pd.DataFrame(data=analyzer.get_trend())
        overall_df = overall_df[analyzer.range_max_yrs.min():pd.to_datetime('today')]
        overall_df['Daily closing price'] = analyzer.get_original()[analyzer.range_max_yrs.min():pd.to_datetime('today')]['Close']
        sns.lineplot(data=overall_df, dashes=False, ax=axs[current_axis], legend='full')
        axs[current_axis].set_title(f'Fitting of daily closing prices to STL trend of last {analyzer.range_num_of_years} years')
        axs[current_axis].set_ylabel(analyzer.ticker.info['currency'])
        current_axis += 1
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        # Plot overall STL residual of last x years with STL trend
        overall_df = pd.DataFrame(data=analyzer.get_residual())
        sns.lineplot(data=overall_df, dashes=False, ax=axs[current_axis], legend='full')
        axs[current_axis].set_title(f'Residual of STL trend of last {analyzer.range_num_of_years} years')
        axs[current_axis].set_ylabel(analyzer.ticker.info['currency'])
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        pdf.savefig(fig_overall, facecolor='w')

        # Second page - plot annual analysis
        axs = []
        num_subplots = 5

        fig_annually = plt.figure()
        pdf_layout(fig_annually)
        gs = GridSpec(5, 3, figure=fig_annually)
        fig_annually.suptitle(f'Annual analysis of {analyzer.ticker.info["longName"]}\nof last {analyzer.range_num_of_years} years\n', fontsize=20)

        current_axis = 0

        axs.append(fig_annually.add_subplot(gs[0, :]))   # add plot over full line
        # Plot annual closing prices with confidence band
        annual_df = analyzer.get_annual()
        sns.lineplot(data=annual_df, x='Day', y='Close', ax=axs[current_axis], sort=True)
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702
        sns.lineplot(data=annual_df, x='Day', y='rolling average', ax=axs[current_axis], sort=True, errorbar=None)
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702
        axs[current_axis].xaxis.set_major_locator(mdates.MonthLocator())
        axs[current_axis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_xlabel('Date')
        axs[current_axis].set_title('annually closing prices')
        axs[current_axis].legend(labels=['Daily Mean', '90% Confidence', 'Mean of Rolling Averages'])
        axs[current_axis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        current_axis += 1

        axs.append(fig_annually.add_subplot(gs[1, :]))   # add plot over full line
        # Plot annual seasonal prices with confidence band
        annunal_seasonal_decomp_df = analyzer.get_annual_seasonal()
        sns.lineplot(data=annunal_seasonal_decomp_df, ax=axs[current_axis], x='Day', y='value')
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702
        sns.lineplot(data=annunal_seasonal_decomp_df, x='Day', y='rolling average', ax=axs[current_axis], sort=True, errorbar=None)
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702
        axs[current_axis].xaxis.set_major_locator(mdates.MonthLocator())
        axs[current_axis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_xlabel('Date')
        axs[current_axis].set_title('annually seasonal price changes')
        axs[current_axis].legend(labels=['Daily Mean', '90% Confidence', 'Mean of Rolling Averages'])
        axs[current_axis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        current_axis += 1

        axs.append(fig_annually.add_subplot(gs[2, :]))   # add plot over full line
        # Plot annual residual prices with confidence band
        annunal_resid_decomp_df = analyzer.get_annual_residual()
        sns.lineplot(data=annunal_resid_decomp_df, ax=axs[current_axis], x='Day', y='value')
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702
        sns.lineplot(data=annunal_resid_decomp_df, x='Day', y='rolling average', ax=axs[current_axis], sort=True, errorbar=None)
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702
        axs[current_axis].xaxis.set_major_locator(mdates.MonthLocator())
        axs[current_axis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_xlabel('Date')
        axs[current_axis].set_title('Annually non-seasonal price changes')
        axs[current_axis].legend(labels=['Daily Mean', '90% Confidence', 'Mean of Rolling Averages'])
        axs[current_axis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        current_axis += 1

        axs.append(fig_annually.add_subplot(gs[3, 0]))
        # Plot quarterly seasonal prices
        sns.boxplot(data=analyzer.get_quarterly_seasonal(), x='Quarter', y='value', ax=axs[current_axis])
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_title('Quarterly')
        current_axis += 1
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        axs.append(fig_annually.add_subplot(gs[3, 1:]))
        # Plot monthly seasonal prices
        sns.boxplot(data=analyzer.get_monthly_seasonal(), x='Month', y='value', ax=axs[current_axis])
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_title('Monthly')
        current_axis += 1
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        axs.append(fig_annually.add_subplot(gs[4, :-1]))
        # Plot weekly seasonal prices
        sns.boxplot(data=analyzer.get_weekly_seasonal(), x='Week', y='value', ax=axs[current_axis])
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_title('Weekly')
        axs[current_axis].tick_params(axis='x', labelsize=4)
        current_axis += 1
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        axs.append(fig_annually.add_subplot(gs[4, 2]))
        # Plot weekdaily seasonal prices
        sns.boxplot(data=analyzer.get_weekdaily_seasonal(), x='Weekday', y='value', ax=axs[current_axis])
        axs[current_axis].set_ylabel('USD')
        axs[current_axis].set_title('Weekdaily')
        current_axis += 1
        cur_progress += 1; print_progress(cur_progress, max_progress) # noqa: 702

        pdf.savefig(fig_annually, facecolor='w')

    # Close the PDF file
    plt.close('all')


analyzer = ssn.Analyzer(symbol, max_num_of_years)
analyzer.calc()

create_pdf(analyzer, 'myPlots.pdf')

# Open the PDF file
os.system('open myplots.pdf')
