MODULES = gui drivers data_save laser_ctrl lasermcu sensor_ctrl
PORT = /dev/ttyS4

deploy: main boot $(MODULES)
	picocom -b 115200 $(PORT)

main: main.py
	ampy -p $(PORT) rm $<
	sleep 5
	ampy -p $(PORT) put $<

boot: boot.py
	ampy -p $(PORT) rm $<
	ampy -p $(PORT) put $<

%:
	echo($@)

git:
	git pull
