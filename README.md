# HeRo_KY-040
![This is an image](https://www.linkerkit.de/images/thumb/d/d5/ky-040.jpg/358px-ky-040.jpg)

## Overview
* Raspberry Pi library written in Python for the encoder KY-040
* Uses polling and software debouncing -> no hardware changes needed
* Allows the usage of one or more encoders
* Usable on every GPIO pin

## Basic Knowledge and Special Thanks
This library is based on the experiences and knowledge of John Main. He made a really good job explaining the possibility of how immediately tame the really noisy encoder KY-040. So if you are interested in how it works exactly have a look at his website: https://www.best-microcontroller-projects.com/rotary-encoder.html

## Installation
I recommend you to use pip to install this library. Just run the following command:
```
sudo pip install git+https://github.com/LeoH1310/HeRo_KY-040.git
```
## Example Usage on Raspberry Pi
Import the library into your project:
```python
from HeRo.KY040 import Encoder
```
Define two callback functions and create a new encoder object. You need to pass the CLK, DT, and SW pin. Use the original pin numbers (1-40) NOT the GPIO numbers. As well pass two callback functions called when a rotation or a button state change occurs.
```python
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

myEncoder = Encoder(PIN_CLK, PIN_DT, PIN_SW encoderRotationCallback, encoderButtonCallback)
```
Have a look at the example code for more details.

## Requirements
This library uses the standard library RPi.GPIO. Usually this Python library is installed by default. If not use the following command to install this library:
```
sudo apt-get install python-rpi.gpio
```

## Licence and Copyright
Copyright (c) 2022 HeRo Developers  
Author: Leonhard Hesse  
Created: September 2022

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
