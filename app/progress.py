import json
from redis import Redis

redis = Redis(host="redis", port=6379, decode_responses=True)

def update_progress(job_id, **kwargs):
    data = {}
    for k, v in kwargs.items():
        if v is not None:
            data[k] = json.dumps(v) if k == "result_index" else str(v)
    if data:
        redis.hset(f"job:{job_id}", mapping=data)

def get_progress(job_id):
    return redis.hgetall(f"job:{job_id}")
