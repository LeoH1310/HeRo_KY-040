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

import time

from HeRo.KY040 import Encoder

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
        
# main program
if __name__ == '__main__':

    # create encoder object
    myEncoder = Encoder(PIN_CLK, PIN_DT, PIN_SW, encoderRotationCallback, encoderButtonCallback)

    # run forever
    while True:
        # time for something else
        time.sleep(1)