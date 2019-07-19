MODULES = gui drivers data_save laser_ctrl lasermcu sensors_ctrl
PORT = /dev/ttyS4

.PHONY = git

deploy: git main boot $(MODULES)
	picocom -b 115200 $(PORT)

main: $@.py
	echo $@

boot: $@.py
	echo $@

%:
	echo $@

git:
	git pull
