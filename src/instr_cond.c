#include "instr_dpreg.h"
#include <stdbool.h>

// Initialising Masks

// 0b01111111111000000000110000000000
#define CSEL_TEST 0x7FE00C00
// 0b00011010100000000000000000000000
#define CSEL_EXPECTED 0x1A800000
// 0b01111111111111110000111111100000
#define CSET_TEST 0x7FFF0FE0
// 0b00011010100111110000011111100000
#define CSET_EXPECTED 0x1A9F07E0
// 0b01111111111111110000111111100000
#define CSETM_TEST 0x7FFF0FE0
// 0b01011010100111110000001111100000
#define CSETM_EXPECTED 0x5A9F03E0
// 0b01111111111000000000110000000000
#define CSINC_TEST 0x7FE00C00
// 0b00011010100000000000010000000000
#define CSINC_EXPECTED 0x1A800400
// 0b01111111111000000000110000000000
#define CSINV_TEST 0x7FE00C00
// 0b01011010100000000000000000000000
#define CSINV_EXPECTED 0x5A800000
// 0b01111111111000000000110000000000
#define CSNEG_TEST 0x7FE00C00
// 0b01011010100000000000010000000000
#define CSNEG_EXPECTED 0x5A800400

// Initializing conditions
#define EQ 0x0
#define NE 0x1
#define GE 0xA
#define LT 0xB
#define GT 0xC
#define LE 0xD
#define AL 0xE

#define MSB_64_BIT 0x8000000000000000;
#define MSB_32_BIT 0x80000000;

bool exec_cond_instr(emulstate state, ulong raw) {
    bool sf = get_value(raw, 31, 1);
    byte condition = get_value(raw, 12, 4);
    byte rd_addr = get_value(raw, 0, 5);
    bool execute = 0;

    // Determining conditions
    switch (condition){
    case EQ:
        {execute = (state->pstate.zero == 1);
        break;}
    case NE:
        {execute = (state->pstate.zero == 0);
        break;}
    case GE:
        {execute = (state->pstate.negative == state->pstate.overflow);
        break;}
    case LT:
        {execute = (state->pstate.negative != state->pstate.overflow);
        break;}
    case GT:
        {execute = (state->pstate.zero == 0) && (state->pstate.negative == state->pstate.overflow);
        break;}
    case LE:
        {execute = !((state->pstate.zero == 0) && (state->pstate.negative == state->pstate.overflow));
        break;}
    case AL:
        {execute = 1;
        break;}
    default:
        return false;
    }

    bool csel = (raw & CSEL_TEST) == CSEL_EXPECTED;
    bool cset = (raw & CSET_TEST) == CSET_EXPECTED;
    bool csetm = (raw & CSETM_TEST) == CSETM_EXPECTED;
    bool csinc = (raw & CSINC_TEST) == CSINC_EXPECTED;
    bool csinv = (raw & CSINV_TEST) == CSINV_EXPECTED;
    bool csneg = (raw & CSNEG_TEST) == CSNEG_EXPECTED;

    if (csel) {
        byte rn_addr = get_value(raw, 5, 5);
        byte rm_addr = get_value(raw, 16, 5);
        ullong rn_value = get_reg(state, sf, rn_addr);
        ullong rm_value = get_reg(state, sf, rm_addr);

        if (execute) {
            set_reg(state, sf, rd_addr, rn_value);
        }
        else{ 
            set_reg(state, sf, rd_addr, rm_value);
        }
    }
    else if (cset) {
        if (condition == AL) {
            return false;
        }
        if (execute) {
            set_reg(state, sf, rd_addr, 0x1);
        }
        else{ 
            set_reg(state, sf, rd_addr, 0x0);
        }
    }
    else if (csetm) {
        if (condition == AL) {
            return false;
        }
        if (execute) {
            set_reg(state, sf, rd_addr, ~((ullong) 0x0));
        }
        else{ 
            set_reg(state, sf, rd_addr, 0x0);
        }
    }
    else if (csinc) {
        byte rn_addr = get_value(raw, 5, 5);
        byte rm_addr = get_value(raw, 16, 5);
        ullong rn_value = get_reg(state, sf, rn_addr);
        ullong rm_value = get_reg(state, sf, rm_addr);

        if (execute) {
            set_reg(state, sf, rd_addr, rn_value);
        }
        else{ 
            set_reg(state, sf, rd_addr, (rm_value + 1));
        }
    }
    else if (csinv) {
        byte rn_addr = get_value(raw, 5, 5);
        byte rm_addr = get_value(raw, 16, 5);
        ullong rn_value = get_reg(state, sf, rn_addr);
        ullong rm_value = get_reg(state, sf, rm_addr);

        if (execute) {
            set_reg(state, sf, rd_addr, rn_value);
        }
        else{ 
            set_reg(state, sf, rd_addr, ~rm_value);
        }
    }
    else if (csneg) {
        byte rn_addr = get_value(raw, 5, 5);
        byte rm_addr = get_value(raw, 16, 5);
        ullong rn_value = get_reg(state, sf, rn_addr);
        ullong rm_value = get_reg(state, sf, rm_addr);

        if (execute) {
            set_reg(state, sf, rd_addr, rn_value);
        }
        else{
            ullong new_rm_value = rm_value;
            if (sf) {
                new_rm_value ^= MSB_64_BIT;
            }
            else {
                new_rm_value ^= MSB_32_BIT;
            }
            set_reg(state, sf, rd_addr, new_rm_value);
        }
    }
    else {
        return false;
    }
    return true;
}
