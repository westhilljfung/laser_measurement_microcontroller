# th_ctrl.py
import si7021

class THCtrl:
    def __init__(self):
        self._th_sensor = si7021.SI7021(4, 21)

    def get_th_str(self):
        th_str = "T: " + str("%0.2f" % self._th_sensor.read_temperature()) + " H: " \
            + str("%0.2f" % self._th_sensor.read_relative_humidity())
        return th_str
