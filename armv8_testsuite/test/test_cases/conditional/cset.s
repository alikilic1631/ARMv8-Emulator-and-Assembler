
movz x0, #1
movz x1, #1

cmp x0, x1
cset x2, eq

and x0, x0, x0
