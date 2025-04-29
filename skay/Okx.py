import json
import os
import re
import sys
from time import strftime

import requests
import logging
from okx.websocket.WsPublicAsync import WsPublicAsync
from okx.websocket.WsPrivateAsync import WsPrivateAsync
from okx.Trade import TradeAPI

class OkxBot():

    def __init__(self):
        self.logger = logging.getLogger(os.getenv("BOT_NAME"))
        self.logger.debug(f"{os.getenv("BOT_NAME")} init...")
        self.apiKey = os.getenv('API_KEY')
        self.secretKey = os.getenv("SECRET_KEY")
        self.passphrase = os.getenv("PASSPHRASE")
        self.symbol = os.getenv("SYMBOL")
        self.interval = f'candle{os.getenv("INTERVAL")}'
        self.instruments = None
        self.klines = {}
        self.quoteBalance = 0
        self.baseBalance = 0
        self.orderId = None
        self.order = None

    def msgCallback(self, message):
        msg = json.loads(message)
        ev = msg.get('event')
        arg = msg.get('arg')
        data = msg.get('data')
        if ev == 'error':
            print(f"Error: {msg}")
        elif ev == 'login':
            self.logger.info("Bot is logged in")
        elif ev == 'subscribe':
            self.logger.info(f"Subscribed: {arg.get('channel').title()}")
        elif ev == 'channel-conn-count' and int(msg.get('connCount')) > 20:
            self.logger.debug("Channel conn count > 20")
            exit()
        elif data and arg.get('channel') == 'instruments':
            if data[0]['instId'] == self.symbol:
                print("Instrument: ", data[0])
                self.instruments = data[0]
        elif data and arg.get('channel') == self.interval:
            self.klines = {'open': float(data[0][1]), 'close': float(data[0][4])}
        elif data and arg.get('channel') == 'account':
            for k, i in enumerate(data[0]['details']):
                if i['ccy'] == self.symbol.split('-')[0]:
                    self.baseBalance = float(i['eq'])
                elif i['ccy'] == self.symbol.split('-')[1]:
                    self.quoteBalance = float(i['eq'])
        elif arg and arg['channel'] == 'orders' and data:
            if data[0]['state'] == 'filled' and data[0]['tag'] == 'bot':
                self.order = data[0]

    async def public(self):
        url = "wss://ws.okx.com:8443/ws/v5/public"
        ws = WsPublicAsync(url=url)
        await ws.start()
        args = []
        arg1 = {"channel": "instruments", "instType": "SPOT", "instId": self.symbol}
        args.append(arg1)
        await ws.subscribe(args, callback=self.msgCallback)

    async def business(self):
        url = "wss://ws.okx.com:8443/ws/v5/business"
        ws = WsPublicAsync(url=url)
        await ws.start()
        args = []
        arg1 = {"channel": self.interval, "instId": self.symbol}
        args.append(arg1)
        await ws.subscribe(args, callback=self.msgCallback)

    async def private(self):
        url = "wss://ws.okx.com:8443/ws/v5/private"
        ws = WsPrivateAsync(
            apiKey=os.getenv("API_KEY"),
            secretKey=os.getenv("SECRET_KEY"),
            passphrase=os.getenv("PASSPHRASE"),
            url=url,
            useServerTime=False
        )
        await ws.start()
        args = []
        arg1 = {"channel": "account"}
        arg2 = {
            "channel": "orders",
            "instType": "SPOT",
            "instId": self.symbol
        }
        args.append(arg1)
        args.append(arg2)
        await ws.subscribe(args, callback=self.msgCallback)

    def sendTicker(self, sz, side='buy', tag='bot'):
        tradeAPI = TradeAPI(self.apiKey, self.secretKey, self.passphrase, False, "0")
        result = tradeAPI.place_order(
            instId = self.symbol,
            tdMode = 'cash',
            ordType = "market",
            sz = sz,
            px = self.klines['close'],
            side = side,
            tgtCcy = 'base_ccy',
            tag = tag,
        )
        if result['code'] == '0':
            result['data'][0]['ordId'] = self.orderId
        else:
            self.logger.error(result)
            sys.exit(1)
        return result

    def getInstruments(self):
        res = requests.get(f'https://www.okx.com/api/v5/public/instruments?instType=SPOT&instId={self.symbol}')
        self.instruments = res.json()['data'][0]
