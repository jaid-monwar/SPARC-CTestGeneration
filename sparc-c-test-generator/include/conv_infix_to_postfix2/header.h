/**
 * @file header.h
 * @brief Header file for Infix to Postfix converter
 */

#ifndef CONV_INFIX_TO_POSTFIX2_H
#define CONV_INFIX_TO_POSTFIX2_H

#include <stdint.h>
#include <stddef.h>

/**
 * @brief array implementation of stack using structure
 */
struct Stack {
	char stack[10];		///< array stack
	int top;		///< stores index of the top element
};

extern struct Stack st;		///< global declaration of stack st

/**
 * @brief Function to initialize/reset the stack
 * @returns void
 */
void initStack(void);

/**
 * @brief Function to push on the stack
 * @param opd character to be pushed in the stack
 * @returns void
 */
void push(char opd);

/**
 * @brief Function to pop from the stack
 * @returns popped character
 */
char pop(void);

/**
 * @brief Function to check whether the stack is empty or not
 * @returns 1 if the stack IS empty
 * @returns 0 if the stack is NOT empty
 */
uint16_t isEmpty(void);

/**
 * @brief Function to get top of the stack
 * @returns top of stack
 */
char Top(void);

/**
 * @brief Function to check priority of operators
 * @param opr operator whose priority is to be checked
 * @returns 0 if operator is '+' or '-'
 * @returns 1 if operator is '/' or '*' or '%'
 * @returns -1 otherwise
 */
int16_t priority(char opr);

/**
 * @brief Function to convert infix expression to postfix expression
 * @param inf the input infix expression
 * @returns output postfix expression
 */
char *convert(char inf[]);

/**
 * @brief Safe version of convert that copies result to user-provided buffer
 * @param inf the input infix expression
 * @param output buffer to store the postfix expression (must be at least 25 chars)
 * @param output_size size of the output buffer
 * @returns 0 on success, -1 on error (output buffer too small)
 */
int convert_safe(char inf[], char *output, size_t output_size);

/**
 * @brief Get the current stack size (number of elements)
 * @returns number of elements in the stack
 */
int getStackSize(void);

/**
 * @brief Check if the stack is full
 * @returns 1 if stack is full, 0 otherwise
 */
uint16_t isFull(void);

/**
 * @brief Peek at a specific position in the stack (for testing)
 * @param pos position to peek (0 = bottom, top = st.top)
 * @returns character at position, or '\0' if invalid position
 */
char peekAt(int pos);

/**
 * @brief Validate if an infix expression has balanced parentheses
 * @param inf the input infix expression
 * @returns 1 if balanced, 0 if not balanced
 */
int isBalancedParentheses(char inf[]);

/**
 * @brief Check if a character is a valid operator
 * @param c character to check
 * @returns 1 if valid operator, 0 otherwise
 */
int isOperator(char c);

/**
 * @brief Count the number of operators in an expression
 * @param expr the expression to analyze
 * @returns number of operators found
 */
int countOperators(char expr[]);

/**
 * @brief Count the number of operands (alphanumeric) in an expression
 * @param expr the expression to analyze
 * @returns number of operands found
 */
int countOperands(char expr[]);

#endif /* CONV_INFIX_TO_POSTFIX2_H */
