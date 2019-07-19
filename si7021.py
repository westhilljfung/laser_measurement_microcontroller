"""
``SI7021``
==========
This is a Micropython driver for the SI7021 temeratire and humidity sensor.
*Author(s): Joshua Fung

Modified from below:

``adafruit_si7021``
===================
This is a CircuitPython driver for the SI7021 temperature and humidity sensor.
* Author(s): Radomir Dopieralski
Implementation Notes
--------------------
**Hardware:**
* Adafruit `Si7021 Temperature & Humidity Sensor Breakout Board
  <https://www.adafruit.com/product/3251>`_ (Product ID: 3251)
**Software and Dependencies:**
* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SI7021.git"
"""
try:
    import struct
except ImportError:
    import ustruct as struct

from machine import I2C, Pin
from micropython import const

HUMIDITY = const(0xf5)
TEMPERATURE = const(0xf3)
_RESET = const(0xfe)
_READ_USER1 = const(0xe7)
_USER1_VAL = const(0x3a)

class SI7021:
    """
    A driver for the SI7021 temperature and humidity sensor.
    :param i2c_bus: The `busio.I2C` object to use. This is the only required parameter.
    :param int address: (optional) The I2C address of the device.
    """

    def __init__(self, scl, sda, address=0x40):
        self._i2c = I2C(scl=Pin(scl), sda=Pin(sda))
	self._addr = address
	self._command(_RESET)
        # Make sure the USER1 settings are correct.
        while True:
            # While restarting, the sensor doesn't respond to reads or writes.
            try:
                data = bytearray([_READ_USER1])
                self._i2c.writeto(self._addr, data, False)
                self._i2c.readfrom_into(self._addr, data)
                value = data[0]
            except OSError:
                pass
            else:
                break
        if value != _USER1_VAL:
            raise RuntimeError("bad USER1 register (%x!=%x)" % (
                value, _USER1_VAL))
        self._measurement = 0

    def _command(self, command):
        self._i2c.writeto(self._addr, struct.pack('B', command))

    def _data(self):
        data = bytearray(3)
        data[0] = 0xff
        while True:
            # While busy, the sensor doesn't respond to reads.
            try:
                self._i2c.readfrom_into(self._addr, data)
            except OSError:
                pass
            else:
                if data[0] != 0xff: # Check if read succeeded.
                    break
        value, checksum = struct.unpack('>HB', data)
        return value

    def read_relative_humidity(self):
        """The measured relative humidity in percent."""
        self.start_measurement(HUMIDITY)
        value = self._data()
        self._measurement = 0
        return (((value * 125.0) / 65536.0) - 6.0)

    def read_temperature(self):
        """The measured temperature in degrees Celcius."""
        self.start_measurement(TEMPERATURE)
        value = self._data()
        self._measurement = 0
        return (((value * 175.72) / 65536.0) - 46.85)

    def start_measurement(self, what):
        """
        Starts a measurement.
        Starts a measurement of either ``HUMIDITY`` or ``TEMPERATURE``
        depending on the ``what`` argument. Returns immediately, and the
        result of the measurement can be retrieved with the
        ``temperature`` and ``relative_humidity`` properties. This way it
        will take much less time.
        This can be useful if you want to start the measurement, but don't
        want the call to block until the measurement is ready -- for instance,
        when you are doing other things at the same time.
        """
        if what not in (HUMIDITY, TEMPERATURE):
            raise ValueError()
        if not self._measurement:
            self._command(what)
        elif self._measurement != what:
            raise RuntimeError("other measurement in progress")
        self._measurement = what
