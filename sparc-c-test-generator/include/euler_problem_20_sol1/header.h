#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdio.h>
#include <stdlib.h>
#include <time.h>


// Struct definitions
typedef struct _big_int {
    char value;
    struct _big_int * next_digit;
    struct _big_int * prev_digit;
} big_int;

// Function declarations
big_int * add_digit(big_int * digit, char value);
char remove_digits(big_int * digit, int N);

#endif
