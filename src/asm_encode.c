#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "asm_encode.h"
#include "parse_utils.h"

char *arithmetic[] = {"add", "adds", "sub", "subs", NULL};
char *logic[] = {"and", "bic", "orr", "orn", "eor", "eon", "ands", "bics", NULL};
char *movs[] = {"movn", "movz", "movk", NULL};
// remaining madd, msub

bool is_integer(const char *str, long *num) {
    char *endptr;
    *num = strtol(str, &endptr, 0); // Automatically handles both decimal and hex
    return *endptr == '\0'; // Checks if the entire string was converted
}

char* get_condition_code(const char* str) {
    if (strlen(str) <= 2) {
        return ""; // Return an empty string if the input is too short
    }
    return (char *)(str + 2); // Return a pointer to the third character
}

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
  printf("opcode: %s\n", opcode);
  printf("operands: %s\n", operands);
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

      if ((!r1_sp_used && r1 == MAX_REG) || (!r2_sp_used && r2 == MAX_REG))
      {
        fprintf(stderr, "Error: Cannot use ZR as register in immediate arithmetic\n");
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
  else if (index_of(opcode, movs) >= 0)
  {
    instr = set_value(instr, r1, 0, 5);
    int mov_idx;
    if (strcmp(opcode, "movn") == 0)
    {
      mov_idx = 0;
    }
    else if (strcmp(opcode, "movz") == 0)
    {
      mov_idx = 2;
    }
    else if (strcmp(opcode, "movk") == 0)
    {
      mov_idx = 3;
    }
    instr = set_value(instr, mov_idx, 29, 2);

    if (operands[0] == '#')
    {
      // 0b100101 for wide move
      instr = set_value(instr, 0x25, 23, 6);

      ulong imm;
      operands = finish_parse_operand(parse_imm(operands + 1, &imm));
      instr = set_value(instr, imm, 5, 16);

      if (operands[0] != '\0')
      {
        if (strncmp(operands, "lsl #", 5) != 0)
        {
          fprintf(stderr, "Error: Only LSL shift supported for immediate mov\n");
          exit(1);
        }
        ulong shift;
        operands = finish_parse_operand(parse_imm(operands + 5, &shift));
        ulong hw = shift / 16;
        if (!r1_sf && (hw != 0 || hw != 1))
        {
          fprintf(stderr, "Error: Only LSL #0 or #16 supported for immediate mov on 32-bit registers\n");
          exit(1);
        }
        instr = set_value(instr, hw, 21, 2);
      }

      if (!r1_sp_used && r1 == MAX_REG)
      {
        fprintf(stderr, "Error: Cannot use ZR as register in immediate mov\n");
        exit(1);
      }
      instr = set_value(instr, r1_sf, 31, 1);
    }
  }
  else
  {
    fprintf(stderr, "Error: Unknown opcode\n");
    exit(1);
  }

  if (operands[0] != '\0')
  {
    fprintf(stderr, "Error: Extra operands after instruction\n");
    exit(EXIT_FAILURE);
  }
  return instr;
}

ulong encode_sdt(symbol_table_t st, char *opcode, char *operands) {
    return 0;
}

ulong encode_branch(symbol_table_t st, char *opcode, char *operands, long address) {
    ulong instr = 0;

    if (strcmp(opcode, "b") == 0) {
        ulong literal;
        operands = finish_parse_operand(parse_literal(operands, &literal, st));
        long offset = literal - address;
        instr = set_value(instr, offset / 4, 0, 26);
        instr = set_value(instr, 0x5, 26, 6); // opcode for unconditional branch
    } else if (strcmp(opcode, "br") == 0) {
        // br xn
        bool xn_sf, xn_sp_used;
        ulong xn;
        operands = finish_parse_operand(parse_register(operands, &xn, &xn_sf, &xn_sp_used));
        instr = set_value(instr, 0x0, 0, 5);
        instr = set_value(instr, xn, 5, 5);
        instr = set_value(instr, 0x3587c0, 10, 22); // opcode for register branch
    } else {
        // b.cond <literal>
        // get the letters after the first 2 letters
        char *condition = get_condition_code(opcode);
        ulong literal;
        operands = finish_parse_operand(parse_literal(operands, &literal, st));
        printf("literal: %lu\n", literal);
        printf("condition: %s\n", condition);
        printf("operands: %s\n", operands);
        long offset = literal - address;
        int cond_code;
        if (strcmp(condition, "eq") == 0) cond_code = 0x0;
        else if (strcmp(condition, "ne") == 0) cond_code = 0x1;
        else if (strcmp(condition, "ge") == 0) cond_code = 0xa;
        else if (strcmp(condition, "lt") == 0) cond_code = 0xb;
        else if (strcmp(condition, "gt") == 0) cond_code = 0xc;
        else if (strcmp(condition, "le") == 0) cond_code = 0xd;
        else if (strcmp(condition, "al") == 0) cond_code = 0xe;
        instr = set_value(instr, cond_code, 0, 4);
        instr = set_value(instr, 0x0, 4, 1);
        instr = set_value(instr, offset / 4, 5, 19);
        instr = set_value(instr, 0x54, 24, 8);
    }

    return instr;
}

ulong encode_directives(symbol_table_t st, char *opcode, char *operands)
{
  return 0;
}
