#include "instr_simd_fp.h"

// Testing masks
// 0b1111111001 << 21
#define FDP_TEST 0x7f200000
// 0b0011110001 << 21
#define FDP_EXPECTED 0x1e200000

bool exec_simd_fp_instr(emulstate state, ulong raw)
{
  if ((raw & FDP_TEST) == FDP_EXPECTED)
  {
    // Extract fields
    byte rd = get_value(raw, 0, 5);
    byte opc = get_value(raw, 14, 3);
    bool imm = get_value(raw, 12, 1);
    byte ftype = get_value(raw, 22, 2);
    if (imm)
    {
      return false; // immediate not supported
    }
    byte rn = get_value(raw, 5, 5);
    switch (opc)
    {
    case 3:
    { // fabs
      double val = get_simd_reg(state, rn, ftype);
      fprintf(stderr, "1 RD: %d, RN: %d, VAL: %f\n", rd, rn, val);
      if (val < 0)
        val = -val;
      set_simd_reg(state, rd, ftype, val);
      fprintf(stderr, "2 RD: %d, RN: %d, VAL: %f\n", rd, rn, val);
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
        fprintf(stderr, "FP -> INT: %f (%llx)\n", val, *ptr);
        set_reg(state, sf, rd, *ptr);
      }
      else
      {
        return false;
      }
      return true;
    }
    case 1:
    { // fp -> fp
      double val = get_simd_reg(state, rn, ftype);
      ullong *ptr = (ullong *)(&val);
      fprintf(stderr, "FP -> FP: %f (%llx)\n", val, *ptr);
      set_simd_reg(state, rd, ftype, val);
      return true;
    }
    }
    return false;
  }
  return false;
}