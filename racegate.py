#!/usr/bin/python3
import time
from race import Race, RaceState

current_race = Race(8)
current_race.start()

while current_race.State != RaceState.COMPLETE:
    time.sleep(1)
