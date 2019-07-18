# laser_sys.py
class Sys:

    def __init__(self):
        name = "Westhill Laser Measument System"
        wlan =  network.WLAN(network.STA_IF)
        self.connect_wifi()
        self.set_time()

    def connect_wifi(self):
        if not self.is_connected():
            self.wlan.active(True)
            self.connect(ssid,wp2_pass)            
        return
        
    def set_time(self):
        if self.is_connected():
            ntptime.settime()
        else:
            raise RuntimeError("Wifi is diconnected")
        return
    
    def is_connected(self):
        return self.wlan.isconnected()

    def __str__(self):
        return name
        
