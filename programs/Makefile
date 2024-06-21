ASSEMBLE=../src/assemble

all: led_blink.bin

led_blink.bin:
	../src/assemble led_blink.s led_blink.bin

.PHONY: clean
clean:
	$(RM) led_blink.bin