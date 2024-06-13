#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include "symbol_table.h"

typedef unsigned char byte;
typedef unsigned long ulong;

typedef struct
{
    char *opcode;
    char *operands;
} instr_t;

extern void first_pass(FILE *fin, symbol_table_t symbol_table);
extern void second_pass(FILE *fin, FILE *fout, symbol_table_t symbol_table);