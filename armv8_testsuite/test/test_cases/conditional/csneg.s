
movz x0, #1
movz x1, #2

cmp x0, x1
csneg x2, x0, x1, ne

and x0, x0, x0