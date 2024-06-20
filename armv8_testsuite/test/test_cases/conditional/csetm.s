
movz x0, #10
movz x1, #5

cmp x0, x1
csetm x2, gt

and x0, x0, x0
