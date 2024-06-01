#include <stdbool.h>
#include <stdint.h>
#include "instr_dpimm.h"

#define arith_instr 0b010
#define wide_move_instr 0b101
#define ADD 0b00
#define ADDS 0b01
#define SUB 0b10
#define SUBS 0b11
#define MOVN 0b00
#define MOVZ 0b10
#define MOVK 0b11

void set_pstate_flags(emulstate *state, bool sf, ullong result, ullong rn, ullong op2, bool add)
{
  // Set flags
  state->pstate.negative = (result < 0);
  state->pstate.zero = (result == 0);
  if (add) {
        state->pstate.carry = (result < rn);
        state->pstate.overflow = ((rn > 0) == (op2 > 0)) && ((result > 0) != (rn > 0));
    } else {
        state->pstate.carry = (rn >= op2);
        state->pstate.overflow = ((rn > 0) != (op2 > 0)) && ((result > 0) != (rn > 0));
    }
}

bool exec_dpimm_instr(emulstate *state, ulong raw)
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
      result = rn_val + imm12;
      if (rd != 31)
      {
        set_reg(state, sf, rd, result);
      }
      break;
    case ADDS:
      result = rn_val + imm12;
      if (rd != 31)
      {
        set_reg(state, sf, rd, result);
      }
      set_pstate_flags(state, sf, result, rn_val, operand, true); // update condition flags
      break;
    case SUB:
      result = rn_val - imm12;
      if (rd != 31) 
      {
          set_reg(state, sf, rd, result);
      }
      break;
    case SUBS:
      result = rn_val - operand;
      if (rd != 31) 
      {
          set_reg(state, sf, rd, result);
      }
      set_pstate_flags(state, sf, result, rn_val, operand, false);
      break;
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
      operand = ~operand;
      if (rd != 31)
      {
          set_reg(state, sf, rd, operand);
      }
      break;
    case MOVZ:
      if (rd != 31) 
      {
        set_reg(state, sf, rd, operand);
      }
      break;
    case MOVK:
      if (rd != 31) 
      {
        ullong rd_val = get_reg(state, sf, rd);
        ulong shift = hw * 16;
        ulong mask = 0xFFFF << shift; // 16 bits. Do I need to zero_extend?
        rd_val &= ~(mask);
        rd_val |= (imm16 << shift); // (rd_val & ~mask) | (imm16 << shift)
        set_reg(state, sf, rd, rd_val);
      }
      break;
    default:
      return false;
    }
  }
  return false;
}
