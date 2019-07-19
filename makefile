MODULES = gui drivers data_save laser_ctrl lasermcu sensors_ctrl
PORT = /dev/ttyS4

.PHONY = git main boot

deploy: git main boot $(MODULES)
	picocom -b 115200 $(PORT)

main: main.py
	ampy -p $(PORT) get $< && ampy-p $(PORT) rm $<
	sleep 1
	smpy -p $(PORT) put $<
	sleep 1

boot: boot.py
	ampy -p $(PORT) get $< && ampy-p $(PORT) rm $<
	sleep 1
	smpy -p $(PORT) put $<
	sleep 1

%:
	echo $@

git:
	git pull
