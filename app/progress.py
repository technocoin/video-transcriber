import json
import os
from redis import Redis

# Redis connection (Docker-safe)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


def update_progress(
    job_id: str,
    *,
    status: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    done_files: int | None = None,
    total_files: int | None = None,
    result_index: list | None = None,
):
    """
    Update one or more fields of a job progress hash.
    Only provided fields are updated.
    """
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
    if total_files is not None:
        data["total_files"] = str(total_files)
    if result_index is not None:
        data["result_index"] = json.dumps(result_index)

    if data:
        redis.hset(key, mapping=data)


def get_progress(job_id: str) -> dict:
    """
    Fetch all progress fields for a job.
    Returns an empty dict if job does not exist.
    """
    return redis.hgetall(f"job:{job_id}")
