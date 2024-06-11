#include <stdbool.h>

char *data_processing[] = {"add", "adds", "sub", "subs", "cmp", "cmn", "neg", "negs", 
    "and", "ands", "bic", "bics", "eor", "orr", "eon", "orn", "tst", "movk", "movn", 
    "movz", "mov", "mvn", "madd", "msub", "mul", "mneg", NULL};
char *branching[] = {"b", "b.cond", "br", NULL};
char *loads_stores[] = {"str", "ldr", NULL};

bool instruction_type(const char *instr, char **array) {
    for (int i = 0; array[i] != NULL; i++) {
        if (strcmp(instr, array[i]) == 0) {
            return true;
        }
    }
    return false;
}
