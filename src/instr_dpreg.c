#include "instr_dpreg.h"
#include <stdbool.h>

// Initialising Masks

// 0b1001
#define ARITHMETIC_TEST 9
// 0b1000
#define ARITHMETIC_EXPECTED 8
// 0b1000
#define BIT_LOGIC_TEST 8
// 0b0000
#define BIT_LOGIC_EXPECTED 0
// 0b1111
#define MULTIPLY_TEST 15
// 0b1000
#define MULTIPLY_EXPECTED 8
// 0b1
#define LSB_MASK 1
#define ASR_32BIT_MASK 0xFFFFFFFF
#define ASR_64BIT_MASK 0xFFFFFFFFFFFFFFFF

bool exec_dpreg_instr(emulstate *state, ulong raw)
{

  bool sf = get_value(raw, 31, 1);
  bool M = get_value(raw, 28, 1);
  byte rd_addr = get_value(raw, 0, 5);
  byte rn_addr = get_value(raw, 5, 5);
  byte rm_addr = get_value(raw, 16, 5);
  byte operand = get_value(raw, 10, 6);
  byte opr = get_value(raw, 21, 4);
  byte opc = get_value(raw, 29, 2);
  ullong rd_value = get_reg(state, sf, rd_addr);
  ullong rn_value = get_reg(state, sf, rn_addr);
  ullong rm_value = get_reg(state, sf, rm_addr);

  // Define operation
  bool arithmetic = (opr & ARITHMETIC_TEST) == ARITHMETIC_EXPECTED;
  bool bit_logic = (opr & BIT_LOGIC_TEST) == BIT_LOGIC_EXPECTED;
  bool multiply = (opr & MULTIPLY_TEST) == MULTIPLY_EXPECTED;

  if (!M)
  {
    if ((sf && (operand >= 64)) || (!sf && (operand >= 32)))
    {
      return false;
    }
    
    byte shift = get_value(opr, 1, 2);
    bool N = get_value(opr, 0, 1);

    // Shifts
    switch (shift)
    {
      // LSL
      case 0:
        {rm_value <<= operand;
        break;}
      // LSR
      case 1:
        {rm_value >>= operand;
        break;}
      // ASR
      case 2:
        {bool MSB = 0;
        if (sf) 
        {
          MSB = (rm_value >> 63) == 1;
          rm_value >>= operand;
          if (MSB)
          {
            rm_value |= (ASR_64BIT_MASK << (64 - operand));
          }
        }
        else
        {
          MSB = (rm_value >> 31) == 1;
          rm_value >>= operand;
          if (MSB)
          {
            rm_value |= (ASR_32BIT_MASK << (32 - operand));
          }
        }
        break;}
      // ROR
      case 3:
        {if (!bit_logic)
        {
          return false;
        }

        for (int i = 0; i < operand; i++)
        {
          bool LSB = rm_value & LSB_MASK;
          rm_value >>= 1;
          if (LSB)
          {
            if (sf)
            {
              rm_value |= ((ullong) 1 << 63);
            }
            else 
            {
              rm_value |= ((ullong) 1 << 31);
            }
          }
        }
        break;}
      default:
        {return false;}
    }

    // Checking N (negate)
    if (bit_logic && N) 
    {
      rm_value = ~rm_value;
    }

    if (bit_logic)
    {
      switch (opc)
      {
      // and
      case 0:
        {rd_value = rn_value & rm_value;
        rd_value = sf_checker(rd_value, sf);
        break;}
      // or
      case 1:
        {rd_value = rn_value | rm_value;
        rd_value = sf_checker(rd_value, sf);
        break;}
      // xor
      case 2:
        {rd_value = rn_value ^ rm_value;
        rd_value = sf_checker(rd_value, sf);
        break;}
      // and (setting flags)
      case 3:
        {rd_value = rn_value & rm_value;
        rd_value = sf_checker(rd_value, sf);
        if (sf) 
        {
          state->pstate.negative = (rd_value >> 63) == 1;
        }
        else 
        {
          state->pstate.negative = (rd_value >> 31) == 1;
        }
        state->pstate.zero = rd_value == 0;
        state->pstate.carry = 0;
        state->pstate.overflow = 0;
        break;}
      default:
        {return false;}
      }
    }
    else if (arithmetic)
    {
      switch (opc)
      {
      // add
      case 0:
        {rd_value = rn_value + rm_value;
        rd_value = sf_checker(rd_value, sf);
        break;}
      // add (setting flags)
      case 1:
        {rd_value = rn_value + rm_value;
        rd_value = sf_checker(rd_value, sf);
        if (sf) 
        {
          state->pstate.negative = (rd_value >> 63) == 1;
        }
        else 
        {
          state->pstate.negative = (rd_value >> 31) == 1;
        }
        state->pstate.zero = rd_value == 0;
        state->pstate.carry = rd_value < rn_value;
        state->pstate.overflow = 0;
        if (((rn_value ^ rm_value) >= 0) && ((rn_value ^ rd_value) < 0))
        {
          state->pstate.overflow = 1;
        }
        break;}
      // subtract
      case 2:
        {rd_value = rn_value - rm_value;
        rd_value = sf_checker(rd_value, sf);
        break;}
      // subtract (setting flags)
      case 3:
        {rd_value = rn_value - rm_value;
        rd_value = sf_checker(rd_value, sf);
        if (sf) 
        {
          state->pstate.negative = (rd_value >> 63) == 1;
        }
        else 
        {
          state->pstate.negative = (rd_value >> 31) == 1;
        }
        state->pstate.zero = rd_value == 0;
        state->pstate.carry = rd_value <= rn_value;
        state->pstate.overflow = 0;
        if (((rn_value ^ rm_value) < 0) && ((rn_value ^ rd_value) < 0))
        {
          state->pstate.overflow = 1;
        }
        break;}
      default:
        {return false;}
      }
    }
  }
  else if (M && multiply)
  {
    bool x = get_value(operand , 5, 1);
    byte ra_addr = get_value(operand, 0, 5);
    ullong ra_value = get_reg(state, sf, ra_addr);

    // multiply-subtract
    if (x)
    {

      rd_value = ra_value - (rn_value * rm_value);
      rd_value = sf_checker(rd_value, sf);
    }
    // multiply - add
    else 
    {
      rd_value = ra_value + (rn_value * rm_value);
      rd_value = sf_checker(rd_value, sf);
    }
  }

  set_reg(state, sf, rd_addr, rd_value);
  return true;
}
