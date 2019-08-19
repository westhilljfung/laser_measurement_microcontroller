"""laser_mcu.py

This is a Micropython driver for the Laser Measurement Controller

*Author(s): Joshua Fung
July 30, 2019
"""
import network
import _thread
import utime
import uos
import ujson
import usocket
import uselect

import ntptime
import machine
from micropython import const

import si7021
from utils import timed_function

_ssid = 'Westhill_2.4G'
_wp2_pass = 'Radoslav13'
TIME_ZONE_OFFSET = const(14400)
WIFI_CON_TIMEOUT = const(30000)
SERVER_ADDR = "192.168.0.22"
SELECT_TIMEOUT = 100
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
            self._wlan.connect(_ssid, _wp2_pass)
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
        et = utime.time()
        dt = utime.localtime()
        temp = self._th_sensor.read_temperature()
        rh = self._th_sensor.read_relative_humidity()
        filename = (
            ("TH-%04d" % dt[0])
            + "_"
            + ("%02d" % dt[1])
            + "_"
            + ("%02d" % dt[2])
            + ".txt"
        )
        try:
            f = open(SD_FILE + "/" + filename, "a+")
        except OSError as err:
            raise
        if f.tell() == 0:
            print("YYYY-MM-DD-HH-MM(RTC)\tTemperature(C)\tHumidity(RH%)", file = f)
            
        print("%04d-%02d-%02d-%02d-%02d\t%0.3f\t\t%0.3f" % (dt[0], dt[1], dt[2], dt[3], dt[4], temp, rh), file = f)
        f.close()
        
        content = ('{"temp":%0.3f,"rh":%0.3f,"e_epoch":%d}' % (temp, rh, et))
        try:
            self._post_json("/th/", content)
        except OSError as err:
            print(OSError, err)
        return
    
    def _post_json(self, path, content):
        s = usocket.socket()
        s.connect((SERVER_ADDR, 8000))
        p = uselect.poll()
        p.register(s)
        for so in p.poll(SELECT_TIMEOUT):
            if so[1] | uselect.POLLOUT:
                size = len(content)
                so[0].send(
                    bytes(
                        (
                            "POST %s HTTP/1.1\r\n"
                            "Host: %s\r\n"
                            "Content-Type: application/json\r\n"
                            "Content-Length: %d\r\n\r\n"
                        )
                        % (path, SERVER_ADDR, size),
                        "utf8"
                    )
                )
                so[0].send(bytes(content, "utf8"))
        for so in p.poll(SELECT_TIMEOUT):
            if (so[1] | uselect.POLLIN):
                ret = so[0].readline()
                if ret.split()[1][0] != 50:
                    so[0].close()
                    raise OSError(ret.decode("utf8"))
        s.close()
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
        dt_str = ("Created: "
                  + str(ct[1])
                  +"-" + str(ct[2])
                  + " "
                  + str(ct[3])
                  + ":"
                  + str(ct[4])
        )
        return dt_str
         
    def get_lt_str(self):
        # TODO Daylight Saving Time
        dt = utime.localtime(utime.time() - TIME_ZONE_OFFSET)

        dt_str = (str(dt[0])
                  + "-"
                  + str(dt[1])
                  + "-" + str(dt[2])
                  + " "
                  + str(int(dt[3]))
                  + ":"
                  + str(dt[4])
                  + ":" + str(dt[5])
        )
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

        
