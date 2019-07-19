MKFILE_PATH = $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_BUILD_DIR = build
BUILD_DIR = $(patsubst %,$(MKFILE_PATH)%,$(_BUILD_DIR))
MPY_CROSS = ~/new/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

_MAIN = main.py
_MAIN_MPY = $(patsubst %.py,%.mpy,$(_MAIN))
MAIN_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MAIN_MPY))

_BOOT = boot.py
_BOOT_MPY = $(patsubst %.py,%.mpy,$(_BOOT))
BOOT_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_BOOT_MPY))

_MODULES = gui data_save laser_ctrl sensors_ctrl drivers lasermcu

_MODULES_INIT= $(patsubst %,%/__init__.py,$(_MODULES))
_MODULES_INIT_MPY= $(patsubst %,%/__init__.mpy,$(_MODULES))
MODULES = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES))
MODULES_INIT_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_INIT_MPY))

PORT = /dev/ttyS4
BAUDRATE = 115200

.PHONY: git dir rm_main

all: git dir rm_main $(BOOT_MPY) $(MAIN_MPY) $(MODULES_INIT_MPY)
	picocom -b$(BAUDRATE) $(PORT)

rm_main:
	ampy -p $(PORT) rm $(_MAIN) && sleep 1 || sleep 1
	rm -f $(MAIN_MPY)

dir: $(BUILD_DIR) $(MODULES)

$(BUILD_DIR):
	mkdir -p $@

$(MODULES): %:
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) rm $< && sleep 1 || sleep 1
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

git:
	git pull
	echo $(MODULE) 

clean:
	rm -rf $(BUILD_DIR)
