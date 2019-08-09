"""main.py

Main program for the laser measument system

*Author(s): Joshua Fung
2019-08-9
"""
import esp
from machine import reset

import gui_ctrl


# Only log errors
esp.osdebug(0, esp.LOG_ERROR)
# The LaserGui object controlles all the async update
laser_gui = gui_ctrl.LaserGui()
