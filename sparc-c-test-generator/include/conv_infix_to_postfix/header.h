/**
 * @file header.h
 * @brief Header file for Infix to Postfix Expression Conversion
 * @details Declares structures and functions for converting infix expressions to postfix.
 */

#ifndef CONV_INFIX_TO_POSTFIX_H
#define CONV_INFIX_TO_POSTFIX_H

/// Maximum stack capacity
#define STACK_CAPACITY 100

/**
 * @brief Stack structure for storing characters during conversion
 */
struct Stack
{
    char arr[STACK_CAPACITY];  ///> static array of characters
    int tos;                   ///> stores index on topmost element in stack
};

// Stack operations
void push(struct Stack *p, char ch);   // push element in stack
char pop(struct Stack *p);             // pop topmost element from the stack
int isEmpty(struct Stack s);           // check if stack is empty
int isFull(struct Stack s);            // check if stack is full
int stackSize(struct Stack s);         // get number of elements in stack
char peek(struct Stack s);             // look at top element without removing
void initStack(struct Stack *p);       // initialize stack

// Character classification
int isOprnd(char ch);                  // check if element is operand or not
int isOperator(char ch);               // check if character is an operator

// Precedence operations
int getPrecedence(char op1, char op2); // check operator precedence (1 if op1 > op2)
int getPrecedenceValue(char op);       // get numeric precedence of operator

// Conversion operations
void convert(char infix[], char postfix[]);  // convert infix to postfix expression

// Validation and utility
int isValidInfix(const char *expr);    // validate infix expression
int compareStrings(const char *s1, const char *s2);  // compare two strings

#endif // CONV_INFIX_TO_POSTFIX_H
