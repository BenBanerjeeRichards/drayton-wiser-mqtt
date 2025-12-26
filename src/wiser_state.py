import time

from src.wiser_client import WiserClient
from src.models import WiserState

# cache wiser state for 1 minute
CACHE_DURATION_SEC = 60

class WiserStateApi:

    def __init__(self, wiser_client: WiserClient):
        self.wiser_client = wiser_client
        self.cached_state: WiserState | None = None
        self.cache_expires_at = time.time() - 100


    async def get(self, ignore_cache=False) -> WiserState:
        if not ignore_cache and self.cached_state and time.time() < self.cache_expires_at:
            return self.cached_state
        state = await self.wiser_client.get_state()
        self.cached_state = state
        self.cache_expires_at = time.time() + CACHE_DURATION_SEC
        return state
