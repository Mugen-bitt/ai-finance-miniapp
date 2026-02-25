from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


# ============== User Schemas ==============

class UserBase(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Transaction Schemas ==============

class TransactionBase(BaseModel):
    type: TransactionType
    amount: float = Field(..., gt=0)
    currency: str = Field(default="RUB", max_length=3)
    category: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    transaction_date: Optional[date] = None


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Budget Schemas ==============

class BudgetBase(BaseModel):
    category: str = Field(..., max_length=50)
    monthly_limit: float = Field(..., gt=0)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(..., gt=0)


class Budget(BudgetBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Goal Schemas ==============

class GoalBase(BaseModel):
    goal_name: str = Field(..., max_length=100)
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0.0, ge=0)
    deadline: Optional[date] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    current_amount: Optional[float] = Field(None, ge=0)
    target_amount: Optional[float] = Field(None, gt=0)
    deadline: Optional[date] = None


class Goal(GoalBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Report Schemas ==============

class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class MonthlyReport(BaseModel):
    month: str
    total_income: float
    total_expense: float
    savings: float
    expenses_by_category: List[CategorySummary]
    income_by_category: List[CategorySummary]


# ============== Voice Input Schema ==============

class VoiceTransactionParsed(BaseModel):
    """Схема для ответа от LLM после парсинга голоса."""
    type: TransactionType
    amount: float
    currency: str = "RUB"
    category: str
    description: Optional[str] = None
    date: Optional[date] = None
