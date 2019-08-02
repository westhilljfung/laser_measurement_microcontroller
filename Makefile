# By Joshua Fung 2019/07/19
BUILD_DIR = build

MPY_CROSS = $(HOME)/Documents/laser/mymicropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

reverse = $(if $(1),$(call reverse,$(wordlist 2,$(words $(1)),$(1)))) $(firstword $(1))

_MAIN = test.py boot.py
MAIN = $(patsubst %,$(BUILD_DIR)/%,$(call reverse,$(_MAIN)))
CLEAN_MAIN = $(patsubst %,CLEAN/%,$(_MAIN))

_MODULES = gui_ctrl.py laser_mcu.py si7021.py laser_ctrl.py
_MODULES_MPY =  $(patsubst %.py,%.mpy,$(_MODULES))
MODULES_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_MPY))
CLEAN = $(CLEAN_MAIN)
CLEAN += $(patsubst %,CLEAN/%,$(_MODULES_MPY))

V ?= 0
PORT ?= /dev/ttyUSB0
BAUDRATE ?= 115200
AMPY_BAUD ?= 115200

.PHONY: deploy git dir $(CLEAN) con

deploy: dir $(MODULES_MPY) $(MAIN) con

dir: $(BUILD_DIR)
$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) -b $(AMPY_BAUD) put $@
	sleep 0.5

$(MAIN): $(BUILD_DIR)/%.py: %.py
	cp $< $@
	ampy -p $(PORT) put $@
	sleep 0.5

test.py: main.py
	cp $< $@

git:
	git pull

clean: $(CLEAN)
	rm -rf $(BUILD_DIR)

$(CLEAN): CLEAN/%:
	ampy -p $(PORT) rm $* && sleep 0.5 || sleep 0.5
	rm -f $(BUILD_DIR)/$*

list:
	ampy -p $(PORT) ls

con:
	picocom -b$(BAUDRATE) $(PORT)
