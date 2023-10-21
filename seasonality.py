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
symbol = '^GSPC'      # S&P 500
# symbol = 'AAPL'       # Apple


# set maximum number of years to analyze
max_num_of_years = 5


parser = argparse.ArgumentParser(description='Seasonality Analyzer')
parser.add_argument('-s', '--symbol', type=str, default=symbol, help='Ticker symbol to analyze')
parser.add_argument('-y', '--years', type=int, default=max_num_of_years, help='Maximum number of years to analyze backwards')
parser.add_argument('-v', '--view', type=str, default='console', help='View to render the results (''console'' or ''pdf'')')
parser.add_argument('-f', '--file', type=str, default='myPlots.pdf', help='File name to save the results (optional for ''console'' view))')


analyzer = ssn.Analyzer(parser.parse_args.symbol, parser.parse_args.years)
analyzer.calc()

if parser.parse_args().view == 'console':
    analyzer.render(ssn.Views.CONSOLE)
elif parser.parse_args().view == 'pdf':
    analyzer.render(ssn.Views.PDF, parser.parse_args().file)
    os.system('open myplots.pdf')
else:
    raise ValueError('Unknown view type')
