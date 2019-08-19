"""utils.py

helper functions
"""
import utime

from machine import reset


def timed_function(f, *args, **kwargs):
    """Time function

    Time a function using @timed_function decorator
    """
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

