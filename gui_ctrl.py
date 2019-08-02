"""
gui_ctrl.py
==========
This is the Controller for the GUI
*Author(s): Joshua Fung
July 30, 2019
"""
import lvgl as lv
from micropython import const
import utime
import lvesp32
import TFTFeatherWing as tftwing
import laser_mcu
import gc
import laser_ctrl

DISP_BUF_SIZE = const(9600)

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

"""
GUI Controller
"""
class LaserGui:
    def __init__(self):
        # init LVGL
        lv.init()
        lv.task_core_init()
        
        # MCU Control
        # For some reason the LaserMCU needs to be init before TFT and TS driver
        # Likely because of the SPI
        self._laser_mcu = laser_mcu.LaserMCU()

        # TFT and TS driver
        # POTENTIAL: move into LaserMcu
        self._tft = tftwing.TFTFeatherWing(tft_mhz=24)
        self._tft.init()

        # Laser Measuring Control
        self._laser = laser_ctrl.LaserCtrl()
        self._laser.off()

        # Load Time
        # TODO: also move into LaserMcu
        try:
            self._laser_mcu.set_time_ntp()
        except OSError as err:
            print("OSError: {0}".format(err))
            self._laser_mcu.load_time()

        self._laser_mcu.set_creation_time()
        

        # Register display buffer, driver and input device driver
        self._register_disp_drv()
        self._register_indev_drv()

        # Create screen
        self._load_screen()
        
        # Task to update th
        # TODO: use one line creation
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

        # Laser off on start
        self._laser.off()

        # Task to update output
        self._task_update_laser_output = lv.task_create_basic()
        lv.task_set_cb(self._task_update_laser_output, self._update_laser_output_cb)
        lv.task_set_period(self._task_update_laser_output, 1000)
        lv.task_set_prio(self._task_update_laser_output, lv.TASK_PRIO.OFF)
        
        # Task to get laser output
        self._task_read_laser = lv.task_create_basic()
        lv.task_set_cb(self._task_read_laser, self._read_laser_cb)
        lv.task_set_period(self._task_read_laser, 1000)
        lv.task_set_prio(self._task_read_laser, lv.TASK_PRIO.OFF)

        return

    def _load_screen(self):
        # Create screen obj
        th=lv.theme_night_init(210, lv.font_roboto_16)
        lv.theme_set_current(th)
        self._scr = lv.obj()

        # Add header and body
        self._header = GuiHeader(self._scr, 0, 0, self._laser_mcu.get_creation_time_str())
        self._body = GuiLaserMain(self._scr, 0, self._header.get_height(), self)

        lv.scr_load(self._scr)        
        return
        
    def _update_time_cb(self, data):
        if self._laser_mcu.is_connected():
            self._header.set_left_text(self._laser_mcu.get_local_time_str() + " " + lv.SYMBOL.WIFI)
        else:
            self._header.set_left_text(self._laser_mcu.get_local_time_str())
        return

    def _update_th_cb(self, data):
        self._header.set_right_text(self._laser_mcu.get_th_str())
        return
    
    def _update_laser_output_cb(self, data):
        try:
            pv_str = self._laser.get_values_str()       
        except:
            return
        
        self._body.set_cal_label(pv_str)
        return

    def _read_laser_cb(self, data):
        self._laser.get_phrase_pvs()
        self.start = utime.ticks_us()
        return
    
    def _gc_collect_cb(self, data):
        gc.collect()
        return

    def _save_time_cb(self, data):
        self._laser_mcu.save_time()
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

"""
GUI elements
"""
class TextBtn(lv.btn):
    def __init__(self, parent, text):
        super().__init__(parent)
        
        self.label = lv.label(self)
        self.label.set_text(text)
        self.set_fit2(lv.FIT.TIGHT, lv.FIT.TIGHT)
        return

class NumTextArea(lv.ta):
    def __init__(self, parent, cb):
        super().__init__(parent)

        self.set_one_line(True)
        self.set_max_length(7)
        self.set_accepted_chars("0123456789.+-")
        self.set_width(85)
        self.set_placeholder_text("+00.000")
        self.set_text("+12.000")
        self.set_event_cb(cb)
        return
    
class GuiHeader(lv.cont):
    def __init__(self, scr, x_pos, y_pos, text):
        super().__init__(scr)
        
        self._left_text = lv.label(self)
        self._left_text.set_text("TIME")
        self._left_text.align(self, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        
        self._right_text = lv.label(self)
        self._right_text.set_text("TH: -- H: --")
        self._right_text.align(self, lv.ALIGN.IN_LEFT_MID, 10, 0)

        self._center_text = lv.label(self)
        self._center_text.set_text(text)
        self._center_text.align(self, lv.ALIGN.IN_RIGHT_MID, 100, 0)

        self.set_fit2(lv.FIT.FLOOD, lv.FIT.TIGHT)
        self.set_pos(x_pos, y_pos)
        self._center_text.align(self, lv.ALIGN.IN_RIGHT_MID, -200, 0)
        self._right_text.align(self, lv.ALIGN.IN_LEFT_MID, 10, 0)
        self._left_text.align(self, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        return

    def set_left_text(self, text):
        self._left_text.set_text(text)
        self._left_text.align(self, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        return

    def set_right_text(self, text):
        self._right_text.set_text(text)
        self._right_text.align(self, lv.ALIGN.IN_LEFT_MID, 10, 0)
        return
    
class GuiLaserMain(lv.tabview):
    def __init__(self, parent, x_pos, y_pos, gui_ctrl):
        super().__init__(parent)
        self._gui_ctrl = gui_ctrl
        
        btn_style = self.get_style(lv.tabview.STYLE.BTN_REL)
        btn_style_or = lv.style_t()
        lv.style_copy(btn_style_or, btn_style)
        btn_style.body.padding.left = (parent.get_width() - x_pos) // 5 // 2
        btn_style.body.padding.right = (parent.get_width() - x_pos) // 5 // 2
        self.set_style(lv.tabview.STYLE.BTN_REL, btn_style)

        self.set_size(parent.get_width() - x_pos, parent.get_height() - y_pos)
        self.set_pos(x_pos, y_pos)

        self.set_anim_time(0)
        self.set_sliding(False)        
        self.set_btns_pos(lv.tabview.BTNS_POS.LEFT)

        self.set_event_cb(self._tab_change_handler)

        self._t_start = self.add_tab("New Session")
        self._t_cal = self.add_tab("Calibration")
        self._t_other = self.add_tab("Other")
        self._t_done = self.add_tab("Done")

        # Calibration Screen
        self._cal_label = lv.label(self._t_cal)        
        self._cal_label.set_text("Output: \n")
        self._cal_num_input = NumTextArea(self._t_cal, self.ta_test)
        self._cal_num_input.set_auto_realign(True)
        self._cal_num_input.align(self._cal_label, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 0)

        self._set_cal_1 = TextBtn(self._t_cal, "Set Amp 1")
        self._set_cal_1.set_style(lv.btn.STYLE.REL, btn_style_or)
        self._set_cal_1.align(self._cal_num_input, lv.ALIGN.OUT_RIGHT_MID, 0, 0)
        self._set_cal_1.set_event_cb(self._set_amp_1_cb)

        self._set_cal_2 = TextBtn(self._t_cal, "Set Amp 2")
        self._set_cal_2.set_style(lv.btn.STYLE.REL, btn_style_or)
        self._set_cal_2.align(self._set_cal_1, lv.ALIGN.OUT_RIGHT_MID, 0, 0)
        self._set_cal_2.set_event_cb(self._set_amp_2_cb)
        
        self._kb = lv.kb(self._t_cal)
        self._kb.set_map(["1", "2", "3","\n","4","5", "6",\
                          "\n","7", "8", "9","\n","0",".","Bksp",""])

        self._kb.set_height(180)
        self._kb.set_y(85)
        self._kb.set_ta(self._cal_num_input)

        # Laser Off Screen
        self._text = lv.label(self._t_done)
        self._text.set_text("Laser Off")

        # Other Screen
        self._cal = lv.calendar(self._t_other)
        return

    def _set_amp_1_cb(self, obj, event):
        if event == lv.EVENT.CLICKED:
            try:
                self._gui_ctrl._laser.set_cal_init(0, float(self._cal_num_input.get_text()))
                self._cal_label.set_text("Setting Amp 1")
            except ValueError:
                print("Not a float")
        return
    
    def _set_amp_2_cb(self, obj, event):
        if event == lv.EVENT.CLICKED:
            try:
                self._gui_ctrl._laser.set_cal_init(1, float(self._cal_num_input.get_text()))
                self._cal_label.set_text("Setting Amp 2")
            except ValueError:
                print("Not a float")
        return
    
    def _tab_change_handler(self, obj, event):
        if event == lv.EVENT.VALUE_CHANGED:
            tab_act = obj.get_tab_act()
            if tab_act == 0:
                self._gui_ctrl._laser.on()
                lv.task_set_prio(self._gui_ctrl._task_read_laser, lv.TASK_PRIO.MID)            
                lv.task_set_prio(self._gui_ctrl._task_update_laser_output, lv.TASK_PRIO.MID)
            elif tab_act == 1:
                self._gui_ctrl._laser.on()
                lv.task_set_prio(self._gui_ctrl._task_read_laser, lv.TASK_PRIO.MID)            
                lv.task_set_prio(self._gui_ctrl._task_update_laser_output, lv.TASK_PRIO.MID)
            else:
                lv.task_set_prio(self._gui_ctrl._task_read_laser, lv.TASK_PRIO.OFF)            
                lv.task_set_prio(self._gui_ctrl._task_update_laser_output, lv.TASK_PRIO.OFF)
                self._gui_ctrl._laser.off()
        return
    
    def ta_test(self, obj, event):
        if event == lv.EVENT.PRESSED:
            obj.set_text("+")
        return

    def set_cal_label(self, text):
        self._cal_label.set_text("Output: " + text)
        return


