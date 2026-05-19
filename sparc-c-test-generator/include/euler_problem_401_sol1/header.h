/**
 * \file
 * \brief Header file for Problem 401 solution - Sum of squares of divisors
 */
#ifndef EULER_PROBLEM_401_SOL1_H
#define EULER_PROBLEM_401_SOL1_H

#include <stdint.h>

#define MOD_LIMIT (uint64_t)1e9 /**< modulo limit */
#define MAX_LENGTH 5000         /**< chunk size of array allocation */

/**
 * Check if a number is present in given array
 * \param[in] N number to check
 * \param[in] D array to check
 * \param[in] L length of array
 * \returns 1 if present
 * \returns 0 if absent
 */
char is_in(uint64_t N, uint64_t *D, uint64_t L);

/**
 * Get all integer divisors of a number
 * \param[in] N number to find divisors for
 * \param[out] D array to store divisors in (must be pre-allocated with at least MAX_LENGTH elements)
 * \param[out] out_count pointer to store number of divisors found
 * \returns 0 on success, -1 on error
 */
int get_divisors(uint64_t N, uint64_t *D, uint64_t *out_count);

/**
 * Compute sum of squares of all integer factors of a number
 * \param[in] N number to compute sigma2 for
 * \param[out] result pointer to store the result
 * \returns 0 on success, -1 on error (memory allocation failure)
 */
int sigma2(uint64_t N, uint64_t *result);

/**
 * Sum of squares of factors of numbers from 1 thru N
 * \param[in] N upper limit
 * \param[out] result pointer to store the result
 * \returns 0 on success, -1 on error
 */
int sigma(uint64_t N, uint64_t *result);

/* ============== Utility functions for testing ============== */

/**
 * Count the number of divisors of N
 * \param[in] N number to count divisors for
 * \returns number of divisors, or 0 on error
 */
uint64_t count_divisors(uint64_t N);

/**
 * Check if a number is a perfect square
 * \param[in] N number to check
 * \returns 1 if perfect square, 0 otherwise
 */
int is_perfect_square(uint64_t N);

/**
 * Compute sum of divisors (not squares) for testing
 * \param[in] N number to compute sigma1 for
 * \returns sum of divisors
 */
uint64_t sigma1(uint64_t N);

/**
 * Get the smallest divisor greater than 1
 * \param[in] N number to find smallest divisor for
 * \returns smallest divisor > 1, or N if N is prime, or 0 on error
 */
uint64_t get_smallest_divisor(uint64_t N);

/**
 * Check if N is prime
 * \param[in] N number to check
 * \returns 1 if prime, 0 otherwise
 */
int is_prime(uint64_t N);

/**
 * Compute sigma2 for a single number without modulo (for small numbers)
 * Useful for testing exact values
 * \param[in] N number to compute for
 * \returns sum of squares of divisors (no modulo)
 */
uint64_t sigma2_exact(uint64_t N);

#endif /* EULER_PROBLEM_401_SOL1_H */
