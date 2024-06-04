#include "instr_branch.h"
#include <stdbool.h>

#define UncondTest 0xFC000000
#define UncondExpected 0x14000000

#define RegisterTest 0xFFFFFC1F
#define RegisterExpected 0xD61F0000

#define CondTest 0xFF000010
#define CondExpected 0x54000000

#define EQ 0x0
#define NE 0x1
#define GE 0xA
#define LT 0xB
#define GT 0xC
#define LE 0xD
#define AL 0xE

bool exec_branch_instr(emulstate *state, ulong raw)
{
  // Unconditional branch
  if ((raw & UncondTest) == UncondExpected){
    ulong simm26 = get_value(raw,0,26);
    ullong offset = sign_extend_64bit(simm26 * INSTR_SIZE, 25);
    state->pc += offset;
  }

  // Register branch
  else if ((raw & RegisterTest) == RegisterExpected){ 
    byte xn = get_value(raw,5,5);
    state->pc = get_reg(state, 1, xn);
  }

  // Conditional branch
  else if ((raw & CondTest) == CondExpected) {
    ulong simm19 = get_value(raw,5,19);
    ullong offset = sign_extend_64bit(simm19 * INSTR_SIZE, 18);
    byte cond = get_value(raw,0,4);
    bool execute = 0;

    // Determining conditions
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
    }
    if (execute) {
      state->pc += offset;
    }
    else{ 
      state->pc += INSTR_SIZE;
    }
  }

  else {
    return false;
  }

  return true;
}

ullong sign_extend_64bit(ullong n, int sign_bit)
{
  if (n & (1ull << sign_bit))
  {
    n |= (ullong)(-1) << (sign_bit + 1);
  }
  return n;
}
