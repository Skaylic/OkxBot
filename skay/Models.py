from typing import Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, Table
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr


class Base(DeclarativeBase):

    __table__: Table  # def for mypy

    @declared_attr
    def __tablename__(cls):  # pylint: disable=no-self-argument
        return cls.__name__  # pylint: disable= no-member

    def to_dict(self) -> Dict[str, Any]:
        """Serializes only column data."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    sz = Column(Float, default=0.0)
    px = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)
    grid_px = Column(Float, default=0.0)
    fee = Column(Float, default=0.0)
    side = Column(String)
    is_active = Column(Boolean, default=True)
    symbol = Column(String)
    tag = Column(String)
    ordId = Column(Integer)
    tdMode = Column(String)

    def __repr__(self) -> str:
        return f"Side: {self.side!r} Id: {self.ordId!r} Px: {self.px!r} Sz: {self.sz!r} Active: {self.is_active!r}"

class Profit(Base):
    __tablename__ = "profit"
    id = Column(Integer, primary_key=True)
    cTime = Column(Integer, default=0)
    ord_buy = Column(Float, default=0.0)
    usdt_bal = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"Total: {self.total!r}"
