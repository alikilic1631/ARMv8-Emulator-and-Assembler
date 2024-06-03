#include "instr_branch.h"

#define UncondTest 0x7E000000
#define UncondExpected 0xA000000

#define RegisterTest 0xFFFFFC1F
#define RegisterExpected 0xD61F0000

#define CondTest 0x7F800000
#define CondExpected 0x2A000000

#define EQ 0
#define NE 1
#define GE 10
#define LT 11
#define GT 12
#define LE 13
#define AL 14

bool exec_branch_instr(emulstate *state, ulong raw)
{
  if ((raw & UncondTest) == UncondExpected){
    ulong simm26 = get_value(raw,0,26);
    ullong offset = simm26*4;
    state->pc += sign_extend(offset, get_value(simm26, 0, 26));
  }

  else if ((raw & RegisterTest) == RegisterExpected){ 
    ulong xn = get_value(raw,5,5);
    state->pc += get_reg(state, 1, xn);
  }

  else if ((raw & CondTest) == CondExpected) {
    ulong simm19 = get_value(raw,5,19);
    ullong offset = simm19*4;
    ulong cond = get_value(raw,0,4);
    bool execute = 0;

    switch (cond){
      case EQ:
        execute = (state->pstate.zero == 1);
      case NE:
        execute = (state->pstate.zero == 0);
      case LT:
        execute = (state->pstate.negative == state->pstate.overflow);
      case GT:
        execute = (state->pstate.negative != state->pstate.overflow);
      case LE:
        execute = !((state->pstate.zero == 0) & (state->pstate.negative == state->pstate.overflow));
      case AL:
        execute = 1;

      if (execute) {
        state->pc += sign_extend(offset, get_value(simm19, 0, 19));
      } 
    }

  }

  else {
    return 0;
  }

  return 1;
}
