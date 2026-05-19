/**
 * @file header.h
 * @brief Header file for decimal to any-base conversion functions
 */

#ifndef CONV_DECIMAL_TO_ANY_BASE_H
#define CONV_DECIMAL_TO_ANY_BASE_H

#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Checking if alphabet is valid
 * @param alphabet base alphabet inputed by user
 * @return true if alphabet is bad (invalid), false if valid
 */
bool isbad_alphabet(const char* alphabet);

/**
 * @brief Calculate the final length of the converted number
 * @param nb number to convert
 * @param base calculated from alphabet
 * @return Converted nb string length
 */
uint64_t converted_len(uint64_t nb, uint64_t base);

/**
 * @brief Convert positive decimal integer into anybase recursively
 * @param nb number to convert
 * @param alphabet inputed by user used for base convertion
 * @param base calculated from alphabet
 * @param converted string filled with the convertion's result
 */
void convertion(uint64_t nb, const char* alphabet, uint64_t base, char* converted);

/**
 * @brief Convert any unsigned integers into any ascii positive base
 * @param nb number to convert
 * @param alphabet base's alphabet
 * @return nb converted on success, NULL on error
 */
char* decimal_to_anybase(uint64_t nb, const char* alphabet);

/* Utility functions for testing */

/**
 * @brief Get the length of a converted number string
 * @param nb number to convert
 * @param alphabet base alphabet
 * @return length of converted string, 0 if alphabet is invalid
 */
uint64_t get_converted_length(uint64_t nb, const char* alphabet);

/**
 * @brief Check if two converted numbers are equal
 * @param nb1 first number
 * @param nb2 second number
 * @param alphabet base alphabet
 * @return true if conversions are equal, false otherwise
 */
bool conversions_equal(uint64_t nb1, uint64_t nb2, const char* alphabet);

/**
 * @brief Convert and compare with expected string
 * @param nb number to convert
 * @param alphabet base alphabet
 * @param expected expected result string
 * @return true if conversion matches expected, false otherwise
 */
bool conversion_matches(uint64_t nb, const char* alphabet, const char* expected);

/**
 * @brief Get the base size from an alphabet
 * @param alphabet base alphabet string
 * @return base size, 0 if invalid
 */
uint64_t get_base_size(const char* alphabet);

/**
 * @brief Check if an alphabet is valid for conversion
 * @param alphabet base alphabet string
 * @return true if valid, false if invalid
 */
bool is_valid_alphabet(const char* alphabet);

#endif /* CONV_DECIMAL_TO_ANY_BASE_H */
