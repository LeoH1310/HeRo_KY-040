import time
from threading import Thread

from HeRo_KY040 import Encoder

# define encoder pins using BOARD pinning
PIN_CLK = 29
PIN_DT = 31
PIN_SW = 33

countPressed: int = 0
countControl: int = 0

# callback function for encoder rotation
def encoderRotationCallback(clockwise: bool):
    # DEBUG
    if clockwise:
        print ("ENCODER: Clockwise")
    else:
        print ("ENCODER: Counterclockwise")

# callback function for encoder button pressed
def encoderButtonCallback(pressed: bool):
    # DEBUG
    global countPressed
    global countControl

    if pressed:
        countPressed += 1
        countControl += 1
        print ("ENCODER: Button pressed")    
    else:
        countControl -= 1
        print ("ENCODER: Button released")
        print ("Pressed: ", countPressed)
        print ("Control: ", countControl)
        
    

# wordclock main program
if __name__ == '__main__':

    # create encoder object
    myEncoder = Encoder(PIN_CLK, PIN_DT, PIN_SW, encoderRotationCallback, encoderButtonCallback)

    # run forever
    while True:
        time.sleep(1)