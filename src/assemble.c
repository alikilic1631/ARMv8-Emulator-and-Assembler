#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "assembler.h"
#include "symbol_table.h"
#include "assemble.h"

// function that returns the contents of a file so it can be used later
char *read_file(const char *filename)
{
  FILE *file = fopen(filename, "r");
  if (!file)
  {
    perror("Error opening file");
    return NULL;
  }

  // Get the length of the file
  fseek(file, 0, SEEK_END);
  long file_length = ftell(file);
  fseek(file, 0, SEEK_SET);

  // Allocate memory for the file content
  char *content = (char *)malloc(file_length + 1);
  if (!content)
  {
    perror("Error allocating memory");
    fclose(file);
    return NULL;
  }

  // Read the file content
  fread(content, 1, file_length, file);
  content[file_length] = '\0';
  fclose(file);

  return content;
}

// function that writes a string to a file
void restore_file(const char *content, const char *filename)
{
  FILE *file = fopen(filename, "w");
  if (!file)
  {
    perror("Error opening file for writing");
    return;
  }
  fwrite(content, 1, strlen(content), file);
  fclose(file);
}

// Function to remove comments from the assembly file. The single-line comments start with // and multi-line comments start with /* and end with */
void remove_comments(const char *filename) {
  FILE *file = fopen(filename, "r");
  if (!file) {
    perror("Error opening file");
    return;
  }

  // Get the length of the file
  fseek(file, 0, SEEK_END);
  long file_length = ftell(file);
  fseek(file, 0, SEEK_SET);

  // Allocate memory for the file content
  char *content = (char *)malloc(file_length + 1);
  if (!content) {
    perror("Error allocating memory");
    fclose(file);
    return;
  }

  // Read the file content
  fread(content, 1, file_length, file);
  content[file_length] = '\0';
  fclose(file);

  // Process the content to remove comments
  char *processed_content = (char *)malloc(file_length + 1);
  if (!processed_content) {
    perror("Error allocating memory");
    free(content);
    return;
  }

  int i = 0, j = 0;
  while (content[i] != '\0') {
    if (content[i] == '/' && content[i + 1] == '/') {
      // Single-line comment found, skip until end of line
      while (content[i] != '\n' && content[i] != '\0') {
        i++;
      }
    } else if (content[i] == '/' && content[i + 1] == '*') {
      // Multi-line comment found, skip until closing */
      i += 2;
      while (!(content[i] == '*' && content[i + 1] == '/') && content[i] != '\0') {
        i++;
      }
      if (content[i] != '\0') {
        i += 2;
      }
    } else {
      // Copy non-comment content
      processed_content[j++] = content[i++];
    }
  }

  processed_content[j] = '\0';

  // Write the processed content back to the file
  file = fopen(filename, "w");
  if (!file) {
    perror("Error opening file for writing");
    free(content);
    free(processed_content);
    return;
  }

  fwrite(processed_content, 1, j, file);
  fclose(file);

  // Free allocated memory
  free(content);
  free(processed_content);
}

int main(int argc, char **argv)
{
  // Check correct number of arguments
  if (argc != 3)
  {
    fprintf(stderr, "Usage: %s <file in> <file out>\n", argv[0]);
    return EXIT_FAILURE;
  }

  char *content = read_file(argv[1]);
  remove_comments(argv[1]);

  // open the assembly file
  FILE *fin = fopen(argv[1], "r");
  if (fin == NULL)
  {
    fprintf(stderr, "Error: Could not open file %s\n", argv[1]);
    return EXIT_FAILURE;
  }

  // open the output file
  FILE *fout = fopen(argv[2], "wb");
  if (fout == NULL)
  {
    fprintf(stderr, "Error: Could not open file %s\n", argv[2]);
    return EXIT_FAILURE;
  }

  symbol_table_t symbol_table = symbol_table_init();

  first_pass(fin, symbol_table);
  rewind(fin);
  second_pass(fin, fout, symbol_table);
  fclose(fin);
  fclose(fout);

  restore_file(content, argv[1]);
  free(content);

  symbol_table_free(symbol_table);
  return EXIT_SUCCESS;
}
