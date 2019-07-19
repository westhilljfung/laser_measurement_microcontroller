MKFILE_PATH = $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_BUID_DIR = build
BUID_DIR = $(patsubst %,$(MKFILE_PATH)%,$(_BUID_DIR))
MPY_CROSS = ~/new/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

_MAIN = main.py
_MAIN_MPY = $(patsubst %.py,%.mpy,$(_MAIN))
MAIN_MPY = $(patsubst %,$(BUID_DIR)/%,$(_MAIN_MPY))

_BOOT = boot.py
_BOOT_MPY = $(patsubst %.py,%.mpy,$(_BOOT))
BOOT_MPY = $(patsubst %,$(BUID_DIR)/%,$(_BOOT_MPY))

_MODULES = gui data_save laser_ctrl sensors_ctrl drivers lasermcu
MODULES = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES))
MODULES_INIT = $(patsubst %,%/__init__.py,$(MODULES))

PORT = /dev/ttyS4
BAUDRATE = 115200

.PHONY: git dir rm_main

all: git dir rm_main $(BOOT_MPY) $(MAIN_MPY)
	picocom -b$(BAUDRATE) $(PORT)

rm_main:
	ampy -p $(PORT) rm $(_MAIN) && sleep 1 || sleep 1
	rm -f $(MAIN_MPY)

dir: $(BUID_DIR) $(MODULES)

$(BUID_DIR):
	mkdir -p $@

$(MODULES): %:
	mkdir -p $@

$(BUID_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) rm $< && sleep 1 || sleep 1
	ampy -p $(PORT) put $@ || true
	sleep 1

git:
	git pull
	echo $(MODULE) 

clean:
	rm -rf $(BDIR)
