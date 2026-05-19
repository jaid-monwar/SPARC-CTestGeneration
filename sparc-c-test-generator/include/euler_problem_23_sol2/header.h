/**
 * \file header.h
 * \brief Header file for Euler Problem 23 solution
 *
 * Provides functions for computing abundant numbers and solving
 * Project Euler Problem 23.
 */

#ifndef EULER_PROBLEM_23_SOL2_H
#define EULER_PROBLEM_23_SOL2_H

#include <stdlib.h>

/**
 * Context structure to hold state for abundant number calculations.
 * Uses a bit array for memory-efficient storage of abundant flags.
 */
typedef struct {
    char *abundant_flags;    /**< Bit array for abundant number flags */
    unsigned long max_n;     /**< Maximum number in the range */
    unsigned long flag_size; /**< Size of the flags array in bytes */
} AbundantContext;

/* ============== Core mathematical functions ============== */

/**
 * Calculate the sum of proper divisors of N
 * \param N the number to check
 * \returns sum of proper divisors of N
 */
unsigned long sum_of_divisors(unsigned long N);

/**
 * Classify a number as deficient, perfect, or abundant
 * \param N the number to check
 * \returns -1 if N is deficient (sum of divisors < N)
 * \returns 0 if N is perfect (sum of divisors == N)
 * \returns 1 if N is abundant (sum of divisors > N)
 */
char get_perfect_number(unsigned long N);

/* ============== Context management functions ============== */

/**
 * Initialize an AbundantContext for calculations up to max_n
 * \param max_n maximum number to support
 * \returns pointer to initialized context, or NULL on failure
 */
AbundantContext *context_create(unsigned long max_n);

/**
 * Free an AbundantContext and its resources
 * \param ctx context to free (may be NULL)
 */
void context_destroy(AbundantContext *ctx);

/**
 * Set the abundant flag for a number in the context
 * \param ctx the context
 * \param N the number to mark as abundant
 * \returns 0 on success, -1 on error (NULL ctx or N out of range)
 */
int context_set_abundant(AbundantContext *ctx, unsigned long N);

/**
 * Check if a number is marked as abundant in the context
 * \param ctx the context
 * \param N the number to check
 * \returns 1 if abundant, 0 if not abundant, -1 on error
 */
int context_is_abundant(AbundantContext *ctx, unsigned long N);

/**
 * Find the next abundant number after N in the context
 * \param ctx the context (must be initialized with abundant flags)
 * \param N starting number (exclusive)
 * \returns next abundant number > N, or 0 if none found within max_n
 */
unsigned long context_get_next_abundant(AbundantContext *ctx, unsigned long N);

/**
 * Initialize the context by computing all abundant numbers up to max_n
 * \param ctx the context to initialize
 * \returns 0 on success, -1 on error
 */
int context_compute_abundant_numbers(AbundantContext *ctx);

/**
 * Get the maximum value stored in the context
 * \param ctx the context
 * \returns max_n value, or 0 on error
 */
unsigned long context_get_max_n(AbundantContext *ctx);

/**
 * Get the flag array size in bytes
 * \param ctx the context
 * \returns flag_size value, or 0 on error
 */
unsigned long context_get_flag_size(AbundantContext *ctx);

/**
 * Clear all abundant flags in the context
 * \param ctx the context
 * \returns 0 on success, -1 on error
 */
int context_clear_flags(AbundantContext *ctx);

/* ============== Problem solving functions ============== */

/**
 * Check if a given number can be represented as a sum of two abundant numbers
 * \param ctx the context (must have abundant flags computed)
 * \param N the number to check
 * \returns 1 if N can be expressed as sum of two abundant numbers
 * \returns 0 if N cannot be expressed as sum of two abundant numbers
 * \returns -1 on error
 */
int is_sum_of_abundant(AbundantContext *ctx, unsigned long N);

/**
 * Calculate the sum of all numbers up to max_n that cannot be
 * expressed as the sum of two abundant numbers
 * \param ctx the context (must have abundant flags computed)
 * \returns the sum, or 0 on error
 */
unsigned long compute_non_abundant_sum(AbundantContext *ctx);

/**
 * Solve Euler Problem 23 for a given max value
 * \param max_n maximum value to check (default 28123)
 * \returns sum of numbers that cannot be expressed as sum of two abundant numbers
 */
unsigned long solve_euler_23(unsigned long max_n);

/* ============== Utility functions for testing ============== */

/**
 * Count how many abundant numbers exist in the range [1, max_n]
 * \param ctx the context
 * \returns count of abundant numbers, or 0 on error
 */
unsigned long count_abundant_numbers(AbundantContext *ctx);

/**
 * Get the Nth abundant number (1-indexed)
 * \param ctx the context
 * \param n which abundant number to get (1 = first)
 * \returns the Nth abundant number, or 0 if not found
 */
unsigned long get_nth_abundant(AbundantContext *ctx, unsigned long n);

/**
 * Check if a number is a perfect number
 * \param N the number to check
 * \returns 1 if perfect, 0 if not perfect
 */
int is_perfect_number(unsigned long N);

/**
 * Check if a number is deficient
 * \param N the number to check
 * \returns 1 if deficient, 0 if not deficient
 */
int is_deficient_number(unsigned long N);

/**
 * Check if a number is abundant (standalone, without context)
 * \param N the number to check
 * \returns 1 if abundant, 0 if not abundant
 */
int is_abundant_number(unsigned long N);

#endif /* EULER_PROBLEM_23_SOL2_H */
