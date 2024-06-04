#include "emulator.h"

typedef unsigned long ulong;

extern bool exec_dpreg_instr(emulstate *state, ulong raw);

extern ullong sf_checker(ullong value, bool sf);