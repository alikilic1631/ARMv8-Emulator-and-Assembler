ldr w0, set_output
ldr w2, addr_gpio_sel
str w0, [w2]

begin:
    ldr w0, set_pin
    ldr w2, addr_gpio_set
    str w0, [w2]

    ldr w1, wait_cycles
wait1:
    subs w1, w1, #0x1
    b.ne wait1

    ldr w0, set_pin
    ldr w2, addr_gpio_clr 
    str w0, [w2]

    ldr w1, wait_cycles
wait2:
    subs w1, w1, #0x1
    b.ne wait2
    b begin

set_output:
    .int 0x40

set_pin:
    .int 0x4

wait_cycles:
    .int 0x100000

addr_gpio_sel:
    .int 0x3f200000

addr_gpio_set:
    .int 0x3f20001c

addr_gpio_clr:
    .int 0x3f200028