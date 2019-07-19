#main.py
import gui_ctrl
import utime

laser_gui = gui_ctrl.LaserGui()

while True:
    laser_gui.call_task_handler()
    utime.sleep_ms(10)
    
