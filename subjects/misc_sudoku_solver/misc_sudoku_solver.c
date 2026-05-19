/**
 * @file
 * @brief Sudoku Solver using recursive implementation of brute-force algorithm
 *
 * @details
 * Given an incomplete N*N Sudoku and asked to solve it using the
 * following recursive algorithm:
 * 1. Scan the Sudoku from left to right row-wise to search for an empty cell.
 * 2. If there are no empty cells, print the Sudoku. Go to step 5.
 * 3. In the empty cell, try putting numbers 1 to N
 * while ensuring that no two numbers in a single row, column, or box are same.
 * Go back to step 1.
 * 4. Declare that the Sudoku is Invalid.
 * 5. Exit.
 *
 * @authors [Anuj Shah](https://github.com/anujms1999)
 * @authors [Krishna Vedala](https://github.com/kvedala)
 */
#include <assert.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/** @addtogroup sudoku Sudoku solver
 * @{
 */
/** Structure to hold the matrix and dimensions
 */
struct sudoku
{
    uint8_t *a; /**< matrix as a flattened 1D row-major array */
    uint8_t N;  /**< number of elements */
    uint8_t N2; /**< block of elements */
};

/**
 * Check if `x`^th row is valid
 * @param a ::sudoku to check
 * @param x row to check
 * @param y ignored column
 * @param v value to check if it repeats
 * @returns `true` if valid
 * @returns `false` if in-valid
 */
bool OKrow(const struct sudoku *a, int x, int y, int v)
{
    int offset = x * a->N;
    for (int j = 0; j < a->N; j++)
        if (a->a[offset + j] == v)
            // if the value is found in the row
            return false;
    return true;
}

/**
 * Check if `y`^th column is valid
 * @param a ::sudoku to check
 * @param x ignored row
 * @param y column to check
 * @param v value to check if it repeats
 * @returns `true` if valid
 * @returns `false` if in-valid
 */
bool OKcol(const struct sudoku *a, int x, int y, int v)
{
    for (int i = 0; i < a->N; i++)
        if (a->a[i * a->N + y] == v)
            // if the value is found in the column
            return false;
    return true;
}

/**
 * Check if a 3x3 box is valid
 * @param a matrix to check
 * @param x row index of the element to check
 * @param y column index of the element to check
 * @param v value to check if it repeats
 * @returns `true` if valid
 * @returns `false` if in-valid
 */
bool OKbox(const struct sudoku *a, int x, int y, int v)
{
    /* get start indices of the box that the current (x,y) lies in
       remember that in C/C++, division operation always rounds towards
       -infinity for signed integers and towards 0 for unsigned integers
    */
    int bi = x - x % a->N2, bj = y - y % a->N2;
    // printf("Checking box: (%d,%d)\n", bi, bj);

    for (int i = bi; i < (bi + a->N2); i++)
        for (int j = bj; j < (bj + a->N2); j++)
            if (a->a[i * a->N + j] == v)
                // if the value is found in the box
                return false;
    return true;
}

/**
 * Check if element `v` is valid to place at (x,y) location.
 * @param a ::sudoku to check
 * @param x row to place value
 * @param y column to place value
 * @param v value to check if it is valid
 * @returns `true` if valid
 * @returns `false` if in-valid
 */
bool OK(const struct sudoku *a, int x, int y, int v)
{
    bool result = OKrow(a, x, y, v);
    if (result)
        result = OKcol(a, x, y, v);
    if (result)
        result = OKbox(a, x, y, v);

    return result;
}

/**
 * Print the matrix to stdout
 * @param [in] a array to print
 */
void print(const struct sudoku *a)
{
    int i, j;
    for (i = 0; i < a->N; i++)
        for (j = 0; j < a->N; j++)
            printf("%" SCNu8 "%c", a->a[i * a->N + j],
                   (j == a->N - 1 ? '\n' : ' '));
}

/**
 * @brief Find and get the location for next empty cell.
 *
 * @param [in] a pointer to sudoku instance
 * @param [out] x pointer to row index of next unknown
 * @param [out] y pointer to column index of next unknown
 * @returns `true` if an empty location was found
 * @returns `false` if no more empty locations found
 */
bool get_next_unknown(const struct sudoku *a, int *x, int *y)
{
    for (int i = 0; i < a->N; i++)
    {
        for (int j = 0; j < a->N; j++)
        {
            if (a->a[i * a->N + j] == 0)
            {
                *x = i;
                *y = j;
                return true;
            }
        }
    }

    /* no unknown locations found */
    return false;
}

/**
 * @brief Function to solve a partially filled sudoku matrix. For each unknown
 * value (0), the function fills a possible value and calls the function again
 * to check for valid solution.
 *
 * @param [in,out] a sudoku matrix to solve
 * @return `true` if solution found
 * @return `false` if no solution found
 */
bool solve(struct sudoku *a)
{
    int i, j;

    if (!get_next_unknown(a, &i, &j))
    {
        /* no more empty location found
           implies all good in the matrix
         */
        return true;
    }

    /* try all possible values for the unknown */
    for (uint8_t v = 1; v <= a->N; v++)
    {
        /* try all possible values 1 thru N */
        if (OK(a, i, j, v))
        {
            /* if assignment checks satisfy, set the value and
             continue with remaining elements */
            a->a[i * a->N + j] = v;
            if (solve(a))
            {
                /* solution found */
                return true;
            }

            /* backtrack */
            a->a[i * a->N + j] = 0;
        }
    }

    return false;
}

/** @} */

/* ==================== Utility Functions for Testing ==================== */

/**
 * @brief Create a new sudoku structure with the given size
 * @param N the dimension of the sudoku (e.g., 9 for 9x9)
 * @return pointer to newly allocated sudoku structure, or NULL on failure
 */
struct sudoku *sudoku_create(uint8_t N)
{
    if (N == 0)
        return NULL;

    struct sudoku *s = (struct sudoku *)malloc(sizeof(struct sudoku));
    if (s == NULL)
        return NULL;

    s->N = N;
    s->N2 = (uint8_t)sqrt(N);
    s->a = (uint8_t *)calloc(N * N, sizeof(uint8_t));
    if (s->a == NULL)
    {
        free(s);
        return NULL;
    }

    return s;
}

/**
 * @brief Free a sudoku structure
 * @param s pointer to sudoku structure to free
 */
void sudoku_free(struct sudoku *s)
{
    if (s != NULL)
    {
        if (s->a != NULL)
            free(s->a);
        free(s);
    }
}

/**
 * @brief Initialize a sudoku from an array of values
 * @param s pointer to sudoku structure
 * @param values array of N*N values (row-major order)
 * @return true if successful, false on error
 */
bool sudoku_init_from_array(struct sudoku *s, const uint8_t *values)
{
    if (s == NULL || s->a == NULL || values == NULL)
        return false;

    memcpy(s->a, values, s->N * s->N * sizeof(uint8_t));
    return true;
}

/**
 * @brief Get the value at a specific cell
 * @param s pointer to sudoku structure
 * @param row row index (0-based)
 * @param col column index (0-based)
 * @return the value at (row, col), or 0 if invalid
 */
uint8_t sudoku_get_cell(const struct sudoku *s, int row, int col)
{
    if (s == NULL || s->a == NULL)
        return 0;
    if (row < 0 || row >= s->N || col < 0 || col >= s->N)
        return 0;

    return s->a[row * s->N + col];
}

/**
 * @brief Set the value at a specific cell
 * @param s pointer to sudoku structure
 * @param row row index (0-based)
 * @param col column index (0-based)
 * @param value the value to set
 * @return true if successful, false on error
 */
bool sudoku_set_cell(struct sudoku *s, int row, int col, uint8_t value)
{
    if (s == NULL || s->a == NULL)
        return false;
    if (row < 0 || row >= s->N || col < 0 || col >= s->N)
        return false;

    s->a[row * s->N + col] = value;
    return true;
}

/**
 * @brief Count the number of empty cells (cells with value 0)
 * @param s pointer to sudoku structure
 * @return number of empty cells, or -1 on error
 */
int sudoku_count_empty(const struct sudoku *s)
{
    if (s == NULL || s->a == NULL)
        return -1;

    int count = 0;
    int total = s->N * s->N;
    for (int i = 0; i < total; i++)
    {
        if (s->a[i] == 0)
            count++;
    }
    return count;
}

/**
 * @brief Count the number of filled cells (cells with non-zero value)
 * @param s pointer to sudoku structure
 * @return number of filled cells, or -1 on error
 */
int sudoku_count_filled(const struct sudoku *s)
{
    if (s == NULL || s->a == NULL)
        return -1;

    int total = s->N * s->N;
    int empty = sudoku_count_empty(s);
    if (empty < 0)
        return -1;

    return total - empty;
}

/**
 * @brief Check if the entire sudoku is valid (no conflicts)
 * @param s pointer to sudoku structure
 * @return true if valid, false if invalid or on error
 */
bool sudoku_is_valid(const struct sudoku *s)
{
    if (s == NULL || s->a == NULL)
        return false;

    /* Check each cell that has a value */
    for (int i = 0; i < s->N; i++)
    {
        for (int j = 0; j < s->N; j++)
        {
            uint8_t v = s->a[i * s->N + j];
            if (v != 0)
            {
                /* Temporarily clear the cell to check if value is valid */
                s->a[i * s->N + j] = 0;
                bool valid = OK(s, i, j, v);
                s->a[i * s->N + j] = v;

                if (!valid)
                    return false;
            }
        }
    }
    return true;
}

/**
 * @brief Check if the sudoku is completely solved
 * @param s pointer to sudoku structure
 * @return true if solved (no empty cells and valid), false otherwise
 */
bool sudoku_is_solved(const struct sudoku *s)
{
    if (s == NULL || s->a == NULL)
        return false;

    /* Check for empty cells */
    int empty = sudoku_count_empty(s);
    if (empty != 0)
        return false;

    /* Check validity */
    return sudoku_is_valid(s);
}

/**
 * @brief Compare two sudoku structures for equality
 * @param s1 first sudoku
 * @param s2 second sudoku
 * @return true if equal, false if different or on error
 */
bool sudoku_equals(const struct sudoku *s1, const struct sudoku *s2)
{
    if (s1 == NULL || s2 == NULL)
        return false;
    if (s1->a == NULL || s2->a == NULL)
        return false;
    if (s1->N != s2->N)
        return false;

    int total = s1->N * s1->N;
    return memcmp(s1->a, s2->a, total * sizeof(uint8_t)) == 0;
}

/**
 * @brief Copy a sudoku structure
 * @param src source sudoku
 * @return pointer to newly allocated copy, or NULL on error
 */
struct sudoku *sudoku_copy(const struct sudoku *src)
{
    if (src == NULL || src->a == NULL)
        return NULL;

    struct sudoku *copy = sudoku_create(src->N);
    if (copy == NULL)
        return NULL;

    memcpy(copy->a, src->a, src->N * src->N * sizeof(uint8_t));
    return copy;
}

/**
 * @brief Print the sudoku to a string buffer
 * @param s pointer to sudoku structure
 * @param buffer output buffer
 * @param buffer_size size of the output buffer
 * @return number of characters written, or -1 on error
 */
int sudoku_to_string(const struct sudoku *s, char *buffer, size_t buffer_size)
{
    if (s == NULL || s->a == NULL || buffer == NULL || buffer_size == 0)
        return -1;

    int written = 0;
    int remaining = (int)buffer_size;

    for (int i = 0; i < s->N; i++)
    {
        for (int j = 0; j < s->N; j++)
        {
            int n;
            if (j == s->N - 1)
                n = snprintf(buffer + written, remaining, "%d\n", s->a[i * s->N + j]);
            else
                n = snprintf(buffer + written, remaining, "%d ", s->a[i * s->N + j]);

            if (n < 0 || n >= remaining)
                return -1;

            written += n;
            remaining -= n;
        }
    }

    return written;
}

/**
 * @brief Clear all cells in the sudoku (set all to 0)
 * @param s pointer to sudoku structure
 */
void sudoku_clear(struct sudoku *s)
{
    if (s != NULL && s->a != NULL)
    {
        memset(s->a, 0, s->N * s->N * sizeof(uint8_t));
    }
}

