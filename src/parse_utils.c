#include <ctype.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "parse_utils.h"
#include "symbol_table.h"

char *trim_left(char *str)
{
  while (isspace(*str)) // Safe since '\0' is not a space
  {
    str++;
  }
  return str;
}

char *finish_parse_operand(char *str)
{
  str = trim_left(str);
  if (str[0] == '\0')
  {
    return str;
  }
  else if (str[0] == ',')
  {
    return trim_left(str + 1);
  }
  else
  {
    fprintf(stderr, "Error: Invalid characters after complete operand %s\n", str);
    exit(1);
  }
}

char *parse_register(char *str, ulong *reg, bool *sf, bool *sp_used)
{
  // Set sf flag (true = 64-bit mode = x)
  if (str[0] == 'x')
  {
    *sf = true;
  }
  else if (str[0] == 'w')
  {
    *sf = false;
  }
  else
  {
    fprintf(stderr, "Error: Invalid register specifier %c\n", str[0]);
    exit(1);
  }
  str++;

  bool is_sp = strncmp(str, "sp", 2) == 0;
  if (is_sp || strncmp(str, "zr", 2) == 0)
  {
    *sp_used = is_sp;
    *reg = MAX_REG;
    return str + 2;
  }
  *sp_used = false;

  // Parse register number
  *reg = strtoul(str, &str, 10);
  if (*reg > MAX_REG)
  {
    fprintf(stderr, "Error: Register number out of bounds %lu\n", *reg);
    exit(1);
  }
  return str;
}

char *parse_imm(char *str, ulong *imm)
{
  *imm = strtoul(str, &str, 0);
  return str;
}

char *parse_simm(char *str, long *simm)
{
  *simm = strtol(str, &str, 0);
  return str;
}

char *parse_literal(char *str, ulong *lit, symbol_table_t st)
{
  // Check if the literal is a number
  if (isdigit(str[0]))
  {
    return parse_imm(str, lit);
  }

  // Find end of label
  char *end = str;
  while (!isspace(*end) && *end != '\0' && *end != ',')
  {
    end++;
  }
  long address = symbol_table_find(st, str, end - str);
  if (address < 0)
  {
    fprintf(stderr, "Error: Undefined label %.*s\n", (int)(end - str), str);
    exit(1);
  }
  *lit = address;
  return end;
}
