#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "assembler.h"

char *data_processing[] = {"add", "adds", "sub", "subs", "cmp", "cmn", "neg", "negs",
                           "and", "ands", "bic", "bics", "eor", "orr", "eon", "orn", "tst", "movk", "movn",
                           "movz", "mov", "mvn", "madd", "msub", "mul", "mneg", NULL};
char *branching[] = {"b", "b.cond", "br", NULL};
char *loads_stores[] = {"str", "ldr", NULL};

bool instruction_type(const char *instr, char **array)
{
  for (int i = 0; array[i] != NULL; i++)
  {
    if (strcmp(instr, array[i]) == 0)
    {
      return true;
    }
  }
  return false;
}

void add_symbol(const char *label, int address)
{
  if (symbol_count >= MAX_SYMBOLS)
  {
    fprintf(stderr, "Symbol table overflow\n");
    exit(EXIT_FAILURE);
  }
  strncpy(symbol_table[symbol_count].label, label, MAX_LABEL_LENGTH - 1);
  symbol_table[symbol_count].label[MAX_LABEL_LENGTH - 1] = '\0'; // Ensure null-termination
  symbol_table[symbol_count].address = address;
  symbol_count++;
}

int get_symbol_address(const char *label)
{
  for (int i = 0; i < symbol_count; i++)
  {
    if (strcmp(symbol_table[i].label, label) == 0)
    {
      return symbol_table[i].address;
    }
  }
  fprintf(stderr, "Undefined label: %s\n", label);
  exit(EXIT_FAILURE);
}

void print_symbol_table(void)
{
  for (int i = 0; i < symbol_count; i++)
  {
    printf("%s: %d\n", symbol_table[i].label, symbol_table[i].address);
  }
}

void first_pass(FILE *source_file)
{
  char line[256];
  int address = 0;

  while (fgets(line, sizeof(line), source_file))
  {
    char *label_end = strchr(line, ':');
    if (label_end)
    {
      *label_end = '\0';
      add_symbol(line, address);
    }
    else
    {
      // Increment address by 4 bytes for each instruction or directive
      address += 4;
    }
  }

  // handle the error in case the line cannot be read from the file
  if (ferror(source_file))
  {
    fprintf(stderr, "Error reading from file\n");
    exit(EXIT_FAILURE);
  }

  print_symbol_table();
}

unsigned int encode_add(const char *operands)
{
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

void write_binary(FILE *output_file, unsigned int instruction)
{
  fwrite(&instruction, sizeof(instruction), 1, output_file);
}

void parse_instruction(const char *line, FILE *output_file)
{
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

  if (instruction_type(opcode, data_processing))
  {
    binary_instruction = encode_add(operands);
  }
  else if (instruction_type(opcode, loads_stores))
  {
    // binary_instruction = encode_ldr(operands);
  }
  else if (instruction_type(opcode, branching))
  {
    // binary_instruction = encode_b(operands);
  }
  else
  {
    fprintf(stderr, "Unknown opcode: %s\n", opcode);
    exit(EXIT_FAILURE);
  }

  write_binary(output_file, binary_instruction);
}

void second_pass(FILE *source_file, FILE *output_file)
{
  char line[256];

  while (fgets(line, sizeof(line), source_file))
  {
    char *label_end = strchr(line, ':');
    if (!label_end)
    {
      parse_instruction(line, output_file);
    }
  }
}
