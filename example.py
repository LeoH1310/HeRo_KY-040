import time
from threading import Thread

from HeRo_KY040 import Encoder

# define encoder pins using BOARD pinning
PIN_CLK = 29
PIN_DT = 31
PIN_SW = 33

# callback function for encoder rotation
def encoderRotationCallback(direction: int):
    # DEBUG
    if direction:
        print ("ENCODER: Clockwise")
    else:
        print ("ENCODER: Counterclockwise")

# callback function for encoder button pressed
def encoderButtonPressedCallback():
    # DEBUG
    print ("ENCODER: Button pressed")
    

# wordclock main program
if __name__ == '__main__':

    # create encoder object
    myEncoder = Encoder(PIN_CLK, PIN_DT, PIN_SW, encoderRotationCallback, encoderButtonPressedCallback)

    # running the encoder in a new thread
    # Thread(target=lambda: myEncoder.run()).start()

    # run forever
    while True:
        time.sleep(1)