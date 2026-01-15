from celery import Celery

# celery_app = Celery(
#     "sentinelstream",
#     broker="redis://localhost:6379/0",
#     backend="redis://localhost:6379/0"
# )

from app.config import REDIS_HOST, REDIS_PORT

celery_app = Celery(
    "sentinelstream",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)


celery_app.conf.task_routes = {
    "app.tasks.send_fraud_alert": {"queue": "alerts"}
}

@celery_app.task(name="app.tasks.send_fraud_alert")
def send_fraud_alert(transaction_id: str, score: float):
    print("\n🚨 FRAUD ALERT TRIGGERED 🚨")
    print(f"Transaction: {transaction_id}")
    print(f"Fraud score: {score}")
    print("---------------------------------\n")
