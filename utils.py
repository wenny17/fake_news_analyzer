from contextlib import asynccontextmanager
import time
from async_timeout import timeout as async_timeout

import aionursery


@asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0] from None
        raise


@asynccontextmanager
async def timing_manager(timeout=None):
    t0 = time.monotonic()
    async with async_timeout(timeout) as cm:
        try:
            yield
        finally:
            if cm.expired:
                print(f'Terminated by timeout: {timeout}')
            else:
                time_taken = time.monotonic() - t0
                print('Анализ закончен за {} сек'.format(time_taken))
