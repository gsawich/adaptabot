from kucoin.client import Market
from kucoin.client import Trade

from secrets import API_KEY
from secrets import API_SECRET

marketClient = Market(url='https://openapi-sandbox.kucoin.com')
marketClient = Market(is_sandbox=True)
tradingClient = Trade(key=API_KEY, secret=API_SECRET, passphrase='adaptabot1', is_sandbox=True)
