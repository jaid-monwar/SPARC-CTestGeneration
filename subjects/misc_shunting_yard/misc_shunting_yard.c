/**
 * @file
 * @brief [Shunting Yard Algorithm](https://en.wikipedia.org/wiki/Shunting_yard_algorithm)
 * @details From Wikipedia: In computer science,
 * the shunting yard algorithm is a method for parsing arithmetical or logical expressions, or a combination of both, specified in infix notation.
 * It can produce either a postfix notation string, also known as Reverse Polish notation (RPN), or an abstract syntax tree (AST).
 * The algorithm was invented by Edsger Dijkstra and named the "shunting yard" algorithm because its operation resembles that of a railroad shunting yard.
 * @author [CascadingCascade](https://github.com/CascadingCascade)
 */

#include <stdio.h>      /// for IO operations
#include <stdlib.h>     /// for memory management
#include <string.h>     /// for string operations
#include <ctype.h>      /// for isdigit()

/**
 * @brief Helper function that returns each operator's precedence
 * @param operator the operator to be queried
 * @returns the operator's precedence
 */
int getPrecedence(char operator) {
    switch (operator) {
        case '+':
        case '-': {
            return 1;
        }
        case '*':
        case '/': {
            return 2;
        }
        case '^': {
            return 3;
        }
        default:{
            return -1;
        }
    }
}

/**
 * @brief Helper function that returns each operator's precedence (with error string output)
 * @param operator the operator to be queried
 * @param error_out buffer to store error message (can be NULL)
 * @param error_size size of error buffer
 * @returns the operator's precedence, or -1 for invalid operator
 */
int getPrecedenceWithError(char operator, char *error_out, size_t error_size) {
    int result = getPrecedence(operator);
    if (result == -1 && error_out != NULL && error_size > 0) {
        snprintf(error_out, error_size, "Error: Invalid operator '%c'", operator);
    }
    return result;
}

/**
 * @brief Helper function that returns each operator's associativity
 * @param operator the operator to be queried
 * @returns '1' if the operator is left associative
 * @returns '0' if the operator is right associative
 */
int getAssociativity(char operator) {
    switch (operator) {
        case '^': {
            return 0;
        }
        case '+':
        case '-':
        case '*':
        case '/': {
            return 1;
        }
        default: {
            return -1;
        }
    }
}

/**
 * @brief Helper function that returns each operator's associativity (with error string output)
 * @param operator the operator to be queried
 * @param error_out buffer to store error message (can be NULL)
 * @param error_size size of error buffer
 * @returns '1' if the operator is left associative
 * @returns '0' if the operator is right associative
 * @returns '-1' for invalid operator
 */
int getAssociativityWithError(char operator, char *error_out, size_t error_size) {
    int result = getAssociativity(operator);
    if (result == -1 && error_out != NULL && error_size > 0) {
        snprintf(error_out, error_size, "Error: Invalid operator '%c'", operator);
    }
    return result;
}

/**
 * @brief An implementation of the shunting yard that converts infix notation to reversed polish notation
 * @param input pointer to input string
 * @param output pointer to output location
 * @returns `1` if a parentheses mismatch is detected
 * @returns `0` if no mismatches are detected
 */
int shuntingYard(const char *input, char *output) {
    if (input == NULL || output == NULL) {
        return 1;
    }

    const unsigned int inputLength = strlen(input);
    if (inputLength == 0) {
        output[0] = '\0';
        return 0;
    }

    char* operatorStack = (char*) malloc(sizeof(char) * inputLength);
    if (operatorStack == NULL) {
        return 1;
    }

    unsigned int stackPointer = 0;

    char* str = malloc(sizeof(char) * inputLength + 1);
    if (str == NULL) {
        free(operatorStack);
        return 1;
    }
    strcpy(str, input);
    char* token = strtok(str, " ");

    output[0] = '\0';

    while (token != NULL) {
        if (isdigit(token[0])) {
            strcat(output, token);
            strcat(output, " ");
            token = strtok(NULL, " ");
            continue;
        }

        switch (token[0]) {
            case '(': {
                operatorStack[stackPointer++] = token[0];
                break;
            }

            case ')': {
                if (stackPointer < 1) {
                    free(operatorStack);
                    free(str);
                    return 1;
                }

                while (operatorStack[stackPointer - 1] != '(') {
                    const unsigned int i = (stackPointer--) - 1;
                    strncat(output, &operatorStack[i], 1);
                    strcat(output, " ");

                    if (stackPointer == 0) {
                        free(operatorStack);
                        free(str);
                        return 1;
                    }
                }

                stackPointer--;
                break;
            }

            default: {
                if (stackPointer < 1) {
                    operatorStack[stackPointer++] = token[0];
                    break;
                }

                // Fixed: changed (stackPointer - 1 > 0) to (stackPointer > 0)
                if ((stackPointer > 0) && operatorStack[stackPointer - 1] != '(') {
                    const int precedence1 = getPrecedence(token[0]);
                    const int precedence2 = getPrecedence(operatorStack[stackPointer - 1]);
                    const int associativity = getAssociativity(token[0]);

                    while (((associativity && precedence1 == precedence2) ||
                             precedence2 > precedence1) &&
                            ((stackPointer > 0) && operatorStack[stackPointer - 1] != '(')) {

                        strncat(output, &operatorStack[(stackPointer--) - 1], 1);
                        strcat(output, " ");
                    }
                }

                operatorStack[stackPointer++] = token[0];
                break;
            }
        }

        token = strtok(NULL, " ");
    }

    free(str);

    while (stackPointer > 0) {
        if (operatorStack[stackPointer - 1] == '(') {
            free(operatorStack);
            return 1;
        }

        const unsigned int i = (stackPointer--) - 1;
        strncat(output, &operatorStack[i], 1);
        if (i != 0) {
            strcat(output, " ");
        }
    }

    free(operatorStack);
    return 0;
}

/**
 * @brief An implementation of the shunting yard with error message output
 * @param input pointer to input string
 * @param output pointer to output location
 * @param error_out buffer to store error message (can be NULL)
 * @param error_size size of error buffer
 * @returns `1` if a parentheses mismatch is detected
 * @returns `0` if no mismatches are detected
 */
int shuntingYardWithError(const char *input, char *output, char *error_out, size_t error_size) {
    if (input == NULL || output == NULL) {
        if (error_out != NULL && error_size > 0) {
            snprintf(error_out, error_size, "Error: NULL input or output pointer");
        }
        return 1;
    }

    const unsigned int inputLength = strlen(input);
    if (inputLength == 0) {
        output[0] = '\0';
        return 0;
    }

    char* operatorStack = (char*) malloc(sizeof(char) * inputLength);
    if (operatorStack == NULL) {
        if (error_out != NULL && error_size > 0) {
            snprintf(error_out, error_size, "Error: Memory allocation failed");
        }
        return 1;
    }

    unsigned int stackPointer = 0;

    char* str = malloc(sizeof(char) * inputLength + 1);
    if (str == NULL) {
        free(operatorStack);
        if (error_out != NULL && error_size > 0) {
            snprintf(error_out, error_size, "Error: Memory allocation failed");
        }
        return 1;
    }
    strcpy(str, input);
    char* token = strtok(str, " ");

    output[0] = '\0';

    while (token != NULL) {
        if (isdigit(token[0])) {
            strcat(output, token);
            strcat(output, " ");
            token = strtok(NULL, " ");
            continue;
        }

        switch (token[0]) {
            case '(': {
                operatorStack[stackPointer++] = token[0];
                break;
            }

            case ')': {
                if (stackPointer < 1) {
                    free(operatorStack);
                    free(str);
                    if (error_out != NULL && error_size > 0) {
                        snprintf(error_out, error_size, "Error: Mismatched parentheses - unexpected ')'");
                    }
                    return 1;
                }

                while (operatorStack[stackPointer - 1] != '(') {
                    const unsigned int i = (stackPointer--) - 1;
                    strncat(output, &operatorStack[i], 1);
                    strcat(output, " ");

                    if (stackPointer == 0) {
                        free(operatorStack);
                        free(str);
                        if (error_out != NULL && error_size > 0) {
                            snprintf(error_out, error_size, "Error: Mismatched parentheses - no matching '('");
                        }
                        return 1;
                    }
                }

                stackPointer--;
                break;
            }

            default: {
                if (stackPointer < 1) {
                    operatorStack[stackPointer++] = token[0];
                    break;
                }

                if ((stackPointer > 0) && operatorStack[stackPointer - 1] != '(') {
                    const int precedence1 = getPrecedence(token[0]);
                    const int precedence2 = getPrecedence(operatorStack[stackPointer - 1]);
                    const int associativity = getAssociativity(token[0]);

                    while (((associativity && precedence1 == precedence2) ||
                             precedence2 > precedence1) &&
                            ((stackPointer > 0) && operatorStack[stackPointer - 1] != '(')) {

                        strncat(output, &operatorStack[(stackPointer--) - 1], 1);
                        strcat(output, " ");
                    }
                }

                operatorStack[stackPointer++] = token[0];
                break;
            }
        }

        token = strtok(NULL, " ");
    }

    free(str);

    while (stackPointer > 0) {
        if (operatorStack[stackPointer - 1] == '(') {
            free(operatorStack);
            if (error_out != NULL && error_size > 0) {
                snprintf(error_out, error_size, "Error: Mismatched parentheses - unclosed '('");
            }
            return 1;
        }

        const unsigned int i = (stackPointer--) - 1;
        strncat(output, &operatorStack[i], 1);
        if (i != 0) {
            strcat(output, " ");
        }
    }

    free(operatorStack);
    return 0;
}

/**
 * @brief Check if a character is a valid operator
 * @param c the character to check
 * @returns 1 if valid operator, 0 otherwise
 */
int isValidOperator(char c) {
    return (c == '+' || c == '-' || c == '*' || c == '/' || c == '^');
}

/**
 * @brief Count the number of tokens in a space-separated string
 * @param str the string to analyze
 * @returns the number of tokens, or 0 if str is NULL
 */
int countTokens(const char *str) {
    if (str == NULL || str[0] == '\0') {
        return 0;
    }

    int count = 0;
    size_t len = strlen(str);
    char* copy = malloc(len + 1);
    if (copy == NULL) {
        return 0;
    }
    strcpy(copy, str);

    char* token = strtok(copy, " ");
    while (token != NULL) {
        count++;
        token = strtok(NULL, " ");
    }

    free(copy);
    return count;
}

/**
 * @brief Count the number of operators in a space-separated expression
 * @param str the string to analyze
 * @returns the number of operators, or 0 if str is NULL
 */
int countOperators(const char *str) {
    if (str == NULL || str[0] == '\0') {
        return 0;
    }

    int count = 0;
    size_t len = strlen(str);
    char* copy = malloc(len + 1);
    if (copy == NULL) {
        return 0;
    }
    strcpy(copy, str);

    char* token = strtok(copy, " ");
    while (token != NULL) {
        if (strlen(token) == 1 && isValidOperator(token[0])) {
            count++;
        }
        token = strtok(NULL, " ");
    }

    free(copy);
    return count;
}

/**
 * @brief Count the number of operands (numbers) in a space-separated expression
 * @param str the string to analyze
 * @returns the number of operands, or 0 if str is NULL
 */
int countOperands(const char *str) {
    if (str == NULL || str[0] == '\0') {
        return 0;
    }

    int count = 0;
    size_t len = strlen(str);
    char* copy = malloc(len + 1);
    if (copy == NULL) {
        return 0;
    }
    strcpy(copy, str);

    char* token = strtok(copy, " ");
    while (token != NULL) {
        if (isdigit(token[0])) {
            count++;
        }
        token = strtok(NULL, " ");
    }

    free(copy);
    return count;
}

/**
 * @brief Count the number of parentheses in a space-separated expression
 * @param str the string to analyze
 * @returns the number of parentheses (both left and right), or 0 if str is NULL
 */
int countParentheses(const char *str) {
    if (str == NULL || str[0] == '\0') {
        return 0;
    }

    int count = 0;
    size_t len = strlen(str);
    char* copy = malloc(len + 1);
    if (copy == NULL) {
        return 0;
    }
    strcpy(copy, str);

    char* token = strtok(copy, " ");
    while (token != NULL) {
        if (token[0] == '(' || token[0] == ')') {
            count++;
        }
        token = strtok(NULL, " ");
    }

    free(copy);
    return count;
}

/**
 * @brief Check if parentheses in an expression are balanced
 * @param str the string to analyze
 * @returns 1 if balanced, 0 otherwise
 */
int areParenthesesBalanced(const char *str) {
    if (str == NULL) {
        return 0;
    }
    if (str[0] == '\0') {
        return 1;
    }

    int balance = 0;
    size_t len = strlen(str);
    char* copy = malloc(len + 1);
    if (copy == NULL) {
        return 0;
    }
    strcpy(copy, str);

    char* token = strtok(copy, " ");
    while (token != NULL) {
        if (token[0] == '(') {
            balance++;
        } else if (token[0] == ')') {
            balance--;
            if (balance < 0) {
                free(copy);
                return 0;
            }
        }
        token = strtok(NULL, " ");
    }

    free(copy);
    return (balance == 0) ? 1 : 0;
}

/**
 * @brief Check if a string is valid RPN (Reverse Polish Notation)
 * @param str the string to validate
 * @returns 1 if valid RPN, 0 otherwise
 */
int isValidRPN(const char *str) {
    if (str == NULL) {
        return 0;
    }
    if (str[0] == '\0') {
        return 1;
    }

    int stackCount = 0;
    size_t len = strlen(str);
    char* copy = malloc(len + 1);
    if (copy == NULL) {
        return 0;
    }
    strcpy(copy, str);

    char* token = strtok(copy, " ");
    while (token != NULL) {
        if (isdigit(token[0])) {
            stackCount++;
        } else if (isValidOperator(token[0])) {
            if (stackCount < 2) {
                free(copy);
                return 0;
            }
            stackCount--;
        } else {
            free(copy);
            return 0;
        }
        token = strtok(NULL, " ");
    }

    free(copy);
    return (stackCount == 1) ? 1 : 0;
}

/**
 * @brief Compare two RPN strings for equality (ignoring trailing spaces)
 * @param rpn1 first RPN string
 * @param rpn2 second RPN string
 * @returns 1 if equal, 0 otherwise
 */
int compareRPN(const char *rpn1, const char *rpn2) {
    if (rpn1 == NULL || rpn2 == NULL) {
        return (rpn1 == rpn2) ? 1 : 0;
    }

    size_t len1 = strlen(rpn1);
    size_t len2 = strlen(rpn2);

    while (len1 > 0 && rpn1[len1 - 1] == ' ') len1--;
    while (len2 > 0 && rpn2[len2 - 1] == ' ') len2--;

    if (len1 != len2) {
        return 0;
    }

    return (strncmp(rpn1, rpn2, len1) == 0) ? 1 : 0;
}
