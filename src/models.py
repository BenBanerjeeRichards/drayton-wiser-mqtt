from typing import Any
from pydantic import BaseModel
from typing_extensions import Literal
from decimal import Decimal


class Config(BaseModel):
    mqtt_username: str
    mqtt_password: str
    mqtt_host: str
    mqtt_port: int
    wiser_ip: str
    wiser_secret: str

class HeatingChannelState(BaseModel):
    id: int
    is_firing: bool
    demand_percent: int
    room_ids: list[int]


class HotWaterChannelState(BaseModel):
    id: int
    is_firing: bool
    control_source: Literal["Schedule", "Boost", "Away", "Eco"]
    boost_ends_at_unix: int | None
    schedule_id: int | None


class RoomState(BaseModel):
    id: int
    name: str
    room_stat_id: int | None = None
    current_temperature: Decimal
    setpoint_temperature: Decimal
    demand_percent: int
    is_firing: bool
    control_source: Literal["Schedule", "Boost", "Away", "Eco"]
    boost_ends_at_unix: int | None = None
    schedule_id: int | None


class RoomStatState(BaseModel):
    id: int
    temperature: Decimal
    humidity: int


class WiserSate(BaseModel):
    hot_water_channels: list[HotWaterChannelState]
    heating_channels: list[HeatingChannelState]
    rooms: list[RoomState]
    room_stats: list[RoomStatState]


# Below is the structure of the Wiser data
# Gemini generated from single request
# will need to refine this as we find out all the optional fields

class BoilerSettings(BaseModel):
    ControlType: str
    FuelType: str
    CycleRate: str
    OnOffHysteresis: int


class GeoPosition(BaseModel):
    Latitude: float
    Longitude: float


class LocalDateAndTime(BaseModel):
    Year: int
    Month: str
    Date: int
    Day: str
    Time: int


class BlockPublishing(BaseModel):
    RoomTimeSeries: bool
    EcoMode: bool
    BoilerOnOffEvent: bool
    HotWaterOnOffEvent: bool
    PercentageDemand: bool
    FotaProgress: bool
    SupportPackage: bool
    PairingToken: bool
    Notification: bool
    Describe: bool
    EntireDataModel: bool
    ScheduleUpdate: bool
    SmartPlugUpdate: bool
    LightUpdate: bool
    ShutterUpdate: bool
    TemperatureChangeEvent: bool
    EventSeriesDiagnostic: bool


class Reception(BaseModel):
    Rssi: int
    Lqi: int | None = None


# --- Main Component Models ---

class System(BaseModel):
    PairingStatus: str
    provisionTokenSucceedCount: int
    provisionTokenFailCount: int
    provisionTokenRequestCount: int
    TimeZoneOffset: int
    AutomaticDaylightSaving: bool
    SystemMode: str
    FotaEnabled: bool
    ValveProtectionEnabled: bool
    EcoModeEnabled: bool
    AwayModeAffectsHotWater: bool
    AwayModeSetPointLimit: int
    BoilerSettings: BoilerSettings
    CoolingModeDefaultSetpoint: int
    CoolingAwayModeSetpointLimit: int
    ComfortModeEnabled: bool
    PreheatTimeLimit: int
    DegradedModeSetpointThreshold: int
    GeoPosition: GeoPosition
    UfhOrphanModeOutput: str
    isMigrated: bool
    UnixTime: int
    ActiveSystemVersion: str
    ZigbeePermitJoinActive: bool
    BrandName: str
    CloudConnectionStatus: str
    ChipId: str
    LocalDateAndTime: LocalDateAndTime
    HeatingButtonOverrideState: str
    UserOverridesActive: bool | None = None
    HotWaterButtonOverrideState: str
    OpenThermConnectionStatus: str
    SunriseTimes: list[int]
    SunsetTimes: list[int]
    isTrialist: bool
    isProvisioned: bool
    HardwareGeneration: int


class Cloud(BaseModel):
    DetailedPublishing: bool
    EnableFullScheduleTelemetry: bool
    BlockPublishing: BlockPublishing
    WiserApiHost: str
    BootStrapApiHost: str


class HeatingChannel(BaseModel):
    id: int
    Name: str
    RoomIds: list[int]
    PercentageDemand: int
    DemandOnOffOutput: str
    HeatingRelayState: str
    IsSmartValvePreventingDemand: bool


class HotWater(BaseModel):
    id: int
    # Current HW schedule id being followed (check against Schedules)
    ScheduleId: int
    Mode: str
    AwayModeSuppressed: bool
    # are we heating hot water now?
    WaterHeatingState: Literal["On", "Off"]
    # Set when boost enabled
    OverrideWaterHeatingState: Literal["On", "Off"] | None = None
    # If a boost or override is active, this gives the time we return to the schedule
    OverrideTimeoutUnixTime: int | None = None
    # should be we heating now per schedule
    ScheduledWaterHeatingState: str
    HotWaterRelayState: Literal["On", "Off"]
    # Description of what is firing HW
    HotWaterDescription: Literal["FromBoost", "FromSchedule", "FromAwayMode", "FromEcoIQ"]


class Room(BaseModel):
    id: int
    ManualSetPoint: int | None = None
    # Where the set point comes from. FromNoControl => not used
    SetpointOrigin: Literal["FromSchedule", "FromManualOverride", "FromBoost", "FromNoControl", "FromAwayMode", "FromEcoIQ"]
    OverrideType: str | None = None
    # If set we are not following the scheudle
    OverrideSetpoint: int | None = None
    # If a boost or override is active, this gives the time we return to the schedule
    OverrideTimeoutUnixTime: int | None = None
    # Lookup schedules in Schedules field by this id
    ScheduleId: int
    HeatingRate: int
    RoomStatId: int | None = None
    SmartValveIds: list[int] | None = None
    # Just the room name  (e.g. "Living Room")
    Name: str
    Mode: str
    DemandType: str | None = None
    WindowDetectionActive: bool
    # Room temperature effective for use for the control of the room
    # I guess that if you have TRV + stat, this will be the value of the stat not the TRV
    CalculatedTemperature: int
    # Evaluated set point from either schedule or overridee
    CurrentSetPoint: int
    # Used for proportional control. If big diff between current and setpoint, will be 100%
    # Otherwise will be smaller gap used to drive time or OT based modulation
    PercentageDemand: int | None = None
    # Does we show as 'firing'
    ControlOutputState: Literal['On', 'Off']
    DisplayedSetPoint: int
    # If we were following the schedule, what should the setpoint be
    ScheduledSetPoint: int
    AwayModeSuppressed: bool
    RoundedAlexaTemperature: int
    ComfortTarget: int | None = None
    EffectiveMode: str
    PercentageDemandForItrv: int
    ControlDirection: str
    HeatingType: str | None = None
    # If set this room is not used, and a reason will be given
    Invalid: str | None = None


class Device(BaseModel):
    id: int
    NodeId: int
    ProductType: str
    ProductIdentifier: str
    ActiveFirmwareVersion: str
    ModelIdentifier: str
    DeviceLockEnabled: bool
    DisplayedSignalStrength: str
    ReceptionOfController: Reception
    ReceptionOfDevice: Reception | None = None
    PendingZigbeeMessageMask: int | None = None
    BindingsStatus: str
    ReportConfigStatus: str
    SerialNumber: str | None = None
    ProductModel: str | None = None
    OtaImageQueryCount: int | None = None
    BatteryVoltage: int | None = None
    BatteryLevel: str | None = None


class Zigbee(BaseModel):
    JPANCount: int
    NetworkChannel: int
    UpdateEBLState: str
    CurrentEBLFile: str
    TargetEBLFile: str
    UpdateAttempts: int
    ZigbeeModuleVersion: str
    ZigbeeEUI: str


class RoomStat(BaseModel):
    id: int
    SetPoint: int
    MeasuredTemperature: int
    MeasuredHumidity: int


class DeviceCapabilityMatrix(BaseModel):
    Roomstat: bool
    ITRV: bool
    SmartPlug: bool
    UFH: bool
    UFHFloorTempSensor: bool
    UFHDewSensor: bool
    HACT: bool
    LACT: bool
    Light: bool
    Shutter: bool
    LoadController: bool


class SetPoint(BaseModel):
    Time: int
    DegreesC: int


class DaySchedule(BaseModel):
    SetPoints: list[SetPoint]


class Schedule(BaseModel):
    id: int
    Monday: DaySchedule
    Tuesday: DaySchedule
    Wednesday: DaySchedule
    Thursday: DaySchedule
    Friday: DaySchedule
    Saturday: DaySchedule
    Sunday: DaySchedule
    Type: str


# --- Root Model ---

class WiserRoot(BaseModel):
    System: System
    Cloud: Cloud
    HeatingChannel: list[HeatingChannel]
    HotWater: list[HotWater]
    Room: list[Room]
    Device: list[Device]
    Zigbee: Zigbee
    SmartValve: list[Any]
    RoomStat: list[RoomStat]
    DeviceCapabilityMatrix: DeviceCapabilityMatrix
    Schedule: list[Schedule]
