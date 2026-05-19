/*
    AUTHOR: Christian Bender
    DATE: 12.02.2019
    DESCRIPTION: This program calculates the prime factoriziation of a positive
   integer > 1

    Modified for testability - removed main(), added utility functions
*/

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* initial length of the dynamic array */
#define LEN 10

/* increasing range */
#define STEP 5

/*
    this type is for the representation of the prim factoriziation
    - its series/range of prime factors
    - its length : numbers of prime factors
*/
typedef struct data
{
    int *range;
    int length;
} range;
typedef range *Range;

/* int_fac : calculates the prime factoriziation of positive integers */
Range int_fact(int);

/* increase : increases the dynamic integer array */
int *increase(int *, int);

/* destroy: destroys the range-structure */
void destroy(Range);

/* format_factors : formats prime factors as a string (string-based alternative to print_arr) */
char *format_factors(Range);

/* get_factor_count : returns the number of prime factors */
int get_factor_count(Range);

/* get_factor_at : returns the prime factor at given index, or -1 if out of bounds */
int get_factor_at(Range, int);

/* verify_factorization : verifies that the factors multiply to give the original number */
int verify_factorization(Range, int);

/* compare_factors : compares two Range structures for equality, returns 1 if equal, 0 otherwise */
int compare_factors(Range, Range);

/* create_range_from_array : creates a Range from an array of factors (for test setup) */
Range create_range_from_array(int *factors, int count);

Range int_fact(int n)
{
    if (n <= 1) {
        return NULL; /* n must be greater than 1 */
    }

    int len = LEN;
    int count = 0;
    int i = 0;
    int *arr = (int *)malloc(sizeof(int) * len);
    if (arr == NULL) {
        return NULL;
    }
    Range pstr = (Range)malloc(sizeof(struct data)); /* Fixed: was sizeof(range) which is sizeof(pointer) */
    if (pstr == NULL) {
        free(arr);
        return NULL;
    }

    while (n % 2 == 0)
    {
        n /= 2;
        if (i < len)
        {
            arr[i] = 2;
            i++;
        }
        else
        {
            int *new_arr = increase(arr, len);
            if (new_arr == NULL) {
                free(arr);
                free(pstr);
                return NULL;
            }
            arr = new_arr;
            len += STEP;
            arr[i] = 2;
            i++;
        }
        count++;
    }

    int j = 3;
    while (j * j <= n)
    {
        while (n % j == 0)
        {
            n /= j;
            if (i < len)
            {
                arr[i] = j;
                i++;
            }
            else
            {
                int *new_arr = increase(arr, len);
                if (new_arr == NULL) {
                    free(arr);
                    free(pstr);
                    return NULL;
                }
                arr = new_arr;
                len += STEP;
                arr[i] = j;
                i++;
            }
            count++;
        }

        j += 2;
    }

    if (n > 1)
    {
        if (i < len)
        {
            arr[i] = n;
            i++;
        }
        else
        {
            int *new_arr = increase(arr, len);
            if (new_arr == NULL) {
                free(arr);
                free(pstr);
                return NULL;
            }
            arr = new_arr;
            len += STEP;
            arr[i] = n;
            i++;
        }
        count++;
    }

    pstr->range = arr;
    pstr->length = count;
    return pstr;
}

int *increase(int *arr, int len)
{
    if (arr == NULL) {
        return NULL;
    }
    int *tmp = (int *)realloc(arr, sizeof(int) * (len + STEP));
    return tmp; /* May be NULL if realloc fails */
}

void destroy(Range r)
{
    if (r == NULL) {
        return;
    }
    if (r->range != NULL) {
        free(r->range);
    }
    free(r);
}

/*
    format_factors : formats prime factors as a string
    Returns a dynamically allocated string that must be freed by caller.
    Format: "2-2-3-5" (factors separated by dashes)
    Returns NULL if pStr is NULL or on allocation failure.
*/
char *format_factors(Range pStr)
{
    if (pStr == NULL || pStr->length == 0) {
        return NULL;
    }

    /* Estimate max string size: each factor up to 10 digits + dash */
    int max_size = pStr->length * 12;
    char *result = (char *)malloc(max_size);
    if (result == NULL) {
        return NULL;
    }

    result[0] = '\0';
    char buffer[16];
    int i;

    for (i = 0; i < pStr->length; i++) {
        if (i == 0) {
            sprintf(buffer, "%d", pStr->range[i]);
        } else {
            sprintf(buffer, "-%d", pStr->range[i]);
        }
        strcat(result, buffer);
    }

    return result;
}

/*
    get_factor_count : returns the number of prime factors
    Returns -1 if pStr is NULL.
*/
int get_factor_count(Range pStr)
{
    if (pStr == NULL) {
        return -1;
    }
    return pStr->length;
}

/*
    get_factor_at : returns the prime factor at given index
    Returns -1 if pStr is NULL or index is out of bounds.
*/
int get_factor_at(Range pStr, int index)
{
    if (pStr == NULL || index < 0 || index >= pStr->length) {
        return -1;
    }
    return pStr->range[index];
}

/*
    verify_factorization : verifies that the factors multiply to give the original number
    Returns 1 if the product of factors equals n, 0 otherwise.
    Returns 0 if pStr is NULL.
*/
int verify_factorization(Range pStr, int n)
{
    if (pStr == NULL || pStr->length == 0) {
        return 0;
    }

    int product = 1;
    int i;
    for (i = 0; i < pStr->length; i++) {
        product *= pStr->range[i];
    }

    return (product == n) ? 1 : 0;
}

/*
    compare_factors : compares two Range structures for equality
    Returns 1 if both have the same length and same factors in same order.
    Returns 0 otherwise or if either is NULL.
*/
int compare_factors(Range r1, Range r2)
{
    if (r1 == NULL || r2 == NULL) {
        return 0;
    }

    if (r1->length != r2->length) {
        return 0;
    }

    int i;
    for (i = 0; i < r1->length; i++) {
        if (r1->range[i] != r2->range[i]) {
            return 0;
        }
    }

    return 1;
}

/*
    create_range_from_array : creates a Range from an array of factors
    Useful for setting up expected values in tests.
    Returns NULL on allocation failure or if factors is NULL.
*/
Range create_range_from_array(int *factors, int count)
{
    if (factors == NULL || count <= 0) {
        return NULL;
    }

    Range r = (Range)malloc(sizeof(struct data));
    if (r == NULL) {
        return NULL;
    }

    r->range = (int *)malloc(sizeof(int) * count);
    if (r->range == NULL) {
        free(r);
        return NULL;
    }

    int i;
    for (i = 0; i < count; i++) {
        r->range[i] = factors[i];
    }
    r->length = count;

    return r;
}
