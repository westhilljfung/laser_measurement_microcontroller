import lvgl as lv
import utime
import lvesp32
import TFTFeatherWing as tftwing
from gui import lasermcu

class LaserGui:
    def __init__(self):
        # Initialize TFT Feather Wing Display and Touch Screen
        lv.init()
        
        self.tft = tftwing.TFTFeatherWing()
        self.tft.init()

        self.laser_mcu = lasermcu.LaserMCU()
        
        self.disp_buf = lv.disp_buf_t()
        self.buf_1 = bytearray(480*20)
        self.buf_2 = bytearray(480*20)
        self.disp_drv = lv.disp_drv_t()
        self.disp = None

        self.indev_drv = lv.indev_drv_t()
        self.indev = None

        self.register_disp_drv()
        self.register_indev_drv()
        self.load_screen()

    def register_disp_drv(self):
        # Init buffer
        # TODO don't use len()
        lv.disp_buf_init(self.disp_buf, self.buf_1, self.buf_2, len(self.buf_1)//4)

        # Register display driver
        lv.disp_drv_init(self.disp_drv)
        self.disp_drv.buffer = self.disp_buf
        self.disp_drv.flush_cb = self.tft.flush
        self.disp_drv.hor_res = 480
        self.disp_drv.ver_res = 320
        self.disp = lv.disp_drv_register(self.disp_drv)
        return

    def register_indev_drv(self):
        # Register touch screen driver
        lv.indev_drv_init(self.indev_drv)
        self.indev_drv.type = lv.INDEV_TYPE.POINTER
        self.indev_drv.read_cb = self.tft.read
        self.indev = lv.indev_drv_register(self.indev_drv)
        return

    def load_screen(self):
        # Create screen obj
        th=lv.theme_night_init(210, lv.font_roboto_16)
        lv.theme_set_current(th)
        scr = lv.obj()

        # Add header
        self.header = lv.cont(scr)
        self.header.set_width(480)
        self.sym = lv.label(self.header)
    
        self.sym.set_text(self.laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        header_text = lv.label(self.header)
        header_text.set_text("T: ")

        header_text.align(self.header, lv.ALIGN.IN_LEFT_MID, 10, 0)

        self.sym.align(self.header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        self.header.set_fit2(lv.FIT.NONE, lv.FIT.TIGHT)
        self.header.set_pos(0, 0)
        
        lv.scr_load(scr)
        return

    def update_screen(self):
        if self.laser_mcu.is_connected():
            self.sym.set_text(self.laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        else:
            self.sym.set_text(self.laser_mcu.get_local_time_str())
        self.sym.align(self.header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        return
        
