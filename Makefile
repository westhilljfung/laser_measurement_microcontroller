# By Joshua Fung 2019/07/19
BUILD_DIR = build

MPY_CROSS = $(HOME)/Westhill/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

reverse = $(if $(1),$(call reverse,$(wordlist 2,$(words $(1)),$(1)))) $(firstword $(1))

_MAIN = test.py boot.py
MAIN = $(patsubst %,$(BUILD_DIR)/%,$(call reverse,$(_MAIN)))
CLEAN_MAIN = $(patsubst %,CLEAN/%,$(_MAIN))

_MODULES = gui_ctrl.py laser_mcu.py si7021.py laser_ctrl.py utils.py
_MODULES_MPY =  $(patsubst %.py,%.mpy,$(_MODULES))
MODULES_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_MPY))

V ?= 0
PORT ?= /dev/ttyUSB0
BAUDRATE ?= 115200
AMPY_BAUD ?= 115200

.PHONY: deploy git dir $(CLEAN) start con

all: dir $(MODULES_MPY) $(MAIN)

dir: $(BUILD_DIR)
$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
#ampy -p $(PORT) -b $(AMPY_BAUD) put $@
#sleep 0.5

$(MAIN): $(BUILD_DIR)/%.py: %.py
	cp $< $@
#ampy -p $(PORT) put $@
#sleep 0.5

test.py: main.py
	cp $< $@

git:
	git pull

clean:
	mpfshell -n -c "open ttyUSB0; mrm ./*"
	rm -rf $(BUILD_DIR)

list:
	mpfshell -n -c "open ttyUSB0; ls"

start:
	mpfshell -n -c "open ttyUSB0; repl"
con:
	picocom -b$(BAUDRATE) $(PORT)
