import time

from tenacity import retry, stop_after_attempt, wait_fixed

from src.wiser_client import WiserClient
from src.models import WiserState

# cache wiser state for 1 minute
CACHE_DURATION_SEC = 60


# High level client that handles all wiser related functions
class CachedWiserClient:

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

    # remember there is an exponential backoff too on the api requests
    @retry(wait=wait_fixed(wait=3), stop=stop_after_attempt(3))
    async def boost_heating(self, room_id: int, temperature: float, duration_minutes: int):
        await self.wiser_client.boost_heating(room_id, temperature, duration_minutes)
        info = await self.get(ignore_cache=True)
        room = [room for room in info.rooms if room.id == room_id][0]
        if not (0 <= abs(room.setpoint_temperature - temperature) <= 0.1):
            # just raise error so we can use retry annotation
            raise Exception("Setpoint does not yet match")

    @retry(wait=wait_fixed(wait=3), stop=stop_after_attempt(3))
    async def cancel_heating_boost(self, room_id):
        await self.wiser_client.cancel_heating_boost(room_id)

    @retry(wait=wait_fixed(wait=3), stop=stop_after_attempt(3))
    async def boost_hot_water(self, channel_id: int, duration_minutes: int) -> None:
        await self.wiser_client.boost_hot_water(channel_id, duration_minutes)

    @retry(wait=wait_fixed(wait=3), stop=stop_after_attempt(3))
    async def cancel_hot_water(self, channel_id: int) -> None:
        await self.wiser_client.cancel_hot_water_boost(channel_id)

