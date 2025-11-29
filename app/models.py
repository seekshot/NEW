import datetime as dt

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .db import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False, default="MOCK")
    institution = Column(String, nullable=False)
    last_sync = Column(DateTime, nullable=True)

    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False)
    merchant = Column(Text, nullable=False)
    raw_category = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    bucket = Column(Text, nullable=True)
    source_system = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    account = relationship("Account", back_populates="transactions")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(Text, nullable=False)
    field = Column(String, nullable=False)
    category = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    bucket = Column(String, nullable=False)
    monthly_limit = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False)
    alert_threshold = Column(Float, default=0.8, nullable=False)
