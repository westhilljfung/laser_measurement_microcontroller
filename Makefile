BUILD_DIR = build

MPY_CROSS = ~/new/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

_MAIN = main.py
_MAIN_MPY = $(patsubst %.py,%.mpy,$(_MAIN))
MAIN_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MAIN_MPY))

_MODULES = boot.py gui_ctrl.py laser_mcu.py si7021.py
_MODULES_MPY =  $(patsubst %.py,%.mpy,$(_MODULES))
MODULES_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_MPY))

PORT = /dev/ttyS4
BAUDRATE = 115200

.PHONY: git dir rm_main

all: git Makefile dir rm_main $(MODULES_MPY) $(MAIN_MPY)
	picocom -b$(BAUDRATE) $(PORT)

rm_main:
	ampy -p $(PORT) rm $(_MAIN_MPY) && sleep 1 || sleep 1
	rm -f $(MAIN_MPY)

dir: $(BUILD_DIR)
$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) rm $*.mpy && sleep 1 || sleep 1
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

git:
	git pull

clean:
	rm -rf $(BUILD_DIR)
	$(foreach file, $(_MODULES_MPY), $(echo $(file)))

list:
	ampy -p $(PORT) ls

Makefile:
