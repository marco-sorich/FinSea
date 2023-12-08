import argparse
import os

import seasonality as ssn


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
# symbol = '^GSPC'      # S&P 500
# symbol = 'AAPL'       # Apple
# symbol = '^GDAXI'      # DAX
symbol = '^GDAXI'      # DAX


# set maximum number of years to analyze
max_num_of_years = 5


def view_type(view_str: str) -> ssn.Views:
    if view_str == 'console':
        return ssn.Views.CONSOLE
    elif view_str == 'pdf':
        return ssn.Views.PDF
    else:
        raise argparse.ArgumentTypeError(f'Invalid view: {view_str}')


parser = argparse.ArgumentParser(description='Seasonality Analyzer')
parser.add_argument('-s', '--symbol', type=str, default=symbol, help=f'Ticker symbol to analyze (default: {symbol})')
parser.add_argument('-y', '--years', type=int, default=max_num_of_years, help=f'Maximum number of years to analyze backwards (default: {max_num_of_years} years)')
parser.add_argument('-v', '--view', type=view_type, default=ssn.Views.CONSOLE, help='View to render the results (''console'' or ''pdf'', default: console)')
parser.add_argument('-f', '--file', type=str, default='', help='File name to save the results (optional for console view)')
parser.add_argument('-a', '--ann_conf_band', action='store_true', help='Enable confidence bands to annual plots (time consuming, only for pdf view)')
parser.add_argument('-nop', '--no_overall_daily_prices_plot', action='store_true', help='Disable overall daily prices plot in pdf view')
parser.add_argument('-not', '--no_overall_daily_trend_plot', action='store_true', help='Disable overall daily trend plot in pdf view')
parser.add_argument('-nor', '--no_overall_daily_residual_plot', action='store_true', help='Disable overall daily residual plot in pdf view')
parser.add_argument('-noap', '--no_annual_daily_prices_plot', action='store_true', help='Disable annual daily prices plot in pdf view')
parser.add_argument('-noas', '--no_annual_daily_seasonal_plot', action='store_true', help='Disable annual daily seasonal plot in pdf view')
parser.add_argument('-noar', '--no_annual_daily_redisdual_plot', action='store_true', help='Disable annual daily residual plot in pdf view')
parser.add_argument('-noaw', '--no_annual_weekly_seasonal_plot', action='store_true', help='Disable annual weekly seasonal plot in pdf view')
parser.add_argument('-noam', '--no_annual_monthly_seasonal_plot', action='store_true', help='Disable annual monthly seasonal plot in pdf view')
parser.add_argument('-noaq', '--no_annual_quarterly_seasonal_plot', action='store_true', help='Disable annual quarterly seasonal plot in pdf view')
parser.add_argument('-now', '--no_weekdaily_seasonal_plot', action='store_true', help='Disable weekdaily seasonal plot in pdf view')
parser.add_argument('-pw', '--page_width', type=int, default=210, help='Page width in mm for pdf view (default: 210)')
parser.add_argument('-ph', '--page_height', type=int, default=297, help='Page height in mm for pdf view (default: 297)')
# parser.add_argument('-sd', '--start_date', type=str, help='Start date in YYYY-MM-DD format')
# parser.add_argument('-ed', '--end_date', type=str, help='End date in YYYY-MM-DD format')


analyzer = ssn.Analyzer(parser.parse_args().symbol, parser.parse_args().years)
analyzer.calc()

analyzer.render(
    parser.parse_args().view,
    parser.parse_args().file,
    ann_conf_band=parser.parse_args().ann_conf_band,
    no_overall_daily_prices_plot=parser.parse_args().no_overall_daily_prices_plot,
    no_overall_daily_trend_plot=parser.parse_args().no_overall_daily_trend_plot,
    no_overall_daily_residual_plot=parser.parse_args().no_overall_daily_residual_plot,
    no_annual_daily_prices_plot=parser.parse_args().no_annual_daily_prices_plot,
    no_annual_daily_seasonal_plot=parser.parse_args().no_annual_daily_seasonal_plot,
    no_annual_daily_redisdual_plot=parser.parse_args().no_annual_daily_redisdual_plot,
    no_annual_weekly_seasonal_plot=parser.parse_args().no_annual_weekly_seasonal_plot,
    no_annual_monthly_seasonal_plot=parser.parse_args().no_annual_monthly_seasonal_plot,
    no_annual_quarterly_seasonal_plot=parser.parse_args().no_annual_quarterly_seasonal_plot,
    no_weekdaily_seasonal_plot=parser.parse_args().no_weekdaily_seasonal_plot,
    page_width=parser.parse_args().page_width,
    page_height=parser.parse_args().page_height
)

if parser.parse_args().file != '':
    os.system(f'open {parser.parse_args().file}')
