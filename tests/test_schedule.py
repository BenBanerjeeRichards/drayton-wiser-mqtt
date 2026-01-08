from src.models import Schedule, DaySchedule, SetPoint
from src.wiser_client import get_next_schedule_setpoint
import datetime


def test_get_next_schedule():
    sp1 = SetPoint(DegreesC=10, Time=1000)
    sp2 = SetPoint(DegreesC=15, Time=1200)
    sp3 = SetPoint(DegreesC=20, Time=1730)
    sp4 = SetPoint(DegreesC=25, Time=2200)
    sp5 = SetPoint(DegreesC=30, Time=900)  # make very different for rollover check

    monday = DaySchedule(SetPoints=[sp1, sp2, sp3, sp4])
    tuesday = DaySchedule(SetPoints=[sp5, sp2, sp3, sp4])
    wednesday = DaySchedule(SetPoints=[sp1, sp2, sp3, sp4])
    thursday = DaySchedule(SetPoints=[sp1, sp2, sp3, sp4])
    friday = DaySchedule(SetPoints=[sp1, sp2, sp3, sp4])
    saturday = DaySchedule(SetPoints=[sp1, sp2, sp3, sp4])
    sunday = DaySchedule(SetPoints=[sp1, sp2, sp3, sp4])

    schedule = Schedule(Monday=monday, Tuesday=tuesday, Wednesday=wednesday, Thursday=thursday, Friday=friday,
                        Saturday=saturday,
                        Sunday=sunday, id=12, Type="X")

    dt1, t1 = get_next_schedule_setpoint(schedule=schedule,
                                         now=datetime.datetime(year=2026, month=1, day=2, hour=6, minute=0))
    assert t1 == 1000
    assert dt1 == datetime.date(year=2026, month=1, day=2)

    dt2, t2 =  get_next_schedule_setpoint(schedule=schedule, now=datetime.datetime(year=2026, month=1, day=2, hour=23, minute=30))
    assert t2 == 1000
    assert dt2 == datetime.date(year=2026, month=1, day=3)

    dt3, t3 =  get_next_schedule_setpoint(schedule=schedule, now=datetime.datetime(year=2026, month=1, day=5, hour=00, minute=10))
    assert t3 == 1000
    assert dt3 == datetime.date(year=2026, month=1, day=5)

    dt4, t4 =  get_next_schedule_setpoint(schedule=schedule, now=datetime.datetime(year=2026, month=1, day=5, hour=23, minute=30))
    assert t4 == 900
    assert dt4 == datetime.date(year=2026, month=1, day=6)


    # dt5, t5 = get_time_next_schedule_starts(schedule=schedule,
    #                                      dt=datetime.datetime(year=2026, month=1, day=2, hour=11, minute=30))
    # assert t5 == 1200
    # assert dt5 == datetime.date(year=2026, month=1, day=2)
