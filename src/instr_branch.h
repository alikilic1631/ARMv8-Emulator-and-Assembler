#include "emulator.h"

typedef unsigned long ulong;

extern bool exec_branch_instr(emulstate *state, ulong raw);