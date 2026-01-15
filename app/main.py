import time
from fastapi import FastAPI
from sqlalchemy import select

from app.schemas import TransactionSchema
from app.database import AsyncSessionLocal, engine
from app.models import FactTransaction, DimUser, Base
from app.redis_client import redis_client
from app.rules import apply_rules
from app.ml_model import ml_score
from app.logger import logger
from app.explain import explain_reason
from app.tasks import send_fraud_alert
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import decode_token


from app.auth import create_access_token, verify_password
from app.models import AppUser




app = FastAPI(title="SentinelStream ")



@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def get_or_create_user(session, user_code: str):
    result = await session.execute(
        select(DimUser).where(DimUser.user_code == user_code)
    )
    user = result.scalar_one_or_none()

    if user:
        return user.user_id

    new_user = DimUser(user_code=user_code)
    session.add(new_user)
    await session.flush()      

    return new_user.user_id





@app.post("/transaction")


async def process_transaction(txn: TransactionSchema, user=Depends(decode_token)):
    start_time = time.time()
    
    logger.info(f"TXN {txn.transaction_id} processed")

    cache_key = f"user:{txn.user_id}"
    cached_user = redis_client.get(cache_key)

    if not cached_user:
        redis_client.setex(cache_key, 300, "cached")

    async with AsyncSessionLocal() as session:

        user_dim_id = await get_or_create_user(session, txn.user_id)

        # --- apply rules + ml ---
        decision, rule_name, rule_risk = apply_rules(txn.amount, txn.location)
        model_score = ml_score(txn.amount)

        final_score = rule_risk + model_score
        
        if txn.amount < 1000:
             final_decision = "ACCEPTED"

        elif final_score >= 90:
            final_decision = "REJECTED"
        elif final_score >= 60:
            final_decision = "REVIEW"
        else:
            final_decision = decision
            
        if final_decision == "REJECTED" or final_score >= 80:
            send_fraud_alert.delay(txn.transaction_id, float(final_score))
            
        latency = int((time.time() - start_time) * 1000)

        transaction = FactTransaction(
            transaction_id=txn.transaction_id,
            user_id=user_dim_id,
            amount=txn.amount,
            fraud_score=final_score,
            final_decision=final_decision,
            latency_ms=latency
        )

        db_start = time.time()
        
        session.add(transaction)
        await session.flush()
        await session.commit()
        
        db_latency = int((time.time() - db_start) * 1000)
        logger.info(f"DB Time: {db_latency} ms")

    reasons = explain_reason(txn.amount, rule_name, final_score)

    return {
        "decision": final_decision,
        "fraud_score": final_score,
        "latency_ms": latency,
        "reasons": reasons
    }


@app.get("/fraud/high-risk")
async def get_high_risk():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FactTransaction).where(FactTransaction.fraud_score >= 60)
        )

        rows = result.scalars().all()

        return [
            {"transaction_id": r.transaction_id, "fraud_score": float(r.fraud_score)}
            for r in rows
        ]


from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"ERROR: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.get("/health")
def health():
    return {"status": "OK"}




@app.get("/fraud/rejected")
async def get_rejected():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FactTransaction).where(FactTransaction.final_decision == "REJECTED")
        )

        rows = result.scalars().all()

        return [
            {
                "transaction_id": r.transaction_id,
                "fraud_score": float(r.fraud_score),
                "decision": r.final_decision
            }
            for r in rows
        ]


@app.get("/latency/slow")
async def slow_transactions():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FactTransaction).where(FactTransaction.latency_ms > 400)
        )

        rows = result.scalars().all()

        return [
            {
                "transaction_id": r.transaction_id,
                "latency_ms": r.latency_ms
            }
            for r in rows
        ]


from sqlalchemy import func

@app.get("/metrics/overview")
async def metrics_overview():
    async with AsyncSessionLocal() as session:
        total = await session.execute(
            select(func.count(FactTransaction.transaction_id))
        )

        rejected = await session.execute(
            select(func.count(FactTransaction.transaction_id))
            .where(FactTransaction.final_decision == "REJECTED")
        )

        review = await session.execute(
            select(func.count(FactTransaction.transaction_id))
            .where(FactTransaction.final_decision == "REVIEW")
        )

        avg_latency = await session.execute(
            select(func.avg(FactTransaction.latency_ms))
        )

        return {
            "total_transactions": total.scalar(),
            "rejected": rejected.scalar(),
            "review": review.scalar(),
            "average_latency_ms": round(avg_latency.scalar() or 0, 2)
        }


@app.get("/analytics/top-users")
async def top_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                FactTransaction.user_id,
                func.count(FactTransaction.transaction_id).label("tx_count")
            ).group_by(FactTransaction.user_id)
             .order_by(func.count(FactTransaction.transaction_id).desc())
             .limit(5)
        )

        return [
            {"user_id": r[0], "transactions": r[1]}
            for r in result.all()
        ]


from typing import List
from fastapi import Body

@app.post("/transactions/bulk")
async def bulk_insert(txns: List[TransactionSchema] = Body(...)):
    async with AsyncSessionLocal() as session:
        results = []

        for txn in txns:

            # check if transaction already exists
            existing = await session.get(FactTransaction, txn.transaction_id)

            if existing:
                results.append(
                    {"transaction_id": txn.transaction_id, "status": "SKIPPED_DUPLICATE"}
                )
                continue

            transaction = FactTransaction(
                transaction_id=txn.transaction_id,
                user_id=1,
                amount=txn.amount,
                fraud_score=0,
                final_decision="ACCEPTED",
                latency_ms=0
            )

            session.add(transaction)
            results.append(
                {"transaction_id": txn.transaction_id, "status": "INSERTED"}
            )

        await session.commit()

        return {"results": results}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Log full details to file / console
    logger.error(f"UNHANDLED ERROR -> {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "note": "Something went wrong, our team is checking it."
        },
    )


from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"ERROR: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )



# @app.post("/login")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     async with AsyncSessionLocal() as session:
#         result = await session.execute(
#             select(AppUser).where(AppUser.username == form_data.username)
#         )

#         user = result.scalar_one_or_none()

#         # if not user or not verify_password(form_data.password, user.password):
#         #     raise HTTPException(status_code=401, detail="Invalid credentials")


#         if not user or user.password != form_data.password:
#             raise HTTPException(status_code=401, detail="Invalid credentials")
        
#         token = create_access_token({"sub": user.username}) 

#         return {"access_token": token, "token_type": "bearer"}



@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AppUser).where(AppUser.username == form_data.username)
        )

        user = result.scalar_one_or_none()

        # NO HASH CHECK — plain text
        if not user or form_data.password != user.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        

        token = create_access_token({"sub": user.username})

        return {"access_token": token, "token_type": "bearer"}
