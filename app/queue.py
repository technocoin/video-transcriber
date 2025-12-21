from redis import Redis
from rq import Queue

def get_redis():
    return Redis(host="redis", port=6379, decode_responses=True)

def get_queue():
    return Queue("jobs", connection=get_redis())
