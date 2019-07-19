MODULES = gui drivers data_save laser_ctrl lasermcu sensors_ctrl
PORT = /dev/ttyS4

.PHONY = git

deploy: git main.touch boot.touch $(MODULES)
	picocom -b 115200 $(PORT)

%.touch: %.py
	touch $@
	ampy -p $(PORT) rm $< && sleep 1 || sleep 1
	ampy -p $(PORT) put $<
	sleep 1

%: %
	ampy -p $(PORT) rmdir $@ && sleep 1 || sleep 1
	ampy -p $(PORT) put $@
	sleep 1

git:
	git pull
