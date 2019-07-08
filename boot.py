# boot.py

ssid_ = 'Westhill_2.4G'
wp2_pass = 'Radoslav13'

def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid_, wp2_pass)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

def set_time_from_internet():
    import ntptime
    ntptime.settime()
    
    
do_connect()
set_time_from_internet()
