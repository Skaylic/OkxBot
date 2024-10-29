from typing import Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Table


class Base(DeclarativeBase):

    __table__: Table  # def for mypy

    @declared_attr
    def __tablename__(cls):  # pylint: disable=no-self-argument
        return cls.__name__  # pylint: disable= no-member

    def to_dict(self) -> Dict[str, Any]:
        """Serializes only column data."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Instruments(Base):
    __tablename__ = 'instruments'
    id = Column(Integer, primary_key=True)
    instId = Column(String, unique=True)
    instType = Column(String)
    minSz = Column(Float)
    lotSz = Column(Float)
    baseCcy = Column(String)
    quoteCcy = Column(String)
    state = Column(String)

    def __repr__(self) -> str:
        return f"instId: {self.instId!r} MinSz: {self.minSz!r} State: {self.state!r}"


class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    ordId = Column(Integer)
    cTime = Column(String)
    sz = Column(Float)
    px = Column(Float)
    profit = Column(Float, default=0.0)
    side = Column(String)
    is_active = Column(Boolean, default=True)
    tag = Column(String)
    state = Column(String)
    grid_px = Column(Float, default=0.0)
    fee = Column(Float)
    feeCcy = Column(String)
    instType = Column(String)
    instId = Column(String)
    tgtCcy = Column(String)

    def __repr__(self) -> str:
        return f"Side: {self.side!r} Px: {self.px!r} Sz: {self.sz!r} Active: {self.is_active!r}"
