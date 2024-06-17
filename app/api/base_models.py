from datetime import datetime

from pydantic import BaseModel, validator


class UserCreate(BaseModel):
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    balance: str

    class Config:
        orm_mode = True
        from_attributes = True


class TransactionCreate(BaseModel):
    uid: str
    type: str
    amount: float
    user_id: int
    timestamp: str

    @validator("type")
    def validate_type(cls, value):
        if value not in ["DEPOSIT", "WITHDRAW"]:
            raise ValueError("Invalid transaction type")
        return value

    @validator("timestamp")
    def validate_timestamp(cls, value):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("Invalid timestamp format")


class TransactionResponse(BaseModel):
    uid: str
    type: str
    amount: str
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True
