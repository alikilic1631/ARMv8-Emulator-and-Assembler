
movz x0, #5
movz x1, #10

cmp x0, x1
csel x2, x0, x1, lt

and x0, x0, x0
