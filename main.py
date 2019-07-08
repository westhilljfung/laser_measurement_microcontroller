import lvgl as lv
from SI7021 import SI7021
lv.init()
import utime
# Import ESP32 driver 

import lvesp32

#Import ILI9341, initialize it and register it with LittlevGL

import HX8357 as hx

th_sensor = SI7021(22,23)

d = hx.display(mhz=24, miso=19, mosi=18, clk=5, cs=15, dc=33, rst=4, backlight=13)
d.init()
disp_buf1 = lv.disp_buf_t()
buf1_1 = bytes(480*10)
lv.disp_buf_init(disp_buf1,buf1_1, None, len(buf1_1)//4)
disp_drv = lv.disp_drv_t()
lv.disp_drv_init(disp_drv)
disp_drv.buffer = disp_buf1
disp_drv.flush_cb = d.flush
disp_drv.hor_res = 480
disp_drv.ver_res = 320
lv.disp_drv_register(disp_drv)

th=lv.theme_night_init(210, lv.font_roboto_16)
lv.theme_set_current(th)
scr = lv.obj()
header = lv.cont(scr)
header.set_width(480)
sym = lv.label(header)
sym.set_text(lv.SYMBOL.WIFI + " " + str(utime.localtime()))
header_text = lv.label(header)
header_text.set_text("T: " + str(th_sensor.read_temperature) + " R: " + str(th_sensor.read_relative_humidity))

header_text.align(header, lv.ALIGN.IN_LEFT_MID, 10, 0)

sym.align(header, lv.ALIGN.IN_RIGHT_MID, -10, 0)
header.set_fit2(lv.FIT.NONE, lv.FIT.TIGHT)
header.set_pos(0, 0)

# Load the screen

lv.scr_load(scr)

while True:
    header_text.set_text("T: " + str(th_sensor.read_temperature) + " R: " + str(th_sensor.read_relative_humidity))
    sym.set_text(lv.SYMBOL.WIFI + " " + str(utime.localtime()))
    utime.sleep(0.5)

