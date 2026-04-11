import datetime
from typing import Literal

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt
from src.models import WiserRoot, WiserState, RoomStatState, RoomState, HeatingChannelState, \
    HotWaterChannelState, SetpointOrigin, ControlSource, Schedule


class WiserClient:

    def __init__(self, ip: str, secret: str) -> None:
        self.api = WiserApi(ip, secret)

    async def get_state(self) -> WiserState:
        # Summarise the info from the wiser domain endpoint
        info = await self.api.get_info()
        return wiser_to_state(info)

    async def boost_heating(self, room_id: int, temperature: float, duration_minutes: int):
        wiser_tmp = int(10 * temperature)
        assert 50 <= wiser_tmp <= 240
        assert duration_minutes > 0
        await self.api.patch("Room", room_id, {
            "RequestOverride": {
                "Type": "Manual",
                "Originator": "App",
                "DurationMinutes": duration_minutes,
                "SetPoint": f"{wiser_tmp}"
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

    @retry(wait=wait_exponential(max=3), stop=stop_after_attempt(3))
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


def get_timezone_offset(local_time: int) -> int:
    """
    converts a wiser local_time to the timezone offset
    :param local_time: in wiser format -e.g. HHMM
    :return: the timezone offset from utc in minutes. e.g. 60 means local_time is utc+1
    """
    # Returns the offset from UTC in minutes
    # The wiser stat does not report a TZ, so we instead infer it from the datetime it reports
    now_utc = datetime.datetime.now(datetime.UTC)
    local_hour = int(local_time / 100)
    local_minute = local_time - local_hour * 100

    # the number of minutes into the day - e.g. 3.30pm = 15 * 60 + 30 = 930
    now_day_minutes = now_utc.hour * 60 + now_utc.minute
    local_day_minute = local_hour * 60 + local_minute

    minute_offset = local_day_minute - now_day_minutes
    # modular arithmatic
    if minute_offset < -12 * 24:
        minute_offset = 24 * 60 + minute_offset

    # round result to nearest 5 minute to account for timing differences
    return 5 * round(minute_offset / 5)


# This does the job of translating the fairly complex state on the wiser hub into
# more simple constructs We have a few different modes:
# Manual:          The thermostat setpoint remains as is until manual intervention
# Scheduled:       The thermostat setpoint follows a schedule
# Manual override: The schedule setpoint is overridden. The changed setpoint stays until the next schedule setpoint
#                  NB: nothing to do with Manual mode, this is a _manual_ override of a schedule
# Boost:           A manual override of the schedule setpoint, but reverts back to the schedule after a set period of time
# Away:            Like manual mode, this disables the schedule and sets all thermostats a preset temp
# Eco:             Setpoint adjusted down in advance of schedule setpoint in order to save energy
def wiser_to_state(info: WiserRoot) -> WiserState:
    map_control_source: dict[str, ControlSource] = {
        SetpointOrigin.BOOST: "Boost",
        SetpointOrigin.SCHEDULE: "Schedule",
        SetpointOrigin.AWAY: "Away",
        SetpointOrigin.ECO_IQ: "Eco",
        SetpointOrigin.MANUAL_OVERRIDE: "ManualOverride",
        SetpointOrigin.MANUAL_MODE: "Manual"
    }
    minutes_offset = get_timezone_offset(info.System.LocalDateAndTime.Time)
    room_stats = [
        RoomStatState(id=s.id,
                      temperature=s.MeasuredTemperature / 10.0,
                      humidity=s.MeasuredHumidity) for s in info.RoomStat
    ]

    rooms = []
    for room in info.Room:
        if room.Invalid:
            continue
        if room.ScheduleId:
            next_setpoint_unix = None
            schedule_setpoint_unix = None
            if room.Mode == "Auto":  # i.e. we are following a defined schedule
                schedule = [s for s in info.Schedule if s.id == room.ScheduleId]
                schedule_setpoint_unix = get_next_schedule_timestamp(schedule[0] if schedule else None, minutes_offset)
                control_source = map_control_source[room.SetpointOrigin]

                if room.SetpointOrigin == SetpointOrigin.MANUAL_OVERRIDE and room.OverrideSetpoint == room.ScheduledSetPoint:
                    # SetpointOrigin remains in Manual Override even when set back manually
                    control_source = "Schedule"

                if room.SetpointOrigin in [SetpointOrigin.SCHEDULE, SetpointOrigin.MANUAL_OVERRIDE,
                                           SetpointOrigin.ECO_IQ]:
                    # If we have a manual override, it will also reset at schedule time
                    next_setpoint_unix = schedule_setpoint_unix
                if room.SetpointOrigin == SetpointOrigin.BOOST:
                    # When boosting, we can just read the timestamp the boost expires
                    next_setpoint_unix = room.OverrideTimeoutUnixTime

            rooms.append(RoomState(id=room.id,
                                   name=room.Name,
                                   room_stat_id=room.RoomStatId,
                                   current_temperature=room.CalculatedTemperature / 10.0,
                                   setpoint_temperature=room.CurrentSetPoint / 10.0,
                                   demand_percent=room.PercentageDemand,
                                   is_firing=room.ControlOutputState == "On",
                                   control_source=control_source,
                                   boost_ends_at_unix=room.OverrideTimeoutUnixTime,
                                   schedule_id=room.ScheduleId,
                                   next_setpoint_unix=next_setpoint_unix,
                                   next_schedule_unix=schedule_setpoint_unix
                                   ))

    heatings = [
        HeatingChannelState(id=h.id,
                            is_firing=h.HeatingRelayState == "On",
                            demand_percent=h.PercentageDemand,
                            room_ids=h.RoomIds) for h in info.HeatingChannel
    ]

    hot_waters = []
    for h in info.HotWater:
        control_source = map_control_source[h.HotWaterDescription]
        if h.Mode == "Auto" and h.HotWaterDescription == SetpointOrigin.MANUAL_OVERRIDE and h.WaterHeatingState == h.ScheduledWaterHeatingState:
            control_source = "Schedule"
        hot_waters.append(HotWaterChannelState(id=h.id,
                             is_firing=h.HotWaterRelayState == "On",
                             control_source=control_source,
                             boost_ends_at_unix=h.OverrideTimeoutUnixTime,
                             schedule_id=h.ScheduleId))

    return WiserState(hot_water_channels=hot_waters, heating_channels=heatings, room_stats=room_stats, rooms=rooms)



def get_next_schedule_timestamp(room_schedule: Schedule | None, minutes_offset: int) -> int | None:
    if not room_schedule:
        return None
    schedule_start = get_next_schedule_setpoint(room_schedule, datetime.datetime.now(datetime.UTC), minutes_offset)
    if not schedule_start:
        return None

    dt, time = schedule_start
    return _wiser_schedule_to_unix(dt, time, minutes_offset)


# pass in time to make unit testing easier
def get_next_schedule_setpoint(schedule: Schedule, now: datetime.datetime, minutes_offset: int) -> tuple[datetime.date, int] | None:
    schedule_indexed = [schedule.Monday, schedule.Tuesday, schedule.Wednesday, schedule.Thursday, schedule.Friday,
                        schedule.Saturday,
                        schedule.Sunday]
    day_schedule = schedule_indexed[now.weekday()]
    # convert to wiser format - 17:30 -> 1730
    # add offset to match timezone wiser is in (if UTC+1 ,then minutes_offset = 60)
    minutes_into_day = now.hour * 100 + now.minute + minutes_offset
    # If we are currently in the final schedule of the day, then the next schedule starts tomorrow
    if minutes_into_day > day_schedule.SetPoints[-1].Time:
        tomorrow_schedule = schedule_indexed[(now.weekday() + 1) % 7]
        return (now + datetime.timedelta(days=1)).date(), tomorrow_schedule.SetPoints[0].Time

    # if we before the first schedule of the day, we will be on the previous day schedule still
    # so first schedule is first item
    if minutes_into_day < day_schedule.SetPoints[0].Time:
        return now.date(), day_schedule.SetPoints[0].Time

    for (point, next_point) in zip(day_schedule.SetPoints, day_schedule.SetPoints[1:]):
        if point.Time < minutes_into_day < next_point.Time:
            return now, next_point.Time

    # this can happen it seems if boost ends at end of schedule
    # in the app it shows up as no schedule with the new schedule setpoint
    # only for a minute, but we should handle this case gracefully
    return None


def _wiser_schedule_to_unix(date: datetime.date, wiser_time: int, minutes_offset: int) -> int:
    # wiser_time is in local timezone format
    hour = int(wiser_time / 100)
    minute = wiser_time - hour * 100
    # assume UTC and then we adjust later on
    dt = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=hour, minute=minute, second=0, tzinfo=datetime.UTC)
    return int(dt.timestamp()) - minutes_offset * 60
