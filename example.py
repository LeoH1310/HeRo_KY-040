import time

from HeRo_KY040 import Encoder

# define encoder pins using BOARD pinning
PIN_CLK = 29
PIN_DT = 31
PIN_SW = 33

# callback function for encoder rotation
def encoderRotationCallback(clockwise: bool) -> None:
    if (clockwise):
        print ("ENCODER: Clockwise")
    else:
        print ("ENCODER: Counterclockwise")

# callback function for encoder button
def encoderButtonCallback(pressed: bool) -> None:
    if (pressed):
        print ("ENCODER: Button pressed")    
    else:
        print ("ENCODER: Button released")
        
# wordclock main program
if __name__ == '__main__':

    # create encoder object
    myEncoder = Encoder(PIN_CLK, PIN_DT, PIN_SW, encoderRotationCallback, encoderButtonCallback)

    # run forever
    while True:
        # time for something else
        time.sleep(1)