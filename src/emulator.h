#include <stdbool.h>
#include <stdio.h>
#define MAX_MEMORY 2097152 // 2 MB (spec 1.1)
#define GENERAL_REGS 31    // (spec 1.1)

#ifndef EMULATOR_H
#define EMULATOR_H
typedef unsigned char byte;
typedef unsigned int uint;
typedef unsigned long ulong;
typedef unsigned long long ullong;

typedef struct
{
    bool negative;
    bool zero;
    bool carry;
    bool overflow;
} pstate_t;

typedef struct
{
    byte memory[MAX_MEMORY];
    ullong regs[GENERAL_REGS];
    ullong pc;
    pstate_t pstate;
    // reg sp; // (spec 1.1 - "stack pointer can be ignored for this exercise")

} emulstate;

extern emulstate make_emulstate();
extern void fprint_emulstate(FILE *stream, emulstate *state);
// Returns true if program should continue (no halt)
extern bool emulstep(emulstate *state);

// Utility function to get a range from a ulong. Useful for unpacking an instruction.
extern ulong get_value(ulong from, uint offset, uint size);
// Utility function to set a register value, and correct for 32/64 bit mode.
extern void set_reg(emulstate *state, bool sf, byte rg, ullong value);
#endif