/*
    Prime Factorization Header File

    AUTHOR: Christian Bender (original)
    Modified for testability
*/

#ifndef MATH_PRIME_FACTORIZATION_H
#define MATH_PRIME_FACTORIZATION_H

#include <stdlib.h>

/* initial length of the dynamic array */
#define LEN 10

/* increasing range */
#define STEP 5

/*
    Range type for representing prime factorization
    - range: array of prime factors
    - length: number of prime factors
*/
typedef struct data
{
    int *range;
    int length;
} range;
typedef range *Range;

/*
    int_fact : calculates the prime factorization of positive integers
    Input: n - positive integer > 1
    Returns: Range structure containing prime factors, or NULL if n <= 1 or allocation fails
*/
Range int_fact(int n);

/*
    increase : increases the dynamic integer array by STEP elements
    Input: arr - existing array, len - current length
    Returns: reallocated array or NULL on failure
*/
int *increase(int *arr, int len);

/*
    destroy : frees the Range structure and its array
    Input: r - Range to destroy (safe to call with NULL)
*/
void destroy(Range r);

/*
    format_factors : formats prime factors as a dash-separated string
    Input: pStr - Range structure
    Returns: dynamically allocated string (caller must free), or NULL on error
    Example: for 12 = 2*2*3, returns "2-2-3"
*/
char *format_factors(Range pStr);

/*
    get_factor_count : returns the number of prime factors
    Input: pStr - Range structure
    Returns: number of factors, or -1 if pStr is NULL
*/
int get_factor_count(Range pStr);

/*
    get_factor_at : returns the prime factor at given index
    Input: pStr - Range structure, index - 0-based index
    Returns: prime factor at index, or -1 if NULL or out of bounds
*/
int get_factor_at(Range pStr, int index);

/*
    verify_factorization : verifies that factors multiply to give the original number
    Input: pStr - Range structure, n - original number
    Returns: 1 if product of factors equals n, 0 otherwise
*/
int verify_factorization(Range pStr, int n);

/*
    compare_factors : compares two Range structures for equality
    Input: r1, r2 - Range structures to compare
    Returns: 1 if equal (same length and factors), 0 otherwise
*/
int compare_factors(Range r1, Range r2);

/*
    create_range_from_array : creates a Range from an array of factors
    Useful for setting up expected values in tests.
    Input: factors - array of prime factors, count - number of factors
    Returns: Range structure or NULL on error
*/
Range create_range_from_array(int *factors, int count);

#endif /* MATH_PRIME_FACTORIZATION_H */
