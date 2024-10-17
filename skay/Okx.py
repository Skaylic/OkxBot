import base64
import hmac
import json
import os
from dotenv import load_dotenv
import websockets
from datetime import datetime
import logging
from time import strftime

load_dotenv()

logger = logging.getLogger('SkayBot')


class Okx:

    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('API_SECRET_KEY')
        self.passphrase = os.getenv('API_PASSPHRASE')
        self.symbol = os.getenv('SYMBOL')
        self.qty = float(os.getenv('QTY'))
        self.base_ccy = self.symbol.split('-')[1]
        self.quote_ccy = self.symbol.split('-')[0]
        self.bal_base_ccy = 0.0
        self.bal_quote_ccy = 0.0
        self.mark_px = 0.0
        self.sz = 0.0
        self.mark_price_candle = []
        self.order_id = None
        self.order = None

    def sign(self, key: str, secret: str, passphrase: str):
        ts = str(int(datetime.now().timestamp()))
        args = dict(apiKey=key, passphrase=passphrase, timestamp=ts)
        sign = ts + 'GET' + '/users/self/verify'
        mac = hmac.new(bytes(secret, encoding='utf8'), bytes(sign, encoding='utf-8'), digestmod='sha256')
        args['sign'] = base64.b64encode(mac.digest()).decode(encoding='utf-8')
        return args

    async def send(self, ws, op: str, args: list, ids=''):
        if not ids:
            subs = dict(op=op, args=args)
        else:
            subs = dict(id=ids, op=op, args=args)
        await ws.send(json.dumps(subs))

    async def ws_public(self):
        url = 'wss://wsaws.okx.com:8443/ws/v5/public'
        async with websockets.connect(url) as self.ws_2:
            await self.send(self.ws_2, 'subscribe', [{'channel': 'mark-price', 'instId': self.symbol}])

            async for msg in self.ws_2:
                await self.callback_public(msg)

    async def ws_business(self):
        url = 'wss://wsaws.okx.com:8443/ws/v5/business'
        async with websockets.connect(url) as self.ws_3:
            await self.send(self.ws_3, 'subscribe', [{'channel': 'candle4H', 'instId': self.symbol}])

            async for msg in self.ws_3:
                await self.callback_business(msg)

    async def ws_private(self):
        url = 'wss://wsaws.okx.com:8443/ws/v5/private'
        async with websockets.connect(url) as self.ws_1:
            login_args: dict = self.sign(self.api_key, self.api_secret, self.passphrase)
            await self.send(self.ws_1, 'login', [login_args])

            async for msg in self.ws_1:
                r = await self.callback_private(msg)
                if r == 'login':
                    await self.send(self.ws_1, 'subscribe', [{'channel': 'balance_and_position'}])
                    await self.send(self.ws_1, 'subscribe',
                                    [{'channel': 'orders', 'instType': 'SPOT', 'instId': self.symbol}])

    async def callback_public(self, msg):
        msg = json.loads(msg)
        ev = msg.get('event')
        data = msg.get('data')
        if ev == 'error':
            logger.error(f"Error: {msg}")
        elif ev in ['subscribe', 'unsubscribe'] and msg.get('arg'):
            logger.info(f"{ev.upper()} = {msg.get('arg')['channel']}")
        elif msg.get('arg') and msg.get('arg')['channel'] == 'mark-price' and data and len(data) > 0:
            self.mark_px = float(data[0]['markPx'])
            self.size(self.mark_px)

    async def callback_business(self, msg):
        msg = json.loads(msg)
        ev = msg.get('event')
        data = msg.get('data')
        if ev == 'error':
            logger.error(f"Error: {msg}")
        elif ev in ['subscribe', 'unsubscribe'] and msg.get('arg'):
            logger.info(f"{ev.upper()} = {msg.get('arg')['channel']}")
        elif msg.get('arg') and msg.get('arg')['channel'] == 'candle4H' and data and len(data) > 0:
            self.mark_price_candle = data[0]

    async def callback_private(self, msg):
        msg = json.loads(msg)
        ev = msg.get('event')
        data = msg.get('data')
        if msg.get('event') == 'channel-conn-count-error':
            logger.error('Error: Channel conn count error!')
            exit()
        if ev == 'error':
            logger.error(f"Error: {msg}")
        elif ev == 'login':
            logger.info('Ur Logged in')
            return 'login'
        elif ev in ['subscribe', 'unsubscribe'] and msg.get('arg'):
            logger.info(f"{ev.upper()} = {msg.get('arg')['channel']}")
        elif msg.get('arg') and msg.get('arg')['channel'] == 'balance_and_position' and data and len(data) > 0:
            for bl in data[0]['balData']:
                if bl['ccy'] == self.quote_ccy:
                    self.bal_quote_ccy = float(bl['cashBal'])
                elif bl['ccy'] == self.base_ccy:
                    self.bal_base_ccy = float(bl['cashBal'])
        elif msg.get('op') == 'order' and int(msg.get('code')) == 0:
            self.order_id = data[0]['ordId']
        elif msg.get('op') == 'order' and int(msg.get('code')) == 1 and int(data[0]['sCode']) != 51008:
            logger.error(f'Error: {data[0]["sCode"]} {data[0]["sMsg"]}')
            exit(int(data[0]["sCode"]))
        elif msg.get('arg') and msg.get('arg')['channel'] == 'orders' and data and len(data) > 0:
            if data[0]['state'] == 'filled':
                self.order = data[0]

    async def send_ticker(self, side='buy', sz=None, px=None, tag=''):
        if not sz:
            sz = self.sz
        if not px:
            px = self.mark_px
        if not tag:
            tag = 'bot'
        await self.send(self.ws_1, "order",
                        [{"instId": self.symbol,
                          "tdMode": "cash",
                          "ordType": "market",
                          "sz": sz,
                          "px": px,
                          "side": side,
                          "tgtCcy": 'base_ccy',
                          'tag': tag}],
                        strftime("%Y%m%d%H%M%S"))

    def size(self, mk):
        if self.bal_base_ccy < 200:
            self.sz = self.qty / 2 / mk
        elif 200 < self.bal_base_ccy < 500:
            self.sz = self.qty / mk
        elif 500 < self.bal_base_ccy < 1000:
            self.sz = self.qty * 2 / mk
