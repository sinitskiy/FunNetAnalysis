'''
A context manager that waits for a given interval between operations.
'''

from time import monotonic
import asyncio
from contextlib import asynccontextmanager


class Waiter():
    '''
    A context manager that waits for a given interval between operations.
    '''
    interval: float

    lock: asyncio.Lock
    last_execution_time: float

    def __init__(self, interval: float = 0.5):
        self.interval = interval

        self.lock = asyncio.Lock()
        self.last_execution_time = 0

    @asynccontextmanager
    async def when_ready(self):
        '''
        Wait until the interval has passed since the last operation.
        '''

        await self.lock.acquire()
        try:
            now = monotonic()
            earliest = self.last_execution_time + self.interval
            if now < earliest:
                await asyncio.sleep(earliest - now)

            yield None
        finally:
            self.last_execution_time = monotonic()
            self.lock.release()
