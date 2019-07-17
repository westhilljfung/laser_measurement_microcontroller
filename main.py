import lvgl as lv
import utime

import lvesp32

import TFTFeatherWing as tftWing

lv.init()

tft = tftWing.TFTFeatherWing()
tft.init()

# Init and register buffer for disp 
disp_buf1 = lv.disp_buf_t()
buf1_1 = bytes(480*10)
lv.disp_buf_init(disp_buf1,buf1_1, None, len(buf1_1)//4)
disp_drv = lv.disp_drv_t()
lv.disp_drv_init(disp_drv)

disp_drv.buffer = disp_buf1
disp_drv.flush_cb = tft.flush
disp_drv.hor_res = 480
disp_drv.ver_res = 320
lv.disp_drv_register(disp_drv)

# Attach input touch screen
indev_drv = lv.indev_drv_t()
lv.indev_drv_init(indev_drv)
indev_drv.type = lv.INDEV_TYPE.POINTER
indev_drv.read_cb = tft.read
lv.indev_drv_register(indev_drv)

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

# Load the screen
lv.scr_load(scr)
print("Post Load screen")

while(True):
    print(str(utime.localtime()))
    sym.set_text(lv.SYMBOL.WIFI + " " + str(utime.localtime()))
    utime_sleep_ms(50)


