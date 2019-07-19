# pkg1/module1.py
import pkg1


class Module1:
    def __init__(self):
        self.name = "Module 1"
        print(dir())
        print(pkg1.const_init)
        print(pkg1.const_a)
        print(dir(pkg1.pkg1_1))
        print(pkg1.pkg1_1.const_module1_1)

    def __str__(self):
        return self.name
