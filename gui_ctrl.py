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

        # Task to update header, time and th value
        self._task_update_header = lv.task_create_basic()
        lv.task_set_cb(self._task_update_header, self._update_header_cb)
        lv.task_set_period(self._task_update_header, 1000)
        lv.task_set_prio(self._task_update_header, lv.TASK_PRIO.MID)

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

        # Task to get laser output
        self._task_update_laser_output = lv.task_create_basic()
        lv.task_set_cb(self._task_update_laser_output, self._update_laser_output_cb)
        lv.task_set_period(self._task_update_laser_output, 5)
        lv.task_set_prio(self._task_update_laser_output, lv.TASK_PRIO.MID)

        # Make task to run if not yet
        lv.task_ready(self._task_update_header)
        lv.task_ready(self._task_save_time)
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
        self._header = lv.cont(self._scr)
        self._body = lv.cont(self._scr)
        
        self._sym = lv.label(self._header)

        self._sym.set_text(self._laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        self._header_text = lv.label(self._header)
        self._header_text.set_text(self._th_ctrl.get_th_str())
        self._header_text.align(self._header, lv.ALIGN.IN_LEFT_MID, 10, 0)

        self._sym.align(self._header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        self._header.set_fit2(lv.FIT.FLOOD, lv.FIT.TIGHT)
        self._header.set_pos(0, 0)

        self._laser_output = lv.label(self._body)
        self._laser_output.set_text("Waiting Output")
        
        self._body.set_fit2(lv.FIT.FLOOD, lv.FIT.NONE)
        self._body.set_height(self._scr.get_height() - self._header.get_height())
        self._body.set_pos(0, self._header.get_height())

        lv.scr_load(self._scr)
        
        return

    def call_task_handler(self):
        print("LaserGui call_task_handler")
        lv.task_handler()
        return

    def _update_screen(self):
        if self._laser_mcu.is_connected():
            self._sym.set_text(self._laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        else:
            self._sym.set_text(self._laser_mcu.get_local_time_str())
        self._sym.align(self._header, lv.ALIGN.IN_RIGHT_MID, -10, 0)

        self._header_text.set_text(self._th_ctrl.get_th_str())
        self._header_text.align(self._header, lv.ALIGN.IN_LEFT_MID, 10, 0)
        
        self._laser_output.set_text(self._laser.get_values_str())
        return

    def _update_laser_output_cb(self, data):
        self._laser.get_phrase_pvs()
        return
    
    def _gc_collect_cb(self, data):
        gc.collect()
        return

    def _update_header_cb(self, data):
        self._update_screen()
        return

    def _save_time_cb(self, data):
        self._laser_mcu.save_time()
        return
