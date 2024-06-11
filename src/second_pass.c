#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "second_pass.h"

unsigned int encode_add(const char *operands) {
    unsigned int binary_instruction = 0;

    // Parse the operands
    char rd[8], rn[8], rm[8];
    sscanf(operands, "%s %s %s", rd, rn, rm);

    // Encode the 'add' instruction
    // binary_instruction |= 0b00001011000000000000000000000000; // Set the opcode
    // binary_instruction |= (atoi(rd) & 0b111) << 12; // Set the destination register
    // binary_instruction |= (atoi(rn) & 0b111) << 16; // Set the first operand register
    // binary_instruction |= (atoi(rm) & 0b111) << 0; // Set the second operand register

    return binary_instruction;
}

void write_binary(FILE *output_file, unsigned int instruction) {
    fwrite(&instruction, sizeof(instruction), 1, output_file);
}

void parse_instruction(const char *line, FILE *output_file) {
    char opcode[8];
    char operands[256]; // Assuming enough space for operands
    sscanf(line, "%s %s", opcode, operands);

    unsigned int binary_instruction = 0;

    // Encode the instruction based on the opcode and operands
    // if (strcmp(opcode, "add") == 0) {
    //     // Encode the 'add' instruction
    //     binary_instruction = encode_add(operands);
    // } else if (strcmp(opcode, "ldr") == 0) {
    //     binary_instruction = encode_ldr(operands);
    // }
    
    // else {
    //     fprintf(stderr, "Unknown opcode: %s\n", opcode);
    //     exit(EXIT_FAILURE);
    // }

    if (instruction_type(opcode, data_processing)) {
        binary_instruction = encode_add(operands);
    } else if (instruction_type(opcode, loads_stores)) {
        // binary_instruction = encode_ldr(operands);
    } else if (instruction_type(opcode, branching)) {
        // binary_instruction = encode_b(operands);
    } else {
        fprintf(stderr, "Unknown opcode: %s\n", opcode);
        exit(EXIT_FAILURE);
    }

    write_binary(output_file, binary_instruction);
}

void second_pass(FILE *source_file, FILE *output_file) {
    char line[256];

    while (fgets(line, sizeof(line), source_file)) {
        char *label_end = strchr(line, ':');
        if (!label_end) {
            parse_instruction(line, output_file);
        }
    }
}
