#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define MAX_SYMBOLS 100
#define MAX_LABEL_LENGTH 64

typedef struct
{
    char label[MAX_LABEL_LENGTH];
    int address;
} symbol_t;

symbol_t symbol_table[MAX_SYMBOLS];
int symbol_count = 0;

extern void first_pass(FILE *fin);
extern void second_pass(FILE *fin, FILE *fout);