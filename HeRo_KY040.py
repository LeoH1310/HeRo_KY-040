import time
import RPi.GPIO as GPIO
from threading import Lock
from threading import Event

from threading import Timer
class RepeatablePausableTimer(Timer):
    def __init__(self, interval, function, event, args=None, kwargs=None):
        super().__init__(interval, function, args, kwargs)
        self.pauseEvent = event

    def run(self):
        while not self.finished.wait(self.interval):
            #print('\tTHREAD: This is the thread speaking, we are Waiting for event to start..')
            self.pauseEvent.wait()
            #print('\tTHREAD:  WHOOOOOO HOOOO WE GOT A SIGNAL  : %s' % event_is_set)
            self.function(*self.args, **self.kwargs)

class Encoder:

    BOUNCETIME_BUTTON_MS = 300
    SLEEPCOUNTER = 1000
    ROT_ENC_TABLE = [0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0]

    SLEEP_INTERVAL_S = 5
    POLLING_INTERVAL_S = 0.001

    def __init__(self, clockPin, dataPin, buttonPin, rotaryCallback, buttonPressedCallback):
        # persist values
        self.clockPin = clockPin
        self.dataPin = dataPin
        self.buttonPin = buttonPin
        self.rotaryCallback = rotaryCallback
        self.buttonPressedCallback = buttonPressedCallback
        self.prevNextCode = 0
        self.storage = 0
        self.sleepCounter = 0
        self.rotationLock = Lock()

        self.__sleepTimer = Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)

        self.__event = Event()
        self.__pollingTimer = RepeatablePausableTimer(self.POLLING_INTERVAL_S, self.run, self.__event)

        # test
        self.__pollingTimer.start()

        # set GPIO mode to board pinning
        #gpioMode = GPIO.getmode()
        GPIO.setmode(GPIO.BOARD)
 
        # setup GPIO pins
        GPIO.setup(self.clockPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.dataPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

        # add GPIO interrupts
        GPIO.add_event_detect(self.clockPin, GPIO.BOTH, callback=self.__wakeRotationPolling, bouncetime=1)
        GPIO.add_event_detect(self.buttonPin, GPIO.FALLING, callback=self.__buttonPressedCallback, bouncetime=self.BOUNCETIME_BUTTON_MS)

        # reset GPIO mode
        #GPIO.setmode(gpioMode)

    def run(self):  
        rotationData = self.readRotation()

        if (rotationData == 1):
            self.rotaryCallback(True)
        elif (rotationData == -1):
            self.rotaryCallback(False)


    def __wakeRotationPolling(self, pin):
        # set event to run polling thread
        self.__event.set()

        if(self.__sleepTimer.is_alive()):
            # user is still interacting -> reset the sleep timer
            self.__sleepTimer.interval = self.SLEEP_INTERVAL_S
        else:
            # user interact first time since sleep timer has finished -> create new sleep timer
            self.__sleepTimer = Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
            self.__sleepTimer.start()

    def __stopPolling(self):
        self.__event.clear()    # clear event to pause polling thread

    # polling data from encoder including filtering and validation
    # return 1 for valid CW rotation
    # return -1 for valid CCW rotation
    # return 0 for invalid
    def readRotation(self) -> int:

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
                    return 1

                if ((self.storage & 0xff) == 0x2b):
                    # valid counterclockwise rotation
                    return -1
            
            # no valid data from encoder
            return 0

    def __buttonPressedCallback(self, pin):
        self.buttonPressedCallback()