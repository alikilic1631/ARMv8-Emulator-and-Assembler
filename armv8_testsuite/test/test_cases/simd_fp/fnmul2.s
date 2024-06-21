ldr w0, min_zero_five
ldr w1, thousand_five

fmov s0, w0
fmov s1, w1
fnmul s2, s1, s0
fmov w2, s2

and x0, x0, x0

min_zero_five:
    .int 0xbf000000

thousand_five:
    .int 0x447a2000
