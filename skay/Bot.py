import asyncio
import logging
import os
from time import strftime
from skay.Okx import Okx
from skay.DataBase import DataBase
from skay.Models import Instruments, Orders

db = DataBase().set_db()


class Bot(Okx):

    def __init__(self):
        super(Bot, self).__init__()
        self.qty = float(os.getenv('QTY'))
        self.min = float(os.getenv('MIN'))
        self.max = float(os.getenv('MAX'))
        self.percent = float(os.getenv('PERCENT'))
        self.grid = []
        self.grid_px = 0.0
        self.to_buy = 0.0
        self.y = 0.0

    async def check(self):
        self.logger.info("Bot is running!")
        self.get_grid_position()
        if self.instruments is None:
            self.getInstruments()
            self.save_instruments(self.instruments)
        while True:
            if self.mark_price:
                self.grid_px = round(self.array_grid(self.grid, self.mark_price), 9)
                pos = self.is_position()
                if (self.candle and self.candle['open'] < self.candle['close']
                        and self.to_buy == 0):
                    self.y = self.grid_px
                    self.to_buy = 1
                elif (self.candle and self.candle['open'] > self.candle['close']
                      and self.to_buy == 1):
                    self.to_buy = 0
                if pos and self.quoteBalance > pos.sz and self.order is None:
                    await self.send_ticker(sz=pos.sz, side='sell')
                elif pos and self.quoteBalance < pos.sz and self.order is None:
                    await self.send_ticker(sz=self.qty, side='buy', tag='completed')
                elif (pos is False and self.to_buy == 1 and self.mark_price >= self.y
                      and self.baseBalance > self.qty and self.order is None):
                    self.y = self.grid_px
                    await self.send_ticker(sz=self.qty, side='buy')
                if pos and self.order and self.order['state'] == 'filled' and self.order['side'] == 'sell':
                    self.order['profit'] = 0.0
                    _ord = self.save_order(self.order, False)
                    pos.cTime = strftime('%Y%m%d%H%M%S')
                    pos.is_active = False
                    db.commit()
                    self.logger.info(_ord)
                    self.order = None
                elif (self.order and self.order['state'] == 'filled'
                      and self.order['side'] == 'buy' and self.order['tag'] == 'completed'):
                    self.order['profit'] = 0.0
                    _ord = self.save_order(self.order, False)
                    logger.info(_ord)
                    self.order = None
                elif (self.order and self.order['state'] == 'filled'
                      and self.order['side'] == 'buy' and self.order['tag'] == 'bot'):
                    self.order['fillSz'] = float(self.order['fillSz']) + float(self.order['fee'])
                    self.order['profit'] = (float(self.order['fillPx']) +
                                            (float(self.order['fillPx']) * self.percent / 100))
                    _ord = self.save_order(self.order, True)
                    self.logger.info(_ord)
                    self.order = None
            await asyncio.sleep(1)


    def save_instruments(self, instr):
        _inst = db.query(Instruments.instId == self.symbol).first()
        if _inst:
            _inst = instr
            db.commit()
        else:
            _inst = Instruments(
                instId=instr.get('instId'),
                instType=instr.get('instType'),
                minSz=float(instr.get('minSz')),
                lotSz=float(instr.get('lotSz')),
                baseCcy=instr.get('baseCcy'),
                quoteCcy=instr.get('quoteCcy'),
                state=instr.get('state'),
            )
            db.add(_inst)
            db.commit()
            return _inst


    def save_order(self, order, active=True):
        _ord = Orders(
            ordId=order.get('ordId'),
            cTime=strftime('%Y%m%d%H%M%S'),
            sz=order.get('fillSz'),
            px=order.get('fillPx'),
            grid_px=self.grid_px,
            profit=order.get('profit'),
            fee=order.get('fee'),
            feeCcy=order.get('feeCcy'),
            side=order.get('side'),
            instId=order.get('instId'),
            is_active=active,
            instType=order.get('instType'),
            state=order.get('state'),
            tgtCcy=order.get('tgtCcy'),
            tag=order.get('tag'),
        )
        db.add(_ord)
        db.commit()
        return _ord

    def get_grid_position(self):
        x = self.min
        while x <= self.max:
            x += (x * self.percent / 100)
            self.grid.append(x)

    def array_grid(self, a, val):
        return round(min([x for x in a if x > val] or [None]), 9)

    def is_position(self):
        _ord = (db.query(Orders).filter(Orders.profit < self.mark_price, Orders.is_active == True)
                .order_by(Orders.px).first())
        if _ord:
            return _ord
        _ord = db.query(Orders).filter(Orders.grid_px == self.grid_px,
                                       Orders.is_active == True).first()
        if _ord:
            return None
        else:
            return False

    async def start(self):
        await asyncio.gather(self.ws_private(), self.ws_public(), self.ws_business(), self.check())
