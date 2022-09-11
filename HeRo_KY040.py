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
    BUT_ENC_TABLE = [0,1,1,0]

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
        self.prevNextCodeRot = 0
        self.storageRot = 0
        self.prevNextCodeBut = 0
        self.storageBut = 0

        # create timer and events for polling
        self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)

        self.__pollingEventRot = threading.Event()
        self.__pollingTimerRot = RepeatablePausableTimer(self.POLLING_INTERVAL_S, self.__readRotation, self.__pollingEventRot)
        self.__pollingTimerRot.start()

        self.__pollingEventBut = threading.Event()
        self.__pollingTimerBut = RepeatablePausableTimer(self.POLLING_INTERVAL_S, self.__readButton, self.__pollingEventBut)
        self.__pollingEventBut.set() #debug
        self.__pollingTimerBut.start()

        # set GPIO mode to board pinning
        GPIO.setmode(GPIO.BOARD)
 
        # setup GPIO pins
        GPIO.setup(self.clockPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.dataPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

        # add GPIO interrupts
        GPIO.add_event_detect(self.clockPin, GPIO.BOTH, callback=self.__wakeRotationPolling, bouncetime=1)
        #GPIO.add_event_detect(self.buttonPin, GPIO.FALLING, callback=self.__buttonPressedCallback, bouncetime=self.BOUNCETIME_BUTTON_MS)

    def __wakeRotationPolling(self, pin):
        # set event to run polling thread
        self.__pollingEventRot.set()

        if(self.__sleepTimer.is_alive()):
            # user is still interacting -> reset the sleep timer
            self.__sleepTimer.interval = self.SLEEP_INTERVAL_S
        else:
            # user interact first time since sleep timer has finished -> create new sleep timer
            self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
            self.__sleepTimer.start()

    def __stopPolling(self):
        self.__pollingEventRot.clear()    # clear event to pause polling thread

    # polling data from encoder including filtering and validation
    def __readRotation(self) -> None:

        self.prevNextCodeRot = self.prevNextCodeRot << 2
        if (GPIO.input(self.dataPin)):
            self.prevNextCodeRot = self.prevNextCodeRot | 0x02
        if (GPIO.input(self.clockPin)):
            self.prevNextCodeRot = self.prevNextCodeRot | 0x01
        self.prevNextCodeRot = self.prevNextCodeRot & 0x0f

        # check if code is valid using table
        if (self.ROT_ENC_TABLE[self.prevNextCodeRot]):
            self.storageRot = self.storageRot << 4
            self.storageRot = self.storageRot | self.prevNextCodeRot

            if ((self.storageRot & 0xff) == 0x17):
                # valid clockwise rotation
                self.rotaryCallback(True)

            if ((self.storageRot & 0xff) == 0x2b):
                # valid counterclockwise rotation
                self.rotaryCallback(False)

    def __buttonPressedCallback(self, pin):
        self.buttonPressedCallback()

    def __readButton(self) -> None:

        self.prevNextCodeBut = self.prevNextCodeRot << 1
        if (GPIO.input(self.buttonPin)):
            self.prevNextCodeBut = self.prevNextCodeBut | 0x1
        self.prevNextCodeBut = self.prevNextCodeBut & 0x3

        # check if code is valid using table
        if (self.BUT_ENC_TABLE[self.prevNextCodeBut]):
            self.storageBut = self.storageBut << 2
            self.storageBut = self.storageBut | self.prevNextCodeBut

            if ((self.storageBut & 0xf) == 0x6):
                # pressed and released
                print ("pressed and released")
                

            if ((self.storageBut & 0xf) == 0x7):
                # pressed and hold
                print ("pressed and hold")
