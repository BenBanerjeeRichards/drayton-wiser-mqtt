from typing import Literal

import requests

from src.models import WiserRoot, WiserSate, RoomStatState, RoomState, HeatingChannelState, \
    HotWaterChannelState, SetpointOrigin
from decimal import Decimal


class WiserClient:

    def __init__(self, ip: str, secret: str) -> None:
        self.api = WiserApi(ip, secret)

    def get_state(self) -> WiserSate:
        # Summarise the info from the wiser domain endpoint
        info = self.api.get_info()
        # TODO: currently manual and boost treated the same
        map_control_source: dict[str, Literal["Boost", "Schedule", "Away", "Eco"]] = {
            SetpointOrigin.BOOST: "Boost",
            SetpointOrigin.SCHEDULE: "Schedule",
            SetpointOrigin.AWAY: "Away",
            SetpointOrigin.ECO_IQ: "Eco",
            SetpointOrigin.MANUAL_OVERRIDE: "Boost",
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

        return WiserSate(hot_water_channels=hot_waters, heating_channels=heatings, room_stats=room_stats, rooms=rooms)

    def boost_heating(self, room_id: int, temperature: int, duration_minutes: int):
        assert 50 <= temperature <= 240
        assert duration_minutes > 0
        self.api.patch("Room", room_id, {
            "RequestOverride": {
                "Type": "Manual",
                "Originator": "App",
                "DurationMinutes": duration_minutes,
                "SetPoint": f"{temperature}"
            }
        })

    def cancel_heating_boost(self, room_id: int):
        self.api.patch("Room", room_id, {
            "RequestOverride": {
                "Type": "None",
            }
        })

    def boost_hot_water(self, water_id: int, duration_minutes: int) -> None:
        assert 0 <= duration_minutes <= 60 * 3
        self.api.patch("HotWater", water_id, {
            "RequestOverride": {
                "Type": "Manual",
                "Originator": "App",
                "DurationMinutes": duration_minutes,
                "SetPoint": "1100"
            }
        })

    def cancel_hot_water_boost(self, water_id: int):
        self.api.patch("HotWater", water_id, {
            "RequestOverride": {
                "Type": "None",
            }
        })


class WiserApi:

    def __init__(self, ip: str, secret: str) -> None:
        self.ip = ip
        self.secret = secret

    def patch(self, item: Literal["Room", "HotWater"], item_id: int, params: dict):
        url = f"http://{self.ip}/data/domain/{item}/{item_id}/"
        res = requests.patch(url, headers=self._get_headers(), json=params)
        res.raise_for_status()

    def get_info(self):
        url = f"http://{self.ip}/data/domain/"
        res = requests.get(url, headers=self._get_headers())
        res.raise_for_status()
        return WiserRoot(**res.json())

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Secret": self.secret
        }
