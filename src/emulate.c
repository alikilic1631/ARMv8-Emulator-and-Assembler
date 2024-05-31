#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include "emulator.h"

int main(int argc, char **argv)
{
  // Check correct number of arguments
  if (argc != 2 && argc != 3)
  {
    fprintf(stderr, "Usage: %s <file in> [<file out>]\n", argv[0]);
    return EXIT_FAILURE;
  }

  // If second arg provided, open file for writing, otherwise use stdout.
  FILE *fout = stdout;
  if (argc == 3)
  {
    fout = fopen(argv[2], "w");
    if (fout == NULL)
    {
      fprintf(stderr, "Error: Could not open file %s\n", argv[2]);
      return EXIT_FAILURE;
    }
  }

  // Open input binary file
  FILE *fin = fopen(argv[1], "rb");
  if (fin == NULL)
  {
    fprintf(stderr, "Error: Could not open file %s\n", argv[1]);
    return EXIT_FAILURE;
  }

  // Create emulator state, load memory from binary file, and run
  // emulation steps while HALT is not reached.
  emulstate state = make_emulstate();
  fread(state.memory, 1, MAX_MEMORY, fin); // we expect less than MAX_MEMORY to be writen, ignore return value
  fclose(fin);

  while (emulstep(&state))
  { // keep running while no halt
  }

  // Finaly, print state
  fprint_emulstate(fout, &state);
  fclose(fout); // This is the end, so fclose(stdout) is fine
  return EXIT_SUCCESS;
}
