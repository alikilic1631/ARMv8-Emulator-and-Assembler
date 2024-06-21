#include "symbol_table.h"

typedef unsigned int uint;
typedef unsigned long ulong;
typedef unsigned long long ullong;

extern ulong encode_dp(symbol_table_t st, char *opcode, char *operands);
extern ulong encode_sdt(symbol_table_t st, char *opcode, char *operands, long address);
extern ulong encode_branch(symbol_table_t st, char *opcode, char *operands, long address);
extern ulong encode_directives(symbol_table_t st, char *opcode, char *operands);
extern ulong encode_conditionals(symbol_table_t st, char *opcode, char *operands);
extern ulong encode_simd_fp(symbol_table_t st, char *opcode, char *operands);