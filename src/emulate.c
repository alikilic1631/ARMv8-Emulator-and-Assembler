#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <ctype.h>

// NOTES:
// read in a binary file specified on the terminal
// ./emulate file_in file_out <- optional output file
// no output -> print results to stdout
// output specified -> save results to output file

// object code consists of 32-bit words, each representing instruction/data
// save these words to an array representing the memory

// emulator assumes memory has a capacity of 2MB so all addresses can be reached with 21 bits
// all instructions are 4 bytes long so all instruction addresses are multiples of 4

// 31 general purpose 64-bit registers R0, ..., R30 and 4 64-bit special registers: ZR (returns 0), PC (changed by branch instr), PSTATE, SP (ignored)
// we may define structs for general and special registers
// initially, all memory locations and registers are 0 and PC points to 0x0

// 64-bit mode registers are Xn. 32-bit mode registers are Wn.
// A read from Wn uses the lower 32 bits of Rn.
// 64-bit value can't be written to Wn.

// instruction with value 8a000000 means we stop the program and print the contents of all registers and non-zero memory locations

// fetch: 4-byte instruction fetched from memory
// decode: 4-byte word decoded into a known instruction
// execute: emulate the behaviour of executing the instruction so update the registers, PSTATE, memory.

// INSTRUCTION SET:
// Data Processing: arithmetic/logical. Operand could be immediate or register.
// Single Data Transfer: instructions that read/write to memory.
// Branch: modifies PC.

// Constants
#define MAXLINELEN   1024
#define MAXSYMBOLS   1024
#define MAXSYMBOLLEN 64
#define MEMSIZE      4096

// Typedefs
typedef char symbol[MAXSYMBOLLEN];

typedef struct {
	symbol s;
	unsigned int v;
} symval;

// Global variables
symval symtab[MAXSYMBOLS]; // symtab is an array of structs consisting of symbol s and positive int v
int nsymbols = 0;
uint16_t mem[MEMSIZE];

// SYMBOL TABLE
void init_symtab( void )
{
	nsymbols = 0;
}

int get_sym( char *s )
{
	for( int i=0; i<nsymbols; i++ )
	{
		if( strcmp( symtab[i].s, s ) == 0 )
		{
			return symtab[i].v;
		}
	}
	return -1;
}

void add_sym( char *s, unsigned int v )
{
	assert( get_sym( s ) == -1 );
	assert( nsymbols < MAXSYMBOLS );
	assert( strlen(s) < MAXSYMBOLLEN );
	strcpy( symtab[nsymbols].s, s );
	symtab[nsymbols].v = v;
	nsymbols++;
}

void show_symtab( FILE *out )
{
	for( int i=0; i<nsymbols; i++ )
	{
		fprintf( out, "%s=%d\n", symtab[i].s, mem[symtab[i].v] );
	}
}

// MEMORY
void write_mem( char *context, int addr, int value ) // context is description of the error
{
	if( addr<0 || addr>=MEMSIZE )
	{
		fprintf( stderr, "%s: bad address %d\n", context, addr );
		exit(1);
	}
	if( value<0 || value>=65535 )
	{
		fprintf( stderr, "%s: bad value %d\n", context, value );
		exit(1);
	}
	mem[addr] = value;
}

void init_mem( void )
{
	for( int i = 0; i < MEMSIZE; i++ )
	{
		mem[i] = 0;
	}
}

int load( char *filename )
{
  int nwrites = 0;

  FILE *in = fopen(filename, "r");
  if (in == NULL)
  {
    fprintf(stderr, "emulate: can't open file %s\n", filename);
    exit(1);
  }

  init_symtab();

  char orig[MAXLINELEN];
  return 0; // delete this
}

// run function - fetch, decode, execute until halt


int main(int argc, char **argv)
{
  if( argc < 2 )
	{
		fprintf( stderr, "Usage: ./emulate file_in file_out(optional)\n" );
		exit(1);
	}
  char *file_in = argv[1];
  init_mem();
  // load object code into memory
  // run the object code


  if (argc == 2) {
    show_symtab(stdout);
  } else {
    show_symtab(argv[2]);
  }
  return EXIT_SUCCESS;
}
