MODULES = gui.f~ data_save.f~ laser_ctrl.f~ sensors_ctrl.f~
PORT = /dev/ttyS4

.PHONY = git

deploy: git $(MODULES)  boot.touch~ main.touch~
	picocom -b 115200 $(PORT)

%.touch~: %.py
	touch $@
	ampy -p $(PORT) rm $< && sleep 1 || sleep 1
	ampy -p $(PORT) put $<
	sleep 1

%.f~: %
	ampy -p $(PORT) rm main.py && sleep 1
	touch $@
	ampy -p $(PORT) rmdir $< && sleep 1 || sleep 1
	ampy -p $(PORT) put $<
	sleep 1
	ampy -p $(PORT) put main.py

git:
	git pull
