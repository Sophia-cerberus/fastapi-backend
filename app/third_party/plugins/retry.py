from typing import Callable, Awaitable
import asyncio


class RetryPlugin:
    def __init__(self, max_retries: int, retry_interval):
        self.max_retries = max_retries
        self.retry_interval = retry_interval

    async def execute(self, func: Callable[..., Awaitable], *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_interval)
        raise last_exception 