from typing import Dict, Any
from sqlalchemy import String, Integer, Float, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
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


class Orders(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    ordId: Mapped[int] = mapped_column(Integer)
    cTime: Mapped[str] = mapped_column(String(30))
    sz: Mapped[int] = mapped_column(Float)
    px: Mapped[float] = mapped_column(Float)
    grid_px: Mapped[float] = mapped_column(Float)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    fee: Mapped[float] = mapped_column(Float)
    feeCcy: Mapped[str] = mapped_column(String(30))
    side: Mapped[str] = mapped_column(String(30))
    state: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    instType: Mapped[int] = mapped_column(String(30), default='')
    instId: Mapped[int] = mapped_column(String(30), default='')
    tgtCcy: Mapped[int] = mapped_column(String(30), default='')
    tag: Mapped[str] = mapped_column(String(30), default='')

    def __repr__(self) -> str:
        return f"Side: {self.side!r} Px: {self.px!r} Sz: {self.sz!r} Active: {self.is_active!r}"
