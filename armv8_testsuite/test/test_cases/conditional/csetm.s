
movz x0, #0
movz x1, #1

cmp x0, x1
csetm x2, ne

and x0, x0, x0
