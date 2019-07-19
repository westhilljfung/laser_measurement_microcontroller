# By Joshua Fung 2019/07/19
BUILD_DIR = build

MPY_CROSS = ~/new/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

MAIN = main.py boot.py

_MODULES = gui_ctrl.py laser_mcu.py si7021.py
_MODULES_MPY =  $(patsubst %.py,%.mpy,$(_MODULES))
MODULES_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_MPY))
CLEAN_MODULES_MPY = $(patsubst %,CLEAN/%,$(_MODULES_MPY))

PORT = /dev/ttyS4
BAUDRATE = 115200

.PHONY: deploy git dir rm_main $(CLEAN_MODULES_MPY) con

deploy: git dir rm_main $(MODULES_MPY) $(MAIN) con
rm_main:
	ampy -p $(PORT) rm $(_MAIN) && sleep 1 || sleep 1

dir: $(BUILD_DIR)
$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

$(MAIN): %:
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

git:
	git pull

clean: $(CLEAN_MODULES_MPY)
	rm -rf $(BUILD_DIR)

$(CLEAN_MODULES_MPY): CLEAN/%:
	ampy -p $(PORT) rm $* && sleep 1 || sleep 1

list:
	ampy -p $(PORT) ls

con:
	picocom -b$(BAUDRATE) $(PORT)
