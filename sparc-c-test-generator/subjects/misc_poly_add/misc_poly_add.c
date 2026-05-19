/**
 * @file
 * @brief Implementation of [Addition of two polynomials]
 * (https://en.wikipedia.org/wiki/Polynomial#Addition)
 * @author [Ankita Roy Chowdhury](https://github.com/Ankita19ms0010)
 * @details
 * This code takes two polynomials as input
 * and prints their sum using linked list.
 * The polynomials must be in increasing or decreasing order of degree.
 * Degree must be positive.
 */
#include <stdio.h>  // for io operations
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
void free_poly(struct term *poly)
{
    while (poly)
    {
        struct term *next = poly->next;
        free(poly);
        poly = next;
    }
}

/**
 * The function will create a polynomial
 * @param poly stores the address of the polynomial being created
 * @param coef contains the coefficient of the node
 * @param pow contains the degree
 * @returns 0 on success, -1 on failure (NULL poly or malloc failure)
 */
int create_polynomial(struct term **poly, int coef, int pow)
{
    if (poly == NULL)
    {
        return -1;
    }

    // Creating the polynomial using temporary linked lists
    struct term **temp1 = poly;

    while (*temp1)
    {
        temp1 = &(*temp1)->next;
    }

    // Now temp1 reaches to the end of the list
    *temp1 = (struct term *)malloc(
        sizeof(struct term));  // Create the term and linked as the tail
    if (*temp1 == NULL)
    {
        return -1;
    }
    (*temp1)->coef = coef;
    (*temp1)->pow = pow;
    (*temp1)->next = NULL;
    return 0;
}

/**
 * The function will add 2 polynomials
 * @param pol pointer to store the resultant polynomial
 * @param poly1 first polynomial of the addition
 * @param poly2 second polynomial of the addition
 * @returns 0 on success, -1 on failure (NULL pol or malloc failure)
 */
int poly_add(struct term **pol, struct term *poly1, struct term *poly2)
{
    if (pol == NULL)
    {
        return -1;
    }

    // Handle case where both inputs are NULL
    if (poly1 == NULL && poly2 == NULL)
    {
        *pol = NULL;
        return 0;
    }

    // Creating a temporary linked list to store the resultant polynomial
    struct term *temp = (struct term *)malloc(sizeof(struct term));
    if (temp == NULL)
    {
        return -1;
    }
    temp->next = NULL;
    *pol =
        temp;  //*pol always points to the 1st node of the resultant polynomial

    // Comparing the powers of the nodes of both the polynomials
    // until one gets exhausted
    while (poly1 && poly2)
    {
        /* If the power of the first polynomial is greater than the power of the
       second one place the power and coefficient of that node of the first
       polynomial in temp and increase the pointer poly1
       */
        if (poly1->pow > poly2->pow)
        {
            temp->coef = poly1->coef;
            temp->pow = poly1->pow;
            poly1 = poly1->next;
        }
        /* If the power of the second polynomial is greater than the power of
          the first one place the power and coefficient of that node of the
          second polynomial in temp and increase the pointer poly2
        */
        else if (poly1->pow < poly2->pow)
        {
            temp->coef = poly2->coef;
            temp->pow = poly2->pow;
            poly2 = poly2->next;
        }
        /* If both of them have same power then sum the coefficients
          place both the summed coefficient and the power in temp
          increase both the pointers poly1 and poly2
        */
        else
        {
            temp->coef = poly1->coef + poly2->coef;
            temp->pow = poly1->pow;
            poly1 = poly1->next;
            poly2 = poly2->next;
        }
        /* If none of the polynomials are exhausted
         dynamically create a node in temp
         */
        if (poly1 && poly2)
        {
            temp->next = (struct term *)malloc(
                sizeof(struct term));  // Dynamic node creation
            if (temp->next == NULL)
            {
                free_poly(*pol);
                *pol = NULL;
                return -1;
            }
            temp = temp->next;         // Increase the pointer temp
            temp->next = NULL;
        }
    }
    /* If one of the polynomials is exhausted
    place the rest of the other polynomial as it is in temp
    by creating nodes dynamically
    */
    while (poly1 || poly2)
    {
        temp->next = (struct term *)malloc(
            sizeof(struct term));  // Dynamic node creation
        if (temp->next == NULL)
        {
            free_poly(*pol);
            *pol = NULL;
            return -1;
        }
        temp = temp->next;         // Increasing the pointer
        temp->next = NULL;

        /* If poly1 is not exhausted
        place rest of that polynomial in temp
        */
        if (poly1)
        {
            temp->coef = poly1->coef;
            temp->pow = poly1->pow;
            poly1 = poly1->next;
        }
        /* If poly2 is not exhausted
       place rest of that polynomial in temp
       */
        else if (poly2)
        {
            temp->coef = poly2->coef;
            temp->pow = poly2->pow;
            poly2 = poly2->next;
        }
    }
    return 0;
}

/**
 * The function will display the polynomial
 * @param poly first term of the polynomial to be displayed
 * @returns none
 */
void display_polynomial(struct term *poly)
{
    while (poly != NULL)
    {
        printf("%d x^%d", poly->coef, poly->pow);
        poly = poly->next;
        if (poly != NULL)
        {
            printf(" + ");
        }
    }
}

/**
 * @brief Converts a polynomial to a string representation
 * @param poly first term of the polynomial
 * @param buffer output buffer to store the string
 * @param buffer_size size of the output buffer
 * @returns number of characters written (excluding null terminator),
 *          or -1 if buffer is NULL or buffer_size is 0
 */
int polynomial_to_string(struct term *poly, char *buffer, size_t buffer_size)
{
    if (buffer == NULL || buffer_size == 0)
    {
        return -1;
    }

    buffer[0] = '\0';
    size_t offset = 0;

    if (poly == NULL)
    {
        return 0;
    }

    while (poly != NULL)
    {
        int written = snprintf(buffer + offset, buffer_size - offset,
                               "%d x^%d", poly->coef, poly->pow);
        if (written < 0 || (size_t)written >= buffer_size - offset)
        {
            break;
        }
        offset += written;

        poly = poly->next;
        if (poly != NULL && offset < buffer_size - 1)
        {
            written = snprintf(buffer + offset, buffer_size - offset, " + ");
            if (written < 0 || (size_t)written >= buffer_size - offset)
            {
                break;
            }
            offset += written;
        }
    }

    return (int)offset;
}

/**
 * @brief Counts the number of terms in a polynomial
 * @param poly first term of the polynomial
 * @returns number of terms in the polynomial
 */
int poly_term_count(struct term *poly)
{
    int count = 0;
    while (poly != NULL)
    {
        count++;
        poly = poly->next;
    }
    return count;
}

/**
 * @brief Gets the coefficient of a term with a specific power
 * @param poly first term of the polynomial
 * @param power the power to search for
 * @param found pointer to store whether the term was found (1 if found, 0 if not)
 * @returns the coefficient if found, 0 otherwise
 */
int poly_get_coef_by_power(struct term *poly, int power, int *found)
{
    if (found != NULL)
    {
        *found = 0;
    }

    while (poly != NULL)
    {
        if (poly->pow == power)
        {
            if (found != NULL)
            {
                *found = 1;
            }
            return poly->coef;
        }
        poly = poly->next;
    }
    return 0;
}

/**
 * @brief Gets the highest power (degree) of the polynomial
 * @param poly first term of the polynomial
 * @returns the highest power, or -1 if the polynomial is empty
 */
int poly_get_degree(struct term *poly)
{
    if (poly == NULL)
    {
        return -1;
    }

    int max_pow = poly->pow;
    while (poly != NULL)
    {
        if (poly->pow > max_pow)
        {
            max_pow = poly->pow;
        }
        poly = poly->next;
    }
    return max_pow;
}

/**
 * @brief Compares two polynomials for equality
 * @param poly1 first polynomial
 * @param poly2 second polynomial
 * @returns 1 if equal (same terms in same order), 0 otherwise
 */
int poly_equals(struct term *poly1, struct term *poly2)
{
    while (poly1 != NULL && poly2 != NULL)
    {
        if (poly1->coef != poly2->coef || poly1->pow != poly2->pow)
        {
            return 0;
        }
        poly1 = poly1->next;
        poly2 = poly2->next;
    }

    return (poly1 == NULL && poly2 == NULL);
}

/**
 * @brief Creates a single term (node) and returns it
 * @param coef coefficient of the term
 * @param pow power of the term
 * @returns pointer to the new term, or NULL on failure
 */
struct term *create_term(int coef, int pow)
{
    struct term *node = (struct term *)malloc(sizeof(struct term));
    if (node == NULL)
    {
        return NULL;
    }
    node->coef = coef;
    node->pow = pow;
    node->next = NULL;
    return node;
}

/**
 * @brief Evaluates the polynomial at a given value of x
 * @param poly first term of the polynomial
 * @param x the value to evaluate the polynomial at
 * @returns the result of evaluating the polynomial
 */
double poly_evaluate(struct term *poly, double x)
{
    double result = 0.0;
    while (poly != NULL)
    {
        double term_value = poly->coef;
        for (int i = 0; i < poly->pow; i++)
        {
            term_value *= x;
        }
        result += term_value;
        poly = poly->next;
    }
    return result;
}

/**
 * @brief Creates a copy (deep clone) of a polynomial
 * @param poly the polynomial to copy
 * @returns pointer to the new polynomial, or NULL on failure or if poly is NULL
 */
struct term *poly_copy(struct term *poly)
{
    if (poly == NULL)
    {
        return NULL;
    }

    struct term *new_poly = NULL;
    struct term *tail = NULL;

    while (poly != NULL)
    {
        struct term *node = create_term(poly->coef, poly->pow);
        if (node == NULL)
        {
            free_poly(new_poly);
            return NULL;
        }

        if (new_poly == NULL)
        {
            new_poly = node;
            tail = node;
        }
        else
        {
            tail->next = node;
            tail = node;
        }
        poly = poly->next;
    }

    return new_poly;
}

