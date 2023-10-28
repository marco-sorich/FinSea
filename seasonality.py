import argparse
import os

import seasonality as ssn


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
# symbol = 'BTC-USD'    # Bitcoin USD
# symbol = 'ETH-USD'    # Ethereum USD
# symbol = '^GSPC'      # S&P 500
# symbol = 'AAPL'       # Apple


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


analyzer = ssn.Analyzer(parser.parse_args().symbol, parser.parse_args().years)
analyzer.calc()

analyzer.render(parser.parse_args().view, parser.parse_args().file)

if parser.parse_args().file != '':
    os.system(f'open {parser.parse_args().file}')
