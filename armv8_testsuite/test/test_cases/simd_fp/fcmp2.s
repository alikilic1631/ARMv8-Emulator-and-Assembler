ldr w0, min_one_five 
ldr w1, maxf

fmov s0, w0
fmov s1, w1
fcmp s1, s0

and x0, x0, x0

maxf:
    .int 0x7f7fffff

min_one_five:
    .int 0xbfc00000
