/**
 * \file
 * \brief [Problem 23](https://projecteuler.net/problem=23) solution -
 * optimization using look-up array
 * \author [Krishna Vedala](https://github.com/kvedala)
 *
 * Optimization applied - compute & store abundant numbers once
 * into a look-up array.
 *
 * Modified for unit testing - removed main(), added context-based API
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * Context structure to hold state for abundant number calculations.
 * Replaces global variable for thread-safety and testability.
 */
typedef struct {
    char *abundant_flags;    /**< Bit array for abundant number flags */
    unsigned long max_n;     /**< Maximum number in the range */
    unsigned long flag_size; /**< Size of the flags array in bytes */
} AbundantContext;

/**
 * Calculate the sum of proper divisors of N
 * \param N the number to check
 * \returns sum of proper divisors of N
 */
unsigned long sum_of_divisors(unsigned long N)
{
    if (N <= 1)
    {
        return 0;
    }

    unsigned long sum = 1;
    for (unsigned long i = 2; i * i <= N; i++)
    {
        if (N % i == 0)
        {
            sum += i;
            unsigned long tmp = N / i;
            if (tmp != i)
            {
                sum += tmp;
            }
        }
    }
    return sum;
}

/**
 * Classify a number as deficient, perfect, or abundant
 * \param N the number to check
 * \returns -1 if N is deficient (sum of divisors < N)
 * \returns 0 if N is perfect (sum of divisors == N)
 * \returns 1 if N is abundant (sum of divisors > N)
 */
char get_perfect_number(unsigned long N)
{
    if (N == 0)
    {
        return -1;  /* 0 is considered deficient */
    }
    if (N == 1)
    {
        return -1;  /* 1 has no proper divisors, so deficient */
    }

    unsigned long sum = sum_of_divisors(N);

    if (sum == N)
    {
        return 0;   /* perfect */
    }
    else if (sum > N)
    {
        return 1;   /* abundant */
    }
    else
    {
        return -1;  /* deficient */
    }
}

/**
 * Initialize an AbundantContext for calculations up to max_n
 * \param max_n maximum number to support
 * \returns pointer to initialized context, or NULL on failure
 */
AbundantContext *context_create(unsigned long max_n)
{
    if (max_n == 0)
    {
        return NULL;
    }

    AbundantContext *ctx = (AbundantContext *)malloc(sizeof(AbundantContext));
    if (!ctx)
    {
        return NULL;
    }

    ctx->max_n = max_n;
    /* Calculate bytes needed: (max_n + 7) / 8 to handle all numbers */
    ctx->flag_size = (max_n >> 3) + 1;
    ctx->abundant_flags = (char *)calloc(ctx->flag_size, 1);

    if (!ctx->abundant_flags)
    {
        free(ctx);
        return NULL;
    }

    return ctx;
}

/**
 * Free an AbundantContext and its resources
 * \param ctx context to free (may be NULL)
 */
void context_destroy(AbundantContext *ctx)
{
    if (ctx)
    {
        if (ctx->abundant_flags)
        {
            free(ctx->abundant_flags);
        }
        free(ctx);
    }
}

/**
 * Set the abundant flag for a number in the context
 * \param ctx the context
 * \param N the number to mark as abundant
 * \returns 0 on success, -1 on error (NULL ctx or N out of range)
 */
int context_set_abundant(AbundantContext *ctx, unsigned long N)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return -1;
    }
    if (N > ctx->max_n)
    {
        return -1;
    }

    int byte_offset = N & 7;
    unsigned long index = N >> 3;
    ctx->abundant_flags[index] |= (1 << byte_offset);
    return 0;
}

/**
 * Check if a number is marked as abundant in the context
 * \param ctx the context
 * \param N the number to check
 * \returns 1 if abundant, 0 if not abundant, -1 on error
 */
int context_is_abundant(AbundantContext *ctx, unsigned long N)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return -1;
    }
    if (N > ctx->max_n)
    {
        return -1;
    }

    return (ctx->abundant_flags[N >> 3] & (1 << (N & 7))) ? 1 : 0;
}

/**
 * Find the next abundant number after N in the context
 * \param ctx the context (must be initialized with abundant flags)
 * \param N starting number (exclusive)
 * \returns next abundant number > N, or 0 if none found within max_n
 */
unsigned long context_get_next_abundant(AbundantContext *ctx, unsigned long N)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return 0;
    }

    for (unsigned long i = N + 1; i <= ctx->max_n; ++i)
    {
        if (context_is_abundant(ctx, i) == 1)
        {
            return i;
        }
    }
    return 0;  /* no abundant number found */
}

/**
 * Initialize the context by computing all abundant numbers up to max_n
 * \param ctx the context to initialize
 * \returns 0 on success, -1 on error
 */
int context_compute_abundant_numbers(AbundantContext *ctx)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return -1;
    }

    for (unsigned long N = 1; N <= ctx->max_n; N++)
    {
        char ret = get_perfect_number(N);
        if (ret == 1)
        {
            context_set_abundant(ctx, N);
        }
    }
    return 0;
}

/**
 * Check if a given number can be represented as a sum of two abundant numbers
 * \param ctx the context (must have abundant flags computed)
 * \param N the number to check
 * \returns 1 if N can be expressed as sum of two abundant numbers
 * \returns 0 if N cannot be expressed as sum of two abundant numbers
 * \returns -1 on error
 */
int is_sum_of_abundant(AbundantContext *ctx, unsigned long N)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return -1;
    }
    if (N > ctx->max_n)
    {
        return -1;
    }

    /* Find the first abundant number */
    unsigned long i = context_get_next_abundant(ctx, 0);
    if (i == 0)
    {
        return 0;  /* no abundant numbers in range */
    }

    /* Check pairs: i + j = N where both i and j are abundant */
    while (i <= (N >> 1))
    {
        if (N >= i && context_is_abundant(ctx, N - i) == 1)
        {
            return 1;
        }
        i = context_get_next_abundant(ctx, i);
        if (i == 0)
        {
            break;  /* no more abundant numbers */
        }
    }
    return 0;
}

/**
 * Calculate the sum of all numbers up to max_n that cannot be
 * expressed as the sum of two abundant numbers
 * \param ctx the context (must have abundant flags computed)
 * \returns the sum, or 0 on error
 */
unsigned long compute_non_abundant_sum(AbundantContext *ctx)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return 0;
    }

    unsigned long sum = 0;
    for (unsigned long i = 1; i <= ctx->max_n; i++)
    {
        if (is_sum_of_abundant(ctx, i) == 0)
        {
            sum += i;
        }
    }
    return sum;
}

/* ============== Utility functions for testing ============== */

/**
 * Count how many abundant numbers exist in the range [1, max_n]
 * \param ctx the context
 * \returns count of abundant numbers, or 0 on error
 */
unsigned long count_abundant_numbers(AbundantContext *ctx)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return 0;
    }

    unsigned long count = 0;
    for (unsigned long i = 1; i <= ctx->max_n; i++)
    {
        if (context_is_abundant(ctx, i) == 1)
        {
            count++;
        }
    }
    return count;
}

/**
 * Get the Nth abundant number (1-indexed)
 * \param ctx the context
 * \param n which abundant number to get (1 = first)
 * \returns the Nth abundant number, or 0 if not found
 */
unsigned long get_nth_abundant(AbundantContext *ctx, unsigned long n)
{
    if (!ctx || !ctx->abundant_flags || n == 0)
    {
        return 0;
    }

    unsigned long count = 0;
    for (unsigned long i = 1; i <= ctx->max_n; i++)
    {
        if (context_is_abundant(ctx, i) == 1)
        {
            count++;
            if (count == n)
            {
                return i;
            }
        }
    }
    return 0;
}

/**
 * Check if a number is a perfect number
 * \param N the number to check
 * \returns 1 if perfect, 0 if not perfect
 */
int is_perfect_number(unsigned long N)
{
    return (get_perfect_number(N) == 0) ? 1 : 0;
}

/**
 * Check if a number is deficient
 * \param N the number to check
 * \returns 1 if deficient, 0 if not deficient
 */
int is_deficient_number(unsigned long N)
{
    return (get_perfect_number(N) == -1) ? 1 : 0;
}

/**
 * Check if a number is abundant (standalone, without context)
 * \param N the number to check
 * \returns 1 if abundant, 0 if not abundant
 */
int is_abundant_number(unsigned long N)
{
    return (get_perfect_number(N) == 1) ? 1 : 0;
}

/**
 * Get the maximum value stored in the context
 * \param ctx the context
 * \returns max_n value, or 0 on error
 */
unsigned long context_get_max_n(AbundantContext *ctx)
{
    if (!ctx)
    {
        return 0;
    }
    return ctx->max_n;
}

/**
 * Get the flag array size in bytes
 * \param ctx the context
 * \returns flag_size value, or 0 on error
 */
unsigned long context_get_flag_size(AbundantContext *ctx)
{
    if (!ctx)
    {
        return 0;
    }
    return ctx->flag_size;
}

/**
 * Clear all abundant flags in the context
 * \param ctx the context
 * \returns 0 on success, -1 on error
 */
int context_clear_flags(AbundantContext *ctx)
{
    if (!ctx || !ctx->abundant_flags)
    {
        return -1;
    }
    memset(ctx->abundant_flags, 0, ctx->flag_size);
    return 0;
}

/**
 * Solve Euler Problem 23 for a given max value
 * \param max_n maximum value to check (default 28123)
 * \returns sum of numbers that cannot be expressed as sum of two abundant numbers
 */
unsigned long solve_euler_23(unsigned long max_n)
{
    AbundantContext *ctx = context_create(max_n);
    if (!ctx)
    {
        return 0;
    }

    context_compute_abundant_numbers(ctx);
    unsigned long result = compute_non_abundant_sum(ctx);
    context_destroy(ctx);

    return result;
}
