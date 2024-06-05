#include <stdlib.h>
#include <stdbool.h>
#include "emulator.h"
#include "instr_dpimm.h"
#include "instr_dpreg.h"
#include "instr_sdt.h"
#include "instr_branch.h"

#define NELEMENTS(arr) (sizeof(arr) / sizeof(*arr))
#define MEMORY_BLOCKS 4
#define SF_MASK 0xFFFFFFFF

// Print unknown instruction error message and exit
static void unknown_instr(emulstate *state, ulong instr)
{
  fprintf(stderr, "Error: Unrecognized instruction 0x%08lx\nState Dump:\n", instr);
  fprint_emulstate(stderr, state);
  exit(1);
}

// Create a new emulator state with default values
emulstate make_emulstate()
{
  emulstate state;
  state.pc = 0;
  state.pstate.negative = false;
  state.pstate.zero = true; // (spec 1.1.1 - "initial value of PSTATE has the Z flag set")
  state.pstate.carry = false;
  state.pstate.overflow = false;
  for (int i = 0; i <= GENERAL_REGS; i++)
  {
    state.regs[i] = 0;
  }
  for (int i = 0; i < MAX_MEMORY; i++)
  {
    state.memory[i] = 0;
  }
  return state;
}

// Print emulator state to file
void fprint_emulstate(FILE *fout, emulstate *state)
{
  // Registers
  fprintf(fout, "Registers:\n");
  for (int i = 0; i < GENERAL_REGS; i++)
  {
    fprintf(fout, "X%02d = %016llx\n", i, state->regs[i]);
  }
  fprintf(fout, "PC = %016llx\n", state->pc);
  // PSTATE register
  fprintf(fout, "PSTATE : ");
  char labels[] = {'N', 'Z', 'C', 'V'};
  bool values[] = {state->pstate.negative, state->pstate.zero,
                   state->pstate.carry, state->pstate.overflow};
  for (int idx = 0; idx < NELEMENTS(labels) && idx < NELEMENTS(values); idx++)
  {
    if (values[idx])
    {
      fputc(labels[idx], fout);
    }
    else
    {
      fputc('-', fout);
    }
  }
  // Memory (MEMORY_BLOCKS-byte aligned)
  fprintf(fout, "\nNon-zero memory:\n");
  for (int idx = 0; idx < MAX_MEMORY; idx += MEMORY_BLOCKS)
  {
    // Check all bytes in block for non-zero values.
    bool non_zero = false;
    for (int b = 0; !non_zero && b < MEMORY_BLOCKS; b++)
    {
      non_zero = state->memory[idx + b] != 0;
    }
    if (non_zero)
    {
      fprintf(fout, "0x%08x: 0x", idx);
      // Loop is reversed since little-endian byte order
      for (int b = MEMORY_BLOCKS - 1; b >= 0; b--)
      {
        fprintf(fout, "%02x", state->memory[idx + b]);
      }
      fputc('\n', fout);
    }
  }
}

// Execute a single emulation step
bool emulstep(emulstate *state)
{
  ulong instr = load_mem(state, false, state->pc);
  // Custom HALT instruction (spec 1.9)
  if (instr == 0x8a000000)
    return false;

  // Extract op0 to determine exec instruction structure
  char op0 = (instr >> 25) & 0xf;
  switch (op0)
  {
  case 0x8:
  case 0x9: // Data Proccessing Immediate
    if (!exec_dpimm_instr(state, instr))
      unknown_instr(state, instr);
    state->pc += INSTR_SIZE;
    break;
  case 0x5:
  case 0xd: // Data Proccessing Register
    if (!exec_dpreg_instr(state, instr))
      unknown_instr(state, instr);
    state->pc += INSTR_SIZE;
    break;
  case 0x4:
  case 0x6:
  case 0xc:
  case 0xe:                            // Loads and Stores
    if (!exec_sdt_instr(state, instr)) // DONE
      unknown_instr(state, instr);
    state->pc += INSTR_SIZE;
    break;
  case 0xa:
  case 0xb: // Branches
    if (!exec_branch_instr(state, instr))
      unknown_instr(state, instr);
    // Branch instructions update PC directly
    break;
  default:
    unknown_instr(state, instr);
  }

  return true;
}

// Utility function to get a range from a ulong. Useful for unpacking an instruction.
ulong get_value(ulong from, uint offset, uint size)
{
  // ull required since it might overflow by 1 bit
  ulong mask = (1ull << (offset + size)) - (1ul << offset);
  return (from & mask) >> offset;
}

// Utility function to set a register value, and correct for 32/64 bit mode.
void set_reg(emulstate *state, bool sf, byte rg, ullong value)
{
  if (rg > GENERAL_REGS)
  {
    fprintf(stderr, "Error: Out of bounds register number %d\n", rg);
    exit(1);
  }
  else if (rg == GENERAL_REGS)
  {
    return; // ZR register ignores writes
  }
  state->regs[(int)rg] = sf_checker(value, sf);
}

ullong get_reg(emulstate *state, bool sf, byte rg)
{
  if (rg > GENERAL_REGS)
  {
    fprintf(stderr, "Error: Out of bounds register number %d\n", rg);
    exit(1);
  }
  return sf_checker(state->regs[(int)rg], sf);
}

ullong load_mem(emulstate *state, bool sf, ulong address)
{
  int size = 4;
  if (sf)
    size = 8;
  // Convert little-endian memory to ullong
  ullong data = 0;
  for (int idx = 0; idx < size; idx++)
  {
    data |= (ullong)(state->memory[address + idx]) << (idx * 8);
  }
  return data;
}

void store_mem(emulstate *state, bool sf, ulong address, ullong value)
{
  int size = 4;
  if (sf)
    size = 8;
  // Convert ullong to little-endian memory
  for (int idx = 0; idx < size; idx++)
  {
    state->memory[address + idx] = (value >> (idx * 8)) & 0xff;
  }
}

ullong sf_checker(ullong value, bool sf)
{
  if (!sf)
  {
    value &= SF_MASK;
  }
  return value;
}
