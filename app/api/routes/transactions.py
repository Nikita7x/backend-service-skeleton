from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import models
from app.startups.database import get_async_db
from app.api.base_models import TransactionCreate, TransactionResponse

router = APIRouter()


@router.post("/transaction", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate, db: AsyncSession = Depends(get_async_db)
):
    async with db.begin():
        result = await db.execute(
            select(models.Transaction).filter(models.Transaction.uid == transaction.uid)
        )
        existing_transaction = result.scalar_one_or_none()
        if existing_transaction:
            return TransactionResponse(
                uid=existing_transaction.uid,
                type=existing_transaction.type,
                amount=f"{existing_transaction.amount:.2f}",
                user_id=existing_transaction.user_id,
                timestamp=existing_transaction.timestamp,
            )

        result = await db.execute(
            select(models.User).filter(models.User.id == transaction.user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if transaction.type == "WITHDRAW" and user.balance < transaction.amount:
            raise HTTPException(status_code=402, detail="Insufficient funds")

        new_transaction = models.Transaction(
            uid=transaction.uid,
            user_id=transaction.user_id,
            type=transaction.type,
            amount=transaction.amount,
            timestamp=transaction.timestamp,
        )
        if transaction.type == "DEPOSIT":
            user.balance += transaction.amount
        else:
            if user.balance < transaction.amount:
                raise HTTPException(status_code=400, detail="Insufficient balance")
            user.balance -= transaction.amount
        db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    return TransactionResponse(
        uid=new_transaction.uid,
        type=new_transaction.type,
        amount=f"{new_transaction.amount:.2f}",
        user_id=new_transaction.user_id,
        timestamp=new_transaction.timestamp,
    )


@router.get("/transaction/{uid}", response_model=TransactionResponse)
async def get_transaction(uid: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(models.Transaction).filter(models.Transaction.uid == uid)
    )
    transaction = result.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse(
        uid=transaction.uid,
        type=transaction.type,
        amount=f"{transaction.amount:.2f}",
        user_id=transaction.user_id,
        timestamp=transaction.timestamp,
    )
