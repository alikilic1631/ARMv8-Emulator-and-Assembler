#include <float.h>
#include "instr_simd_fp.h"

// Testing masks
// 0b1111111001 << 21
#define FDP_TEST 0x7f200000
// 0b0011110001 << 21
#define FDP_EXPECTED 0x1e200000
// 0b10111
#define CMP_TEST 0x17
#define CMP_EXPECTED 0

bool exec_simd_fp_instr(emulstate state, ulong raw)
{
  if ((raw & FDP_TEST) == FDP_EXPECTED)
  {
    // Extract fields
    byte rd = get_value(raw, 0, 5);
    byte rn = get_value(raw, 5, 5);
    byte opc = get_value(raw, 14, 3);
    byte arith = get_value(raw, 10, 4);
    byte ftype = get_value(raw, 22, 2);

    // 2-source DP
    if (arith != 0)
    {
      arith = get_value(raw, 10, 6);
      byte rm = get_value(raw, 16, 5);
      double n = get_simd_reg(state, rn, ftype);
      double m = get_simd_reg(state, rm, ftype);
      switch (arith)
      {
      case 2:
      { // fmul
        set_simd_reg(state, rd, ftype, n * m);
        return true;
      }
      case 6:
      { // fdiv
        set_simd_reg(state, rd, ftype, n / m);
        return true;
      }
      case 10:
      { // fadd
        set_simd_reg(state, rd, ftype, n + m);
        return true;
      }
      case 14:
      { // fsub
        set_simd_reg(state, rd, ftype, n - m);
        return true;
      }
      case 18:
      { // fmax
        if (n > m)
        {
          set_simd_reg(state, rd, ftype, n);
        }
        else
        {
          set_simd_reg(state, rd, ftype, m);
        }
        return true;
      }
      case 22:
      { // fmin
        if (n < m)
        {
          set_simd_reg(state, rd, ftype, n);
        }
        else
        {
          set_simd_reg(state, rd, ftype, m);
        }
        return true;
      }
      case 34:
      { // fnmull
        set_simd_reg(state, rd, ftype, -(n * m));
        return true;
      }
      case 8:
      {
        if ((rd & CMP_TEST) == CMP_EXPECTED)
        { // fcmp
          opc = get_value(raw, 3, 1);
          ldouble result = n; // ldouble because easier to check overflow.
          if (opc == 0 || rm != 0)
          {
            result -= m;
          }
          ldouble min, max;
          switch (ftype)
          {
          case 0:
          {
            min = FLT_MIN;
            max = FLT_MAX;
            break;
          }
          case 1:
          {
            min = DBL_MIN;
            max = DBL_MAX;
            break;
          }
          }
          state->pstate.negative = n < m;
          state->pstate.zero = n == m;
          state->pstate.carry = false;
          state->pstate.overflow = result >= max || result <= -max ||
                                   (result > 0 && result <= min) || (result < 0 && result >= -min);
          return true;
        }
        else
          return false;
      }
      default:
        return false;
      }
    }

    // 1-source DP
    bool imm = get_value(raw, 12, 1);
    if (imm)
    {
      return false; // immediate not supported
    }
    switch (opc)
    {
    case 3:
    { // fabs
      double val = get_simd_reg(state, rn, ftype);
      if (val < 0)
        val = -val;
      set_simd_reg(state, rd, ftype, val);
      return true;
    }
    case 5:
    { // fneg
      double val = get_simd_reg(state, rn, ftype);
      set_simd_reg(state, rd, ftype, -val);
      return true;
    }
    case 0:
    case 4:
    {
      byte opcode = get_value(raw, 16, 3);
      bool sf = get_value(raw, 31, 1);

      if (opcode == 7)
      { // int -> fp
        double val;
        ullong *ptr = (ullong *)(&val);
        *ptr = get_reg(state, sf, rn);
        set_simd_reg(state, rd, 1, val);
      }
      else if (opcode == 6)
      { // fp -> int
        double val = get_simd_reg(state, rn, 1);
        ullong *ptr = (ullong *)(&val);
        set_reg(state, sf, rd, *ptr);
      }
      else
      {
        byte rm = get_value(raw, 16, 5);
        double n = get_simd_reg(state, rn, ftype);
        switch (rm)
        {
        case 24:
        { // fcvtzs
          set_reg(state, sf, rd, (long long)n);
          return true;
        }
        case 2:
        { // scvtf
          ullong val = get_reg(state, sf, rn);
          set_simd_reg(state, rd, ftype, val);
          return true;
        }
        default:
          return false;
        }
      }
      return true;
    }
    case 1:
    { // fp -> fp
      double val = get_simd_reg(state, rn, ftype);
      set_simd_reg(state, rd, ftype, val);
      return true;
    }
    }
    return false;
  }
  return false;
}