# By Joshua Fung 2019/07/19
BUILD_DIR = build

MPY_CROSS = ~/new/micropython/mpy-cross/mpy-cross
MPY_CROSS_FLAG=

_MAIN = main.py boot.py
MAIN = $(patsubst %,$(BUILD_DIR)/%,$(_MAIN))
CLEAN_MAIN = $(patsubst %,CLEAN/%,$(MAIN))

_MODULES = gui_ctrl.py laser_mcu.py si7021.py
_MODULES_MPY =  $(patsubst %.py,%.mpy,$(_MODULES))
MODULES_MPY = $(patsubst %,$(BUILD_DIR)/%,$(_MODULES_MPY))
CLEAN = $(CLEAN_MAIN)
CLEAN += $(patsubst %,CLEAN/%,$(_MODULES_MPY))

PORT = /dev/ttyS4
BAUDRATE = 115200

.PHONY: deploy git dir $(CLEAN_MAIN) $(CLEAN_MODULES_MPY) con

deploy: git dir $(CLEAN_MAIN) $(MODULES_MPY) $(MAIN) con

dir: $(BUILD_DIR)
$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.mpy: %.py
	$(MPY_CROSS) $(MPY_CROSS_FLAG) -o $@ $*.py
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

$(MAIN): $(BUILD_DIR)/%.py: %.py
	cp $< $@
	ampy -p $(PORT) put $@ && sleep 1 || sleep 1

git:
	git pull

clean: $(CLEAN)
	rm -rf $(BUILD_DIR)

$(CLEAN): CLEAN/%:
	ampy -p $(PORT) rm $* && sleep 1 || sleep 1

list:
	ampy -p $(PORT) ls

con:
	picocom -b$(BAUDRATE) $(PORT)
