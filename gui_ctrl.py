# gui_ctrl.py
import lvgl as lv
from micropython import const
import utime
import lvesp32
import TFTFeatherWing as tftwing
import laser_mcu
import th_ctrl
import gc
import laser_ctrl

DISP_BUF_SIZE = const(9600)

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

class LaserGui:
    def __init__(self):
        # LVGL
        lv.init()
        lv.task_core_init()

        # MCU Control
        self._laser_mcu = laser_mcu.LaserMCU()

        # TFT and TS driver
        self._tft = tftwing.TFTFeatherWing()
        self._tft.init()

        # TH sensor
        self._th_ctrl = th_ctrl.THCtrl()

        # Laser Measuring Control
        self._laser = laser_ctrl.LaserCtrl()
        self._laser.on()

        # Load Time
        if self._laser_mcu.is_connected():
            self._laser_mcu.set_time_ntp()
        else:
            self._laser_mcu.load_time()

        self._laser_mcu.set_creation_time()

        # Register display buffer, driver and input device driver
        self._register_disp_drv()
        self._register_indev_drv()

        # Create screen
        self._load_screen()

        self.start=utime.ticks_us()
        
        # Task to update th
        self._task_update_th = lv.task_create_basic()
        lv.task_set_cb(self._task_update_th, self._update_th_cb)
        lv.task_set_period(self._task_update_th, 1000)
        lv.task_set_prio(self._task_update_th, lv.TASK_PRIO.MID)

        # Task to update time
        self._task_update_time = lv.task_create_basic()
        lv.task_set_cb(self._task_update_time, self._update_time_cb)
        lv.task_set_period(self._task_update_time, 1000)
        lv.task_set_prio(self._task_update_time, lv.TASK_PRIO.MID)
        
        # Task to save time to flash
        self._task_save_time = lv.task_create_basic()
        lv.task_set_cb(self._task_save_time, self._save_time_cb)
        lv.task_set_period(self._task_save_time, 60000)
        lv.task_set_prio(self._task_save_time, lv.TASK_PRIO.MID)

        # Task to gc collect
        self._task_gc_collect = lv.task_create_basic()
        lv.task_set_cb(self._task_gc_collect, self._gc_collect_cb)
        lv.task_set_period(self._task_gc_collect, 5000)
        lv.task_set_prio(self._task_gc_collect, lv.TASK_PRIO.MID)

        # Task to update output
        self._task_update_laser_output = lv.task_create_basic()
        lv.task_set_cb(self._task_update_laser_output, self._update_laser_output_cb)
        lv.task_set_period(self._task_update_laser_output, 1000)
        lv.task_set_prio(self._task_update_laser_output, lv.TASK_PRIO.MID)
        
        # Task to get laser output
        self._task_read_laser = lv.task_create_basic()
        lv.task_set_cb(self._task_read_laser, self._read_laser_cb)
        lv.task_set_period(self._task_read_laser, 1000)
        lv.task_set_prio(self._task_read_laser, lv.TASK_PRIO.MID)

        return

    def _register_disp_drv(self):
        # Init buffer
        self._disp_buf = lv.disp_buf_t()
        self._buf_1 = bytearray(DISP_BUF_SIZE)
        self._buf_2 = bytearray(DISP_BUF_SIZE)
        self._disp_drv = lv.disp_drv_t()
        lv.disp_buf_init(self._disp_buf, self._buf_1, self._buf_2, DISP_BUF_SIZE//4)

        # Register display driver
        lv.disp_drv_init(self._disp_drv)
        self._disp_drv.buffer = self._disp_buf
        self._disp_drv.flush_cb = self._tft.flush
        self._disp_drv.hor_res = 480
        self._disp_drv.ver_res = 320
        self._disp = lv.disp_drv_register(self._disp_drv)
        return

    def _register_indev_drv(self):
        # Register touch screen driver
        self._indev_drv = lv.indev_drv_t()
        lv.indev_drv_init(self._indev_drv)
        self._indev_drv.type = lv.INDEV_TYPE.POINTER
        self._indev_drv.read_cb = self._tft.read
        self._indev = lv.indev_drv_register(self._indev_drv)
        return

    def _load_screen(self):
        # Create screen obj
        th=lv.theme_night_init(210, lv.font_roboto_16)
        lv.theme_set_current(th)
        self._scr = lv.obj()
        
        # Add header and body
        self._header = GuiHeader(self._scr, 0, 0)
        self._sidebar = GUISidebar(self._scr, self._header.get_height(), 0)
        self._body = GuiLaserMain(self._scr, self._header.get_height(), self._sidebar.get_width())
        
        lv.scr_load(self._scr)
        
        return

    def call_task_handler(self):
        print("LaserGui call_task_handler")
        lv.task_handler()
        return

    def _update_time_cb(self, data):
        if self._laser_mcu.is_connected():
            self._header.set_left_text(self._laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        else:
            self._header.set_left_text(self._laser_mcu.get_local_time_str())
        return

    def _update_th_cb(self, data):
        self._header.set_right_text(self._th_ctrl.get_th_str())
        return
    
    def _update_laser_output_cb(self, data):
        self._body.set_text(self._laser.get_values_str())
        return

    def _read_laser_cb(self, data):
        self._laser.get_phrase_pvs()
        self.start=utime.ticks_us()
        return
    
    def _gc_collect_cb(self, data):
        gc.collect()
        return

    @timed_function
    def _save_time_cb(self, data):
        self._laser_mcu.save_time()
        return
    
class TextBtn(lv.btn):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.symbol = lv.label(self)
        
        self.label = lv.label(self)
        self.label.set_text(text)
        self.set_fit(lv.FIT.TIGHT)
        return
    
class GuiHeader(lv.cont):
    def __init__(self, scr, x_pos, y_pos):
        super().__init__(scr)
        self._left_text = lv.label(self._header)
        self._left_text.set_text(" ")
        self._left_text.align(self._header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        
        self._right_text = lv.label(self._header)
        self._right_text.set_text(" ")
        self._right_text.align(self._header, lv.ALIGN.IN_LEFT_MID, 10, 0)

        self.set_fit2(lv.FIT.FLOOD, lv.FIT.TIGHT)
        self.set_pos(x_pos, y_pos)
        return

    def set_left_text(self, text):
        self._left_text.set_text(text)
        self._left_text.align(self, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        return

    def set_right_test(self, text):
        self._right_text.set_text(text)
        self._right_text.align(self, lv.ALIGN.IN_RIGHT_MID, 10, 0)
        return

class GuiSidebar(lv.cont):
    def __init__(self, scr, x_pos, y_pos):
        super().__init__(scr)
        
        self.set_fit2(lv.FIT.TIGHT, lv.FIT.NONE)
        self.set_height(scr.get_height() - y_pos)
        self.set_pos(x_pos, y_pos)

        self._btn = TextBtn("Test")
        return

class GuiLaserMain(lv.cont):
    def __init__(self, scr, x_pos, y_pos):
        super().__init__(scr)
        
        self._laser_output = lv.label(self)
        self._laser_output.set_text("Waiting Output")
        
        self.set_fit2(lv.FIT.NONE, lv.FIT.NONE)
        self.set_width(scr.get_width() - x_pos)
        self.set_height(scr.get_height() - y_pos)
        self._body.set_pos(x_pos, y_pos)
        return

    def set_text(self, text):
        self._laser_output.set_text(text)
        return
