import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    name: str
    provider: str = "MOCK"
    institution: str
    last_sync: Optional[dt.datetime] = None


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int

    class Config:
        orm_mode = True


class TransactionRead(BaseModel):
    id: str
    account_id: int
    date: dt.date
    amount: float
    currency: str
    merchant: str
    raw_category: Optional[str]
    category: Optional[str]
    bucket: Optional[str]
    source_system: str
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        orm_mode = True


class RuleBase(BaseModel):
    pattern: str
    field: str
    category: str
    bucket: str
    priority: int = 0
    enabled: bool = True


class RuleCreate(RuleBase):
    pass


class RuleRead(RuleBase):
    id: int

    class Config:
        orm_mode = True


class BudgetBase(BaseModel):
    bucket: str
    monthly_limit: float
    currency: str
    alert_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class BudgetCreate(BudgetBase):
    pass


class BudgetRead(BudgetBase):
    id: int

    class Config:
        orm_mode = True


class IngestRunRequest(BaseModel):
    account_ids: List[int]
    since: Optional[dt.datetime] = None


class IngestMockRequest(BaseModel):
    account_id: int


class ApplyRulesRequest(BaseModel):
    account_id: Optional[int] = None


class NotionSyncRequest(BaseModel):
    account_id: Optional[int] = None
    date_from: Optional[dt.date] = Field(default=None, alias="from")
    date_to: Optional[dt.date] = Field(default=None, alias="to")

    class Config:
        allow_population_by_field_name = True


class MonthlyReportItem(BaseModel):
    bucket: str
    total_spend: float
    limit: Optional[float]
    utilization: Optional[float]
    over_budget: bool
