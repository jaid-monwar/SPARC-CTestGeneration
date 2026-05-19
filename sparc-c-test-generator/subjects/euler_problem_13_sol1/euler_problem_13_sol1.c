/**
 * \file
 * \brief [Problem 13](https://projecteuler.net/problem=13) solution
 * \author [Krishna Vedala](https://github.com/kvedala)
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/** Function to read the number from a file and store it in array.
    \n index 0 of output buffer => units place
    \n index 1 of output buffer => tens place and so on
    i.e., index i => 10^i th place
 */
int get_number(FILE *fp, char *buffer, uint8_t *out_int)
{
    if (fp == NULL || buffer == NULL || out_int == NULL)
    {
        return -1;
    }

    int l = fscanf(fp, "%s\n", buffer);
    if (l != 1)
    {
        perror("Error reading line.");
        return -1;
    }
    // printf("Number: %s\t length: %ld, %ld\n", buffer, strlen(buffer), l);

    long L = strlen(buffer);
    if (L == 0)
    {
        return -1;
    }

    for (int i = 0; i < L; i++)
    {
        if (buffer[i] < 0x30 || buffer[i] > 0x39)
        {
            perror("found inavlid character in the number!");
            return -1;
        }
        else
        {
            out_int[L - i - 1] = buffer[i] - 0x30;
        }
    }

    return 0;
}

/**
 * Function to add arbitrary length decimal integers stored in an array.
 * a + b = c = new b
 * \param a First number array
 * \param b Second number array (result is stored here)
 * \param N Length of the number arrays
 * \return 0 on success, -1 on error
 */
int add_numbers(uint8_t *a, uint8_t *b, uint8_t N)
{
    if (a == NULL || b == NULL || N == 0)
    {
        return -1;
    }

    int carry = 0;
    uint8_t *c = b; /* accumulate the result in the array 'b' */

    for (int i = 0; i < N; i++)
    {
        // printf("\t%d + %d + %d ", a[i], b[i], carry);
        c[i] = carry + a[i] + b[i];  // NOLINT // This is a known false-positive
        if (c[i] > 9)                /* check for carry */
        {
            carry = 1;
            c[i] -= 10;
        }
        else
        {
            carry = 0;
        }
        // printf("= %d, %d\n", carry, c[i]);
    }

    for (int i = N; i < N + 10; i++)
    {
        if (carry == 0)
        {
            break;
        }
        // printf("\t0 + %d + %d ", b[i], carry);
        c[i] = carry + c[i];
        if (c[i] > 9)
        {
            carry = 1;
            c[i] -= 10;
        }
        else
        {
            carry = 0;
        }
        // printf("= %d, %d\n", carry, c[i]);
    }
    return 0;
}

/** Function to print a long number */
int print_number(uint8_t *number, uint8_t N, int8_t num_digits_to_print)
{
    if (number == NULL || N == 0)
    {
        return -1;
    }

    uint8_t start_pos = N - 1;
    uint8_t end_pos;

    /* skip all initial zeros */
    while (start_pos > 0 && number[start_pos] == 0) start_pos--;

    /* if end_pos < 0, print all digits */
    if (num_digits_to_print < 0)
    {
        end_pos = 0;
    }
    else if (num_digits_to_print <= start_pos)
    {
        end_pos = start_pos - num_digits_to_print + 1;
    }
    else
    {
        fprintf(stderr, "invalid number of digits argumet!\n");
        return -1;
    }

    for (int i = start_pos; i >= end_pos; i--) putchar(number[i] + 0x30);

    putchar('\n');

    return 0;
}

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
int parse_number_string(const char *input_str, uint8_t *out_int, uint8_t max_len)
{
    if (input_str == NULL || out_int == NULL || max_len == 0)
    {
        return -1;
    }

    long L = strlen(input_str);
    if (L == 0 || L > max_len)
    {
        return -1;
    }

    /* Initialize output array to zero */
    memset(out_int, 0, max_len);

    for (int i = 0; i < L; i++)
    {
        if (input_str[i] < '0' || input_str[i] > '9')
        {
            return -1;  /* Invalid character */
        }
        out_int[L - i - 1] = input_str[i] - '0';
    }

    return 0;
}

/**
 * Convert number array to string representation.
 * Useful for test assertions.
 * \param number Input array of digits (index 0 = units place)
 * \param N Length of the number array
 * \param out_str Output string buffer
 * \param out_str_len Length of output buffer
 * \return 0 on success, -1 on error
 */
int number_to_string(uint8_t *number, uint8_t N, char *out_str, size_t out_str_len)
{
    if (number == NULL || out_str == NULL || N == 0 || out_str_len == 0)
    {
        return -1;
    }

    uint8_t start_pos = N - 1;

    /* Skip leading zeros */
    while (start_pos > 0 && number[start_pos] == 0) start_pos--;

    size_t num_digits = start_pos + 1;
    if (num_digits >= out_str_len)
    {
        return -1;  /* Output buffer too small */
    }

    size_t out_idx = 0;
    for (int i = start_pos; i >= 0; i--)
    {
        out_str[out_idx++] = number[i] + '0';
    }
    out_str[out_idx] = '\0';

    return 0;
}

/**
 * Get the first N digits of a number as a string.
 * \param number Input array of digits (index 0 = units place)
 * \param N Length of the number array
 * \param num_digits Number of digits to extract from the front
 * \param out_str Output string buffer
 * \param out_str_len Length of output buffer
 * \return 0 on success, -1 on error
 */
int get_first_n_digits(uint8_t *number, uint8_t N, uint8_t num_digits, char *out_str, size_t out_str_len)
{
    if (number == NULL || out_str == NULL || N == 0 || out_str_len == 0 || num_digits == 0)
    {
        return -1;
    }

    if (num_digits >= out_str_len)
    {
        return -1;
    }

    uint8_t start_pos = N - 1;

    /* Skip leading zeros */
    while (start_pos > 0 && number[start_pos] == 0) start_pos--;

    size_t actual_digits = start_pos + 1;
    if (num_digits > actual_digits)
    {
        return -1;  /* Not enough digits */
    }

    for (uint8_t i = 0; i < num_digits; i++)
    {
        out_str[i] = number[start_pos - i] + '0';
    }
    out_str[num_digits] = '\0';

    return 0;
}

/* ============================================================================
 * UTILITY FUNCTIONS FOR TEST ASSERTIONS
 * ============================================================================ */

/**
 * Count the number of significant digits in a number array.
 * \param number Input array of digits
 * \param N Length of the number array
 * \return Number of significant digits, or 0 if invalid input
 */
uint8_t count_digits(uint8_t *number, uint8_t N)
{
    if (number == NULL || N == 0)
    {
        return 0;
    }

    uint8_t start_pos = N - 1;
    while (start_pos > 0 && number[start_pos] == 0) start_pos--;

    /* Handle case of all zeros */
    if (start_pos == 0 && number[0] == 0)
    {
        return 1;  /* Zero has 1 digit */
    }

    return start_pos + 1;
}

/**
 * Compare two number arrays for equality.
 * \param a First number array
 * \param b Second number array
 * \param N Length of arrays
 * \return 1 if equal, 0 if not equal or invalid input
 */
int numbers_equal(uint8_t *a, uint8_t *b, uint8_t N)
{
    if (a == NULL || b == NULL || N == 0)
    {
        return 0;
    }

    for (uint8_t i = 0; i < N; i++)
    {
        if (a[i] != b[i])
        {
            return 0;
        }
    }
    return 1;
}

/**
 * Check if a digit array represents zero.
 * \param number Input array of digits
 * \param N Length of the number array
 * \return 1 if zero, 0 otherwise
 */
int is_zero(uint8_t *number, uint8_t N)
{
    if (number == NULL || N == 0)
    {
        return 0;
    }

    for (uint8_t i = 0; i < N; i++)
    {
        if (number[i] != 0)
        {
            return 0;
        }
    }
    return 1;
}

/**
 * Initialize a number array to zero.
 * \param number Array to initialize
 * \param N Length of array
 */
void init_number(uint8_t *number, uint8_t N)
{
    if (number != NULL && N > 0)
    {
        memset(number, 0, N);
    }
}

/**
 * Copy a number array from source to destination.
 * \param dest Destination array
 * \param src Source array
 * \param N Length of arrays
 * \return 0 on success, -1 on error
 */
int copy_number(uint8_t *dest, uint8_t *src, uint8_t N)
{
    if (dest == NULL || src == NULL || N == 0)
    {
        return -1;
    }

    memcpy(dest, src, N);
    return 0;
}

/**
 * Get a specific digit from a number array.
 * \param number Input array of digits
 * \param N Length of the number array
 * \param position Position from the right (0 = units place)
 * \return Digit value (0-9), or -1 on error
 */
int get_digit_at(uint8_t *number, uint8_t N, uint8_t position)
{
    if (number == NULL || position >= N)
    {
        return -1;
    }
    return number[position];
}

