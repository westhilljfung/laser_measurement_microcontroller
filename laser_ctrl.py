from machine import UART
import utime

class LaserCtrl:
    def __init__(self):
        self._laser = UART(2)
        self._laser.init(baudrate=38400)
        self._amp_stack = ((00,01),(02,03))

    def laser_reset(self):
        for laser_pair in self._amp_stack:
            for amp in laser_pair:
                self._laser.write("SW,%02d,005,0\r\n" % amp)
                while not self._laser.any():
                    utime.sleep_us(1)
                print(laser.readline())
                self._laser.write("SW,%02d,005,1\r\n" % amp)
                while not self._laser.any():
                    utime.sleep_us(1)
                print(laser.readline())
