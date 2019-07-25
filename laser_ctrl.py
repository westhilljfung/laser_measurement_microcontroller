from machine import UART
import utime
from micropython import const

DEFAULT_PANEL_WIDTH_MM = const(1245)
MAX_AMP_NUM = const(4)

class LaserCtrl:
    def __init__(self):
        self._laser = UART(2)
        self._laser.init(baudrate=38400)
        self._amp_stack = ((00,01),(02,03))
        self._read_buf = bytearray("0"*38)
        self._pv = [0.0] * 4
        self._laser_on = True
        self.get_pvs()
        self.get_pvs()
        print("init laser ctrl")

    def reset_all(self):
        self.write_all("005","0")
        self.write_all("005","1")
        self.write_all("065","+99.999")
        self.write_all("066","-99.999")

    def get_values_str(self):
        pv_str = ""
        for pv in self._pv:
            pv_str += ("%07.3f " % pv)
        return pv_str

    def get_phrase_pvs(self):
        self._laser.write("M0\r\n")
        for amp in range(0,4):
            self._pv[amp] = float(self._read_buf[amp*8+3:amp*8+10])
        while not self._laser.any():
            utime.sleep_us(1)
        self._laser.readinto(self._read_buf)
    
    def get_pvs(self):
        self._laser.write("M0\r\n")
        while not self._laser.any():
            utime.sleep_us(1)
        self._laser.readinto(self._read_buf)

    def write_all(self, cmd, data):
        start = utime.ticks_us()
        self._laser.write("AW,%s,%s\r\n" % (cmd, data))
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        while not self._laser.any():
            utime.sleep_us(1)
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        print(self._laser.readline())
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

    def write_amp(self, amp, cmd, data):
        start = utime.ticks_us()
        self._laser.write("SW,%02d,%s,%s\r\n" % (amp, cmd, data))
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        while not self._laser.any():
            utime.sleep_us(1)
        print(utime.ticks_diff(utime.ticks_us(), start))
        start = utime.ticks_us()
        print(self._laser.readline())
        print(utime.ticks_diff(utime.ticks_us(), start))

    def toggle(self):
        if self._laser_on:
            self.off()
            self._laser_on = False
        else:
            self.on()
            self._laser_on = True

    def off(self):
        self.write_all("100", "1")

    def on(self):
        self.write_all("100", "0")
