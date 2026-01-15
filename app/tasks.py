from app.celery_app import celery_app
from app.logger import logger

@celery_app.task
def send_fraud_alert(transaction_id: str, score: float):
    logger.warning(f"[ALERT] HIGH RISK FRAUD -> TXN:{transaction_id} SCORE:{score}")
    return "alert_sent"
