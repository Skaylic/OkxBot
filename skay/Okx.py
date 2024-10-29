import os
import websockets
import json
import hmac
import base64
import logging
from time import strftime
from datetime import datetime
import requests

# wss://wsaws.okx.com:8443/ws/v5/public
# wss://wsaws.okx.com:8443/ws/v5/private
# wss://wsaws.okx.com:8443/ws/v5/business

logger = logging.getLogger(os.getenv("BOT_NAME"))


class Okx:

    def __init__(self):
        self.logger = logging.getLogger(os.getenv("BOT_NAME"))
        self.logger.info("Bot is started!")
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('API_SECRET')
        self.passphrase = os.getenv('PASSPHRASE')
        self.symbol = os.getenv('SYMBOL')
        self.candle = {}
        self.mark_price = 0.0
        self.baseBalance = 0.0
        self.quoteBalance = 0.0
        self.instruments = None
        self.orderId = None
        self.order = None

    async def send(self, ws, op: str, args: list, ids=''):
        if not ids:
            subs = dict(op=op, args=args)
        else:
            subs = dict(id=ids, op=op, args=args)
        await ws.send(json.dumps(subs))

    async def callbackMessage(self, ws):
        while True:
            try:
                msg = json.loads(await ws.recv())
                ev = msg.get('event')
                arg = msg.get('arg')
                data = msg.get('data')
            except websockets.ConnectionClosedOK:
                break
            if ev == 'login' and msg['code'] == '0':
                self.logger.info(f"Login in!")
                return 'login'
            elif ev == 'subscribe':
                self.logger.info(f"{ev.title()}: {arg['channel']}")
            elif ev == 'error':
                self.logger.error(f"{msg['code']}: {msg['msg']}")
                exit(msg['code'])
            elif ev == 'channel-conn-count':
                self.logger.info(f"{msg['channel'].title()} connCount: {msg['connCount']}")
            if arg and arg['channel'] == 'mark-price' and data:
                self.mark_price = float(data[0]['markPx'])
            elif arg and arg['channel'] == 'mark-price-candle4H' and data:
                self.candle = {'open': data[0][1], 'close': data[0][4]}
            elif arg and arg['channel'] == 'balance_and_position' and data:
                for dt in data[0]['balData']:
                    if dt['ccy'] == self.instruments['baseCcy']:
                        self.baseBalance = float(dt['cashBal'])
                    elif dt['ccy'] == self.instruments['quoteCcy']:
                        self.quoteBalance = float(dt['cashBal'])
            elif 'op' in msg and msg['op'] == 'order':
                if int(data[0]['sCode']) == 0:
                    self.orderId = data[0]['ordId']
                elif int(data[0]['sCode']) != 0:
                    logger.error(f'Error: {data[0]['sCode']} {data[0]["sMsg"]}')
            elif arg and arg['channel'] == 'orders' and data:
                if data[0]['state'] == 'filled':
                    self.order = data[0]

    def sign(self, key: str, secret: str, passphrase: str):
        ts = str(int(datetime.now().timestamp()))
        args = dict(apiKey=key, passphrase=passphrase, timestamp=ts)
        sign = ts + 'GET' + '/users/self/verify'
        mac = hmac.new(bytes(secret, encoding='utf8'), bytes(sign, encoding='utf-8'), digestmod='sha256')
        args['sign'] = base64.b64encode(mac.digest()).decode(encoding='utf-8')
        return args

    async def ws_private(self):
        url = 'wss://ws.okx.com/ws/v5/private'

        async with websockets.connect(url) as self.ws:
            login_args: dict = self.sign(self.api_key, self.api_secret, self.passphrase)
            await self.send(self.ws, 'login', [login_args])
            r = await self.callbackMessage(self.ws)
            if r == 'login':
                await self.send(self.ws, 'subscribe', [{'channel': 'balance_and_position'}])
                await self.send(self.ws, 'subscribe',
                                [{'channel': 'orders', 'instType': 'SPOT', 'instId': self.symbol}])
                await self.callbackMessage(self.ws)

    async def ws_business(self):
        url = 'wss://ws.okx.com/ws/v5/business'

        async with websockets.connect(url) as self.ws_1:
            await self.send(self.ws_1, 'subscribe', [{'channel': 'mark-price-candle4H', 'instId': self.symbol}])
            await self.callbackMessage(self.ws_1)

    async def ws_public(self):
        url = 'wss://ws.okx.com/ws/v5/public'

        async with websockets.connect(url) as self.ws_2:
            await self.send(self.ws_2, 'subscribe', [{'channel': 'mark-price', 'instId': self.symbol}])
            await self.callbackMessage(self.ws_2)

    def send_ticker(self, sz, side='buy', tag=''):
        if not tag:
            tag = 'bot'
        self.send(self.ws_2, "order",
                  [{"instId": self.symbol,
                    "tdMode": "cash",
                    "ordType": "market",
                    "sz": sz,
                    "px": self.mark_price,
                    "side": side,
                    "tgtCcy": 'base_ccy',
                    'tag': tag}],
                  strftime("%Y%m%d%H%M%S"))

    def getInstruments(self):
        res = requests.get(f'https://www.okx.com/api/v5/public/instruments?instType=SPOT&instId={self.symbol}')
        self.instruments = res.json()['data'][0]
