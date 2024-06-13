#include <stdbool.h>
#include <stdint.h>
#include "instr_dpimm.h"

#define arith_instr 2
#define wide_move_instr 5
#define ADD 0
#define ADDS 1
#define SUB 2
#define SUBS 3
#define MOVN 0
#define MOVZ 2
#define MOVK 3

bool exec_dpimm_instr(emulstate state, ulong raw)
{
  bool sf = get_value(raw, 31, 1); // 0=32-bit, 1=64-bit
  ulong rd = get_value(raw, 0, 5); // 11111=Zero Register
  ulong opc = get_value(raw, 29, 2);
  ulong operand = get_value(raw, 5, 18);
  ulong opi = get_value(raw, 23, 3);

  if (opi == arith_instr)
  {
    // Arithmetic instructions
    bool sh = get_value(raw, 22, 1);
    ulong imm12 = get_value(raw, 10, 12);
    ulong rn = get_value(raw, 5, 5);
    ullong rn_val = get_reg(state, sf, rn);
    ullong result;

    if (sh)
    {
      imm12 <<= 12;
    }

    switch (opc)
    {
    case ADD:
    {
      result = rn_val + imm12;
      set_reg(state, sf, rd, result);
      return true;
    }
    case ADDS:
    {
      result = rn_val + imm12;
      set_reg(state, sf, rd, result);
      set_pstate_flags(state, sf, result, rn_val, imm12, true); // update condition flags
      return true;
    }
    case SUB:
    {
      result = rn_val - imm12;
      set_reg(state, sf, rd, result);
      return true;
    }
    case SUBS:
    {
      result = rn_val - imm12;
      set_reg(state, sf, rd, result);
      set_pstate_flags(state, sf, result, rn_val, imm12, false);
      return true;
    }
    default:
      return false;
    }
  }
  else if (opi == wide_move_instr)
  {
    // Wide move instructions
    ulong hw = get_value(raw, 21, 2);
    ulong imm16 = get_value(raw, 5, 16);
    operand = imm16 << (hw * 16);

    switch (opc)
    {
    case MOVN:
    {
      operand = ~operand;
      set_reg(state, sf, rd, operand);
      return true;
    }
    case MOVZ:
      set_reg(state, sf, rd, operand);
      return true;
    case MOVK:
    {
      ullong rd_val = get_reg(state, sf, rd);
      ulong shift = hw * 16;
      ulong mask = 0xFFFFul << shift;
      rd_val &= ~(mask);
      rd_val |= (imm16 << shift); // (rd_val & ~mask) | (imm16 << shift)
      set_reg(state, sf, rd, rd_val);
      return true;
    }
    default:
      return false;
    }
  }
  return false;
}

void set_pstate_flags(emulstate state, bool sf, ullong result, ullong rn, ullong op2, bool add)
{
  // Set flags
  if (sf)
  {
    state->pstate.negative = (result >> 63) != 0;
  }
  else
  {
    state->pstate.negative = (result >> 31) != 0;
  }
  state->pstate.zero = (result == 0);
  if (add)
  {
    state->pstate.carry = (result < rn);
    if (((rn ^ op2) >= 0) && ((rn ^ result) < 0))
    {
      state->pstate.overflow = 1;
    }
  } else
  {
    state->pstate.carry = (rn >= op2);
    state->pstate.overflow = 0;
    if (((rn ^ op2) < 0) && ((rn ^ result) < 0))
    {
      state->pstate.overflow = 1;
    }
  }
}
