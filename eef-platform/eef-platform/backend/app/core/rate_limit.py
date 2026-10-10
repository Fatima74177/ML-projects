"""Small fixed-window API rate limiter with a local fallback."""
from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from threading import Lock

from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RequestRateLimiter:
    _INCREMENT_SCRIPT = """
    local count = redis.call('INCR', KEYS[1])
    if count == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    return count
    """

    def __init__(self, max_local_clients: int = 10_000) -> None:
        self._max_local_clients = max_local_clients
        self._local_counts: OrderedDict[str, tuple[int, int]] = OrderedDict()
        self._lock = Lock()
        self._redis_client: Redis | None = None
        self._redis_retry_after = 0.0

    def is_limited(
        self,
        client_id: str,
        limit: int,
        redis_enabled: bool = False,
        redis_url: str = "",
    ) -> bool:
        now = time.time()
        window = int(now // 60)
        client_key = hashlib.sha256(client_id.encode("utf-8")).hexdigest()
        redis_key = f"eef:rate-limit:{client_key}:{window}"

        if redis_enabled:
            count = self._redis_count(redis_key, redis_url)
            if count is not None:
                return count > limit

        with self._lock:
            previous_window, count = self._local_counts.get(client_key, (window, 0))
            if previous_window != window:
                count = 0
            count += 1
            self._local_counts[client_key] = (window, count)
            self._local_counts.move_to_end(client_key)
            while len(self._local_counts) > self._max_local_clients:
                self._local_counts.popitem(last=False)
        return count > limit

    def _redis_count(self, key: str, redis_url: str) -> int | None:
        if time.monotonic() < self._redis_retry_after:
            return None

        try:
            with self._lock:
                if self._redis_client is None:
                    self._redis_client = Redis.from_url(
                        redis_url,
                        socket_connect_timeout=0.25,
                        socket_timeout=0.25,
                    )
                client = self._redis_client
            return int(client.eval(self._INCREMENT_SCRIPT, 1, key, 65))
        except RedisError as exc:
            logger.warning("Redis rate limiter unavailable; using local fallback: %s", exc)
            with self._lock:
                self._redis_client = None
                self._redis_retry_after = time.monotonic() + 5
            return None