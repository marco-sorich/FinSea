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


analyzer = ssn.Analyzer(symbol, max_num_of_years)
analyzer.calc()
analyzer.render(ssn.Views.PDF, 'myPlots.pdf')

# Open the PDF file
os.system('open myplots.pdf')
