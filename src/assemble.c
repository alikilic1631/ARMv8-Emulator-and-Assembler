#include <stdlib.h>
#include <stdio.h>
#include "assemble.h"
#include "assembler.h"

int main(int argc, char **argv)
{
  // Check correct number of arguments
  if (argc != 3)
  {
    fprintf(stderr, "Usage: %s <file in> <file out>\n", argv[0]);
    return EXIT_FAILURE;
  }

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

  first_pass(fin);
  second_pass(fin, fout);

  return EXIT_SUCCESS;
}
