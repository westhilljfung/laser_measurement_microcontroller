MKFILE_PATH = $(abspath $(lastword $(MAKEFILE_LIST)))
_BDIR = build
BDIR = $(patsubst %,$(MKFILE_PATH)/%,$(_BDIR))
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
	mkdir -p $@ || true

$(MODULES): %:
	mkdir -p $@ || true

$(BUID_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ .mpy $*.py
	ampy -p $(PORT) rm $< && sleep 1 || sleep 1
	ampy -p $(PORT) put $@ || true
	sleep 1

git:
	git pull

clean:
	echo $(MKFILE_PATH)
	echo $(_BDIR)
	echo $(BDIR)
	rm -rf $(BDIR)
