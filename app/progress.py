import json
from redis import Redis

redis = Redis(host="redis", port=6379, decode_responses=True)


def update_progress(
    job_id: str,
    *,
    status: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    done_files: int | None = None,
    result_index: list | None = None,
):
    key = f"job:{job_id}"
    data = {}

    if status is not None:
        data["status"] = status
    if progress is not None:
        data["progress"] = str(progress)
    if message is not None:
        data["message"] = message
    if done_files is not None:
        data["done_files"] = str(done_files)
    if result_index is not None:
        data["result_index"] = json.dumps(result_index)

    if data:
        redis.hset(key, mapping=data)


def get_progress(job_id: str) -> dict:
    return redis.hgetall(f"job:{job_id}")
