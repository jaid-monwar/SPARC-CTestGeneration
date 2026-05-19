/**
 * @file header.h
 * @brief Header file for Heap Sort implementation
 */

#ifndef SORTING_HEAP_SORT_2_H
#define SORTING_HEAP_SORT_2_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

/**
 * @brief Swapped two numbers using pointer
 * @param first pointer of first number
 * @param second pointer of second number
 */
void swap(int8_t *first, int8_t *second);

/**
 * @brief heapifyDown Adjusts new root to the correct position in the heap
 * This heapify procedure can be thought of as building a heap from
 * the top down by successively shifting downward to establish the
 * heap property.
 * @param arr array to be sorted
 * @param size size of array
 * @return void
 */
void heapifyDown(int8_t *arr, const uint8_t size);

/**
 * @brief heapifyUp Adjusts arr[i] to the correct position in the heap
 * This heapify procedure can be thought of as building a heap from
 * the bottom up by successively shifting upward to establish the
 * heap property.
 * @param arr array to be sorted
 * @param i index of the pushed element
 * @return void
 */
void heapifyUp(int8_t *arr, uint8_t i);

/**
 * @brief Heap Sort algorithm
 * @param arr array to be sorted
 * @param size size of the array
 * @returns void
 */
void heapSort(int8_t *arr, const uint8_t size);

/**
 * @brief Create a new array with given values
 * @param values source array to copy from
 * @param size number of elements
 * @returns pointer to newly allocated array, or NULL on failure
 */
int8_t *createArray(const int8_t *values, uint8_t size);

/**
 * @brief Free an array
 * @param arr pointer to array to free
 */
void freeArray(int8_t *arr);

/**
 * @brief Check if array is sorted in ascending order
 * @param arr array to check
 * @param size size of array
 * @returns 1 if sorted, 0 otherwise
 */
int isSorted(const int8_t *arr, uint8_t size);

/**
 * @brief Compare two arrays for equality
 * @param arr1 first array
 * @param arr2 second array
 * @param size size of both arrays
 * @returns 1 if equal, 0 otherwise
 */
int arraysEqual(const int8_t *arr1, const int8_t *arr2, uint8_t size);

/**
 * @brief Copy an array
 * @param src source array
 * @param size size of array
 * @returns pointer to newly allocated copy, or NULL on failure
 */
int8_t *copyArray(const int8_t *src, uint8_t size);

/**
 * @brief Get element at index
 * @param arr array
 * @param size size of array
 * @param index index to access
 * @param out_value pointer to store the value
 * @returns 1 on success, 0 if index out of bounds or arr is NULL
 */
int getElement(const int8_t *arr, uint8_t size, uint8_t index, int8_t *out_value);

/**
 * @brief Find minimum value in array
 * @param arr array to search
 * @param size size of array
 * @param out_min pointer to store minimum value
 * @returns 1 on success, 0 if array is empty or NULL
 */
int findMin(const int8_t *arr, uint8_t size, int8_t *out_min);

/**
 * @brief Find maximum value in array
 * @param arr array to search
 * @param size size of array
 * @param out_max pointer to store maximum value
 * @returns 1 on success, 0 if array is empty or NULL
 */
int findMax(const int8_t *arr, uint8_t size, int8_t *out_max);

/**
 * @brief Check if array contains a specific value
 * @param arr array to search
 * @param size size of array
 * @param value value to find
 * @returns 1 if found, 0 otherwise
 */
int containsValue(const int8_t *arr, uint8_t size, int8_t value);

/**
 * @brief Count occurrences of a value in array
 * @param arr array to search
 * @param size size of array
 * @param value value to count
 * @returns number of occurrences
 */
uint8_t countOccurrences(const int8_t *arr, uint8_t size, int8_t value);

/**
 * @brief Convert array to string representation
 * @param arr array to convert
 * @param size size of array
 * @param buffer output buffer
 * @param buffer_size size of output buffer
 * @returns number of characters written (excluding null terminator), or -1 on error
 */
int arrayToString(const int8_t *arr, uint8_t size, char *buffer, size_t buffer_size);

/**
 * @brief Verify heap property (max-heap) for array
 * @param arr array to verify
 * @param size size of array
 * @returns 1 if valid max-heap, 0 otherwise
 */
int isMaxHeap(const int8_t *arr, uint8_t size);

#endif /* SORTING_HEAP_SORT_2_H */
