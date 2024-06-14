#include "emulator.h"

typedef unsigned long ulong;

extern void set_pstate_flags(emulstate state, bool sf, ullong result, ullong rn, ullong op2, bool add);
extern bool exec_dpimm_instr(emulstate state, ulong raw);