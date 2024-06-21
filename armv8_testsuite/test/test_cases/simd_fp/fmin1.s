ldr x0, five_five
ldr x1, zero_twofive

fmov d0, x0
fmov d1, x1
fmin d2, d1, d0
fmov x2, d2

and x0, x0, x0

zero_twofive:
    .int 0x00000000
    .int 0x3fd00000

five_five:
    .int 0x00000000
    .int 0x40160000
