/**
 * @file header.h
 * @brief Header file for Shunting Yard Algorithm implementation
 */

#ifndef MISC_SHUNTING_YARD_H
#define MISC_SHUNTING_YARD_H

#include <stddef.h>

/**
 * @brief Helper function that returns each operator's precedence
 * @param operator the operator to be queried
 * @returns the operator's precedence (1 for +/-, 2 for *//, 3 for ^)
 * @returns -1 for invalid operator
 */
int getPrecedence(char operator);

/**
 * @brief Helper function that returns each operator's precedence (with error string output)
 * @param operator the operator to be queried
 * @param error_out buffer to store error message (can be NULL)
 * @param error_size size of error buffer
 * @returns the operator's precedence, or -1 for invalid operator
 */
int getPrecedenceWithError(char operator, char *error_out, size_t error_size);

/**
 * @brief Helper function that returns each operator's associativity
 * @param operator the operator to be queried
 * @returns 1 if the operator is left associative (+, -, *, /)
 * @returns 0 if the operator is right associative (^)
 * @returns -1 for invalid operator
 */
int getAssociativity(char operator);

/**
 * @brief Helper function that returns each operator's associativity (with error string output)
 * @param operator the operator to be queried
 * @param error_out buffer to store error message (can be NULL)
 * @param error_size size of error buffer
 * @returns 1 if the operator is left associative
 * @returns 0 if the operator is right associative
 * @returns -1 for invalid operator
 */
int getAssociativityWithError(char operator, char *error_out, size_t error_size);

/**
 * @brief An implementation of the shunting yard that converts infix notation to reversed polish notation
 * @param input pointer to input string (space-separated tokens)
 * @param output pointer to output location (must be pre-allocated with sufficient size)
 * @returns 0 if successful
 * @returns 1 if a parentheses mismatch is detected or other error
 */
int shuntingYard(const char *input, char *output);

/**
 * @brief An implementation of the shunting yard with error message output
 * @param input pointer to input string (space-separated tokens)
 * @param output pointer to output location (must be pre-allocated with sufficient size)
 * @param error_out buffer to store error message (can be NULL)
 * @param error_size size of error buffer
 * @returns 0 if successful
 * @returns 1 if a parentheses mismatch is detected or other error
 */
int shuntingYardWithError(const char *input, char *output, char *error_out, size_t error_size);

/**
 * @brief Check if a character is a valid operator
 * @param c the character to check
 * @returns 1 if valid operator (+, -, *, /, ^), 0 otherwise
 */
int isValidOperator(char c);

/**
 * @brief Count the number of tokens in a space-separated string
 * @param str the string to analyze
 * @returns the number of tokens, or 0 if str is NULL
 */
int countTokens(const char *str);

/**
 * @brief Count the number of operators in a space-separated expression
 * @param str the string to analyze
 * @returns the number of operators, or 0 if str is NULL
 */
int countOperators(const char *str);

/**
 * @brief Count the number of operands (numbers) in a space-separated expression
 * @param str the string to analyze
 * @returns the number of operands, or 0 if str is NULL
 */
int countOperands(const char *str);

/**
 * @brief Count the number of parentheses in a space-separated expression
 * @param str the string to analyze
 * @returns the number of parentheses (both left and right), or 0 if str is NULL
 */
int countParentheses(const char *str);

/**
 * @brief Check if parentheses in an expression are balanced
 * @param str the string to analyze
 * @returns 1 if balanced, 0 otherwise
 */
int areParenthesesBalanced(const char *str);

/**
 * @brief Check if a string is valid RPN (Reverse Polish Notation)
 * @param str the string to validate
 * @returns 1 if valid RPN, 0 otherwise
 */
int isValidRPN(const char *str);

/**
 * @brief Compare two RPN strings for equality (ignoring trailing spaces)
 * @param rpn1 first RPN string
 * @param rpn2 second RPN string
 * @returns 1 if equal, 0 otherwise
 */
int compareRPN(const char *rpn1, const char *rpn2);

#endif /* MISC_SHUNTING_YARD_H */
