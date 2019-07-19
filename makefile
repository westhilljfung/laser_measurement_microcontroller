BUID_DIR = build
MPY_CROSS = ~/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

_MAIN = main.py
_MAIN_MPY = $(patsubst %.py,%.mpy,$(_MAIN))
MAIN_MPY = $(patsubst %,$(BUID_DIR)/%,$(_MAIN_MPY))

_BOOT = boot.py
_BOOT_MPY = $(patsubst %.py,%.mpy,$(_BOOT))
BOOT_MPY = $(patsubst %,$(BUID_DIR)/%,$(_BOOT_MPY))

MODULES = gui data_save laser_ctrl sensors_ctrl drivers lasermcu

PORT = /dev/ttyS4
BAUDRATE = 115200

.PHONY: git dir rm_main

all: git dir rm_main $(MODULES) $(BOOT_MPY) $(MAIN_MPY)
	picocom -b$(BAUDRATE) $(PORT)

rm_main:
	ampy -p $(PORT) rm $(_MAIN) && sleep 1 || sleep 1
	rm $(MAIN_MPY)

dir: $(BUID_DIR)

$(BUID_DIR):
	mkdir -p $@

$(BUID_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $(BUILD_DIR)/$*.mpy $*.py
	ampy -p $(PORT) rm $* && sleep 1 || sleep 1
	ampy -p $(PORT) put $(BUILD_DIR)/$*
	sleep 1

git:
	git pull

clean:
	rm -rf $(BUID_DIR)
