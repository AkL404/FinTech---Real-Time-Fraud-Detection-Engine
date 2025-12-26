import time
from fastapi import FastAPI
from sqlalchemy import select

from app.schemas import TransactionSchema
from app.database import AsyncSessionLocal, engine
from app.models import FactTransaction, DimUser, Base
from app.redis_client import redis_client

app = FastAPI(title="SentinelStream – Week 2")


# --- OPTIONAL: auto create tables (only if needed) ---
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -------------------------------
# DIM USER HELPER
# -------------------------------
async def get_or_create_user(session, user_code: str):
    result = await session.execute(
        select(DimUser).where(DimUser.user_code == user_code)
    )
    user = result.scalar_one_or_none()

    if user:
        return user.user_id

    new_user = DimUser(user_code=user_code)
    session.add(new_user)
    await session.flush()       # populate PK in DB

    return new_user.user_id


# -------------------------------
# MAIN ENDPOINT
# -------------------------------
@app.post("/transaction")
async def process_transaction(txn: TransactionSchema):
    start_time = time.time()

    # Redis cache check
    cache_key = f"user:{txn.user_id}"
    cached_user = redis_client.get(cache_key)

    if not cached_user:
        redis_client.setex(cache_key, 300, "cached")

    async with AsyncSessionLocal() as session:

        
        user_dim_id = await get_or_create_user(session, txn.user_id)

        transaction = FactTransaction(
            transaction_id=txn.transaction_id,
            user_id=user_dim_id,         
            amount=txn.amount,
            fraud_score=0,
            final_decision="ACCEPTED"
        )

        session.add(transaction)
        await session.flush()
        await session.commit()

    latency = int((time.time() - start_time) * 1000)

    return {
        "status": "ACCEPTED",
        "transaction_id": txn.transaction_id,
        "latency_ms": latency
    }
