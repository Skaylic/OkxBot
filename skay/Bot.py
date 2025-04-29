import os
import asyncio
from time import strftime
from skay.Okx import OkxBot
from skay.Models import Orders
from skay.DataBase import DataBase

db = DataBase().set_db()

class Bot(OkxBot):

    def __init__(self):
        OkxBot.__init__(self)
        self.qty = float(os.getenv('QTY'))
        self.min = float(os.getenv('MIN'))
        self.max = float(os.getenv('MAX'))
        self.percent = float(os.getenv('PERCENT'))
        self.grid = []
        self.grid_px = 0.0
        self.y = 0.0
        self.buy_sell = False
        self.to_buy = 0
        self.qb = 0

    def check(self):
        if self.instruments is None:
            self.getInstruments()
        if  len(self.grid) < 1:
            self.get_grid_position()
        if self.klines and self.baseBalance:
            self.check_qty()
            self.grid_px = round(self.array_grid(self.grid, self.klines['close']), 9)
            pos = self.is_position()
            if (self.klines and self.klines['open'] < self.klines['close']
                    and self.to_buy == 0):
                self.y = self.grid_px
                self.to_buy = 1
            elif (self.klines and self.klines['open'] > self.klines['close']
                  and self.to_buy == 1):
                self.to_buy = 0
            if pos and self.order is None and self.baseBalance >= pos.sz:
                self.sendTicker(sz=pos.sz, side='sell')
                self.y = self.klines['close']
            elif pos and self.order is None and self.baseBalance < pos.sz:
                self.logger.debug(f'Не достаточно {self.instruments['baseCcy']} на балансе!')
                self.sendTicker(sz=pos.sz * 2, side='buy', tag='replenishment')
            elif (pos is False and self.order is None and self.to_buy == 1 and self.klines['close'] >= self.y
                  and self.quoteBalance > self.qty):
                self.y = self.grid_px
                self.sendTicker(sz=self.qty / self.klines['close'], side='buy')
            if self.order and self.order.get('state') == 'filled' and self.order.get('side') == 'sell':
                self.order['profit'] = 0.0
                _ord = self.save_order(self.order, False)
                pos.is_active = False
                db.commit()
                self.logger.info(_ord)
                self.orderId = None
                self.order = None
            elif self.order and self.order.get('state') == 'filled' and self.order.get('side') == 'buy':
                self.order['sz'] = round(float(self.order['sz']) + float(self.order['fee']), 11)
                self.order['profit'] = round((float(self.order['avgPx']) +
                                              (float(self.order['avgPx']) * self.percent / 100)), 10)
                _ord = self.save_order(self.order, True)
                self.logger.info(_ord)
                self.orderId = None
                self.order = None

    def check_qty(self):
        while self.qty / self.klines['close'] <= float(self.instruments['minSz']):
            self.qty += 1

    def array_grid(self, a, val):
        return round(min([x for x in a if x > val] or [None]), 9)

    def get_grid_position(self):
        x = self.min
        while x <= self.max:
            x += (x * self.percent / 100)
            self.grid.append(x)

    def is_position(self):
        _ord = (db.query(Orders).filter(Orders.profit <= self.klines['close'], Orders.symbol == self.symbol, Orders.is_active == True)
                .order_by(Orders.profit).first())
        if _ord:
            return _ord
        _ord = (db.query(Orders).filter(Orders.grid_px == self.grid_px, Orders.symbol == self.symbol, Orders.is_active == True)
                .order_by(Orders.grid_px).first())
        if _ord:
            return None
        else:
            return False

    def save_order(self, order, active=True):
        _ord = Orders(
            sz=order.get('sz'),
            px=order.get('avgPx'),
            grid_px=self.grid_px,
            profit=order.get('profit'),
            fee=order.get('fee'),
            side=order.get('side'),
            is_active=active,
            symbol=order.get('instId'),
            tag=order.get('tag'),
            ordId=order.get('ordId'),
            tdMode=order.get('tdMode')
        )
        db.add(_ord)
        db.commit()
        return _ord

    async def run(self):
        self.logger.debug(f"{os.getenv("BOT_NAME")} is start...")
        await asyncio.gather(self.private(), self.public(), self.business())
        while True:
            self.check()
            await asyncio.sleep(1)
