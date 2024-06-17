from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette import status

from app.models import models
from app.startups.database import get_async_db
from app.api.base_models import UserCreate, UserResponse

router = APIRouter()


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    async with db.begin():
        result = await db.execute(
            select(models.User).filter(models.User.name == user.name)
        )
        db_user = result.scalar_one_or_none()
        if db_user:
            return UserResponse(
                id=db_user.id, name=db_user.name, balance=f"{db_user.balance:.2f}"
            )

        new_user = models.User(name=user.name)
        db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id, name=new_user.name, balance=f"{new_user.balance:.2f}"
    )


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_async_db), date: datetime = Query(None)
):
    async with db.begin():
        result = await db.execute(select(models.User).filter(models.User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if date:
            balance = await get_balance_on_date(user_id, date, db)
        else:
            balance = user.balance

        return UserResponse(id=user.id, name=user.name, balance=f"{balance:.2f}")


async def get_balance_on_date(user_id: int, date: datetime, db: AsyncSession):
    result = await db.execute(
        select(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .filter(models.Transaction.timestamp <= date)
    )
    transactions = result.scalars().all()

    balance = 0.0
    for txn in transactions:
        if txn.type == "DEPOSIT":
            balance += txn.amount
        elif txn.type == "WITHDRAW":
            balance -= txn.amount

    return balance
