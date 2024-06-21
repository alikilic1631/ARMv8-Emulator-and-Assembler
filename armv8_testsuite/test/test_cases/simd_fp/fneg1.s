ldr x0, neg_ten
fmov d0, x0
fneg d1, d0
fmov x1, d1

and x0, x0, x0

neg_ten:
    .int 0x00000000
    .int 0xc0240000
