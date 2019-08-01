from machine import UART
import utime
from micropython import const
import array

DEFAULT_PANEL_WIDTH_MM = const(1245)
MAX_AMP_NUM = const(4)
READ_BUF_SIZE = const(36)
MAX_PANEL_DATA = const(1200*2)

class LaserCtrl:
    def __init__(self):
        self._laser = UART(2)
        self._laser.init(baudrate=38400)
        self._read_buf = bytearray("0" * READ_BUF_SIZE)
        self._pvs = array.array('f', [0.0] * MAX_AMP_NUM)
        self._cals = array.array('f', [0.0] * (MAX_AMP_NUM // 2))
        self._laser_on = True
        try:
            self.get_phrase_pvs()
        except ValueError:
            pass
        return
    
    def reset_all(self):
        self.write_all("005","0")
        self.write_all("005","1")
        self.write_all("065","+99.999")
        self.write_all("066","-99.999")

    def get_values_str(self):
        pv_str = ""
        for pv in self._pvs:
            pv_str += ("% 07.3f " % pv)

        pv_str += '\n'
        
        for cal in self._cals:
            pv_str += ("% 07.3f " % cal)
        return pv_str

    def set_cal_init(self, num, ref):
        self.write_amp(num*2+1, "067", "%+07.3f" % (ref - self._pvs[num*2]))
        self.write_amp(num*2+1, "001", "0")
        self.write_amp(num*2+1, "001", "1")

    def get_phrase_pvs(self):
        self._laser.write("M0\r\n")
        while not self._laser.any():
            utime.sleep_us(1)
        self._laser.readinto(self._read_buf)
        try:
            for amp in range(0,MAX_AMP_NUM):
                self._pvs[amp] = float(self._read_buf[amp*8+3:amp*8+10])
                if not amp % 2:
                    self._cals[amp//2] = self._pvs[amp]
                else:
                    self._cals[amp//2] += self._pvs[amp]
        except ValueError:
            print(self._read_buf.decode("ascii"))
            raise ValueError
        return self._cals
            
    def write_all(self, cmd, data):
        self._laser.write("AW,%s,%s\r\n" % (cmd, data))
        while not self._laser.any():
            utime.sleep_us(1)
        self._laser.readline()

    def read_all(self, cmd):
        for amp in range(0,MAX_AMP_NUM):
            self._laser.write("SR,%02d,%s\r\n" % (amp, cmd))
            while not self._laser.any():
                utime.sleep_us(1)
            self._laser.readline()

    def write_amp(self, amp, cmd, data):
        self._laser.write("SW,%02d,%s,%s\r\n" % (amp, cmd, data))
        while not self._laser.any():
            utime.sleep_us(1)
        self._laser.readline()

    def off(self):
        self.write_all("100", "1")
        self.write_all("155", "2")

    def on(self):
        self.write_all("100", "0")        
        self.write_all("155", "0")

class Panel:
    def __init__(self, num):
        self._creation = utime.locatime()
        self._data = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._num = num
        return
