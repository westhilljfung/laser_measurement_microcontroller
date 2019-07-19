MODULES = gui drivers data_save laser_ctrl lasermcu sensor_ctrl
PORT = /dev/ttyS4

.PHONY = git

deploy: git main boot $(MODULES)
	picocom -b 115200 $(PORT)

main: main.py
	ampy -p $(PORT) rm $<
	sleep 3
	ampy -p $(PORT) put $<
	sleep 3

boot: boot.py
	ampy -p $(PORT) rm $<
	sleep 3
	ampy -p $(PORT) put $<
	sleep 3

%:
	echo($@)

git:
	git pull
