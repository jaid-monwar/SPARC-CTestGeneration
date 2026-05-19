/**
 * \file header.h
 * \brief Header file for Problem 13 solution - Large number addition
 */
#ifndef EULER_PROBLEM_13_SOL1_H
#define EULER_PROBLEM_13_SOL1_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================================
 * ORIGINAL FUNCTIONS
 * ============================================================================ */

/**
 * Function to read the number from a file and store it in array.
 * index 0 of output buffer => units place
 * index 1 of output buffer => tens place and so on
 * i.e., index i => 10^i th place
 * \param fp File pointer to read from
 * \param buffer Temporary character buffer
 * \param out_int Output array for digits
 * \return 0 on success, -1 on error
 */
int get_number(FILE *fp, char *buffer, uint8_t *out_int);

/**
 * Function to add arbitrary length decimal integers stored in an array.
 * a + b = c = new b (result stored in b)
 * \param a First number array
 * \param b Second number array (result is stored here)
 * \param N Length of the number arrays
 * \return 0 on success, -1 on error
 */
int add_numbers(uint8_t *a, uint8_t *b, uint8_t N);

/**
 * Function to print a long number to stdout.
 * \param number Array of digits (index 0 = units place)
 * \param N Length of the number array
 * \param num_digits_to_print Number of digits to print (-1 for all)
 * \return 0 on success, -1 on error
 */
int print_number(uint8_t *number, uint8_t N, int8_t num_digits_to_print);

/* ============================================================================
 * STRING-BASED ALTERNATIVES FOR TESTING (no FILE* dependency)
 * ============================================================================ */

/**
 * String-based number parser - parses a number string directly into output array.
 * Replaces FILE-based get_number for testing purposes.
 * \param input_str The number string to parse
 * \param out_int Output array to store digits (index 0 = units place)
 * \param max_len Maximum length of output array
 * \return 0 on success, -1 on error
 */
int parse_number_string(const char *input_str, uint8_t *out_int, uint8_t max_len);

/**
 * Convert number array to string representation.
 * Useful for test assertions.
 * \param number Input array of digits (index 0 = units place)
 * \param N Length of the number array
 * \param out_str Output string buffer
 * \param out_str_len Length of output buffer
 * \return 0 on success, -1 on error
 */
int number_to_string(uint8_t *number, uint8_t N, char *out_str, size_t out_str_len);

/**
 * Get the first N digits of a number as a string.
 * \param number Input array of digits (index 0 = units place)
 * \param N Length of the number array
 * \param num_digits Number of digits to extract from the front
 * \param out_str Output string buffer
 * \param out_str_len Length of output buffer
 * \return 0 on success, -1 on error
 */
int get_first_n_digits(uint8_t *number, uint8_t N, uint8_t num_digits, char *out_str, size_t out_str_len);

/* ============================================================================
 * UTILITY FUNCTIONS FOR TEST ASSERTIONS
 * ============================================================================ */

/**
 * Count the number of significant digits in a number array.
 * \param number Input array of digits
 * \param N Length of the number array
 * \return Number of significant digits, or 0 if invalid input
 */
uint8_t count_digits(uint8_t *number, uint8_t N);

/**
 * Compare two number arrays for equality.
 * \param a First number array
 * \param b Second number array
 * \param N Length of arrays
 * \return 1 if equal, 0 if not equal or invalid input
 */
int numbers_equal(uint8_t *a, uint8_t *b, uint8_t N);

/**
 * Check if a digit array represents zero.
 * \param number Input array of digits
 * \param N Length of the number array
 * \return 1 if zero, 0 otherwise
 */
int is_zero(uint8_t *number, uint8_t N);

/**
 * Initialize a number array to zero.
 * \param number Array to initialize
 * \param N Length of array
 */
void init_number(uint8_t *number, uint8_t N);

/**
 * Copy a number array from source to destination.
 * \param dest Destination array
 * \param src Source array
 * \param N Length of arrays
 * \return 0 on success, -1 on error
 */
int copy_number(uint8_t *dest, uint8_t *src, uint8_t N);

/**
 * Get a specific digit from a number array.
 * \param number Input array of digits
 * \param N Length of the number array
 * \param position Position from the right (0 = units place)
 * \return Digit value (0-9), or -1 on error
 */
int get_digit_at(uint8_t *number, uint8_t N, uint8_t position);

#endif /* EULER_PROBLEM_13_SOL1_H */
