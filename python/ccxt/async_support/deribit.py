# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async_support.base.exchange import Exchange
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import PermissionDenied


class deribit (Exchange):

    def describe(self):
        return self.deep_extend(super(deribit, self).describe(), {
            'id': 'deribit',
            'name': 'Deribit',
            'countries': ['NL'],  # Netherlands
            'version': 'v1',
            'userAgent': None,
            'rateLimit': 2000,
            'has': {
                'CORS': True,
                'editOrder': True,
                'fetchOrder': True,
                'fetchOrders': False,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'fetchMyTrades': True,
                'fetchTickers': False,
            },
            'timeframes': {},
            'urls': {
                # 'test': 'https://test.deribit.com',
                'logo': 'https://user-images.githubusercontent.com/1294454/41933112-9e2dd65a-798b-11e8-8440-5bab2959fcb8.jpg',
                'api': 'https://www.deribit.com',
                'www': 'https://www.deribit.com',
                'doc': [
                    'https://www.deribit.com/pages/docs/api',
                    'https://github.com/deribit',
                ],
                'fees': 'https://www.deribit.com/pages/information/fees',
                'referral': 'https://www.deribit.com/reg-1189.4038',
            },
            'api': {
                'public': {
                    'get': [
                        'test',
                        'getinstruments',
                        'index',
                        'getcurrencies',
                        'getorderbook',
                        'getlasttrades',
                        'getsummary',
                        'stats',
                        'getannouncments',
                    ],
                },
                'private': {
                    'get': [
                        'account',
                        'getopenorders',
                        'positions',
                        'orderhistory',
                        'orderstate',
                        'tradehistory',
                        'newannouncements',
                    ],
                    'post': [
                        'buy',
                        'sell',
                        'edit',
                        'cancel',
                        'cancelall',
                    ],
                },
            },
            'exceptions': {
                'Invalid API Key.': AuthenticationError,
                'Access Denied': PermissionDenied,
            },
            'options': {
                'fetchTickerQuotes': True,
            },
        })

    async def fetch_markets(self, params={}):
        marketsResponse = await self.publicGetGetinstruments()
        markets = marketsResponse['result']
        result = []
        for p in range(0, len(markets)):
            market = markets[p]
            id = market['instrumentName']
            base = market['baseCurrency']
            quote = market['currency']
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            result.append({
                'id': id,
                'symbol': id,
                'base': base,
                'quote': quote,
                'active': market['isActive'],
                'precision': {
                    'amount': market['minTradeSize'],
                    'price': market['tickSize'],
                },
                'limits': {
                    'amount': {
                        'min': market['minTradeSize'],
                    },
                    'price': {
                        'min': market['tickSize'],
                    },
                },
                'type': market['kind'],
                'spot': False,
                'future': market['kind'] == 'future',
                'option': market['kind'] == 'option',
                'info': market,
            })
        return result

    async def fetch_balance(self, params={}):
        account = await self.privateGetAccount()
        result = {
            'BTC': {
                'free': account['result']['availableFunds'],
                'used': account['result']['maintenanceMargin'],
                'total': account['result']['equity'],
            },
        }
        return self.parse_balance(result)

    async def fetch_deposit_address(self, currency, params={}):
        account = await self.privateGetAccount()
        return {
            'currency': 'BTC',
            'address': account['depositAddress'],
            'tag': None,
            'info': account,
        }

    def parse_ticker(self, ticker, market=None):
        timestamp = self.safe_integer(ticker, 'created')
        iso8601 = None if (timestamp is None) else self.iso8601(timestamp)
        symbol = self.find_symbol(self.safe_string(ticker, 'instrumentName'), market)
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': iso8601,
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'bidPrice'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'askPrice'),
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': self.safe_float(ticker, 'volume'),
            'info': ticker,
        }

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetGetsummary(self.extend({
            'instrument': market['id'],
        }, params))
        return self.parse_ticker(response['result'], market)

    def parse_trade(self, trade, market=None):
        id = self.safe_string(trade, 'tradeId')
        symbol = None
        if market is not None:
            symbol = market['symbol']
        timestamp = self.safe_integer(trade, 'timeStamp')
        return {
            'info': trade,
            'id': id,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'order': None,
            'type': None,
            'side': trade['direction'],
            'price': self.safe_float(trade, 'price'),
            'amount': self.safe_float(trade, 'quantity'),
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'instrument': market['id'],
        }
        if limit is not None:
            request['limit'] = limit
        else:
            request['limit'] = 10000
        response = await self.publicGetGetlasttrades(self.extend(request, params))
        return self.parse_trades(response['result'], market, since, limit)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetGetorderbook({'instrument': market['id']})
        timestamp = int(response['usOut'] / 1000)
        orderbook = self.parse_order_book(response['result'], timestamp, 'bids', 'asks', 'price', 'quantity')
        return self.extend(orderbook, {
            'nonce': self.safe_integer(response, 'tstamp'),
        })

    def parse_order_status(self, status):
        statuses = {
            'open': 'open',
            'cancelled': 'canceled',
            'filled': 'closed',
        }
        if status in statuses:
            return statuses[status]
        return status

    def parse_order(self, order, market=None):
        #
        #     {
        #         "orderId": 5258039,          # ID of the order
        #         "type": "limit",             # not documented, but present in the actual response
        #         "instrument": "BTC-26MAY17",  # instrument name(market id)
        #         "direction": "sell",         # order direction, "buy" or "sell"
        #         "price": 1860,               # float, USD for futures, BTC for options
        #         "label": "",                 # label set by the owner, up to 32 chars
        #         "quantity": 10,              # quantity, in contracts($10 per contract for futures, ฿1 — for options)
        #         "filledQuantity": 3,         # filled quantity, in contracts($10 per contract for futures, ฿1 — for options)
        #         "avgPrice": 1860,            # average fill price of the order
        #         "commission": -0.000001613,  # in BTC units
        #         "created": 1494491899308,    # creation timestamp
        #         "state": "open",             # open, cancelled, etc
        #         "postOnly": False            # True for post-only orders only
        # open orders --------------------------------------------------------
        #         "lastUpdate": 1494491988754,  # timestamp of the last order state change(before self cancelorder of course)
        # closed orders ------------------------------------------------------
        #         "tstamp": 1494492913288,     # timestamp of the last order state change, documented, but may be missing in the actual response
        #         "modified": 1494492913289,   # timestamp of the last db write operation, e.g. trade that doesn't change order status, documented, but may missing in the actual response
        #         "adv": False                 # advanced type(false, or "usd" or "implv")
        #         "trades": [],                # not documented, injected from the outside of the parseOrder method into the order
        #     }
        #
        timestamp = self.safe_integer(order, 'created')
        lastUpdate = self.safe_integer(order, 'lastUpdate')
        lastTradeTimestamp = self.safe_integer_2(order, 'tstamp', 'modified')
        id = self.safe_string(order, 'orderId')
        price = self.safe_float(order, 'price')
        average = self.safe_float(order, 'avgPrice')
        amount = self.safe_float(order, 'quantity')
        filled = self.safe_float(order, 'filledQuantity')
        if lastTradeTimestamp is None:
            if filled is not None:
                if filled > 0:
                    lastTradeTimestamp = lastUpdate
        remaining = None
        cost = None
        if filled is not None:
            if amount is not None:
                remaining = amount - filled
            if price is not None:
                cost = price * filled
        status = self.parse_order_status(self.safe_string(order, 'state'))
        side = self.safe_string(order, 'direction')
        if side is not None:
            side = side.lower()
        feeCost = self.safe_float(order, 'commission')
        if feeCost is not None:
            feeCost = abs(feeCost)
        fee = {
            'cost': feeCost,
            'currency': 'BTC',
        }
        type = self.safe_string(order, 'type')
        return {
            'info': order,
            'id': id,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': lastTradeTimestamp,
            'symbol': order['instrument'],
            'type': type,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': cost,
            'average': average,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': fee,
            'trades': None,  # todo: parse trades
        }

    async def fetch_order(self, id, symbol=None, params={}):
        await self.load_markets()
        response = await self.privateGetOrderstate({'orderId': id})
        return self.parse_order(response['result'])

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        request = {
            'instrument': self.market_id(symbol),
            'quantity': amount,
            'type': type,
        }
        if price is not None:
            request['price'] = price
        method = 'privatePost' + self.capitalize(side)
        response = await getattr(self, method)(self.extend(request, params))
        order = self.safe_value(response['result'], 'order')
        if order is None:
            return response
        return self.parse_order(order)

    async def edit_order(self, id, symbol, type, side, amount=None, price=None, params={}):
        await self.load_markets()
        request = {
            'orderId': id,
        }
        if amount is not None:
            request['quantity'] = amount
        if price is not None:
            request['price'] = price
        response = await self.privatePostEdit(self.extend(request, params))
        return self.parse_order(response['result'])

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        response = await self.privatePostCancel(self.extend({'orderId': id}, params))
        return self.parse_order(response['result'])

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'instrument': market['id'],
        }
        response = await self.privateGetGetopenorders(self.extend(request, params))
        return self.parse_orders(response['result'], market, since, limit)

    async def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'instrument': market['id'],
        }
        response = await self.privateGetOrderhistory(self.extend(request, params))
        return self.parse_orders(response['result'], market, since, limit)

    async def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'instrument': market['id'],
        }
        if limit is not None:
            request['count'] = limit  # default = 20
        response = await self.privateGetTradehistory(self.extend(request, params))
        return self.parse_trades(response['result'], market, since, limit)

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        query = '/' + 'api/' + self.version + '/' + api + '/' + path
        url = self.urls['api'] + query
        if api == 'public':
            if params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            nonce = str(self.nonce())
            auth = '_=' + nonce + '&_ackey=' + self.apiKey + '&_acsec=' + self.secret + '&_action=' + query
            if method == 'POST':
                params = self.keysort(params)
                auth += '&' + self.urlencode(params)
            hash = self.hash(self.encode(auth), 'sha256', 'base64')
            signature = self.apiKey + '.' + nonce + '.' + self.decode(hash)
            headers = {
                'x-deribit-sig': signature,
            }
            if method != 'GET':
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                body = self.urlencode(params)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}
