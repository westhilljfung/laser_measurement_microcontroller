# sys_status/laser_sys.py
import network
import ntptime
import utime
import sys_status

class Sys:

    def __init__(self):
        self.name = "Westhill Laser Measument System"
        self.wlan =  network.WLAN(network.STA_IF)
        self.connect_wifi()
        self.set_time()

    def connect_wifi(self):
        if not self.is_connected():
            self.wlan.active(True)
            self.wlan.connect(sys_status.ssid, sys_status.wp2_pass)
            while not self.is_connected():
                utime.sleep(1)
        return
        
    def set_time(self):
        if self.is_connected():
            ntptime.settime()
        else:
            raise RuntimeError("Wifi is diconnected")
        return
    
    def is_connected(self):
        return self.wlan.isconnected()

    def __str__(self):
        return self.name
        
