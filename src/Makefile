CC      ?= gcc
CFLAGS  ?= -std=c17 -g\
	-D_POSIX_SOURCE -D_DEFAULT_SOURCE\
	-Wall -Werror -pedantic

.SUFFIXES: .c .o

.PHONY: all clean

all: assemble emulate

assemble: assemble.o assembler.o symbol_table.o parse_utils.o asm_encode.o
emulate: emulate.o emulator.o instr_dpimm.o instr_dpreg.o instr_sdt.o instr_branch.o instr_cond.o

clean:
	$(RM) *.o assemble emulate
	
