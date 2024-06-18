// Testing CSET Instruction

// Initialize registers
movz x0, #0        // x0 = 0
movz x1, #1        // x1 = 1

// Use CSET
cmp x0, x1         // Compare x0 with x1
cset x2, eq        // Set x2 to 1 if x0 == x1, otherwise x2 = 0

// Halt the program
and x0, x0, x0
