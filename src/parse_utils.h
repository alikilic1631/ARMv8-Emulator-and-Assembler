#include <stdbool.h>
#include "symbol_table.h"

#ifndef PARSE_UTILS_H
#define PARSE_UTILS_H

#define MAX_REG 31

typedef unsigned char byte;
typedef unsigned long ulong;

// Returns a substring of the argument string without leading whitespace.
extern char *trim_left(char *str);
// Finishes parsing an operand by looking for '\0' or ',' and returns the remaining substring.
extern char *finish_parse_operand(char *str);
// Parses a register from the argument string and returns the remaining substring.
extern char *parse_register(char *str, ulong *reg, bool *sf, bool *sp_used);
// Parses a register or SIMD register from the argument string and returns the remaining substring.
extern char *parse_reg_or_simd(char *str, ulong *reg, bool *sf, bool *sp_used, char *ftype);
// Parses an unsigned immediate value from the argument string and returns the remaining substring.
extern char *parse_imm(char *str, ulong *imm);
// Parses a signed immediate value from the argument string and returns the remaining substring.
extern char *parse_simm(char *str, long *imm);
// Parses a signed floating immediate value from the argument string and returns the remaining substring.
extern char *parse_fimm(char *str, double *fimm);
// Parses a literal (immediate address or label) from the argument string and returns the remaining substring.
extern char *parse_literal(char *str, ulong *lit, symbol_table_t st);

#endif