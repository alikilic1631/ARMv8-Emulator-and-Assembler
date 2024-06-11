#include <stdlib.h>
#include <string.h>

#define MAX_SYMBOLS 100
#define MAX_LABEL_LENGTH 64

typedef struct {
    char label[MAX_LABEL_LENGTH];
    int address;
} symbol_t;

symbol_t symbol_table[MAX_SYMBOLS];
int symbol_count = 0;
