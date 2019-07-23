from machine import UART
import utime
from micropython import const

DEFAULT_PANEL_WIDTH_MM = const(1245)

class LaserCtrl:
    def __init__(self):
        self._laser = UART(2)
        self._laser.init(baudrate=38400)
        self._amp_stack = ((00,01),(02,03))
        self.get_all_pv()

    def reset_all(self):
        self.write_all("005","0")
        self.write_all("005","1")
        
    def get_all_pv(self):
        start = utime.ticks_us()
        self._laser.write("M0\r\n")
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        while not self._laser.any():
            utime.sleep_us(1)
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        print(self._laser.readline())
        print(utime.ticks_diff(utime.ticks_us(), start))

    def write_all(self, cmd, data):
        start = utime.ticks_us()
        self._laser.write("AW,%s,%s\r\n" % (cmd, data))
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        while not self._laser.any():
            utime.sleep_us(1)
        print(utime.ticks_diff(utime.ticks_us(), start)) 
        
    def read_all(self, cmd):
        for laser_pair in self._amp_stack:
            for amp in laser_pair:
                start = utime.ticks_us()
                self._laser.write("SR,%02d,%s\r\n" % (amp, cmd))
                print(utime.ticks_diff(utime.ticks_us(), start))
                start = utime.ticks_us()
                while not self._laser.any():
                    utime.sleep_us(1)
                print(utime.ticks_diff(utime.ticks_us(), start))  
                start = utime.ticks_us()
                print(self._laser.readline())
                print(utime.ticks_diff(utime.ticks_us(), start))
