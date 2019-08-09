"""gui_ctrl.py

This is the Controller for the GUI

*Author(s): Joshua Fung
July 30, 2019
"""
import utime
import _thread
import gc

import lvgl as lv
from micropython import const
import lvesp32
import TFTFeatherWing as tftwing

import laser_mcu
import laser_ctrl


DISP_BUF_SIZE = const(9600)
MATERIAL_TYPE = ("WPC", "ECEL", "OTHER")
THICKNESS_TYPE = ("12", "5", "5.5", "6.5")


class LaserGui:
    """Gui Controller"""
    
    def __init__(self):
        # init LVGL
        lv.init()
        # MCU Control
        self.mcu = laser_mcu.LaserMCU()
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
            self.mcu.set_time_ntp()
        except OSError as err:
            print("OSError: {0}".format(err))
            self.mcu.load_time()
        self.mcu.set_creation_time()
        # Register display buffer, driver and input device driver
        self._register_disp_drv()
        self._register_indev_drv()
        # Create screen
        self._load_screen()
        # Register Tasks
        self._register_tasks()
        # Create lock for panel wait process
        self._lock = _thread.allocate_lock()
        return

    def _register_tasks(self):
        # Task to update th
        self._task_update_th = lv.task_create(None, 1000, lv.TASK_PRIO.MID, None)
        lv.task_set_cb(self._task_update_th, self._update_th_cb)
        # Task to save th
        self._task_save_th = lv.task_create(None, 60000, lv.TASK_PRIO.MID, None)
        lv.task_set_cb(self._task_save_th, self._save_th_cb)
        # Task to update time
        self._task_update_time = lv.task_create(None, 1000, lv.TASK_PRIO.MID, None)
        lv.task_set_cb(self._task_update_time, self._update_time_cb)
        # Task to save time to flash
        self._task_save_time = lv.task_create(None, 60000, lv.TASK_PRIO.MID, None)
        lv.task_set_cb(self._task_save_time, self._save_time_cb)
        # Task to gc collect
        self._task_gc_collect = lv.task_create(None, 10000, lv.TASK_PRIO.MID, None)
        lv.task_set_cb(self._task_gc_collect, self._gc_collect_cb)
        # Task to update output
        self._task_update_laser_output = lv.task_create(None, 200, lv.TASK_PRIO.OFF, None)
        lv.task_set_cb(self._task_update_laser_output, self._update_laser_output_cb)
        # Task to wait for wait panel function
        self._task_wait_panel = lv.task_create(None, 1000, lv.TASK_PRIO.OFF, None)
        lv.task_set_cb(self._task_wait_panel, self._check_wait_panel_cb)
        return
    
    def _load_screen(self):
        # Create screen obj
        th=lv.theme_night_init(210, lv.font_roboto_16)
        lv.theme_set_current(th)
        self._scr = lv.obj()
        # Add header and body
        self.hdr = GuiHeader(self._scr, 0, 0, self.mcu.get_creation_time_str())
        self._body = GuiLaserMain(self._scr, 0, self.hdr.get_height(), self)
        # Load screen
        lv.scr_load(self._scr)        
        return

    def _check_wait_panel_cb(self, data):
        if not self._lock.locked():
            lv.task_set_prio(self._task_wait_panel, lv.TASK_PRIO.OFF)
            lv.task_set_prio(self._task_update_time, lv.TASK_PRIO.MID)
            lv.task_set_prio(self._task_update_th, lv.TASK_PRIO.MID)
            lv.task_set_prio(self._task_gc_collect, lv.TASK_PRIO.MID)            
            self._body._session_label.set_text(str(self._laser._session))
            self._body._session.set_hidden(False)
            self._body._re_measure_btn.set_hidden(False) 
            self._body._preload_cont.set_hidden(True)
            self._body._chart.set_point_count(self._laser._session.panel._in)
            filter_size = self._laser._session.panel._in // 20
            for d in self._laser._session.panel._data1[0:self._laser._session.panel.size2]:
                self._body._chart.set_next(self._body._ser1, int(d*1000))
            for d in self._laser._session.panel._data2[0:self._laser._session.panel.size2]:
                self._body._chart.set_next(self._body._ser2, int(d*1000))
            for d in self._laser._session.panel._cdata1[0:self._laser._session.panel.size]:
                self._body._chart.set_next(self._body._ser3, int(d*1000))
            for d in self._laser._session.panel._cdata2[0:self._laser._session.panel.size]:
                self._body._chart.set_next(self._body._ser4, int(d*1000))
            self.mcu.alt()
        return
        
    def _update_time_cb(self, data):
        if self.mcu.is_connected():
            self.hdr.set_left_text(self.mcu.get_lt_str() + " " + lv.SYMBOL.WIFI)
        else:
            self.hdr.set_left_text(self.mcu.get_lt_str())
        return

    def _save_th_cb(self, data):
        self.mcu.save_th_data()
        return
    
    def _update_th_cb(self, data):
        self.hdr.set_right_text(self.mcu.get_th_str())
        return
    
    def _update_laser_output_cb(self, data):
        try:
            self._laser.get_phrase_pvs()     
        except:
            return
        pv_str = self._laser.get_values_str()  
        self._body.set_cal_label(pv_str)
        return
    
    def _gc_collect_cb(self, data):
        gc.collect()
        return

    def _save_time_cb(self, data):
        self.mcu.save_time()
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
        # Left label
        self._left_text = lv.label(self)
        self._left_text.set_text("TIME")
        # Right label
        self._right_text = lv.label(self)
        self._right_text.set_text("TH: -- H: --")
        # Center label
        self._center_text = lv.label(self)
        self._center_text.set_text(text)
        # Fit and Align
        self.set_fit2(lv.FIT.FLOOD, lv.FIT.TIGHT)
        self.set_pos(x_pos, y_pos)
        self._center_text.set_auto_realign(True)
        self._right_text.set_auto_realign(True)
        self._left_text.set_auto_realign(True)
        self._center_text.align(self, lv.ALIGN.IN_RIGHT_MID, -200, 0)
        self._right_text.align(self, lv.ALIGN.IN_LEFT_MID, 10, 0)
        self._left_text.align(self, lv.ALIGN.IN_RIGHT_MID, -10, 0)
        return

    def set_left_text(self, text):
        self._left_text.set_text(text)
        return

    def set_right_text(self, text):
        self._right_text.set_text(text)
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

        self.set_tab_act(3, lv.ANIM.OFF)

        # Session screen
        # Stat new session
        self._start_session = lv.cont(self._t_start)
        self._start_session.set_fit(lv.FIT.FLOOD)
        self._start_session.set_layout(lv.LAYOUT.PRETTY)

        self._new_session_label = lv.label(self._start_session)
        self._new_session_label.set_text("Set info, and start a new measuring session!")
        
        self._material_sel = lv.roller(self._start_session)
        self._material_sel.set_options("\n".join(material for material in MATERIAL_TYPE), \
                                       lv.roller.MODE.INIFINITE)

        self._thickness_sel = lv.roller(self._start_session)
        self._thickness_sel.set_options("\n".join(thickness for thickness in THICKNESS_TYPE), \
                                       lv.roller.MODE.INIFINITE)

        self._start_btn = TextBtn(self._start_session, "Start")
        self._start_btn.set_style(lv.btn.STYLE.REL, btn_style_or)
        self._start_btn.set_event_cb(self._start_session_cb)

        # Measuring Screen
        self._session = lv.cont(self._t_start)
        self._session.set_fit(lv.FIT.FLOOD)
        self._session.set_layout(lv.LAYOUT.PRETTY)

        self._session_label = lv.label(self._session)
        self._session_label.set_text("\n\n")

        self._start_measure_btn = TextBtn(self._session, "New Panel")
        self._start_measure_btn.set_style(lv.btn.STYLE.REL, btn_style_or)
        self._start_measure_btn.set_event_cb(self._start_measure_cb)

        self._done_measure_btn = TextBtn(self._session, "Finish")
        self._done_measure_btn.set_style(lv.btn.STYLE.REL, btn_style_or)
        self._done_measure_btn.set_event_cb(self._done_measure_cb)
        
        self._re_measure_btn = TextBtn(self._session, "Re-measure")
        self._re_measure_btn.set_style(lv.btn.STYLE.REL, btn_style_or)
        self._re_measure_btn.set_event_cb(self._re_measure_cb)

        self._chart = lv.chart(self._session)
        self._chart.set_height(110)
        self._chart.set_point_count(700)
        self._chart.set_range(11000,13000)
        self._ser1 = self._chart.add_series(lv.color_hex(0x0000b3))
        self._ser2 = self._chart.add_series(lv.color_hex(0xe60000))
        self._ser3 = self._chart.add_series(lv.color_hex(0x00e600))       
        self._ser4 = self._chart.add_series(lv.color_hex(0xffffff))

        self._session.set_hidden(True)
        
        lv.page.glue_obj(self._start_session, True)
        lv.page.glue_obj(self._session, True)

        self._preload_cont = lv.cont(self._t_start)
        self._preload_cont.set_fit(lv.FIT.FLOOD)
        self._preload_cont.set_layout(lv.LAYOUT.CENTER)
        self._preload = lv.preload(self._preload_cont)

        self._preload_cont.set_hidden(True)
        
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

    def _start_measure_cb(self, obj, event):
        if event == lv.EVENT.CLICKED:
            panel, thickness = self._gui_ctrl._laser._session.new_panel()
            _thread.start_new_thread(self._gui_ctrl._laser.wait_for_panel, [panel, thickness, self._gui_ctrl._lock])

            lv.task_set_prio(self._gui_ctrl._task_wait_panel, lv.TASK_PRIO.MID)
            lv.task_set_prio(self._gui_ctrl._task_update_time, lv.TASK_PRIO.OFF)
            lv.task_set_prio(self._gui_ctrl._task_update_th, lv.TASK_PRIO.OFF)
            lv.task_set_prio(self._gui_ctrl._task_gc_collect, lv.TASK_PRIO.OFF)

            self._session.set_hidden(True)
            self._preload_cont.set_hidden(False)
        return

    def _re_measure_cb(self, obj, event):
        if event == lv.EVENT.CLICKED:
            panel, thickness = self._gui_ctrl._laser._session.re_panel()
            _thread.start_new_thread(self._gui_ctrl._laser.wait_for_panel, [panel, thickness, self._gui_ctrl._lock])

            lv.task_set_prio(self._gui_ctrl._task_wait_panel, lv.TASK_PRIO.MID)
            lv.task_set_prio(self._gui_ctrl._task_update_time, lv.TASK_PRIO.OFF)
            lv.task_set_prio(self._gui_ctrl._task_update_th, lv.TASK_PRIO.OFF)
            lv.task_set_prio(self._gui_ctrl._task_gc_collect, lv.TASK_PRIO.OFF)

            self._session.set_hidden(True)
            self._preload_cont.set_hidden(False)
        return

    def _done_measure_cb(self, obj, event):
        if event == lv.EVENT.CLICKED:
            self._done_measure()
        return

    def _done_measure(self):
        self._gui_ctrl._laser.end_session()
        self._gui_ctrl._laser.off()
            
        self._start_session.set_hidden(False)
        self._session.set_hidden(True)
        return

    def _start_session_cb(self, obj, event):
        if event == lv.EVENT.CLICKED:
            material = MATERIAL_TYPE[self._material_sel.get_selected()]
            thickness = THICKNESS_TYPE[self._thickness_sel.get_selected()]
            self._gui_ctrl._laser.on()
            self._gui_ctrl._laser.start_session(material, thickness)
            self._session_label.set_text(str(self._gui_ctrl._laser._session))
            self._start_session.set_hidden(True)
            self._session.set_hidden(False)
            self._re_measure_btn.set_hidden(True) 
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
                self._gui_ctrl._laser.off()       
                lv.task_set_prio(self._gui_ctrl._task_update_laser_output, lv.TASK_PRIO.OFF)
            else:
                if self._gui_ctrl._laser._session is not None:
                    self._done_measure()
                if tab_act == 1:
                    self._gui_ctrl._laser.on()           
                    lv.task_set_prio(self._gui_ctrl._task_update_laser_output, lv.TASK_PRIO.MID)
                else:         
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


