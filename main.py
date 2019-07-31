#main.py
import gui_ctrl
import esp

esp.osdebug(0, esp.LOG_ERROR)

# The LaserGui object controlles all the async update
laser_gui = gui_ctrl.LaserGui()
