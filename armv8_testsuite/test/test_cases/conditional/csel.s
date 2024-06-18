// Testing CSEL Instruction

// Initialize registers
movz x0, #5        // x0 = 5
movz x1, #10       // x1 = 10

// Use CSEL
cmp x0, x1         // Compare x0 with x1
csel x2, x0, x1, lt // x2 = x0 if x0 < x1, else x2 = x1

// Halt the program
and x0, x0, x0
