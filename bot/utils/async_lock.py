import asyncio
import fasteners


class AsyncInterProcessLock:
    def __init__(self, path):
        self.lock = fasteners.InterProcessLock(path)

    async def __aenter__(self):
        await asyncio.to_thread(self.lock.acquire)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.to_thread(self.lock.release)
