MODULES = gui drivers data_save laser_ctrl lasermcu sensors_ctrl
PORT = /dev/ttyS4

.PHONY = git

deploy: git main.py boot.py $(MODULES)
	picocom -b 115200 $(PORT)

main.py: main.py
	ampy -p $(PORT) rm $@ && sleep 1 || sleep 1
	ampy -p $(PORT) put $@
	sleep 1

boot.py: boot.py
	ampy -p $(PORT) rm $@ && sleep 1 || sleep 1
	ampy -p $(PORT) put $@
	sleep 1

%:
	echo $@

git:
	git pull
