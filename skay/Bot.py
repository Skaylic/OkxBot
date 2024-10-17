import os
import asyncio
from time import strftime
import logging
from skay.Okx import Okx
from skay.Database import Database
from skay.Models import Orders

logger = logging.getLogger('SkayBot')
db = Database().set_db()


class Bot(Okx):

    def __init__(self):
        super().__init__()
        self.min = float(os.getenv('MIN'))
        self.max = float(os.getenv('MAX'))
        self.percent = float(os.getenv('PERCENT'))
        self.grid = []
        self.grid_px = 0.0
        self.a = 0
        self.y = 0
        self.order = None

    async def check(self):
        self.get_grid_position()
        while True:
            if self.mark_px:
                self.grid_px = round(self.array_grid(self.grid, self.mark_px), 9)
                pos = self.is_position()
                if (self.mark_price_candle and self.mark_price_candle[1] < self.mark_price_candle[4]
                        and self.a == 0):
                    self.y = self.grid_px
                    self.a = 1
                elif (self.mark_price_candle and self.mark_price_candle[1] > self.mark_price_candle[4]
                      and self.a == 1):
                    self.a = 0
                if pos and self.bal_quote_ccy > pos.sz and self.order is None:
                    await self.send_ticker(side='sell', sz=pos.sz + pos.fee)
                elif pos and self.bal_quote_ccy < pos.sz and self.order is None:
                    await self.send_ticker(side='buy', tag='completed')
                elif (pos is False and self.a == 1 and self.mark_px >= self.y
                      and self.bal_base_ccy > self.qty and self.order is None):
                    await self.send_ticker(side='buy')
                if pos and self.order and self.order['state'] == 'filled' and self.order['side'] == 'sell':
                    summ = ((float(self.order.get('avgPx')) * float(self.order.get('sz')) + float(
                        self.order.get('fee')))
                            - (float(pos.sz) * float(pos.px)) + (float(pos.fee) * float(pos.px)))
                    self.order.update({'profit': summ})
                    _ord = self.save_order(self.order, False)
                    pos.cTime = strftime('%Y%m%d%H%M%S')
                    pos.is_active = False
                    db.commit()
                    logger.info(_ord)
                    self.order = None
                elif (self.order and self.order['state'] == 'filled'
                        and self.order['side'] == 'buy' and self.order['tag'] == 'completed'):
                    self.order['profit'] = 0.0
                    _ord = self.save_order(self.order, False)
                    logger.info(_ord)
                    self.order = None
                elif (self.order and self.order['state'] == 'filled'
                      and self.order['side'] == 'buy' and self.order['tag'] == 'bot'):
                    self.order['profit'] = 0.0
                    _ord = self.save_order(self.order, True)
                    logger.info(_ord)
                    self.order = None
            await asyncio.sleep(1)

    def save_order(self, order, active=True):
        _ord = Orders(
            instType=order.get('instType'),
            sz=order.get('sz'),
            px=order.get('avgPx'),
            grid_px=self.grid_px,
            fee=order.get('fee'),
            profit=order.get('profit'),
            side=order.get('side'),
            feeCcy=order.get('feeCcy'),
            instId=order.get('instId'),
            tgtCcy=order.get('tgtCcy'),
            ordId=order.get('ordId'),
            state=order.get('state'),
            cTime=strftime('%Y%m%d%H%M%S'),
            tag=order.get('tag'),
            is_active=active
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
        mrx = float(self.mark_px - (self.mark_px * self.percent / 100))
        _ord = (db.query(Orders).filter(Orders.side == 'buy', Orders.px < mrx, Orders.is_active == True)
                .order_by(Orders.px).first())
        if _ord:
            return _ord
        _ord = db.query(Orders).filter(Orders.side == 'buy', Orders.grid_px == self.grid_px,
                                       Orders.is_active == True).first()
        if _ord:
            return None
        else:
            return False

    async def run(self):
        logger.info('Started ' + strftime('%Y-%m-%d %H:%M:%S'))
        await asyncio.gather(self.check(), self.ws_private(), self.ws_public(), self.ws_business())
