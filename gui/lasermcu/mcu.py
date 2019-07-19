# lasermcu/mcu.py
import network
import ntptime
import utime
import lasermcu

class LaserMCU:

    def __init__(self):
        self.name = "Westhill Laser Measument System"
        self.wlan =  network.WLAN(network.STA_IF)
        self.connect_wifi()
        self.set_time()

    def connect_wifi(self):
        if not self.is_connected():
            self.wlan.active(True)
            self.wlan.connect(lasermcu.ssid, lasermcu.wp2_pass)
            while not self.is_connected():
                utime.sleep(1)
        return
        
    def set_time(self):
        if self.is_connected():
            ntptime.settime()
        else:
            raise RuntimeError("Wifi is diconnected")
        return

    def get_time(self):
        return utime.localtime()

    def get_local_time_str(self):
        # TODO Daylight Saving Time
        dt = utime.localtime(utime.time() - 14400)
        dt_str = str(dt[0]) + "-" + str(dt[1]) + "-" + str(dt[2]) + " " \
            + str(int(dt[3])) + ":" + str(dt[4]) + ":" + str(dt[5])
        return dt_str
    
    def is_connected(self):
        return self.wlan.isconnected()

    def __str__(self):
        return self.name
        
