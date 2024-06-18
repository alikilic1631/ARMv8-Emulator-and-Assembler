// Testing CSINV Instruction

// Initialize registers
movz x0, #0        // x0 = 0
movz x1, #1        // x1 = 1

// Use CSINV
cmp x0, x1         // Compare x0 with x1
csinv x2, x0, x1, lt // x2 = ~x0 if x0 < x1, else x2 = x1

// Halt the program
and x0, x0, x0
