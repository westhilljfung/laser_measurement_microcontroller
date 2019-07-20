# laser_mcu.py
import network
import ntptime
import utime
from micropython import const

ssid = 'Westhill_2.4G'
wp2_pass = 'Radoslav13'

TIME_ZONE_OFFSET = const(14400)
WIFI_CON_TIMEOUT = const(60000)

class LaserMCU:

    def __init__(self):
        self.name = "Westhill Laser Measument System"
        self.wlan =  network.WLAN(network.STA_IF)
        self.connect_wifi()
        self.set_time()
        self.set_creation_time()

    def connect_wifi(self):
        if not self.is_connected():
            self.wlan.active(True)
            self.wlan.connect(ssid, wp2_pass)
            start = utime.ticks_ms()
            break_loop = False
            while not break_loop:
                utime.sleep_ms(5)
                if utime.ticks_diff(utime.ticks_ms, start) >= WIFI_CON_TIMEOUT\
                   or self.is_connected():
                    break_loop = True
        return
        
    def set_time(self):
        try:
            ntptime.settime()
        except:
            pass
        return

    def set_creation_time(self):
        self.time_created =  utime.time()
        return
    
    def get_local_time_str(self):
        # TODO Daylight Saving Time
        dt = utime.localtime(utime.time() - TIME_ZONE_OFFSET)
        ct = utime.localtime(self.time_created - TIME_ZONE_OFFSET)
        
        dt_str = "Created: " + str(ct[1]) + "-" + str(ct[2]) + " " + str(ct[3]) \
            + ":" + str(ct[4]) + " " + str(dt[0]) + "-" + str(dt[1]) + "-" \
            + str(dt[2]) + " " + str(int(dt[3])) + ":" + str(dt[4]) + ":" + str(dt[5])
        return dt_str
    
    def is_connected(self):
        return self.wlan.isconnected()

    def __str__(self):
        return self.name
        
