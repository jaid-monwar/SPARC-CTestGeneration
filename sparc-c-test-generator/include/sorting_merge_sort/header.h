/**
 * @file header.h
 * @brief Header file for merge sort algorithm implementation
 */

#ifndef SORTING_MERGE_SORT_H
#define SORTING_MERGE_SORT_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================
 * Core merge sort functions
 * ============================================================ */

/**
 * @brief Swap two integer variables
 * @param a pointer to first variable
 * @param b pointer to second variable
 */
void swap(int *a, int *b);

/**
 * @brief Perform merge of segments
 * @param a array to sort
 * @param l left index for merge
 * @param r right index for merge
 * @param n total number of elements in the array
 */
void merge(int *a, int l, int r, int n);

/**
 * @brief Merge sort algorithm implementation
 * @param a array to sort
 * @param n number of elements in the array
 * @param l index to sort from
 * @param r index to sort till
 */
void merge_sort(int *a, int n, int l, int r);

/* ============================================================
 * Utility functions for testing
 * ============================================================ */

/**
 * @brief Check if an array is sorted in ascending order
 * @param arr array to check
 * @param n number of elements
 * @return 1 if sorted, 0 otherwise
 */
int is_sorted(int *arr, int n);

/**
 * @brief Count elements in array (returns n if valid, -1 if NULL)
 * @param arr array to count
 * @param n expected number of elements
 * @return n if array is not NULL, -1 otherwise
 */
int array_count(int *arr, int n);

/**
 * @brief Create a copy of an array
 * @param src source array
 * @param n number of elements
 * @return newly allocated copy, or NULL on failure
 */
int *array_copy(int *src, int n);

/**
 * @brief Check if two arrays are equal
 * @param a first array
 * @param b second array
 * @param n number of elements
 * @return 1 if equal, 0 otherwise
 */
int arrays_equal(int *a, int *b, int n);

/**
 * @brief Find minimum value in array
 * @param arr array to search
 * @param n number of elements
 * @return minimum value, or 0 if array is NULL or empty
 */
int array_min(int *arr, int n);

/**
 * @brief Find maximum value in array
 * @param arr array to search
 * @param n number of elements
 * @return maximum value, or 0 if array is NULL or empty
 */
int array_max(int *arr, int n);

/**
 * @brief Search for a value in array
 * @param arr array to search
 * @param n number of elements
 * @param value value to find
 * @return index of first occurrence, or -1 if not found
 */
int array_search(int *arr, int n, int value);

/**
 * @brief Count occurrences of a value in array
 * @param arr array to search
 * @param n number of elements
 * @param value value to count
 * @return number of occurrences
 */
int array_count_value(int *arr, int n, int value);

/**
 * @brief Create an array from a string of space-separated integers
 * @param str input string (e.g., "5 3 8 1 2")
 * @param n pointer to store the number of elements parsed
 * @return newly allocated array, or NULL on failure
 */
int *array_from_string(const char *str, int *n);

/**
 * @brief Convert array to string representation
 * @param arr array to convert
 * @param n number of elements
 * @param buffer output buffer
 * @param buffer_size size of output buffer
 * @return pointer to buffer, or NULL on failure
 */
char *array_to_string(int *arr, int n, char *buffer, int buffer_size);

/**
 * @brief Free an array (wrapper for free)
 * @param arr array to free
 */
void array_free(int *arr);

#endif /* SORTING_MERGE_SORT_H */
