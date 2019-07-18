import lvgl as lv
import utime
import lvesp32
import TFTFeatherWing as tftwing

lv.init()

class LaserGui:
    def __init__(self):
        # Initialize TFT Feather Wing Display and Touch Screen
        self.tft = tftwing.TFTFeatherWing()
        self.tft.init()

        self.disp_buf = lv.disp_buf_t()
        self.buf_1 = bytearray(480*20)
        self.disp_drv = lv.disp_drv_t()
        self.disp = None

        self.indev_drv = lv.indev_drv_t()
        self.indev = None

        register_disp_drv()
        register_indev_drv()
        load_screen()

    def register_disp_drv(self):
        # Init buffer
        lv.disp_buf_init(self.disp_buf, self.buf_1, None, len(buf_1)//4)

        # Register display driver
        lv.disp_drv_init(self.disp_drv)
        disp_drv.buffer = disp_buf
        disp_drv.flush_cb = self.tft.flush
        disp_drv.hor_res = 480
        disp_drv.ver_res = 320
        self.disp = lv.disp_drv_register(disp_drv)
        return

    def register_indev_drv(self):
        # Register touch screen driver
        lv.indev_drv_init(self.indev_drv)
        indev_drv.type = lv.INDEV_TYPE.POINTER
        indev_drv.read_cb = self.tft.read
        self.indev = lv.indev_drv_register(indev_drv)
        return

    def load_screen(self):
        # Create screen obj
        th=lv.theme_night_init(210, lv.font_roboto_16)
        lv.theme_set_current(th)
        scr = lv.obj()

        # Add header
        header = lv.cont(scr)
        header.set_width(480)
        sym = lv.label(header)
        sym.set_text(lv.SYMBOL.WIFI + " " + str(utime.localtime()))
        header_text = lv.label(header)
        header_text.set_text("T: ")

        header_text.align(header, lv.ALIGN.IN_LEFT_MID, 10, 0)

        sym.align(header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        header.set_fit2(lv.FIT.NONE, lv.FIT.TIGHT)
        header.set_pos(0, 0)
        
        lv.scr_load(scr)
        return
