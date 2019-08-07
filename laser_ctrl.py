from machine import UART
import utime
from micropython import const
import array
import _thread

DEFAULT_PANEL_WIDTH_MM = const(1245)
MAX_AMP_NUM = const(4)
READ_BUF_SIZE = const(36)
MAX_PANEL_DATA = const(700)
PANEL_WAIT_TIMEOUT = const(30000)

"""
Timing function

Use @timed_function decorator
"""
def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

class LaserCtrl:
    def __init__(self):
        self._laser = UART(2)
        self._laser.init(baudrate=38400)
        self._read_buf = bytearray("0" * READ_BUF_SIZE)
        self._pvs = array.array('f', [0.0] * MAX_AMP_NUM)
        self._cals = array.array('f', [0.0] * (MAX_AMP_NUM // 2))
        self._laser_on = True
        self._session = None
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
        # Without the zero shift value memory function "152" the shift will be forgotten after power cycle
        self.write_amp(num*2+1, "067", "%+07.3f" % (ref - self._pvs[num*2]))
        self.write_amp(num*2+1, "001", "0")
        self.write_amp(num*2+1, "001", "1")

    def get_phrase_pvs(self):      
        self._laser.write("M0\r\n")
        while not self._laser.any():
            pass
        self._laser.readinto(self._read_buf)
        for amp in range(0,MAX_AMP_NUM):
            try:
                self._pvs[amp] = float(self._read_buf[amp*8+3:amp*8+10])
            except ValueError:
                print(self._read_buf.decode("ascii"))
                raise ValueError
            if not amp % 2:
                self._cals[amp//2] = self._pvs[amp]
            else:
                self._cals[amp//2] += self._pvs[amp]
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
            print(self._laser.readline())

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

    def start_session(self, material, thickness):
        self._session = MeasurementSession(material, thickness)
        return

    def end_session(self):
        self._session = None
        return

    """
    A blocking function to wait for panel to read
    """
    def wait_for_panel(self, panel, lock):
        lock.acquire()
        cals = self.get_phrase_pvs()
        if cals[0] > 0 or cals[1] > 0:
            lock.release()
            raise RuntimeError("Panel already under measure")
        while True:
            cals = self.get_phrase_pvs()
            if cals[0] < 0 or cals[1] < 0:
                continue
            else:
                panel.start_measure(cals)
                while True:
                    cals = self.get_phrase_pvs()
                    if cals[0] < 0 or cals[1] < 0:
                        break
                    else:
                        try:
                            panel.add_points(cals)
                        except IndexError:
                            break
                break
        lock.release()
        return

class MeasurementSession:
    def __init__(self, material, thickness):
        self._start_date_time = utime.localtime()
        self._material = material
        self._thickness = thickness
        self._index = -1
        self._panel = Panel()
        return

    def __str__(self):
        data_str = str(self._start_date_time) + "\n " + str(self._index) + " " + str(self._material) + " " + str(self._thickness)
        return data_str

    def new_panel(self):
        self._index += 1
        return self._panel
    
class Panel:
    def __init__(self):
        self._creation = utime.localtime()
        self._time = array.array('l', [0] * MAX_PANEL_DATA)
        self._data1 = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._data2 = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._data_num = 0
        return

    def start_measure(self, points):
        self._t_start = utime.ticks_us()
        self._data_num = 0
        self.add_points(points)
        return

    def add_points(self, points):
        try:
            self._time[self._data_num] = utime.ticks_diff(utime.ticks_us(), self._t_start)
            self._data1[self._data_num] = points[0]
            self._data2[self._data_num] = points[1]
        except IndexError:
            raise
        self._data_num += 1
