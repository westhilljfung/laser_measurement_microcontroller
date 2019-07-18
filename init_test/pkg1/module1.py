# pkg1/module1.py
import .

class Module1:
    def __init__(self):
        self.name = "Module 1"
        print(dir())
        print(const_init)
        print(const_a)

    def __str__(self):
        return self.name
