/**
 * @file header.h
 * @brief Header file for the Vector implementation
 * @details Declares the Vector struct and all associated functions
 */

#ifndef DS_VECTOR_H
#define DS_VECTOR_H

#include <stdio.h>
#include <stdlib.h>

/** This is the struct that defines the vector. */
typedef struct {
    int len;           ///< contains the length of the vector
    int current;       ///< holds the current item
    int* contents;     ///< the internal array itself
} Vector;

/**
 * This function initilaizes the vector and gives it a size of 1
 * and initializes the first index to 0.
 * @params Vector* (a pointer to the Vector struct)
 * @params int     (the actual data to be passed to the vector)
 * @returns 0 on success, -1 on failure
 */
int init(Vector* vec, int val);

/**
 * This function clears the heap memory allocated by the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @returns: none
 */
void delete(Vector* vec);

/**
 * This function clears the contents of the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @returns 0 on success, -1 on failure
 */
int clear(Vector* vec);

/**
 * This function returns the length the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @returns: int
 */
int len(Vector* vec);

/**
 * This function pushes a value to the end of the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @params int     (the value to be pushed)
 * @returns 0 on success, -1 on failure
 */
int push(Vector* vec, int val);

/**
 * This function get the item at the specified index of the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @params int     (the index to get value from)
 * @returns: int
 */
int get(Vector* vec, int index);

/**
 * This function sets an item at the specified index of the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @params int     (the index to set value at)
 * @returns: none
 */
void set(Vector* vec, int index, int val);

/**
 * This function gets the next item from the Vector each time it's called.
 * @params Vector* (a pointer to the Vector struct)
 * @returns: int
 */
int next(Vector* vec);

/**
 * This function returns the pointer to the begining of the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @returns: void*
 */
void* begin(Vector* vec);

/**
 * This function prints the entire Vector as a list.
 * @params Vector* (a pointer to the Vector struct)
 * @returns: none
 */
void print(Vector* vec);

/**
 * This function converts the Vector to a string representation.
 * String-based alternative to print() for testing without stdout.
 * @params Vector* (a pointer to the Vector struct)
 * @params char* buffer (output buffer to write string to)
 * @params int buffer_size (size of the output buffer)
 * @returns number of characters written, or -1 on error
 */
int vector_to_string(Vector* vec, char* buffer, int buffer_size);

/**
 * Utility function to check if a value exists in the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @params int val (the value to search for)
 * @returns index of the value if found, -1 if not found
 */
int vector_find(Vector* vec, int val);

/**
 * Utility function to check if the Vector contains a specific value.
 * @params Vector* (a pointer to the Vector struct)
 * @params int val (the value to search for)
 * @returns 1 if found, 0 if not found
 */
int vector_contains(Vector* vec, int val);

/**
 * Utility function to check if the Vector is empty.
 * @params Vector* (a pointer to the Vector struct)
 * @returns 1 if empty (len == 0), 0 otherwise
 */
int vector_is_empty(Vector* vec);

/**
 * Utility function to compare two Vectors for equality.
 * @params Vector* vec1 (first vector)
 * @params Vector* vec2 (second vector)
 * @returns 1 if equal, 0 if not equal
 */
int vector_equals(Vector* vec1, Vector* vec2);

/**
 * Utility function to get the sum of all elements in the Vector.
 * @params Vector* (a pointer to the Vector struct)
 * @returns sum of all elements, or 0 if vector is NULL/empty
 */
int vector_sum(Vector* vec);

/**
 * Utility function to reset the iterator to the beginning.
 * @params Vector* (a pointer to the Vector struct)
 */
void vector_reset_iterator(Vector* vec);

#endif /* DS_VECTOR_H */
