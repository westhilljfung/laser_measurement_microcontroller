MODULES = gui drivers data_save laser_ctrl lasermcu sensors_ctrl
PORT = /dev/ttyS4

.PHONY = git

deploy: git main.py boot.py $(MODULES)
	picocom -b 115200 $(PORT)

%.py:
	echo $@
%:
	echo $@

git:
	git pull
