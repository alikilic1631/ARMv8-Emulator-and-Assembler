#include <assert.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "assembler.h"
#include "asm_encode.h"
#include "parse_utils.h"

#define MAX_LINE_LENGTH 256
#define INSTR_SIZE 4

char *data_processing[] = {"add", "adds", "sub", "subs",
                            "and", "ands", "bic", "bics", "eor", "orr", "eon", "orn", "movk", "movn",
                            "movz", "madd", "msub", NULL};
char *dp_aliases[] = {"cmp", "cmn", "neg", "negs", "tst", "mvn", "mov", "mul", "mneg", NULL};
char *branching[] = {"b", "br", "b.eq", "b.ne", "b.ge", "b.lt", "b.gt", "b.le", "b.al", NULL};
char *sdts[] = {"str", "ldr", NULL};
char *directives[] = {".int", NULL};

static bool instruction_type(const char *instr, char **array)
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

static char *prepend(const char *prefix, const char *str)
{
  char *result = malloc(strlen(prefix) + strlen(str) + 1);
  strcpy(result, prefix);
  strcat(result, str);
  return result;
}

// function to add a string to end of a char pointer
static char *append(const char *str, const char *suffix)
{
  char *result = malloc(strlen(str) + strlen(suffix) + 1);
  strcpy(result, str);
  strcat(result, suffix);
  return result;
}

// function that splits a string given by a char pointer by the comma and adds a given string to the middle
static char *split_and_add(const char *str, const char *middle)
{
  char *result = malloc(strlen(str) + strlen(middle) + 1);
  strcpy(result, str);
  char *comma = strchr(result, ',');
  if (comma == NULL)
  {
    fprintf(stderr, "Expected comma in string: %s\n", str);
    exit(EXIT_FAILURE);
  }
  comma++;
  while (*comma == ' ')
  {
    comma++;
  }
  strcpy(comma, middle);
  return result;
}

static void parse_labels(symbol_table_t st, long *address, char *line)
{
  line = trim_left(line);
  while (line[0] != '\0') // parse all labels in line (can contain multiple labels)
  {
    // find position of colon (if any)
    char *label_end = strchr(line, ':');
    if (label_end == NULL) // instruction line
    {
      *address += INSTR_SIZE;
      break;
    }
    else // label line
    {
      // allocate and copy label
      *label_end = '\0';

      // append to symbol table and continue
      symbol_table_append(st, line, *address);
      line = trim_left(label_end + 1);
    }
  }
}

void first_pass(FILE *source_file, symbol_table_t st)
{
  char line_buf[MAX_LINE_LENGTH];
  long address = 0;

  while (fgets(line_buf, sizeof(line_buf), source_file))
  {
    parse_labels(st, &address, line_buf);
  }

  // handle the error in case the line cannot be read from the file
  if (ferror(source_file))
  {
    fprintf(stderr, "Error reading from file\n");
    exit(EXIT_FAILURE);
  }
}

static void write_binary(FILE *output_file, ulong instruction)
{
  // don't use fwrite on entire instruction directly to avoid undefined
  // behaviour due to different memory layouts on different systems.
  for (int idx = 0; idx < INSTR_SIZE; idx++)
  {
    byte b = (instruction >> (idx * 8)) & 0xFF;
    fwrite(&b, 1, 1, output_file);
  }
}

static void parse_instruction(FILE *output_file, symbol_table_t st, char *line, long *address)
{
  char *label_end;
  while ((label_end = strchr(line, ':')) != NULL)
  {
    line = label_end + 1;
  }
  line = trim_left(line);
  if (line[0] == '\0') // empty line
    return;

  for (int idx = 0; line[idx] != '\0'; idx++)
  {
    line[idx] = tolower(line[idx]);
  }
  char *operands = strchr(line, ' ');
  assert(operands != NULL); // all instructions have operands
  operands[0] = '\0';       // split opcode and operands
  operands = trim_left(operands + 1);
  char *opcode = line;

  ulong binary_instruction;
  if (instruction_type(opcode, dp_aliases)) 
  {
    if (strcmp(opcode, "cmp") == 0) binary_instruction = encode_dp(st, "subs", prepend("xzr, ", operands));
    else if (strcmp(opcode, "cmn") == 0) binary_instruction = encode_dp(st, "adds", prepend("xzr, ", operands));
    else if (strcmp(opcode, "neg") == 0) binary_instruction = encode_dp(st, "sub", split_and_add(operands, " xzr, "));
    else if (strcmp(opcode, "negs") == 0) binary_instruction = encode_dp(st, "subs", split_and_add(operands, " xzr, "));
    else if (strcmp(opcode, "tst") == 0) binary_instruction = encode_dp(st, "ands", prepend("xzr, ", operands));
    else if (strcmp(opcode, "mvn") == 0) binary_instruction = encode_dp(st, "orn", split_and_add(operands, " xzr, "));
    else if (strcmp(opcode, "mov") == 0) binary_instruction = encode_dp(st, "orr", split_and_add(operands, " xzr, "));
    else if (strcmp(opcode, "mul") == 0) binary_instruction = encode_dp(st, "madd", append(operands, ", xzr"));
    else if (strcmp(opcode, "mneg") == 0) binary_instruction = encode_dp(st, "msub", append(operands, ", xzr"));
  }
  else if (instruction_type(opcode, data_processing))
  {
    binary_instruction = encode_dp(st, opcode, operands);
  }
  else if (instruction_type(opcode, sdts))
  {
    binary_instruction = encode_sdt(st, opcode, operands);
  }
  else if (instruction_type(opcode, branching))
  {
    binary_instruction = encode_branch(st, opcode, operands, *address);
  }
  else if (instruction_type(opcode, directives))
  {
    binary_instruction = encode_directives(st, opcode, operands);
  }
  else
  {
    fprintf(stderr, "Unknown opcode: %s\n", opcode);
    exit(EXIT_FAILURE);
  }

  write_binary(output_file, binary_instruction);
}

void second_pass(FILE *source_file, FILE *output_file, symbol_table_t st)
{
  char line_buf[MAX_LINE_LENGTH];
  long address = 0;

  while (fgets(line_buf, sizeof(line_buf), source_file))
  {
    printf("Parsing instruction: %s\n", line_buf);
    if (strcmp(line_buf, "and x0, x0, x0") == 0) // halt instruction
    {
      break;
    }
    parse_instruction(output_file, st, line_buf, &address);
    address += INSTR_SIZE;
  }
}
