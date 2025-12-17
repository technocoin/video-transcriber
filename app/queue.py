import os
from redis import Redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def get_redis() -> Redis:
    return Redis.from_url(REDIS_URL)

def get_queue(name: str = "jobs") -> Queue:
    return Queue(name, connection=get_redis())
