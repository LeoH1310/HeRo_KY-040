import time
import RPi.GPIO as GPIO
import threading

class RepeatablePausableTimer(threading.Timer):
    def __init__(self, interval, function, event, args=None, kwargs=None):
        super().__init__(interval, function, args, kwargs)
        self.runEvent = event

    def run(self):
        while not self.finished.wait(self.interval):
            # wait for the run event
            self.runEvent.wait()
            self.function(*self.args, **self.kwargs)

class Encoder:

    BOUNCETIME_BUTTON_MS = 300
    ROT_ENC_TABLE = [0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0]

    SLEEP_INTERVAL_S = 1
    POLLING_INTERVAL_S = 0.001

    def __init__(self, clockPin, dataPin, buttonPin, rotaryCallback, buttonPressedCallback):
        # persist given values
        self.clockPin = clockPin
        self.dataPin = dataPin
        self.buttonPin = buttonPin
        self.rotaryCallback = rotaryCallback
        self.buttonPressedCallback = buttonPressedCallback

        # initialize filter and storage variables 
        self.prevNextCode = 0
        self.storage = 0

        # create timer and events for polling
        self.__readRotationLock = threading.Lock()
        self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
        self.__pollingEvent = threading.Event()
        self.__pollingTimer = RepeatablePausableTimer(self.POLLING_INTERVAL_S, self.__readRotation, self.__pollingEvent)

        # set GPIO mode to board pinning
        GPIO.setmode(GPIO.BOARD)
 
        # setup GPIO pins
        GPIO.setup(self.clockPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.dataPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

        # add GPIO interrupts
        GPIO.add_event_detect(self.clockPin, GPIO.BOTH, callback=self.__wakeRotationPolling, bouncetime=1)
        GPIO.add_event_detect(self.buttonPin, GPIO.FALLING, callback=self.__buttonPressedCallback, bouncetime=self.BOUNCETIME_BUTTON_MS)

    def __wakeRotationPolling(self, pin):
        # set event to run polling thread
        self.__pollingEvent.set()

        if(self.__sleepTimer.is_alive()):
            # user is still interacting -> reset the sleep timer
            self.__sleepTimer.interval = self.SLEEP_INTERVAL_S
        else:
            # user interact first time since sleep timer has finished -> create new sleep timer
            self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
            self.__sleepTimer.start()

    def __stopPolling(self):
        self.__pollingEvent.clear()    # clear event to pause polling thread

    # polling data from encoder including filtering and validation
    def __readRotation(self) -> None:

        with self.rotationLock:

            self.prevNextCode = self.prevNextCode << 2
            if (GPIO.input(self.dataPin)):
                self.prevNextCode = self.prevNextCode | 0x02
            if (GPIO.input(self.clockPin)):
                self.prevNextCode = self.prevNextCode | 0x01
            self.prevNextCode = self.prevNextCode & 0x0f

            # check if code is valid using table
            if (self.ROT_ENC_TABLE[self.prevNextCode]):
                self.storage = self.storage << 4
                self.storage = self.storage | self.prevNextCode

                if ((self.storage & 0xff) == 0x17):
                    # valid clockwise rotation
                    self.rotaryCallback(True)

                if ((self.storage & 0xff) == 0x2b):
                    # valid counterclockwise rotation
                    self.rotaryCallback(False)

    def __buttonPressedCallback(self, pin):
        self.buttonPressedCallback()