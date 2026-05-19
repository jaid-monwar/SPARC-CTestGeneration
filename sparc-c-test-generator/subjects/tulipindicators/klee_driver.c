/*
 * KLEE symbolic execution driver for Tulip Indicators.
 *
 * Iterates concretely over all 104 indicators, calling each one with
 * symbolic input data so KLEE can explore paths within every function.
 *
 * Compile to LLVM bitcode:
 *   clang -emit-llvm -c -g -O0 -I<klee-include-path> klee_driver.c -o tulipindicators.bc
 *
 * Run with KLEE:
 *   klee --libc=uclibc --posix-runtime tulipindicators.bc
 */

#include <assert.h>
#include "klee/klee.h"
#include "src/tulipindicators.c"

#define DATA_SIZE 8
#define MAX_INPUTS 4
#define MAX_OUTPUTS 3

int main(void) {
    /*
     * Separate arrays so each is its own KLEE memory object.
     * (KLEE rejects klee_make_symbolic on sub-regions of a single object.)
     */
    TI_REAL input0[DATA_SIZE], input1[DATA_SIZE];
    TI_REAL input2[DATA_SIZE], input3[DATA_SIZE];
    klee_make_symbolic(input0, sizeof(input0), "input0");
    klee_make_symbolic(input1, sizeof(input1), "input1");
    klee_make_symbolic(input2, sizeof(input2), "input2");
    klee_make_symbolic(input3, sizeof(input3), "input3");

    const TI_REAL *inputs[] = { input0, input1, input2, input3 };

    /* Concrete options: period=3, secondary=5, tertiary=2.
     * Using concrete values avoids unsolvable FP constraints in STP. */
    TI_REAL options[] = { 3.0, 5.0, 2.0 };

    TI_REAL out0[DATA_SIZE], out1[DATA_SIZE], out2[DATA_SIZE];
    TI_REAL *outputs[] = { out0, out1, out2 };

    /* Concretely iterate every indicator so KLEE visits all functions. */
    for (int i = 0; i < TI_INDICATOR_COUNT; i++) {
        if (ti_indicators[i].indicator) {
            ti_indicators[i].indicator(
                DATA_SIZE,
                (TI_REAL const *const *)inputs,
                options,
                (TI_REAL *const *)outputs);
        }
    }

    return 0;
}
