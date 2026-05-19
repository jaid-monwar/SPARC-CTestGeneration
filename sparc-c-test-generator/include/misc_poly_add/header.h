/**
 * @file header.h
 * @brief Header file for polynomial addition implementation
 * @details Provides declarations for polynomial operations using linked lists
 */

#ifndef MISC_POLY_ADD_H
#define MISC_POLY_ADD_H

#include <stdio.h>
#include <stdlib.h>

/**
 * @brief identifier for single-variable polynomial coefficients as a linked
 * list
 */
struct term
{
    int coef;          /**< coefficient value */
    int pow;           /**< power of the polynomial term */
    struct term *next; /**< pointer to the successive term */
};

/**
 * @brief Frees memory space
 * @param poly first term of polynomial
 * @returns void
 */
void free_poly(struct term *poly);

/**
 * @brief Creates a polynomial by appending a term
 * @param poly stores the address of the polynomial being created
 * @param coef contains the coefficient of the node
 * @param pow contains the degree
 * @returns 0 on success, -1 on failure (NULL poly or malloc failure)
 */
int create_polynomial(struct term **poly, int coef, int pow);

/**
 * @brief Adds two polynomials
 * @param pol pointer to store the resultant polynomial
 * @param poly1 first polynomial of the addition
 * @param poly2 second polynomial of the addition
 * @returns 0 on success, -1 on failure (NULL pol or malloc failure)
 */
int poly_add(struct term **pol, struct term *poly1, struct term *poly2);

/**
 * @brief Displays the polynomial to stdout
 * @param poly first term of the polynomial to be displayed
 * @returns none
 */
void display_polynomial(struct term *poly);

/**
 * @brief Converts a polynomial to a string representation
 * @param poly first term of the polynomial
 * @param buffer output buffer to store the string
 * @param buffer_size size of the output buffer
 * @returns number of characters written (excluding null terminator),
 *          or -1 if buffer is NULL or buffer_size is 0
 */
int polynomial_to_string(struct term *poly, char *buffer, size_t buffer_size);

/**
 * @brief Counts the number of terms in a polynomial
 * @param poly first term of the polynomial
 * @returns number of terms in the polynomial
 */
int poly_term_count(struct term *poly);

/**
 * @brief Gets the coefficient of a term with a specific power
 * @param poly first term of the polynomial
 * @param power the power to search for
 * @param found pointer to store whether the term was found (1 if found, 0 if not)
 * @returns the coefficient if found, 0 otherwise
 */
int poly_get_coef_by_power(struct term *poly, int power, int *found);

/**
 * @brief Gets the highest power (degree) of the polynomial
 * @param poly first term of the polynomial
 * @returns the highest power, or -1 if the polynomial is empty
 */
int poly_get_degree(struct term *poly);

/**
 * @brief Compares two polynomials for equality
 * @param poly1 first polynomial
 * @param poly2 second polynomial
 * @returns 1 if equal (same terms in same order), 0 otherwise
 */
int poly_equals(struct term *poly1, struct term *poly2);

/**
 * @brief Creates a single term (node) and returns it
 * @param coef coefficient of the term
 * @param pow power of the term
 * @returns pointer to the new term, or NULL on failure
 */
struct term *create_term(int coef, int pow);

/**
 * @brief Evaluates the polynomial at a given value of x
 * @param poly first term of the polynomial
 * @param x the value to evaluate the polynomial at
 * @returns the result of evaluating the polynomial
 */
double poly_evaluate(struct term *poly, double x);

/**
 * @brief Creates a copy (deep clone) of a polynomial
 * @param poly the polynomial to copy
 * @returns pointer to the new polynomial, or NULL on failure or if poly is NULL
 */
struct term *poly_copy(struct term *poly);

#endif /* MISC_POLY_ADD_H */
