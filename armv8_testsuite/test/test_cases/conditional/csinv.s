
movz x0, #0
movz x1, #1

cmp x0, x1
csinv x2, x0, x1, lt

and x0, x0, x0
