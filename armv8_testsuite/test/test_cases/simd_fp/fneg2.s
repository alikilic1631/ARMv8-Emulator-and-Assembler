ldr x0, ten
ldr w1, neg_ten
fmov d0, x0
fmov s1, w1

fneg d0, d0
fneg s1, s1

fmov x2, d0
fmov w3, s1

and x0, x0, x0

neg_ten:
    .int 0xc1200000

ten:
    .int 0x00000000
    .int 0x40240000
