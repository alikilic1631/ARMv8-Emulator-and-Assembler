#include <stdlib.h>

#define MAX_ARG_COUNT

typedef struct {
    int argc;
    char *argv[MAX_ARG_COUNT];
} instr_t;
