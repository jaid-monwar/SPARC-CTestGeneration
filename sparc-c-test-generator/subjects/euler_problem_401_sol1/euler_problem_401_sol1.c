/**
 * \file
 * \brief [Problem 401](https://projecteuler.net/problem=401) solution -
 * Sum of squares of divisors
 * \author [Krishna Vedala](https://github.com/kvedala)
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define __STDC_FORMAT_MACROS
#include <inttypes.h>

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
char is_in(uint64_t N, uint64_t *D, uint64_t L)
{
    uint64_t i;
    if (D == NULL || L == 0)
    {
        return 0;
    }
    for (i = 0; i < L; i++)
    {
        if (D[i] == N)
        {
            return 1;
        }
    }
    return 0;
}

/**
 * Get all integer divisors of a number
 * \param[in] N number to find divisors for
 * \param[out] D array to store divisors in (must be pre-allocated with at least MAX_LENGTH elements)
 * \param[out] out_count pointer to store number of divisors found
 * \returns 0 on success, -1 on error
 */
int get_divisors(uint64_t N, uint64_t *D, uint64_t *out_count)
{
    uint64_t q, r;
    int64_t i;
    uint64_t num = 0;

    if (D == NULL || out_count == NULL)
    {
        return -1;
    }

    if (N == 0)
    {
        *out_count = 0;
        return 0;
    }

    if (N == 1)
    {
        D[0] = 1;
        *out_count = 1;
        return 0;
    }

    // search till sqrt(N)
    // because after this, the pair of divisors will repeat themselves
    for (i = 1; i * i <= N + 1; i++)
    {
        r = N % i;  // get remainder

        // remainder = 0 if 'i' is a divisor of 'N'
        if (r == 0)
        {
            q = N / i;
            if (!is_in(i, D, num))  // if divisor was not already stored
            {
                if (num >= MAX_LENGTH)
                {
                    // Array full, return what we have
                    *out_count = num;
                    return 0;
                }
                D[num] = i;
                num++;
            }
            if (!is_in(q, D, num))  // if divisor was not already stored
            {
                if (num >= MAX_LENGTH)
                {
                    // Array full, return what we have
                    *out_count = num;
                    return 0;
                }
                D[num] = q;
                num++;
            }
        }
    }
    *out_count = num;
    return 0;
}

/**
 * Compute sum of squares of all integer factors of a number
 * \param[in] N number to compute sigma2 for
 * \param[out] result pointer to store the result
 * \returns 0 on success, -1 on error (memory allocation failure)
 */
int sigma2(uint64_t N, uint64_t *result)
{
    uint64_t sum = 0, L;
    uint64_t i;
    uint64_t *D;

    if (result == NULL)
    {
        return -1;
    }

    if (N == 0)
    {
        *result = 0;
        return 0;
    }

    D = (uint64_t *)malloc(MAX_LENGTH * sizeof(uint64_t));
    if (D == NULL)
    {
        return -1;
    }

    if (get_divisors(N, D, &L) != 0)
    {
        free(D);
        return -1;
    }

    for (i = 0; i < L; i++)
    {
        uint64_t DD = (D[i] * D[i]) % MOD_LIMIT;
        sum += DD;
    }

    free(D);
    *result = sum % MOD_LIMIT;
    return 0;
}

/**
 * Sum of squares of factors of numbers from 1 thru N
 * \param[in] N upper limit
 * \param[out] result pointer to store the result
 * \returns 0 on success, -1 on error
 */
int sigma(uint64_t N, uint64_t *result)
{
    uint64_t s, sum = 0;
    uint64_t i;

    if (result == NULL)
    {
        return -1;
    }

    for (i = 1; i <= N; i++)
    {
        if (sigma2(i, &s) != 0)
        {
            return -1;
        }
        sum += s;
    }
    *result = sum % MOD_LIMIT;
    return 0;
}

/* ============== Utility functions for testing ============== */

/**
 * Count the number of divisors of N
 * \param[in] N number to count divisors for
 * \returns number of divisors, or 0 on error
 */
uint64_t count_divisors(uint64_t N)
{
    uint64_t count = 0;
    uint64_t *D = (uint64_t *)malloc(MAX_LENGTH * sizeof(uint64_t));
    if (D == NULL)
    {
        return 0;
    }

    if (get_divisors(N, D, &count) != 0)
    {
        free(D);
        return 0;
    }

    free(D);
    return count;
}

/**
 * Check if a number is a perfect square
 * \param[in] N number to check
 * \returns 1 if perfect square, 0 otherwise
 */
int is_perfect_square(uint64_t N)
{
    uint64_t root;
    if (N == 0)
    {
        return 1;
    }
    root = 1;
    while (root * root < N)
    {
        root++;
    }
    return (root * root == N) ? 1 : 0;
}

/**
 * Compute sum of divisors (not squares) for testing
 * \param[in] N number to compute sigma1 for
 * \returns sum of divisors
 */
uint64_t sigma1(uint64_t N)
{
    uint64_t sum = 0, L;
    uint64_t i;
    uint64_t *D;

    if (N == 0)
    {
        return 0;
    }

    D = (uint64_t *)malloc(MAX_LENGTH * sizeof(uint64_t));
    if (D == NULL)
    {
        return 0;
    }

    if (get_divisors(N, D, &L) != 0)
    {
        free(D);
        return 0;
    }

    for (i = 0; i < L; i++)
    {
        sum += D[i];
    }

    free(D);
    return sum;
}

/**
 * Get the smallest divisor greater than 1
 * \param[in] N number to find smallest divisor for
 * \returns smallest divisor > 1, or N if N is prime, or 0 on error
 */
uint64_t get_smallest_divisor(uint64_t N)
{
    uint64_t i;
    if (N <= 1)
    {
        return N;
    }
    for (i = 2; i * i <= N; i++)
    {
        if (N % i == 0)
        {
            return i;
        }
    }
    return N;  // N is prime
}

/**
 * Check if N is prime
 * \param[in] N number to check
 * \returns 1 if prime, 0 otherwise
 */
int is_prime(uint64_t N)
{
    if (N <= 1)
    {
        return 0;
    }
    if (N <= 3)
    {
        return 1;
    }
    if (N % 2 == 0 || N % 3 == 0)
    {
        return 0;
    }
    uint64_t i = 5;
    while (i * i <= N)
    {
        if (N % i == 0 || N % (i + 2) == 0)
        {
            return 0;
        }
        i += 6;
    }
    return 1;
}

/**
 * Compute sigma2 for a single number without modulo (for small numbers)
 * Useful for testing exact values
 * \param[in] N number to compute for
 * \returns sum of squares of divisors (no modulo)
 */
uint64_t sigma2_exact(uint64_t N)
{
    uint64_t sum = 0, L;
    uint64_t i;
    uint64_t *D;

    if (N == 0)
    {
        return 0;
    }

    D = (uint64_t *)malloc(MAX_LENGTH * sizeof(uint64_t));
    if (D == NULL)
    {
        return 0;
    }

    if (get_divisors(N, D, &L) != 0)
    {
        free(D);
        return 0;
    }

    for (i = 0; i < L; i++)
    {
        sum += D[i] * D[i];
    }

    free(D);
    return sum;
}
