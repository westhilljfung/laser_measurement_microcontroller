# laser_mcu.py
import network
import ntptime
import utime
from micropython import const
import machine
import uos
import ujson

ssid = 'Westhill_2.4G'
wp2_pass = 'Radoslav13'

TIME_ZONE_OFFSET = const(14400)
WIFI_CON_TIMEOUT = const(60000)
TIME_FILE = "/time"

class LaserMCU:

    def __init__(self):
        self.name = "Westhill Laser Measument System"
        self.wlan =  network.WLAN(network.STA_IF)
        self.connect_wifi()
        self.sd = machine.SDCard(slot=3, sck=machine.Pin(14), miso=machine.Pin(12)
                                 ,mosi=machine.Pin(13),cs=machine.Pin(15))
        uos.mount(self.sd, "/sd")
        print(uos.listdir("/sd/DCIM"))

    def connect_wifi(self):
        if not self.is_connected():
            self.wlan.active(True)
            self.wlan.connect(ssid, wp2_pass)
            start = utime.ticks_ms()
            while True:
                utime.sleep_ms(5)
                print(utime.ticks_diff(utime.ticks_ms, start))
                if utime.ticks_diff(utime.ticks_ms, start) >= WIFI_CON_TIMEOUT:
                    print("Fail to connect WIFI")
                    break
                elif self.is_connected():
                    break
        return
        
    def set_time_ntp(self):
        try:
            ntptime.settime()
        except:
            pass
        return
    """
    def set_time(self, datetime):
        RTC().datetime(datetime)
        return
    """
    def set_creation_time(self):
        self.time_created = utime.time()
        return

    def save_time(self):
        file = open(TIME_FILE, "w")
        file.write(ujson.dumps(utime.localtime()))
        file.close()
        return

    def load_time(self):
        file = open(TIME_FILE, "r")
        machine.RTC().datetime(ujson.loads(file.readline()))
        file.close()
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
        
