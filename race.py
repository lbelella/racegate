import threading
import time
import RPi.GPIO as GPIO
from enum import Enum

CHANNEL = 7

class PIRReader(threading.Thread):
    def __init__(self, channel):
        threading.Thread.__init__(self)
        self.daemon = True
        self.channel = channel
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.channel, GPIO.IN)
        self.State = None
        self.PrevState = None
        self.RisingEdgeEvent = threading.Event()

    def run(self):
        tmp_state = GPIO.input(self.channel)
        self.State = tmp_state
        self.PrevState = self.State

        while True:
            tmp_state = GPIO.input(self.channel)

            if tmp_state != self.State:
                self.PrevState = self.State
                self.State = tmp_state

                if self.State == 1:
                    self.RisingEdgeEvent.set()
                    self.RisingEdgeEvent.clear()

                # Ghetto de-bounce
                time.sleep(3)
            
class RaceState(Enum):
    IDLE = 1
    WAITING_FOR_TRIGGER = 2
    RUNNING = 3
    COMPLETE = 4

class Race(threading.Thread):
    def __init__(self, lap_count, timeout=0):
        threading.Thread.__init__(self)
        self.daemon = True
        self.LapCount = lap_count
        self.CurrentLap = 0
        self.Timeout = timeout
        self.LapTimes = []
        self.State = RaceState.IDLE
        self.StartTime = 0
        self.pir = PIRReader(CHANNEL)
        self.pir.start()
        self.current_lap_start = 0

    def wait_for_trigger(self):
        self.pir.RisingEdgeEvent.wait()
        self.current_lap_start = time.perf_counter()

    def count_laps(self):
        for lap in range(self.LapCount):
            self.pir.RisingEdgeEvent.wait()
            lap_end = time.perf_counter()
            elapsed = lap_end - self.current_lap_start
            self.current_lap_start = lap_end
            print("Lap {0}: {1:.3f}".format(lap + 1, elapsed))

    def run(self):
        while True:
            if self.State == RaceState.IDLE:
                print("Starting race!!!")
                self.State = RaceState.WAITING_FOR_TRIGGER

            elif self.State == RaceState.WAITING_FOR_TRIGGER:
                print("Waiting for start trigger")
                self.wait_for_trigger()
                self.State = RaceState.RUNNING
                time.sleep(1)

            elif self.State == RaceState.RUNNING:
                print("Running")
                self.count_laps()
                self.State = RaceState.COMPLETE

            elif self.State == RaceState.COMPLETE:
                print("Race complete!")
                break
