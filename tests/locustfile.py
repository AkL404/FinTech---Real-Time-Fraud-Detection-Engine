# from locust import HttpUser, task, between
# import uuid

# class TransactionUser(HttpUser):
#     wait_time = between(0.01, 0.05)

#     @task
#     def send_transaction(self):
#         self.client.post("/transaction", json={
#             "transaction_id": str(uuid.uuid4()),
#             "user_id": "user_123",
#             "amount": 1200,
#             "currency": "INR",
#             "merchant": "Amazon",
#             "location": "Kochi"
#         })


from locust import HttpUser, task, between
import uuid
import random

class TransactionUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def send_transaction(self):
        amount = random.choice([200, 500, 1200, 8000, 12000])
        location = random.choice(["USA", "India", "Nigeria", "Russia", "UK"])

        self.client.post(
            "/transaction",
            json={
                "transaction_id": str(uuid.uuid4()),
                "user_id": "user_123",
                "amount": amount,
                "currency": "USD",
                "merchant": "Amazon",
                "location": location
            }
        )
