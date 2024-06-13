#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

typedef struct
{
    char *label;
    long address;
} symbol_t;

struct symbol_table_t
{
    symbol_t *elements;
    int cap;
    int len;
};
// Symbol Table ADT
typedef struct symbol_table_t *symbol_table_t;

// Allocates and initialises a new symbol table.
extern symbol_table_t symbol_table_init();
// Frees the memory allocated for a symbol table.
extern void symbol_table_free(symbol_table_t st);
// Appends a new symbol to the symbol table.
extern void symbol_table_append(symbol_table_t st, char *label, long address);
// Finds a symbol in the symbol table and returns its address.
extern long symbol_table_find(symbol_table_t st, char *label, int label_len);
#endif