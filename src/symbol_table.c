#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "symbol_table.h"
#include "assert.h"

#define INIT_CAP 4

symbol_table_t symbol_table_init()
{
  symbol_table_t st = malloc(sizeof(symbol_table_t));
  st->elements = malloc(INIT_CAP * sizeof(symbol_t));
  st->cap = INIT_CAP;
  st->len = 0;
  return st;
}

static void symbol_table_grow(symbol_table_t st)
{
  if (st->len < st->cap)
    return; // Only grow if full.
  st->cap <<= 1;
  st->elements = realloc(st->elements, st->cap * sizeof(symbol_t));
}

static void symbol_free(void *symbol)
{
  symbol_t *sym = symbol;
  free(sym->label);
}

void symbol_table_free(symbol_table_t st)
{
  for (int i = 0; i < st->len; i++)
  {
    symbol_free(&(st->elements[i]));
  }
  free(st->elements);
  free(st);
}

void symbol_table_append(symbol_table_t st, char *label, long address)
{
  symbol_table_grow(st);
  char *label_cpy = malloc(strlen(label) + 1);
  assert(label_cpy != NULL);
  strcpy(label_cpy, label);
  st->elements[st->len].label = label_cpy;
  st->elements[st->len].address = address;
  st->len++;
}

long symbol_table_find(symbol_table_t st, char *label, int label_len)
{
  for (int i = 0; i < st->len; i++)
  {
    if (
        (label_len >= 0 && strncmp(label, st->elements[i].label, label_len) == 0) ||
        (label_len < 0 && strcmp(label, st->elements[i].label) == 0)
      )
    {
      return st->elements[i].address;
    }
  }
  return -1;
}

void print_symbol_table(symbol_table_t st)
{
  for (int i = 0; i < st->len; i++)
  {
    printf("%s: %ld\n", st->elements[i].label, st->elements[i].address);
  }
}
