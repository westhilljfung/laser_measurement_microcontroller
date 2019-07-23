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
        # Initialize TFT Feather Wing Display and Touch Screen
        lv.init()
        
        self._laser_mcu = laser_mcu.LaserMCU()

        self._tft = tftwing.TFTFeatherWing()
        self._tft.init()
        
        if self._laser_mcu.is_connected():
            self._laser_mcu.set_time_ntp()
        else:
            self._laser_mcu.load_time()
            pass
        
        self._laser_mcu.set_creation_time()
            
        self._th_ctrl = th_ctrl.THCtrl()

        #self._laser = laser_ctrl.LaserCtrl()
        #self._laser.reset_all()

        lv.task_core_init()
        print("task1")
        self._task_update_header = lv.task_create_basic()
        lv.task_set_cb(self._task_update_header, self.update_header)
        lv.task_set_period(self._task_update_header, 500)
        lv.task_set_prio(self._task_update_header, lv.TASK_PRIO.MID)
        print("task2")
        
        self._task_save_time = lv.task_create_basic()
        lv.task_set_cb(self._task_save_time, self._save_time)
        lv.task_set_period(self._task_save_time, 60000)
        lv.task_set_prio(self._task_save_time, lv.TASK_PRIO.MID)
        
        print("buffer")
        self._disp_buf = lv.disp_buf_t()
        self._buf_1 = bytearray(DISP_BUF_SIZE)
        self._buf_2 = bytearray(DISP_BUF_SIZE)
        self._disp_drv = lv.disp_drv_t()
        self._disp = None
        
        self._indev_drv = lv.indev_drv_t()
        self._indev = None

        self._register_disp_drv()
        self._register_indev_drv()
        print("load screen")
        self._load_screen()

        print("task ready")
        lv.task_ready(self._task_update_header)
        
        lv.task_ready(self._task_save_time)
        

    def _save_time(self):
        print("save Time")
        self._laser_mcu.save_time()
        
    def _register_disp_drv(self):
        # Init buffer
        # TODO don't use len()
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

        # Add header
        self._header = lv.cont(self._scr)
        self._header.set_width(480)
        self._sym = lv.label(self._header)
    
        self._sym.set_text(self._laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        self._header_text = lv.label(self._header)
        self._header_text.set_text(self._th_ctrl.get_th_str())
        self._header_text.align(self._header, lv.ALIGN.IN_LEFT_MID, 10, 0)

        self._sym.align(self._header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        self._header.set_fit2(lv.FIT.NONE, lv.FIT.TIGHT)
        self._header.set_pos(0, 0)
        
        lv.scr_load(self._scr)
        return
    def _set_datetime_gui(self):
        self._datetime_gui =lv.obj()
        self._cal = lv.calendar(self._datetime_gui)
        lv.scr_load(self._datetime_gui)
        
    def call_task_handler(self):
        lv.task_handler()

    def update_screen(self):
        if self._laser_mcu.is_connected():
            self._sym.set_text(self._laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        else:
            self._sym.set_text(self._laser_mcu.get_local_time_str())
        self._sym.align(self._header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
                                   
        self._header_text.set_text(self._th_ctrl.get_th_str())
        self._header_text.align(self._header, lv.ALIGN.IN_LEFT_MID, 10, 0)
        gc.collect()
        return

    def update_header(self, data):
        #print("Update Header")
        self.update_screen()
        
