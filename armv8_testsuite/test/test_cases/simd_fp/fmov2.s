ldr x0, big_num
fmov s0, w0
fmov s1, s0
fmov w1, s1

and x0, x0, x0

big_num:
    .int 0x88000000
