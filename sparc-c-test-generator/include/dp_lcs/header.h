#ifndef DP_LCS_H
#define DP_LCS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Direction constants for backtracking */
enum {LEFT, UP, DIAG};

/**
 * @brief Computes LCS between s1 and s2 using a dynamic-programming approach
 * @param s1 first null-terminated string
 * @param s2 second null-terminated string
 * @param l1 length of s1
 * @param l2 length of s2
 * @param L matrix of size (l1+1) x (l2+1) for LCS lengths
 * @param B matrix of size (l1+1) x (l2+1) for directions
 */
void lcslen(const char *s1, const char *s2, int l1, int l2, int **L, int **B);

/**
 * @brief Builds the LCS according to B using a traceback approach
 * @param s1 first null-terminated string
 * @param l1 length of s1
 * @param l2 length of s2
 * @param L matrix of size (l1+1) x (l2+1) for LCS lengths
 * @param B matrix of size (l1+1) x (l2+1) for directions
 * @returns newly allocated LCS string, or NULL on failure
 */
char *lcsbuild(const char *s1, int l1, int l2, int **L, int **B);

/**
 * @brief Allocates and initializes a 2D matrix of integers
 * @param rows number of rows
 * @param cols number of columns
 * @returns pointer to allocated matrix, or NULL on failure
 */
int **allocate_matrix(int rows, int cols);

/**
 * @brief Frees a 2D matrix of integers
 * @param matrix pointer to the matrix
 * @param rows number of rows
 */
void free_matrix(int **matrix, int rows);

/**
 * @brief Gets the LCS length from the L matrix
 * @param L the LCS length matrix
 * @param l1 length of first string
 * @param l2 length of second string
 * @returns LCS length
 */
int get_lcs_length(int **L, int l1, int l2);

/**
 * @brief Computes and returns the LCS of two strings
 * @param s1 first null-terminated string
 * @param s2 second null-terminated string
 * @param out_length pointer to store the LCS length (can be NULL)
 * @returns newly allocated LCS string, or NULL on failure
 */
char *compute_lcs(const char *s1, const char *s2, int *out_length);

/**
 * @brief Checks if a string is a valid subsequence of another
 * @param subsequence the potential subsequence
 * @param original the original string
 * @returns 1 if valid subsequence, 0 otherwise
 */
int is_valid_subsequence(const char *subsequence, const char *original);

/**
 * @brief Checks if a string is a common subsequence of two strings
 * @param subsequence the potential common subsequence
 * @param s1 first string
 * @param s2 second string
 * @returns 1 if valid common subsequence, 0 otherwise
 */
int is_common_subsequence(const char *subsequence, const char *s1, const char *s2);

/**
 * @brief Verifies that a computed LCS is correct
 * @param s1 first string
 * @param s2 second string
 * @param lcs the computed LCS
 * @param expected_length expected length of LCS
 * @returns 1 if LCS is valid, 0 otherwise
 */
int verify_lcs(const char *s1, const char *s2, const char *lcs, int expected_length);

/**
 * @brief Gets the direction value at a specific position in the B matrix
 * @param B the directions matrix
 * @param i row index
 * @param j column index
 * @returns direction value (LEFT, UP, or DIAG), or -1 on error
 */
int get_direction(int **B, int i, int j);

/**
 * @brief Gets the LCS value at a specific position in the L matrix
 * @param L the LCS length matrix
 * @param i row index
 * @param j column index
 * @returns LCS length value at position, or -1 on error
 */
int get_lcs_value(int **L, int i, int j);

#endif /* DP_LCS_H */
