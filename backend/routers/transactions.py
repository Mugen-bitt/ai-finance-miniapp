from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from database import get_db
from models import Transaction, User, TransactionType
from schemas import (
    TransactionCreate, Transaction as TransactionSchema,
    MonthlyReport, CategorySummary
)
from auth import get_current_user_dev

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionSchema)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dev)
):
    """Создать новую транзакцию."""
    db_transaction = Transaction(
        user_id=current_user.id,
        type=transaction.type,
        amount=transaction.amount,
        currency=transaction.currency,
        category=transaction.category,
        description=transaction.description,
        transaction_date=transaction.transaction_date or date.today()
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.get("/", response_model=List[TransactionSchema])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dev)
):
    """Получить список транзакций с фильтрами."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if type:
        query = query.filter(Transaction.type == type)
    if category:
        query = query.filter(Transaction.category == category)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    return query.order_by(Transaction.transaction_date.desc()).offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=TransactionSchema)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dev)
):
    """Получить транзакцию по ID."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dev)
):
    """Удалить транзакцию."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted"}


@router.get("/report/monthly", response_model=MonthlyReport)
async def get_monthly_report(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dev)
):
    """Получить месячный отчёт."""
    # Фильтр по месяцу и году
    base_query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        extract('year', Transaction.transaction_date) == year,
        extract('month', Transaction.transaction_date) == month
    )

    # Общий доход
    total_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.income,
        extract('year', Transaction.transaction_date) == year,
        extract('month', Transaction.transaction_date) == month
    ).scalar()

    # Общий расход
    total_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.expense,
        extract('year', Transaction.transaction_date) == year,
        extract('month', Transaction.transaction_date) == month
    ).scalar()

    # Расходы по категориям
    expenses_by_cat = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.expense,
        extract('year', Transaction.transaction_date) == year,
        extract('month', Transaction.transaction_date) == month
    ).group_by(Transaction.category).all()

    # Доходы по категориям
    income_by_cat = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.income,
        extract('year', Transaction.transaction_date) == year,
        extract('month', Transaction.transaction_date) == month
    ).group_by(Transaction.category).all()

    return MonthlyReport(
        month=f"{year}-{month:02d}",
        total_income=float(total_income),
        total_expense=float(total_expense),
        savings=float(total_income) - float(total_expense),
        expenses_by_category=[
            CategorySummary(category=cat, total=float(total), count=count)
            for cat, total, count in expenses_by_cat
        ],
        income_by_category=[
            CategorySummary(category=cat, total=float(total), count=count)
            for cat, total, count in income_by_cat
        ]
    )


@router.get("/categories/list")
async def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dev)
):
    """Получить список использованных категорий."""
    categories = db.query(Transaction.category).filter(
        Transaction.user_id == current_user.id
    ).distinct().all()

    return [cat[0] for cat in categories]
