"""laser_ctrl.py

Controller for the laser sensor

*Author(s): Joshua Fung
2019-08-09
"""
import utime
import array
import ujson
import _thread

from machine import UART
from micropython import const

from laser_mcu import TIME_ZONE_OFFSET, SD_FILE


DEFAULT_PANEL_WIDTH_MM = const(1245)
MAX_AMP_NUM = const(4)
READ_BUF_SIZE = const(36)
MAX_PANEL_DATA = const(600)
PANEL_WAIT_TIMEOUT = const(30000)

_ZERO_SHIFT = "001"
_RESET = "003"
_INITIAL_RESET = "005"
_HIGH_VALUE = "065"
_LOW_VALUE = "066"
_SHIFT_VALUE = "067"
_LASER_STOP = "100"
_ZERO_SHIFT_MEM = "152"
_POWER_SAVE = "155"


def timed_function(f, *args, **kwargs):
    """Time function

    Time a function using @timed_function decorator
    """
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
        self._session_file = None
        self.get_phrase_pvs()
        return

    def reset_all(self):
        self.write_all(_INITIAL_RESET,"0")
        self.write_all(_INITIAL_RESET,"1")
        self.write_all(_HIGH_VALUE,"+99.999")
        self.write_all(_LOW_VALUE,"-99.999")

    def get_values_str(self):
        pv_str = ""
        for pv in self._pvs:
            pv_str += ("% 07.3f " % pv)
        pv_str += '\n'
        for cal in self._cals:
            pv_str += ("% 07.3f " % cal)
        return pv_str

    def set_cal_init(self, num, ref):
        # Without the _ZERO_SHIFT_MEM shift will be forgotten after power cycle
        self.write_amp(num*2 + 1, _ZERO_SHIFT_MEM, "1")
        self.write_amp(num*2 + 1, _SHIFT_VALUE, "%+07.3f" % (ref - self._pvs[num*2]))
        self.write_amp(num*2 + 1, _ZERO_SHIFT, "0")
        self.write_amp(num*2 + 1, _ZERO_SHIFT, "1")
        self.write_amp(num*2 + 1, _ZERO_SHIFT_MEM, "0")
        return

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
                return
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
        self.write_all(_LASER_STOP, "1")
        self.write_all(_POWER_SAVE, "2")

    def on(self):
        self.write_all(_LASER_STOP, "0")
        self.write_all(_POWER_SAVE, "0")

    def start_session(self, material, thickness):
        self._session = MeasurementSession(material, thickness)
        self._session_file = open(SD_FILE + "/" + self._session.get_filename(), "a+")
        self._write_session_file()
        return

    def _write_session_file(self):
        start = utime.ticks_us()
        self._session_file.write("Time: ")
        ujson.dump(utime.localtime(self._session._start_time), self._session_file)
        self._session_file.write("\nMaterial: ")
        self._session_file.write(self._session._material)
        self._session_file.write("\nThickness: ")
        self._session_file.write(self._session._thickness)
        self._session_file.write("\n\n")
        delta = utime.ticks_diff(utime.ticks_us(), start)
        print("Write header: %d" % delta)
        return

    def end_session(self):
        self._session = None
        self._session_file.close()
        self._session_file = None
        return

    def wait_for_panel(self, panel, thickness, lock):
        """A blocking function to wait for panel to read"""
        lock.acquire()
        cals = self.get_phrase_pvs()
        if cals[0] > 0 or cals[1] > 0:
            panel.err = RuntimeError("Panel already under measure")
            lock.release()
            return
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
                        except IndexError as err:
                            panel.err = err
                            lock.release()
                            return
                self._cal_move_mean(panel, thickness)
                self._write_panel(panel)
                break
        lock.release()
        return

    def _write_panel(self, panel):
        print("ID: %d" % self._session.count, file = self._session_file)
        # json dump is faster than any format print
        #start = utime.ticks_us()
        ujson.dump(panel._time[0:panel._data_num], self._session_file)
        self._session_file.write("\n")
        ujson.dump(panel._data1[0:panel._data_num], self._session_file)
        self._session_file.write("\n")
        ujson.dump(panel._data2[0:panel._data_num], self._session_file)
        self._session_file.write("\n")
        self._session_file.flush()
        #delta = utime.ticks_diff(utime.ticks_us(), start)
        #print("Write with json with slice and write newlinw: %d" % delta)
        return

    def _cal_move_mean(self, panel, thickness):
        filter_size = panel._data_num // 20
        panel.size = panel._data_num - filter_size
        panel.size2 = panel._data_num - filter_size//2
        for i in range(0, panel.size):
            sum1 = 0
            sum2 = 0
            n = filter_size
            for j in range(0, filter_size):
                if (panel._data1[i + j] > thickness + 1
                    or panel._data1[i + j] < thickness - 1
                    or panel._data2[i + j] > thickness + 1
                    or panel._data2[i + j] < thickness - 1):
                    n -= 1
                    continue
                sum1 += panel._data1[i + j]
                sum2 += panel._data2[i + j]
            # There is a chance n will be zero
            if n > 0:
                panel._cdata1[i] = sum1 / n
                panel._cdata2[i] = sum2 / n
            else:
                panel._cdata1[i] = 0
                panel._cdata2[i] = 0
        return


class MeasurementSession:

    def __init__(self, material, thickness):
        self._start_time = utime.time()
        self._material = material
        self._thickness = thickness
        self.count = 0
        self.panel = Panel()
        return

    def get_filename(self):
        st = utime.localtime(self._start_time)
        str_ = (str(st[0])
                + "-"
                + str(st[1])
                + "-"
                + str(st[2])
                + "-"
                + str(st[3])
                + "-"
                + str(st[4])
                + "_"
                + self._material
                + "_"
                + self._thickness
                + ".txt"
        )
        return str_

    def __str__(self):
        st = utime.localtime(self._start_time - TIME_ZONE_OFFSET)
        str_ = ("Session started: "
                + str(st[0])
                + " "
                + str(st[1])
                + " "
                + str(st[2])
                + " "
                + str(st[3])
                + " "
                + str(st[4])
                + "\nPanel Count: "
                + str(self.count)
                + " Material: "
                + self._material
                + " Thickness:"
                + self._thickness
                + "mm"
        )
        return str_

    def new_panel(self):
        self.count += 1
        return self.panel, float(self._thickness)

    def re_panel(self):
        return self.panel, float(self._thickness)


class Panel:

    def __init__(self):
        self._creation = utime.localtime()
        self.err = None
        self._time = array.array('l', [0] * MAX_PANEL_DATA)
        self._data1 = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._data2 = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._cdata1 = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._cdata2 = array.array('f', [0.0] * MAX_PANEL_DATA)
        self._data_num = 0
        self.size = 0
        self.size2 = 0
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
