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
    ullong offset = sign_extend(simm26*4, get_value(raw, 0, 26));
    state->pc += offset;
  }

  else if ((raw & RegisterTest) == RegisterExpected){ 
    byte xn = get_value(raw,5,5);
    state->pc = get_reg(state, 1, xn);
  }

  else if ((raw & CondTest) == CondExpected) {
    ulong simm19 = get_value(raw,5,19);
    ullong offset = sign_extend(simm19, get_value(raw, 0, 19));
    ulong cond = get_value(raw,0,4);
    bool execute = 0;

    switch (cond){
      case EQ:
        {execute = (state->pstate.zero == 1);
        break;}
      case NE:
        {execute = (state->pstate.zero == 0);
        break;}
      case GE:
        {execute = (state->pstate.negative == state->pstate.overflow);
        break;}
      case LT:
        {execute = (state->pstate.negative != state->pstate.overflow);
        break;}
      case GT:
        {execute = (state->pstate.zero == 0) && (state->pstate.negative == state->pstate.overflow);
        break;}
      case LE:
        {execute = !((state->pstate.zero == 0) && (state->pstate.negative == state->pstate.overflow));
        break;}
      case AL:
        {execute = 1;
        break;}
      default:
        return false;

      if (execute) {
        state->pc += offset;
      } 
    }

  }

  else {
    return false;
  }

  return true;
}
