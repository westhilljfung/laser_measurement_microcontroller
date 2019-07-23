from machine import UART
import utime

class LaserCtrl:
    def __init__(self):
        self._laser = UART(2)
        self._laser.init(baudrate=38400)
        self._amp_stack = ((00,01),(02,03))
        self.get_all_pv()

    def reset_all(self):
        for laser_pair in self._amp_stack:
            for amp in laser_pair:
                start = utime.ticks_us()
                self._laser.write("SW,%02d,005,0\r\n" % amp)
                print(utime.ticks_diff(utime.ticks_us(), start))
                start = utime.ticks_us()
                while not self._laser.any():
                    utime.sleep_us(1)
                print(utime.ticks_diff(utime.ticks_us(), start))  
                start = utime.ticks_us()
                print(self._laser.readline())
                print(utime.ticks_diff(utime.ticks_us(), start))
                start = utime.ticks_us()
                self._laser.write("SW,%02d,005,1\r\n" % amp)
                print(utime.ticks_diff(utime.ticks_us(), start))
                start = utime.ticks_us()
                while not self._laser.any():
                    utime.sleep_us(1)
                print(utime.ticks_diff(utime.ticks_us(), start))
                start = utime.ticks_us()
                print(self._laser.readline())
                print(utime.ticks_diff(utime.ticks_us(), start))

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

    def read__all(self, cmd):
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
