# By Joshua Fung 2019/07/19
BUILD_DIR = build

MPY_CROSS = $(HOME)/Documents/laser/mymicropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

reverse = $(if $(1),$(call reverse,$(wordlist 2,$(words $(1)),$(1)))) $(firstword $(1))

_MAIN = test.py boot.py
MAIN = $(patsubst %,$(BUILD_DIR)/%,$(call reverse,$(_MAIN)))
CLEAN_MAIN = $(patsubst %,CLEAN/%,$(_MAIN))

_MODULES = gui_ctrl.py laser_mcu.py si7021.py th_ctrl.py laser_ctrl.py
_MODULES_MPY =  $(patsubst %.py,%.mpy,$(_MODULES))
MODULES_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_MPY))
CLEAN = $(CLEAN_MAIN)
CLEAN += $(patsubst %,CLEAN/%,$(_MODULES_MPY))

PORT = /dev/ttyUSB1
BAUDRATE = 115200
AMPY_BAUD = 115200

.PHONY: deploy git dir $(CLEAN) con

deploy: dir $(MODULES_MPY) $(MAIN) con

dir: $(BUILD_DIR)
$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) -b $(AMPY_BAUD) put $@ && sleep 1 || sleep 1

$(MAIN): $(BUILD_DIR)/%.py: %.py
	cp $< $@
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

test.py: main.py
	cp $< $@

git:
	git pull

clean: $(CLEAN)
	rm -rf $(BUILD_DIR)

$(CLEAN): CLEAN/%:
	ampy -p $(PORT) rm $* && sleep 1 || sleep 1
	rm -f $(BUILD_DIR)/$*

list:
	ampy -p $(PORT) ls

con:
	picocom -b$(BAUDRATE) $(PORT)
