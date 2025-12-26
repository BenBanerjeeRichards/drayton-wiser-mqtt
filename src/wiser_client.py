from typing import Literal

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt

from src.models import WiserRoot, WiserState, RoomStatState, RoomState, HeatingChannelState, \
    HotWaterChannelState, SetpointOrigin, ControlSource


class WiserClient:

    def __init__(self, ip: str, secret: str) -> None:
        self.api = WiserApi(ip, secret)

    async def get_state(self) -> WiserState:
        # Summarise the info from the wiser domain endpoint
        info = await self.api.get_info()
        # TODO: currently manual and boost treated the same
        map_control_source: dict[str, ControlSource] = {
            SetpointOrigin.BOOST: "Boost",
            SetpointOrigin.SCHEDULE: "Schedule",
            SetpointOrigin.AWAY: "Away",
            SetpointOrigin.ECO_IQ: "Eco",
            SetpointOrigin.MANUAL_OVERRIDE: "ManualOverride",
            SetpointOrigin.MANUAL_MODE: "Boost"
        }
        room_stats = [
            RoomStatState(id=s.id,
                          temperature=s.MeasuredTemperature / 10.0,
                          humidity=s.MeasuredHumidity) for s in info.RoomStat
        ]

        rooms = [
            RoomState(id=r.id,
                      name=r.Name,
                      room_stat_id=r.RoomStatId,
                      current_temperature=r.CalculatedTemperature / 10.0,
                      setpoint_temperature=r.CurrentSetPoint / 10.0,
                      demand_percent=r.PercentageDemand,
                      is_firing=r.ControlOutputState == "On",
                      control_source=map_control_source[r.SetpointOrigin],
                      boost_ends_at_unix=r.OverrideTimeoutUnixTime,
                      schedule_id=r.ScheduleId
                    ) for r in info.Room if not r.Invalid
        ]

        heatings = [
            HeatingChannelState(id=h.id,
                                is_firing=h.HeatingRelayState == "On",
                                demand_percent=h.PercentageDemand,
                                room_ids=h.RoomIds) for h in info.HeatingChannel
        ]

        hot_waters = [
            HotWaterChannelState(id=h.id,
                                 is_firing=h.HotWaterRelayState == "On",
                                 control_source=map_control_source[h.HotWaterDescription],
                                 boost_ends_at_unix=h.OverrideTimeoutUnixTime,
                                 schedule_id=h.ScheduleId) for h in info.HotWater
        ]

        return WiserState(hot_water_channels=hot_waters, heating_channels=heatings, room_stats=room_stats, rooms=rooms)

    async def boost_heating(self, room_id: int, temperature: int, duration_minutes: int):
        assert 50 <= temperature <= 240
        assert duration_minutes > 0
        await self.api.patch("Room", room_id, {
            "RequestOverride": {
                "Type": "Manual",
                "Originator": "App",
                "DurationMinutes": duration_minutes,
                "SetPoint": f"{temperature}"
            }
        })

    async def cancel_heating_boost(self, room_id: int):
        await self.api.patch("Room", room_id, {
            "RequestOverride": {
                "Type": "None",
            }
        })

    async def boost_hot_water(self, water_id: int, duration_minutes: int) -> None:
        assert 0 <= duration_minutes <= 60 * 3
        await self.api.patch("HotWater", water_id, {
            "RequestOverride": {
                "Type": "Manual",
                "Originator": "App",
                "DurationMinutes": duration_minutes,
                "SetPoint": "1100"
            }
        })

    async def cancel_hot_water_boost(self, water_id: int):
        await self.api.patch("HotWater", water_id, {
            "RequestOverride": {
                "Type": "None",
            }
        })


class WiserApi:

    def __init__(self, ip: str, secret: str) -> None:
        self.ip = ip
        self.secret = secret
        self.headers = {
            "Content-Type": "application/json",
            "Secret": self.secret
        }

    @retry(wait=wait_exponential(max=30), stop=stop_after_attempt(8))
    async def patch(self, item: Literal["Room", "HotWater"], item_id: int, params: dict):
        async with httpx.AsyncClient() as client:
            url = f"http://{self.ip}/data/domain/{item}/{item_id}/"
            res = await client.patch(url, headers=self.headers, json=params)
            res.raise_for_status()

    @retry(wait=wait_exponential(max=30), stop=stop_after_attempt(8))
    async def get_info(self):
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"http://{self.ip}/data/domain/"
            res = await client.get(url, headers=self.headers)
            res.raise_for_status()
            return WiserRoot(**res.json())

