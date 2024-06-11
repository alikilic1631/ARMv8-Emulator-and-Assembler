#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "first_pass.h"

void add_symbol(const char *label, int address) {
    if (symbol_count >= MAX_SYMBOLS) {
        fprintf(stderr, "Symbol table overflow\n");
        exit(EXIT_FAILURE);
    }
    strncpy(symbol_table[symbol_count].label, label, MAX_LABEL_LENGTH - 1);
    symbol_table[symbol_count].label[MAX_LABEL_LENGTH - 1] = '\0'; // Ensure null-termination
    symbol_table[symbol_count].address = address;
    symbol_count++;
}

int get_symbol_address(const char *label) {
    for (int i = 0; i < symbol_count; i++) {
        if (strcmp(symbol_table[i].label, label) == 0) {
            return symbol_table[i].address;
        }
    }
    fprintf(stderr, "Undefined label: %s\n", label);
    exit(EXIT_FAILURE);
}

void print_symbol_table(void) {
    for (int i = 0; i < symbol_count; i++) {
        printf("%s: %d\n", symbol_table[i].label, symbol_table[i].address);
    }
}

void first_pass(FILE *source_file) {
    char line[256];
    int address = 0;

    while (fgets(line, sizeof(line), source_file)) {
        char *label_end = strchr(line, ':');
        if (label_end) {
            *label_end = '\0';
            add_symbol(line, address);
        } else {
            // Increment address by 4 bytes for each instruction or directive
            address += 4;
        }
    }

    // handle the error in case the line cannot be read from the file
    if (ferror(source_file)) {
        fprintf(stderr, "Error reading from file\n");
        exit(EXIT_FAILURE);
    }

    print_symbol_table();
}
