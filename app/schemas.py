from pydantic import BaseModel

class TransactionSchema(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant: str
    location: str
