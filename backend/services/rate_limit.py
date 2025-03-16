# services/rate_limit.py

import json
import logging
import time

from db.redis_client import add_key_value_redis, get_value_redis

logger = logging.getLogger("RateLimit")

RATE_LIMIT_WINDOW = 3600
RATE_LIMIT_MAX_REQUESTS = 100


async def is_rate_limited(user_id: str) -> bool:
    current_time = int(time.time())
    rate_limit_key = f"hubspot_rate_limit:{user_id}"

    rate_limit_data = await get_value_redis(rate_limit_key)

    if rate_limit_data:
        rate_limit_data = json.loads(rate_limit_data)
        request_count = rate_limit_data["count"]
        last_request_time = rate_limit_data["timestamp"]

        if current_time - last_request_time > RATE_LIMIT_WINDOW:
            request_count = 0

        if request_count >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for user_id={user_id}")
            return True

        await add_key_value_redis(
            rate_limit_key,
            json.dumps({"count": request_count + 1,
                        "timestamp": current_time}),
            expire=RATE_LIMIT_WINDOW,
        )
    else:
        await add_key_value_redis(
            rate_limit_key,
            json.dumps({"count": 1, "timestamp": current_time}),
            expire=RATE_LIMIT_WINDOW
        )

    return False
