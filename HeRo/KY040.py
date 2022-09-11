# Copyright (c) 2022 HeRo Developers
# Author: Leonhard Hesse
# Created: September 2022

# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.

# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.

# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
    """A class that represents an encoder of type KY-040.

    On object creation pass the BOARD pins connected to CLK, DT and SW as well as two callback functions 
    to call when a rotation of the encoder or a state change of the button occurs.

    Reading the encoder and the button uses polling controlled via timers running in different threads.
    This leads to a hight CPU usage during interaction with the encoder. To minimise this downside 
    a sleeptimer is implemented to run the polling threads only if there is currently a user interaction. 
    For starting this sleeptimer the CLK and the SW pin generating GPIO events.
    """

    ROT_ENC_TABLE = [0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0]
    BUT_ENC_TABLE = [0,1,1,0]

    SLEEP_INTERVAL_S = 1
    POLLING_INTERVAL_S = 0.001

    def __init__(self, clockPin, dataPin, buttonPin, rotaryCallback, buttonCallback):
        # persist given values
        self.clockPin = clockPin
        self.dataPin = dataPin
        self.buttonPin = buttonPin
        self.rotaryCallback = rotaryCallback
        self.buttonCallback = buttonCallback

        # initialize filter and storage variables 
        self.prevNextCodeRot = 0
        self.storageRot = 0
        self.prevNextCodeBut = 0
        self.storageBut = 0

        # create timer and events for polling
        self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
        self.__sleepTimer.daemon = True

        self.__pollingEventRot = threading.Event()
        self.__pollingTimerRot = RepeatablePausableTimer(self.POLLING_INTERVAL_S, self.__readRotation, self.__pollingEventRot)
        self.__pollingTimerRot.daemon = True
        self.__pollingTimerRot.start()

        self.__pollingEventBut = threading.Event()
        self.__pollingLockBut = threading.Lock()
        self.__pollingTimerBut = RepeatablePausableTimer(self.POLLING_INTERVAL_S, self.__readButton, self.__pollingEventBut)
        self.__pollingTimerBut.daemon = True
        self.__pollingTimerBut.start()

        # set GPIO mode to board pinning
        GPIO.setmode(GPIO.BOARD)
 
        # setup GPIO pins
        GPIO.setup(self.clockPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.dataPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

        # add GPIO interrupts
        GPIO.add_event_detect(self.clockPin, GPIO.BOTH, callback=self.__wakeRotationPolling, bouncetime=1)
        GPIO.add_event_detect(self.buttonPin, GPIO.BOTH, callback=self.__wakeButtonPolling, bouncetime=1)

    def __wakeRotationPolling(self, pin):
        # set event to run rotation polling thread
        self.__pollingEventRot.set()

        if(self.__sleepTimer.is_alive()):
            # user is still interacting -> reset the sleep timer
            self.__sleepTimer.interval = self.SLEEP_INTERVAL_S
        else:
            # user interact first time since sleep timer has finished -> create new sleep timer
            self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
            self.__sleepTimer.start()

    def __wakeButtonPolling(self, pin):
        # set event to run button pollin thread
        if (not(self.__pollingEventBut.is_set())):
            self.__readButton(firstRun=True)
            self.__pollingEventBut.set()

        if(self.__sleepTimer.is_alive()):
            # user is still interacting -> reset the sleep timer
            self.__sleepTimer.interval = self.SLEEP_INTERVAL_S
        else:
            # user interact first time since sleep timer has finished -> create new sleep timer
            self.__sleepTimer = threading.Timer(self.SLEEP_INTERVAL_S, self.__stopPolling)
            self.__sleepTimer.start()

    def __stopPolling(self):
        self.__pollingEventRot.clear()    # clear event to pause rotation polling thread
        self.__pollingEventBut.clear()    # clear event to pause button polling thread

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

    # polling data from button including filtering and validation
    def __readButton(self, firstRun=False) -> None:

        # this function is called by the timer controlled polling routine and once
        # during the wakeup process. therfore we need thread synchronization unsing a lock
        with self.__pollingLockBut:

            self.prevNextCodeBut = self.prevNextCodeBut << 1

            # on first run after wakeup we need to add a high signal to the validation
            # to not miss the first press because signal level will already be low when 
            # timer controlled polling reaches here
            if (firstRun):
                self.prevNextCodeBut = self.prevNextCodeBut | 0x1
            else: 
                if (GPIO.input(self.buttonPin)):
                    self.prevNextCodeBut = self.prevNextCodeBut | 0x1

            self.prevNextCodeBut = self.prevNextCodeBut & 0x3

            # check if code is valid using table
            if (self.BUT_ENC_TABLE[self.prevNextCodeBut]):
                self.storageBut = self.storageBut << 2
                self.storageBut = self.storageBut | self.prevNextCodeBut

                if ((self.storageBut & 0xf) == 0x6):
                    # valid button press
                    self.buttonCallback(True)
                    
                if ((self.storageBut & 0xf) == 0x9):
                    # valid button release
                    self.buttonCallback(False)
