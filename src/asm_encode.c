#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "asm_encode.h"
#include "parse_utils.h"

char *arithmetic[] = {"add", "adds", "sub", "subs", NULL};
char *logic[] = {"and", "bic", "orr", "orn", "eor", "eon", "ands", "bics", NULL};

static int index_of(char *opcode, char **array)
{
  for (int i = 0; array[i] != NULL; i++)
  {
    if (strcmp(opcode, array[i]) == 0)
    {
      return i;
    }
  }
  return -1;
}

// Utility function to set a range of bits in a `base` ulong.
static ulong set_value(ulong base, ulong value, uint offset, uint size)
{
  ulong mask = (1ull << (offset + size)) - (1ul << offset);
  return (base & ~mask) | ((value << offset) & mask);
}

ulong encode_dp(symbol_table_t st, char *opcode, char *operands)
{
  ulong instr = 0;
  bool r1_sf, r1_sp_used;
  ulong r1;
  operands = finish_parse_operand(parse_register(operands, &r1, &r1_sf, &r1_sp_used));

  int arith_idx;
  int logic_idx;
  if ((arith_idx = index_of(opcode, arithmetic)) >= 0)
  {
    bool r2_sf, r2_sp_used;
    ulong r2;
    operands = finish_parse_operand(parse_register(operands, &r2, &r2_sf, &r2_sp_used));

    instr = set_value(instr, r1, 0, 5);
    instr = set_value(instr, r2, 5, 5);
    instr = set_value(instr, arith_idx, 29, 2);
    if (operands[0] == '#')
    {
      // 0b100010 for arithmetic immediate
      instr = set_value(instr, 0x22, 23, 6);

      ulong imm;
      operands = finish_parse_operand(parse_imm(operands + 1, &imm));
      instr = set_value(instr, imm, 10, 12);

      if (operands[0] != '\0')
      {
        if (strncmp(operands, "lsl #", 5) != 0)
        {
          fprintf(stderr, "Error: Only LSL shift supported for immediate arithmetic\n");
          exit(1);
        }
        ulong shift;
        operands = finish_parse_operand(parse_imm(operands + 5, &shift));
        if (shift == 12)
        {
          instr = set_value(instr, 1, 22, 1);
        }
        else if (shift == 0)
        {
          instr = set_value(instr, 0, 22, 1);
        }
        else
        {
          fprintf(stderr, "Error: Only LSL #0 or #12 supported for immediate arithmetic\n");
          exit(1);
        }
      }

      if (!r2_sp_used && r2 == MAX_REG)
      {
        fprintf(stderr, "Error: Cannot use ZR as Rn in immediate arithmetic\n");
        exit(1);
      }
      // adds and subs are allowed to use ZR for Rd
      if (arith_idx != 1 && arith_idx != 3 && !r1_sp_used && r1 == MAX_REG)
      {
        fprintf(stderr, "Error: Cannot use ZR as Rd in immediate arithmetic without setting flags\n");
        exit(1);
      }
      if (r1_sf != r2_sf)
      {
        fprintf(stderr, "Error: Register sizes must match in immediate arithmetic\n");
        exit(1);
      }
      instr = set_value(instr, r1_sf, 31, 1);
    }
  }
  else if ((logic_idx = index_of(opcode, logic)) >= 0)
  {
    bool r2_sf, r2_sp_used;
    ulong r2;
    operands = finish_parse_operand(parse_register(operands, &r2, &r2_sf, &r2_sp_used));

    bool r3_sf, r3_sp_used;
    ulong r3;
    operands = finish_parse_operand(parse_register(operands, &r3, &r3_sf, &r3_sp_used));

    instr = set_value(instr, r1, 0, 5);
    instr = set_value(instr, r2, 5, 5);
    instr = set_value(instr, r3, 16, 5);
    instr = set_value(instr, logic_idx % 2, 21, 1); // negation bit
    // 0b01010 for bit-logic
    instr = set_value(instr, 0xa, 24, 5);
    instr = set_value(instr, logic_idx / 2, 29, 2);

    if (r1_sp_used || r2_sp_used || r3_sp_used)
    {
      fprintf(stderr, "Error: Cannot use SP as register in bit-logic\n");
      exit(1);
    }

    if (r1_sf != r2_sf || r1_sf != r3_sf)
    {
      fprintf(stderr, "Error: Register sizes must match in bit-logic\n");
      exit(1);
    }
    instr = set_value(instr, r1_sf, 31, 1);

    if (operands[0] != '\0')
    {
      ulong shift_type = 0;
      ulong shift_imm = 0;
      if (strncmp(operands, "lsl #", 5) == 0)
      {
        shift_type = 0;
      }
      else if (strncmp(operands, "lsr #", 5) == 0)
      {
        shift_type = 1;
      }
      else if (strncmp(operands, "asr #", 5) == 0)
      {
        shift_type = 2;
      }
      else if (strncmp(operands, "ror #", 5) == 0)
      {
        shift_type = 3;
      }
      else
      {
        fprintf(stderr, "Error: Unsupported shift type\n");
        exit(1);
      }
      operands = finish_parse_operand(parse_imm(operands + 5, &shift_imm));
      instr = set_value(instr, shift_imm, 10, 6);
      instr = set_value(instr, shift_type, 22, 2);
    }
  }
  if (operands[0] != '\0')
  {
    fprintf(stderr, "Error: Extra operands after instruction\n");
    exit(1);
  }
  return instr;
}

ulong encode_sdt(symbol_table_t st, char *opcode, char *operands)
{
  return 0;
}

ulong encode_branch(symbol_table_t st, char *opcode, char *operands)
{
  return 0;
}

ulong encode_directives(symbol_table_t st, char *opcode, char *operands)
{
  return 0;
}
