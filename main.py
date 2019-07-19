#main.py
import gui_ctrl
import utime

laser_gui = gui.LaserGui()

while True:
    laser_gui.update_screen()
    utime.sleep_ms(10)
