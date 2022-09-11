import time
import RPi.GPIO as GPIO

class Encoder:

    BOUNCETIME_BUTTON_MS = 300
    SLEEPCOUNTER = 1000
    ROT_ENC_TABLE = [0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0]

    def __init__(self, clockPin, dataPin, buttonPin, rotaryCallback, buttonPressedCallback):
        # persist values
        self.clockPin = clockPin
        self.dataPin = dataPin
        self.buttonPin = buttonPin
        self.rotaryCallback = rotaryCallback
        self.buttonPressedCallback = buttonPressedCallback
        self.prevNextCode = 0
        self.storage = 0
        self.sleepCounter = self.SLEEPCOUNTER

        # set GPIO mode to board pinning
        gpioMode = GPIO.getmode()
        GPIO.setmode(GPIO.BOARD)
 
        # setup GPIO pins
        GPIO.setup(self.clockPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.dataPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

        # add GPIO interrupts
        GPIO.add_event_detect(self.clockPin, GPIO.RISING, callback=self.wakeRotationPolling)
        GPIO.add_event_detect(self.buttonPin, GPIO.FALLING, callback=self._buttonPressedCallback, bouncetime=self.BOUNCETIME_BUTTON_MS)

        # reset GPIO mode
        GPIO.setmode(gpioMode)

    def run(self):
        # run forever
        while True:
            
            if (self.sleepCounter != 0):
                time.sleep(0.0025)
            else:
                time.sleep(0.01)    

            rotationData = self.readRotation()

            if (rotationData == 1):
                self.rotaryCallback(True)
            elif (rotationData == -1):
                self.rotaryCallback(False)
                
            if (self.sleepCounter > 0):
                self.sleepCounter -= 1

    def wakeRotationPolling(self):
        self.sleepCounter = self.SLEEPCOUNTER

    # polling data from encoder including filtering and validation
    # return 1 for valid CW rotation
    # return -1 for valid CCW rotation
    # return 0 for invalid
    def readRotation(self) -> int:

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

    def _buttonPressedCallback(self, pin):
        self.buttonPressedCallback()