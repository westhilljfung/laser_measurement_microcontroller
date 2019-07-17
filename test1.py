# init

import lvgl as lv
lv.init()

class driver:       
    def init_gui(self):

        import lvesp32
        import TFTFeatherWing as tftWing

        # Initialize ILI9341 display

        tft = tftWing.TFTFeatherWing()
        tft.init()

        # Register display driver 

        disp_buf = lv.disp_buf_t()
        buf_1 = bytearray(480*10)
        buf_2 = bytearray(480*10)
        lv.disp_buf_init(disp_buf, buf_1, buf_2, 480*10)

        disp_drv = lv.disp_drv_t()
        lv.disp_drv_init(disp_drv)
        disp_drv.buffer = disp_buf
        disp_drv.flush_cb = tft.flush
        disp_drv.hor_res = 480
        disp_drv.ver_res = 320
        lv.disp_drv_register(disp_drv)

        # Register raw resistive touch driver
        indev_drv = lv.indev_drv_t()
        lv.indev_drv_init(indev_drv) 
        indev_drv.type = lv.INDEV_TYPE.POINTER;
        indev_drv.read_cb = tft.read;
        lv.indev_drv_register(indev_drv);

drv = driver()
drv.init_gui()

# Animation helper class

class Anim(lv.anim_t):
    def __init__(self, obj, val, size, exec_cb, path_cb, time=500, playback = False, ready_cb=None):
        super().__init__()
        lv.anim_init(self)
        lv.anim_set_time(self, time, 0)
        lv.anim_set_values(self, val, val+size)
        try:
            lv.anim_set_exec_cb(self, obj, exec_cb)
        except TypeError:
            lv.anim_set_custom_exec_cb(self, exec_cb)
        lv.anim_set_path_cb(self, path_cb )
        if playback: lv.anim_set_playback(self, 0)
        if ready_cb: lv.anim_set_ready_cb(self, ready_cb)
        lv.anim_create(self)

# An animated chart

class AnimatedChart(lv.chart):
    def __init__(self, parent, val, size):            
        super().__init__(parent)
        self.val = val
        self.size = size
        self.max = 2000
        self.min = 500
        self.factor = 100
        self.anim_phase1()

    def anim_phase1(self):
        Anim(
            self, 
            self.val, 
            self.size, 
            lambda a, val: self.set_range(0, val), 
            lv.anim_path_ease_in, 
            ready_cb=lambda a:self.anim_phase2(),
            time=(self.max * self.factor) // 100)

    def anim_phase2(self):
        Anim(
            self, 
            self.val+self.size, 
            -self.size, 
            lambda a, val: self.set_range(0, val), 
            lv.anim_path_ease_out, 
            ready_cb=lambda a:self.anim_phase1(),
            time=(self.min * self.factor) // 100)

# Create the chart

scr = lv.obj()
chart = AnimatedChart(scr, 100, 1000)
chart.set_width(scr.get_width() - 100)
chart.align(scr, lv.ALIGN.CENTER, 0, 0)
series1 = chart.add_series(lv.color_hex(0xFF0000))
chart.set_type(chart.TYPE.POINT | chart.TYPE.LINE)
chart.set_series_width(3)
chart.set_range(0,100)
chart.init_points(series1, 10)
chart.set_points(series1, [10,20,30,20,10,40,50,90,95,90])
chart.set_x_tick_texts('a\nb\nc\nd\ne', 2, lv.chart.AXIS.DRAW_LAST_TICK)
chart.set_x_tick_length(10, 5)
chart.set_y_tick_texts('1\n2\n3\n4\n5', 2, lv.chart.AXIS.DRAW_LAST_TICK)
chart.set_y_tick_length(10, 5)
chart.set_div_line_count(3, 3)
chart.set_margin(30)

# Create a slider that controls the chart animation speed

def on_slider_changed(self, obj=None, event=-1):
    chart.factor = slider.get_value()

slider = lv.slider(scr)
slider.align(chart, lv.ALIGN.OUT_RIGHT_TOP, 10, 0)
slider.set_width(30)
slider.set_height(chart.get_height())
slider.set_range(10, 200)
slider.set_value(chart.factor, 0)
slider.set_event_cb(on_slider_changed)

# Load the screen

lv.scr_load(scr)

