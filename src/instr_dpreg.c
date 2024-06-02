#include "instr_dpreg.h"
#include <stdbool.h>

// Initialising Masks

// 0b111
#define DP_REG_TEST 7
// 0b101
#define DP_REG_EXPECTED 5
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
// ~(0b1 << 31)
#define ASR_32BIT_MASK 2147483647
// ~(0b1 << 63)
#define ASR_64BIT_MASK 9223372036854775807
// 0b1
#define LSB_MASK 1
// 0b1 << 31
#define MSB_32BIT_MASK 2147483648
// 0b1 << 63  
#define MSB_64BIT_MASK 0x8000000000000000

bool exec_dpreg_instr(emulstate *state, ulong raw)
{
  // byte reg_indicator = get_value(raw, 25, 3);
  // if ((reg_indicator & DP_REG_TEST) != DP_REG_EXPECTED)
  // {
  //   return false;
  // }

  bool sf = get_value(raw, 31, 1);
  bool M = get_value(raw, 28, 1);
  byte rd_addr = get_value(raw, 0, 5);
  byte rn_addr = get_value(raw, 5, 5);
  byte rm_addr = get_value(raw, 16, 5);
  byte operand = get_value(raw, 10, 6);
  byte opr = get_value(raw, 21, 4);
  byte opc = get_value(raw, 29, 2);
  byte rd_value = get_reg(state, sf, rd_addr);
  byte rn_value = get_reg(state, sf, rn_addr);
  byte rm_value = get_reg(state, sf, rm_addr);

  // Define operation
  bool arithmetic = (opr & ARITHMETIC_TEST) == ARITHMETIC_EXPECTED;
  bool bit_logic = (opr & BIT_LOGIC_TEST) == BIT_LOGIC_TEST;
  bool multiply = (opr & MULTIPLY_TEST) == MULTIPLY_EXPECTED;

  if (!M)
  {
    byte shift = get_value(opr, 1, 2);
    bool N = get_value(opr, 0, 1);

    switch (shift)
    {
      case 0:
        rm_value <<= operand;
        //set_reg(state, sf, rm_addr, rm_value);
        break;
      case 1:
        rm_value >>= operand;
        //set_reg(state, sf, rm_addr, rm_value);
        break;
      case 2:
        bool MSB = rm_value < 0;
        for (int i = 0; i < operand; i++) 
        {
          rm_value >>= 1;
          if (MSB) 
          {
            if (sf)
            {
              rm_value |= MSB_64BIT_MASK;
            }
            else 
            {
              rm_value |= MSB_32BIT_MASK;
            }
          }
        }
        //set_reg(state, sf, rm_addr, rm_value);
        // if (sf) 
        // {
        //   bool MSB = rm >> 63;
        //   for (int i = 0; i < operand; i++) 
        //   {
        //     rm >>= 1;
        //     if (MSB) {
        //       rm |= MSB_64BIT_MASK;
        //     }
        //   }
        // }
        // else 
        // {
        //   bool MSB = rm >> 31;
        //   for (int j = 0; j < operand; j++) 
        //   {
        //     rm >>= 1;
        //     if (MSB) {
        //       rm |= MSB_32BIT_MASK;
        //     }
        //   }
        // }
        break;
      case 3:
        if (!bit_logic)
        {
          return false;
        }

        for (int i = 0; i< operand; i++)
        {
          bool LSB = rm_value & LSB_MASK;
          rm_value >>= 1;
          if (LSB)
          {
            if (sf)
            {
              rm_value |= MSB_64BIT_MASK;
            }
            else 
            {
              rm_value |= MSB_32BIT_MASK;
            }
          }
        }
        //set_reg(state, sf, rm_addr, rm_value);
        // if (bit_logic)
        // {
        //   for (int i = 0; i < operand; i++) 
        //   {
        //     bool LSB = rm_value & LSB_MASK;
        //     rm >>= 1;
        //     if (LSB) 
        //     {
        //       if (sf) 
        //       {
        //         rm |= MSB_64BIT_MASK;
        //       }
        //       else
        //       {
        //         rm |= MSB_32BIT_MASK;
        //       }
        //     }
        //   }
        // }
        break;
      default:
        return false;
        break;
    }

    if (bit_logic & N) 
    {
      rm_value = ~rm_value;
    }

    set_reg(state, sf, rm_addr, rm_value);

    if (bit_logic)
    {
      switch (opc)
      {
      case 0:
        rd_value = rn_value & rm_value;
        break;
      case 1:
        rd_value = rn_value | rm_value;
        break;
      case 2:
        rd_value = rn_value ^ rm_value;
        break;
      case 3:
        rd_value = rn_value & rm_value;
        state->pstate.negative = rd_value < 0;
        state->pstate.zero = rd_value == 0;
        state->pstate.carry = 0;
        state->pstate.overflow = 0;
        break;
      default:
        break;
      }
    }
    else if (arithmetic)
    {
      switch (opc)
      {
      case 0:
        rd_value = rn_value + rm_value;
        break;
      case 1:
        rd_value = rn_value + rm_value;
        state->pstate.negative = rd_value < 0;
        state->pstate.zero = rd_value == 0;
        state->pstate.carry = rd_value < rn_value;
        state->pstate.overflow = 0;
        if (((rn_value ^ rm_value) >= 0) & ((rn_value ^ rd_value) < 0))
        {
          state->pstate.overflow = 1;
        }
        // if (sf)
        // {
        //   if ((rn_value >> 63 == rm_value >> 63) & (rn_value >> 63 != rd_value >> 63)) {
        //     state->pstate.overflow = 1;
        //   }
        //   else
        //   {
        //     state->pstate.carry = 0;
        //   }
        // }
        // else
        // {
        //   if ((rn_value >> 31 == rm_value >> 31) & (rn_value >> 31 != rd_value >> 31)) {
        //     state->pstate.overflow = 1;
        //   }
        //   else
        //   {
        //     state->pstate.carry = 0;
        //   }
        // }
        break;
      case 2:
        rd_value = rn_value - rm_value;
        break;
      case 3:
        rd_value = rn_value - rm_value;
        state->pstate.negative = rd_value < 0;
        state->pstate.zero = rd_value == 0;
        state->pstate.carry = rd_value > rn_value;
        state->pstate.overflow = 0;
        if (((rn_value ^ rm_value) < 0) & ((rn_value ^ rd_value) < 0))
        {
          state->pstate.overflow = 1;
        }
        // if (sf)
        // {
        //   if ((rn_value >> 63 != rm_value >> 63) & (rn_value >> 63 != rd_value >> 63)) {
        //     state->pstate.overflow = 1;
        //   }
        //   else
        //   {
        //     state->pstate.carry = 0;
        //   }
        // }
        // else
        // {
        //   if ((rn_value >> 31 != rm_value >> 31) & (rn_value >> 31 != rd_value >> 31)) {
        //     state->pstate.overflow = 1;
        //   }
        //   else
        //   {
        //     state->pstate.carry = 0;
        //   }
        // }
        break;
      default:
        return false;
        break;
      }
    }
  }
  else if (M & multiply)
  {
    bool x = get_value(operand , 6, 1);
    byte ra_addr = get_value(operand, 0, 5);
    byte ra_value = get_reg(state, sf, ra_addr);

    if (x)
    {
      rd_value = ra_value - (rn_value * rm_value);
    }
    else 
    {
      rd_value = ra_value + (rn_value * rm_value);
    }
  }

  set_reg(state, sf, rd_addr, rd_value);
  return true;
}
