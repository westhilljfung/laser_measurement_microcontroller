""" 
laser_mcu.py
==========
This is a Micropython driver for the Laser Measurement Controller
*Author(s): Joshua Fung
July 30, 2019
"""
import network
import ntptime
import utime
from micropython import const
import machine
import uos
import ujson
import si7021
import _thread

ssid = 'Westhill_2.4G'
wp2_pass = 'Radoslav13'

TIME_ZONE_OFFSET = const(14400)
WIFI_CON_TIMEOUT = const(30000)
TIME_FILE = "/time"
SD_FILE = "/sd"

class LaserMCU:
    def __init__(self):
        self._name = "Westhill Laser Measument System"
        self._wlan = network.WLAN(network.STA_IF)
        self.connect_wifi()
        self._sd = machine.SDCard(slot=3, sck=machine.Pin(14), miso=machine.Pin(12)
                                 ,mosi=machine.Pin(13),cs=machine.Pin(15))
        uos.mount(self._sd, SD_FILE)
        self._th_sensor = si7021.SI7021(4, 21)
        self._buzz = Buzzer(26)
        
    def connect_wifi(self):
        if not self.is_connected():
            self._wlan.active(True)
            self._wlan.connect(ssid, wp2_pass)
            start = utime.ticks_ms()
            print("Connecting Wifi: [", end = '')
            while True:
                utime.sleep_ms(WIFI_CON_TIMEOUT // 40)
                print("-", end="")
                if utime.ticks_diff(utime.ticks_ms(), start) >= WIFI_CON_TIMEOUT:
                    print("]")
                    print("Fail to connect WIFI")
                    break
                elif self.is_connected():
                    print("]")
                    break
        return

    def alt(self):
        self._buzz.alt()
        return

    def warn(self):
        self._buzz.warn()
        return
    
    def save_th_data(self):
        # Time in utc
        dt = utime.localtime()
        filename = ("TH-%04d" % dt[0]) + "_" + ("%02d" % dt[1]) + "_" \
            + ("%02d" % dt[2]) + ".txt"
        try:
            f = open(SD_FILE + "/" + filename, "a+")
        except OSError as err:
            raise
        if f.tell() == 0:
            print("YYYY-MM-DD-HH-MM(RTC)\tTemperature(C)\tHumidity(RH%)", file = f)
            
        print("%04d-%02d-%02d-%02d-%02d\t%0.3f\t\t%0.3f" \
              % (dt[0], dt[1], dt[2], dt[3], dt[4],\
                self._th_sensor.read_temperature(),\
                 self._th_sensor.read_relative_humidity()), file = f)
        f.close()
        return

    def get_th_str(self):
        th_str = "T: " + str("%0.2f" % self._th_sensor.read_temperature()) + " H: " \
            + str("%0.2f" % self._th_sensor.read_relative_humidity())
        return th_str
    
    def set_time_ntp(self):
        if not self.is_connected():
            raise OSError("Wifi not connected")
        ntptime.settime()
        return

    def set_creation_time(self):
        self.time_created = utime.time()
        return

    def save_time(self):
        file = open(TIME_FILE, "w")
        ujson.dump(utime.localtime(), file)
        file.close()
        return

    def load_time(self):
        file = open(TIME_FILE, "r")
        old_time = ujson.load(file)
        machine.RTC().datetime(old_time[0:3] + [0] + old_time[3:6] + [0])
        file.close()
        return

    def get_creation_time_str(self):        
        ct = utime.localtime(self.time_created - TIME_ZONE_OFFSET)
        dt_str = "Created: " + str(ct[1]) + "-" + str(ct[2]) + " " + str(ct[3]) \
            + ":" + str(ct[4])
        return dt_str
         
    def get_local_time_str(self):
        # TODO Daylight Saving Time
        dt = utime.localtime(utime.time() - TIME_ZONE_OFFSET)

        dt_str = str(dt[0]) + "-" + str(dt[1]) + "-" + str(dt[2]) + " " \
            + str(int(dt[3])) + ":" + str(dt[4]) + ":" + str(dt[5])
        return dt_str

    def is_connected(self):
        return self._wlan.isconnected()

    def __str__(self):
        return self._name

class Buzzer:
    def __init__(self, pin):
        self._pin = machine.Pin(pin)
        return
    
    def warn(self):
        _thread.start_new_thread(self._warn, [3])
        return
        
    def _warn(self, i):
        for x in range(0, i):
            pwn = machine.PWM(self._pin, freq = 554)
            utime.sleep_ms(100)
            pwn = machine.PWM(self._pin, freq=440)
            utime.sleep_ms(400)
        pwn.deinit()
        return

    def alt(self):
        _thread.start_new_thread(self._alt, [1])
        return
        
    def _alt(self, i):
        for x in range(0, i):
            pwn = machine.PWM(self._pin, freq=440)
            utime.sleep_ms(400)
            pwn.deinit()
            utime.sleep_ms(100)
        pwn.deinit()
        return

        
