import redis
from app.config import REDIS_HOST, REDIS_PORT




redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    socket_timeout=0.1,     
    socket_connect_timeout=0.3
)
