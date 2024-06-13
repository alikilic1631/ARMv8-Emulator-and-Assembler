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

char *data_processing[] = {"add", "adds", "sub", "subs", "cmp", "cmn", "neg", "negs",
                           "and", "ands", "bic", "bics", "eor", "orr", "eon", "orn", "tst", "movk", "movn",
                           "movz", "mov", "mvn", "madd", "msub", "mul", "mneg", NULL};
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

static void parse_instruction(FILE *output_file, symbol_table_t st, char *line)
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
  if (instruction_type(opcode, data_processing))
  {
    binary_instruction = encode_dp(st, opcode, operands);
  }
  else if (instruction_type(opcode, sdts))
  {
    binary_instruction = encode_sdt(st, opcode, operands);
  }
  else if (instruction_type(opcode, branching))
  {
    binary_instruction = encode_branch(st, opcode, operands);
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

  while (fgets(line_buf, sizeof(line_buf), source_file))
  {
    parse_instruction(output_file, st, line_buf);
  }
}
