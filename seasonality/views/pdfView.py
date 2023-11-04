import datetime as dt

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages

import pandas as pd

import seaborn as sns

from progress.bar import Bar

from .view import View
from ..model import Model


def _pdf_layout(figure: plt.Figure) -> None:
    """ Layouts the figure for PDF export """
    figure.subplots_adjust(top=0.85, bottom=0.15, left=0.1, hspace=0.7, wspace=0.7)


class PdfView(View):

    def __init__(
            self, model: Model,
            file_path: str,
            ann_conf_band=("ci", 95),
            no_overall_daily_prices_plot: bool = False,
            no_overall_daily_trend_plot: bool = False,
            no_overall_daily_residual_plot: bool = False,
            no_annual_daily_prices_plot: bool = False,
            no_annual_daily_seasonal_plot: bool = False,
            no_annual_daily_redisdual_plot: bool = False,
            no_annual_weekly_seasonal_plot: bool = False,
            no_annual_monthly_seasonal_plot: bool = False,
            no_annual_quarterly_seasonal_plot: bool = False,
            no_weekdaily_seasonal_plot: bool = True,
            page_width: int = 210,
            page_height: int = 297,
    ) -> None:
        """ Creates a new PdfView object with the given self._model and file path """
        super().__init__(model)
        if file_path == '':
            raise ValueError('File path must not be empty')
        if no_overall_daily_prices_plot and no_overall_daily_trend_plot and no_overall_daily_residual_plot and no_annual_daily_prices_plot and no_annual_daily_seasonal_plot and no_annual_daily_redisdual_plot and no_annual_weekly_seasonal_plot and no_annual_monthly_seasonal_plot and no_annual_quarterly_seasonal_plot and no_weekdaily_seasonal_plot:
            raise ValueError('At least one plot must be enabled')
        self._file_path = file_path
        self._ann_conf_band = ann_conf_band
        self._no_overall_daily_prices_plot = no_overall_daily_prices_plot
        self._no_overall_daily_trend_plot = no_overall_daily_trend_plot
        self._no_overall_daily_residual_plot = no_overall_daily_residual_plot
        self._no_annual_daily_prices_plot = no_annual_daily_prices_plot
        self._no_annual_daily_seasonal_plot = no_annual_daily_seasonal_plot
        self._no_annual_daily_redisdual_plot = no_annual_daily_redisdual_plot
        self._no_annual_weekly_seasonal_plot = no_annual_weekly_seasonal_plot
        self._no_annual_monthly_seasonal_plot = no_annual_monthly_seasonal_plot
        self._no_annual_quarterly_seasonal_plot = no_annual_quarterly_seasonal_plot
        self._no_weekdaily_seasonal_plot = no_weekdaily_seasonal_plot
        self._page_width = page_width
        self._page_height = page_height

    def render(self) -> None:
        """ Creates a PDF file with the analysis results """

        # configure progress bar
        max_progress = 11 - self._no_overall_daily_prices_plot - self._no_overall_daily_trend_plot - self._no_overall_daily_residual_plot - self._no_annual_daily_prices_plot - self._no_annual_daily_seasonal_plot - self._no_annual_daily_redisdual_plot - self._no_annual_weekly_seasonal_plot - self._no_annual_monthly_seasonal_plot - self._no_annual_quarterly_seasonal_plot - self._no_weekdaily_seasonal_plot
        bar = Bar('Processing', max=max_progress, suffix='%(percent).1f%% - ETA %(eta)ds')
        bar.next()

        # Set the figure size to DIN A4 dimensions with a 10mm border
        fig_width = self._page_width + 20  # 10mm border on each side
        fig_height = self._page_height + 20  # 10mm border on each side

        # set number of days for rolling averages for full data plots
        rolling_narrow_resolution = 50
        rolling_wide_resolution = 200

        # configure graphical apperance of plots
        sns.set_theme(context='paper', font_scale=0.8, rc={'figure.figsize': (fig_width / 25.4, fig_height / 25.4)}, style='darkgrid')

        # get long name of ticker and prepare for MathText
        symbol_name = self._model.get_symbol_name()
        symbol_name_mathtext = symbol_name.replace("^", "").replace(" ", "\\ ")

        # Create new PDF file
        with PdfPages(self._file_path) as pdf:

            # first page - plot overall analysis
            num_subplots = 3 - self._no_overall_daily_prices_plot - self._no_overall_daily_trend_plot - self._no_overall_daily_residual_plot
            if num_subplots > 0:
                fig_overall, axs = plt.subplots(num_subplots, 1)
                _pdf_layout(fig_overall)
                fig_overall.suptitle(f'Overall analysis of\n$\\bf{{{symbol_name_mathtext}}}$', fontsize=20)

                # if only one subplot, convert to list
                if num_subplots == 1:
                    axs = [axs]
                current_axis = 0

                # Plot overall daily closing prices of last x years
                if not self._no_overall_daily_prices_plot:
                    overall_df = pd.DataFrame(data=self._model.get_overall_daily_prices())
                    overall_df[f'{rolling_wide_resolution} days rolling average'] = overall_df['Close'].rolling(rolling_wide_resolution).mean()
                    overall_df[f'{rolling_narrow_resolution} days rolling average'] = overall_df['Close'].rolling(rolling_narrow_resolution).mean()
                    overall_df.rename(columns={'Close': 'Daily closing price'}, inplace=True)
                    overall_df = overall_df[self._model.range_max_yrs.min():pd.to_datetime('today')]
                    sns.lineplot(data=overall_df, dashes=False, ax=axs[current_axis], legend='full')
                    axs[current_axis].set_title(f'Daily close prices of last {self._model.range_num_of_years} years')
                    axs[current_axis].set_ylabel(self._model.ticker.info['currency'])
                    current_axis += 1
                    bar.next()

                # Plot overall daily trend of last x years
                if not self._no_overall_daily_trend_plot:
                    overall_df = pd.DataFrame(data=self._model.get_overall_daily_trend())
                    overall_df = overall_df[self._model.range_max_yrs.min():pd.to_datetime('today')]
                    overall_df['Daily closing price'] = self._model.get_overall_daily_prices()[self._model.range_max_yrs.min():pd.to_datetime('today')]['Close']
                    sns.lineplot(data=overall_df, dashes=False, ax=axs[current_axis], legend='full')
                    axs[current_axis].set_title(f'Fitting of daily closing prices to STL trend of last {self._model.range_num_of_years} years')
                    axs[current_axis].set_ylabel(self._model.ticker.info['currency'])
                    current_axis += 1
                    bar.next()

                # Plot overall daily residual of last x years
                if not self._no_overall_daily_residual_plot:
                    overall_df = pd.DataFrame(data=self._model.get_overall_daily_residual())
                    sns.lineplot(data=overall_df, dashes=False, ax=axs[current_axis], legend='full')
                    axs[current_axis].set_title(f'Residual of STL trend of last {self._model.range_num_of_years} years')
                    axs[current_axis].set_ylabel(self._model.ticker.info['currency'])
                    bar.next()

                pdf.savefig(fig_overall, facecolor='w')

            # Second page - plot annual analysis
            axs = []
            num_lines = 5 - self._no_annual_daily_prices_plot - self._no_annual_daily_seasonal_plot - self._no_annual_daily_redisdual_plot
            if self._no_annual_quarterly_seasonal_plot and self._no_annual_monthly_seasonal_plot:
                num_lines -= 1
            if self._no_annual_weekly_seasonal_plot and self._no_weekdaily_seasonal_plot:
                num_lines -= 1
            num_cols = 3

            if num_lines > 0:
                fig_annually = plt.figure()
                _pdf_layout(fig_annually)
                gs = GridSpec(num_lines, num_cols, figure=fig_annually)
                fig_annually.suptitle(f'Annual analysis of\n$\\bf{{{symbol_name_mathtext}}}$\nof last {self._model.range_num_of_years} years\n', fontsize=20)

                current_axis = 0

                # Plot annual daily closing prices with confidence band
                if not self._no_annual_daily_prices_plot:
                    axs.append(fig_annually.add_subplot(gs[0, :]))   # add plot over full line
                    annual_df = self._model.get_annual_daily_prices()
                    sns.lineplot(data=annual_df, x='Day', y='Close', ax=axs[current_axis], sort=True, errorbar=self._ann_conf_band)
                    axs[current_axis].xaxis.set_major_locator(mdates.MonthLocator())
                    axs[current_axis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_xlabel('Date')
                    axs[current_axis].set_title('annually closing prices')
                    labels = ['Daily Mean', 'today']
                    if self._ann_conf_band:
                        labels.insert(1, '90% Confidence')
                    axs[current_axis].legend(labels=labels)
                    axs[current_axis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
                    current_axis += 1
                    bar.next()

                # Plot annual daily seasonal prices with confidence band
                if not self._no_annual_daily_seasonal_plot:
                    axs.append(fig_annually.add_subplot(gs[1, :]))   # add plot over full line
                    annunal_seasonal_decomp_df = self._model.get_annual_daily_seasonal()
                    sns.lineplot(data=annunal_seasonal_decomp_df, ax=axs[current_axis], x='Day', y='value', errorbar=self._ann_conf_band)
                    axs[current_axis].xaxis.set_major_locator(mdates.MonthLocator())
                    axs[current_axis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_xlabel('Date')
                    axs[current_axis].set_title('annually seasonal price changes')
                    labels = ['Daily Mean', 'today']
                    if self._ann_conf_band:
                        labels.insert(1, '90% Confidence')
                    axs[current_axis].legend(labels=labels)
                    axs[current_axis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
                    current_axis += 1
                    bar.next()

                # Plot annual daily residual prices with confidence band
                if not self._no_annual_daily_redisdual_plot:
                    axs.append(fig_annually.add_subplot(gs[2, :]))   # add plot over full line
                    annunal_resid_decomp_df = self._model.get_annual_daily_residual()
                    sns.lineplot(data=annunal_resid_decomp_df, ax=axs[current_axis], x='Day', y='value', errorbar=self._ann_conf_band)
                    axs[current_axis].xaxis.set_major_locator(mdates.MonthLocator())
                    axs[current_axis].axvline(f'{"{:02d}".format(dt.date.today().month)}-{"{:02d}".format(dt.date.today().day)}', ymin=0.05, ymax=0.95, linestyle='dashed')
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_xlabel('Date')
                    axs[current_axis].set_title('Annually non-seasonal price changes')
                    labels = ['Daily Mean', 'today']
                    if self._ann_conf_band:
                        labels.insert(1, '90% Confidence')
                    axs[current_axis].legend(labels=labels)
                    axs[current_axis].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
                    current_axis += 1
                    bar.next()

                # Plot annual quarterly seasonal prices
                if not self._no_annual_quarterly_seasonal_plot:
                    if self._no_annual_monthly_seasonal_plot:
                        axs.append(fig_annually.add_subplot(gs[3, :]))
                    else:
                        axs.append(fig_annually.add_subplot(gs[3, 0]))
                    sns.boxplot(data=self._model.get_annual_quarterly_seasonal(), x='Quarter', y='value', ax=axs[current_axis])
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_title('Quarterly')
                    current_axis += 1
                    bar.next()

                # Plot annual monthly seasonal prices
                if not self._no_annual_monthly_seasonal_plot:
                    if self._no_annual_quarterly_seasonal_plot:
                        axs.append(fig_annually.add_subplot(gs[3, :]))
                    else:
                        axs.append(fig_annually.add_subplot(gs[3, 1:]))
                    sns.boxplot(data=self._model.get_monthly_seasonal(), x='Month', y='value', ax=axs[current_axis])
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_title('Monthly')
                    current_axis += 1
                    bar.next()

                # Plot annual weekly seasonal prices
                if not self._no_annual_weekly_seasonal_plot:
                    if self._no_weekdaily_seasonal_plot:
                        axs.append(fig_annually.add_subplot(gs[4, :]))
                    else:
                        axs.append(fig_annually.add_subplot(gs[4, :-1]))
                    sns.boxplot(data=self._model.get_annual_weekly_seasonal(), x='Week', y='value', ax=axs[current_axis])
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_title('Weekly')
                    axs[current_axis].tick_params(axis='x', labelsize=4)
                    current_axis += 1
                    bar.next()

                # Plot weekdaily seasonal prices
                if not self._no_weekdaily_seasonal_plot:
                    if self._no_annual_weekly_seasonal_plot:
                        axs.append(fig_annually.add_subplot(gs[4, :]))
                    else:
                        axs.append(fig_annually.add_subplot(gs[4, 2]))
                    sns.boxplot(data=self._model.get_weekdaily_seasonal(), x='Weekday', y='value', ax=axs[current_axis])
                    axs[current_axis].set_ylabel('USD')
                    axs[current_axis].set_title('Weekdaily')
                    current_axis += 1
                    bar.next()

                pdf.savefig(fig_annually, facecolor='w')

        # Close the PDF file
        plt.close('all')

        # Close the progress bar
        bar.finish()
