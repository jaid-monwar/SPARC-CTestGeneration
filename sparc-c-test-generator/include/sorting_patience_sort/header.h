/**
 * @file header.h
 * @brief Header file for Patience Sort algorithm
 */

#ifndef SORTING_PATIENCE_SORT_H
#define SORTING_PATIENCE_SORT_H

#include <stdlib.h>

/**
 * @brief Sorts the target array using patience sort algorithm
 * @param array pointer to the array to be sorted
 * @param length length of the target array
 * @returns 0 on success, -1 on error (null array, invalid length, or allocation failure)
 */
int patienceSort(int *array, int length);

/**
 * @brief Check if an array is sorted in ascending order
 * @param array pointer to the array to check
 * @param length length of the array
 * @returns 1 if sorted in ascending order, 0 otherwise
 */
int isSorted(int *array, int length);

/**
 * @brief Check if an array is sorted in descending order
 * @param array pointer to the array to check
 * @param length length of the array
 * @returns 1 if sorted in descending order, 0 otherwise
 */
int isSortedDescending(int *array, int length);

/**
 * @brief Count occurrences of a value in an array
 * @param array pointer to the array
 * @param length length of the array
 * @param value value to count
 * @returns count of occurrences, or -1 on error
 */
int countOccurrences(int *array, int length, int value);

/**
 * @brief Find the minimum value in an array
 * @param array pointer to the array
 * @param length length of the array
 * @param result pointer to store the minimum value
 * @returns 0 on success, -1 on error
 */
int findMin(int *array, int length, int *result);

/**
 * @brief Find the maximum value in an array
 * @param array pointer to the array
 * @param length length of the array
 * @param result pointer to store the maximum value
 * @returns 0 on success, -1 on error
 */
int findMax(int *array, int length, int *result);

/**
 * @brief Check if two arrays have the same elements (same multiset)
 * @param array1 pointer to first array
 * @param array2 pointer to second array
 * @param length length of both arrays
 * @returns 1 if same elements, 0 otherwise
 */
int haveSameElements(int *array1, int *array2, int length);

/**
 * @brief Copy an array to a new allocated array
 * @param array pointer to the source array
 * @param length length of the array
 * @returns pointer to the copy, or NULL on error
 */
int* copyArray(int *array, int length);

/**
 * @brief Compare two arrays for equality
 * @param array1 pointer to first array
 * @param array2 pointer to second array
 * @param length length of both arrays
 * @returns 1 if equal, 0 otherwise
 */
int arraysEqual(int *array1, int *array2, int length);

/**
 * @brief Format array as string for debugging (writes to provided buffer)
 * @param array pointer to the array
 * @param length length of the array
 * @param buffer output buffer
 * @param bufferSize size of the output buffer
 * @returns 0 on success, -1 on error
 */
int arrayToString(int *array, int length, char *buffer, int bufferSize);

#endif /* SORTING_PATIENCE_SORT_H */
