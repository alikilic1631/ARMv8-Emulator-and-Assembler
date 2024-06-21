movz w0, #10
ldr x1, big

scvtf d0, x0
scvtf d1, x1
scvtf s3, w0

fmul d2, d1, d0

fcvtzs x0, d0
fcvtzs x1, d1
fcvtzs x2, d2
fcvtzs w3, s3

and x0, x0, x0

big:
    .int 0x00000000
    .int 0x40000000
