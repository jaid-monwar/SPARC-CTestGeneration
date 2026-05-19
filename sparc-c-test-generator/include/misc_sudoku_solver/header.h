/**
 * @file misc_sudoku_solver.h
 * @brief Header file for Sudoku Solver using recursive brute-force algorithm
 */
#ifndef MISC_SUDOKU_SOLVER_H
#define MISC_SUDOKU_SOLVER_H

#include <inttypes.h>
#include <stdbool.h>
#include <stddef.h>

/** Structure to hold the matrix and dimensions */
struct sudoku
{
    uint8_t *a; /**< matrix as a flattened 1D row-major array */
    uint8_t N;  /**< number of elements */
    uint8_t N2; /**< block of elements */
};

/* ==================== Core Sudoku Functions ==================== */

/**
 * @brief Check if `x`^th row is valid for placing value v
 * @param a sudoku to check
 * @param x row to check
 * @param y ignored column
 * @param v value to check if it repeats
 * @returns true if valid, false if in-valid
 */
bool OKrow(const struct sudoku *a, int x, int y, int v);

/**
 * @brief Check if `y`^th column is valid for placing value v
 * @param a sudoku to check
 * @param x ignored row
 * @param y column to check
 * @param v value to check if it repeats
 * @returns true if valid, false if in-valid
 */
bool OKcol(const struct sudoku *a, int x, int y, int v);

/**
 * @brief Check if a box is valid for placing value v
 * @param a matrix to check
 * @param x row index of the element to check
 * @param y column index of the element to check
 * @param v value to check if it repeats
 * @returns true if valid, false if in-valid
 */
bool OKbox(const struct sudoku *a, int x, int y, int v);

/**
 * @brief Check if element v is valid to place at (x,y) location
 * @param a sudoku to check
 * @param x row to place value
 * @param y column to place value
 * @param v value to check if it is valid
 * @returns true if valid, false if in-valid
 */
bool OK(const struct sudoku *a, int x, int y, int v);

/**
 * @brief Print the matrix to stdout
 * @param a array to print
 */
void print(const struct sudoku *a);

/**
 * @brief Find and get the location for next empty cell
 * @param a pointer to sudoku instance
 * @param x pointer to row index of next unknown
 * @param y pointer to column index of next unknown
 * @returns true if an empty location was found, false otherwise
 */
bool get_next_unknown(const struct sudoku *a, int *x, int *y);

/**
 * @brief Solve a partially filled sudoku matrix
 * @param a sudoku matrix to solve
 * @return true if solution found, false otherwise
 */
bool solve(struct sudoku *a);

/* ==================== Utility Functions for Testing ==================== */

/**
 * @brief Create a new sudoku structure with the given size
 * @param N the dimension of the sudoku (e.g., 9 for 9x9)
 * @return pointer to newly allocated sudoku structure, or NULL on failure
 */
struct sudoku *sudoku_create(uint8_t N);

/**
 * @brief Free a sudoku structure
 * @param s pointer to sudoku structure to free
 */
void sudoku_free(struct sudoku *s);

/**
 * @brief Initialize a sudoku from an array of values
 * @param s pointer to sudoku structure
 * @param values array of N*N values (row-major order)
 * @return true if successful, false on error
 */
bool sudoku_init_from_array(struct sudoku *s, const uint8_t *values);

/**
 * @brief Get the value at a specific cell
 * @param s pointer to sudoku structure
 * @param row row index (0-based)
 * @param col column index (0-based)
 * @return the value at (row, col), or 0 if invalid
 */
uint8_t sudoku_get_cell(const struct sudoku *s, int row, int col);

/**
 * @brief Set the value at a specific cell
 * @param s pointer to sudoku structure
 * @param row row index (0-based)
 * @param col column index (0-based)
 * @param value the value to set
 * @return true if successful, false on error
 */
bool sudoku_set_cell(struct sudoku *s, int row, int col, uint8_t value);

/**
 * @brief Count the number of empty cells (cells with value 0)
 * @param s pointer to sudoku structure
 * @return number of empty cells, or -1 on error
 */
int sudoku_count_empty(const struct sudoku *s);

/**
 * @brief Count the number of filled cells (cells with non-zero value)
 * @param s pointer to sudoku structure
 * @return number of filled cells, or -1 on error
 */
int sudoku_count_filled(const struct sudoku *s);

/**
 * @brief Check if the entire sudoku is valid (no conflicts)
 * @param s pointer to sudoku structure
 * @return true if valid, false if invalid or on error
 */
bool sudoku_is_valid(const struct sudoku *s);

/**
 * @brief Check if the sudoku is completely solved
 * @param s pointer to sudoku structure
 * @return true if solved (no empty cells and valid), false otherwise
 */
bool sudoku_is_solved(const struct sudoku *s);

/**
 * @brief Compare two sudoku structures for equality
 * @param s1 first sudoku
 * @param s2 second sudoku
 * @return true if equal, false if different or on error
 */
bool sudoku_equals(const struct sudoku *s1, const struct sudoku *s2);

/**
 * @brief Copy a sudoku structure
 * @param src source sudoku
 * @return pointer to newly allocated copy, or NULL on error
 */
struct sudoku *sudoku_copy(const struct sudoku *src);

/**
 * @brief Print the sudoku to a string buffer
 * @param s pointer to sudoku structure
 * @param buffer output buffer
 * @param buffer_size size of the output buffer
 * @return number of characters written, or -1 on error
 */
int sudoku_to_string(const struct sudoku *s, char *buffer, size_t buffer_size);

/**
 * @brief Clear all cells in the sudoku (set all to 0)
 * @param s pointer to sudoku structure
 */
void sudoku_clear(struct sudoku *s);

#endif /* MISC_SUDOKU_SOLVER_H */
