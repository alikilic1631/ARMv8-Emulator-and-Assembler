#include <stdbool.h>
#include "instr_sdt.h"

// Testing masks
// 0b101111101 << 23
#define SDT_TEST 3196059648
// 0b101110000 << 23
#define SDT_EXPECTED 3087007744
// 0b10111111 << 24
#define LOAD_LITERAL_TEST 3204448256
// 0b00011000 << 24
#define LOAD_LITERAL_EXPECTED 402653184
// 0b100000111111 << 10
#define REG_OFFSET_TEST 2161664
// 0b100000011010 << 10
#define REG_OFFSET_EXPECTED 2123776
// 0b100000000001 << 10
#define INDEX_TEST 2098176
// 0b000000000001 << 10
#define INDEX_EXPECTED 1024

bool exec_sdt_instr(emulstate *state, ulong raw)
{
  bool sf = get_value(raw, 30, 1);
  bool L = true;
  bool addr_set = false;
  ullong addr = 0;
  byte rt = get_value(raw, 0, 5);

  // Calculate offset
  if ((raw & SDT_TEST) == SDT_EXPECTED)
  {
    bool U = get_value(raw, 24, 1);
    L = get_value(raw, 22, 1);
    byte xn = get_value(raw, 5, 5);
    if (U)
    {
      // Unsigned offset
      ulong imm12 = get_value(raw, 10, 12);
      addr = get_reg(state, sf, xn) + imm12;
      addr_set = true;
    }
    else if ((raw & REG_OFFSET_TEST) == REG_OFFSET_EXPECTED)
    {
      // Register offset
      byte xm = get_value(raw, 16, 5);
      addr = get_reg(state, sf, xn) + get_reg(state, sf, xm);
      addr_set = true;
    }
    else if ((raw & INDEX_TEST) == INDEX_EXPECTED)
    {
      // Pre/post indexed offset
      long simm9 = sign_extend(get_value(raw, 12, 9), 8);
      bool I = get_value(raw, 11, 1);
      addr = get_reg(state, sf, xn);
      if (I)
      {
        addr += simm9;
      }
      addr_set = true;
    }
  }
  else if ((raw & LOAD_LITERAL_TEST) == LOAD_LITERAL_EXPECTED)
  {
    // Literal Address
    long simm19 = sign_extend(get_value(raw, 5, 19), 18);
    // TODO : Does this become *8 when 64-bit? I thought that's what
    //        the spec (1.7.1) says, but tests broke...
    addr = state->pc + simm19 * 4;
    addr_set = true;
  }

  // Apply load/store
  if (addr_set)
  {
    if (L)
    {
      ullong value = load_mem(state, sf, addr);
      set_reg(state, sf, rt, value);
    }
    else
    {
      ullong value = get_reg(state, sf, rt);
      store_mem(state, sf, addr, value);
    }
    return true;
  }
  return false;
}
