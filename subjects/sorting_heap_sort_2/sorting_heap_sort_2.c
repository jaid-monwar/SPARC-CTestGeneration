/**
 * @file
 * @author [Dhruv Pasricha](https://github.com/DhruvPasricha)
 * @brief [Heap Sort](https://en.wikipedia.org/wiki/Heapsort) implementation
 * @details
 * Heap-sort is a comparison-based sorting algorithm.
 * Heap-sort can be thought of as an improved selection sort:
 * like selection sort, heap sort divides its input into a sorted
 * and an unsorted region, and it iteratively shrinks the unsorted
 * region by extracting the largest element from it and inserting
 * it into the sorted region.
 *
 * Unlike selection sort,
 * heap sort does not waste time with a linear-time scan of the
 * unsorted region; rather, heap sort maintains the unsorted region
 * in a heap data structure to more quickly find the largest element
 * in each step.
 * Time Complexity : O(Nlog(N))
 */

#include <stdio.h>    /// for IO operations
#include <stdlib.h>   /// for dynamic memory allocation
#include <string.h>   /// for string operations
#include <inttypes.h> /// for uint8_t, int8_t

/**
 * @brief Swapped two numbers using pointer
 * @param first pointer of first number
 * @param second pointer of second number
 */
void swap(int8_t *first, int8_t *second)
{
    int8_t temp = *first;
    *first = *second;
    *second = temp;
}

/**
 * @brief heapifyDown Adjusts new root to the correct position in the heap
 * This heapify procedure can be thought of as building a heap from
 * the top down by successively shifting downward to establish the
 * heap property.
 * @param arr array to be sorted
 * @param size size of array
 * @return void
*/
void heapifyDown(int8_t *arr, const uint8_t size)
{
    uint8_t i = 0;

    while (2 * i + 1 < size)
    {
        uint8_t maxChild = 2 * i + 1;

        if (2 * i + 2 < size && arr[2 * i + 2] > arr[maxChild])
        {
            maxChild = 2 * i + 2;
        }

        if (arr[maxChild] > arr[i])
        {
            swap(&arr[i], &arr[maxChild]);
            i = maxChild;
        }
        else
        {
            break;
        }
    }
}

/**
 * @brief heapifyUp Adjusts arr[i] to the correct position in the heap
 * This heapify procedure can be thought of as building a heap from
 * the bottom up by successively shifting upward to establish the
 * heap property.
 * @param arr array to be sorted
 * @param i index of the pushed element
 * @return void
*/
void heapifyUp(int8_t *arr, uint8_t i)
{
    while (i > 0 && arr[(i - 1) / 2] < arr[i])
    {
        swap(&arr[(i - 1) / 2], &arr[i]);
        i = (i - 1) / 2;
    }
}

/**
 * @brief Heap Sort algorithm
 * @param arr array to be sorted
 * @param size size of the array
 * @returns void
 */
void heapSort(int8_t *arr, const uint8_t size)
{
    if (size <= 1)
    {
        return;
    }

    for (uint8_t i = 0; i < size; i++)
    {
        // Pushing `arr[i]` to the heap

        /*heapifyUp Adjusts arr[i] to the correct position in the heap*/
        heapifyUp(arr, i);
    }

    for (uint8_t i = size - 1; i >= 1; i--)
    {
        // Moving current root to the end
        swap(&arr[0], &arr[i]);

        // `heapifyDown` adjusts new root to the correct position in the heap
        heapifyDown(arr, i);

    }
}

/**
 * @brief Create a new array with given values
 * @param values source array to copy from
 * @param size number of elements
 * @returns pointer to newly allocated array, or NULL on failure
 */
int8_t *createArray(const int8_t *values, uint8_t size)
{
    if (size == 0)
    {
        return NULL;
    }
    int8_t *arr = (int8_t *)malloc(size * sizeof(int8_t));
    if (arr == NULL)
    {
        return NULL;
    }
    for (uint8_t i = 0; i < size; i++)
    {
        arr[i] = values[i];
    }
    return arr;
}

/**
 * @brief Free an array
 * @param arr pointer to array to free
 */
void freeArray(int8_t *arr)
{
    free(arr);
}

/**
 * @brief Check if array is sorted in ascending order
 * @param arr array to check
 * @param size size of array
 * @returns 1 if sorted, 0 otherwise
 */
int isSorted(const int8_t *arr, uint8_t size)
{
    if (arr == NULL || size <= 1)
    {
        return 1;
    }
    for (uint8_t i = 0; i < size - 1; i++)
    {
        if (arr[i] > arr[i + 1])
        {
            return 0;
        }
    }
    return 1;
}

/**
 * @brief Compare two arrays for equality
 * @param arr1 first array
 * @param arr2 second array
 * @param size size of both arrays
 * @returns 1 if equal, 0 otherwise
 */
int arraysEqual(const int8_t *arr1, const int8_t *arr2, uint8_t size)
{
    if (arr1 == NULL && arr2 == NULL)
    {
        return 1;
    }
    if (arr1 == NULL || arr2 == NULL)
    {
        return 0;
    }
    for (uint8_t i = 0; i < size; i++)
    {
        if (arr1[i] != arr2[i])
        {
            return 0;
        }
    }
    return 1;
}

/**
 * @brief Copy an array
 * @param src source array
 * @param size size of array
 * @returns pointer to newly allocated copy, or NULL on failure
 */
int8_t *copyArray(const int8_t *src, uint8_t size)
{
    return createArray(src, size);
}

/**
 * @brief Get element at index
 * @param arr array
 * @param size size of array
 * @param index index to access
 * @param out_value pointer to store the value
 * @returns 1 on success, 0 if index out of bounds or arr is NULL
 */
int getElement(const int8_t *arr, uint8_t size, uint8_t index, int8_t *out_value)
{
    if (arr == NULL || index >= size || out_value == NULL)
    {
        return 0;
    }
    *out_value = arr[index];
    return 1;
}

/**
 * @brief Find minimum value in array
 * @param arr array to search
 * @param size size of array
 * @param out_min pointer to store minimum value
 * @returns 1 on success, 0 if array is empty or NULL
 */
int findMin(const int8_t *arr, uint8_t size, int8_t *out_min)
{
    if (arr == NULL || size == 0 || out_min == NULL)
    {
        return 0;
    }
    *out_min = arr[0];
    for (uint8_t i = 1; i < size; i++)
    {
        if (arr[i] < *out_min)
        {
            *out_min = arr[i];
        }
    }
    return 1;
}

/**
 * @brief Find maximum value in array
 * @param arr array to search
 * @param size size of array
 * @param out_max pointer to store maximum value
 * @returns 1 on success, 0 if array is empty or NULL
 */
int findMax(const int8_t *arr, uint8_t size, int8_t *out_max)
{
    if (arr == NULL || size == 0 || out_max == NULL)
    {
        return 0;
    }
    *out_max = arr[0];
    for (uint8_t i = 1; i < size; i++)
    {
        if (arr[i] > *out_max)
        {
            *out_max = arr[i];
        }
    }
    return 1;
}

/**
 * @brief Check if array contains a specific value
 * @param arr array to search
 * @param size size of array
 * @param value value to find
 * @returns 1 if found, 0 otherwise
 */
int containsValue(const int8_t *arr, uint8_t size, int8_t value)
{
    if (arr == NULL)
    {
        return 0;
    }
    for (uint8_t i = 0; i < size; i++)
    {
        if (arr[i] == value)
        {
            return 1;
        }
    }
    return 0;
}

/**
 * @brief Count occurrences of a value in array
 * @param arr array to search
 * @param size size of array
 * @param value value to count
 * @returns number of occurrences
 */
uint8_t countOccurrences(const int8_t *arr, uint8_t size, int8_t value)
{
    if (arr == NULL)
    {
        return 0;
    }
    uint8_t count = 0;
    for (uint8_t i = 0; i < size; i++)
    {
        if (arr[i] == value)
        {
            count++;
        }
    }
    return count;
}

/**
 * @brief Convert array to string representation
 * @param arr array to convert
 * @param size size of array
 * @param buffer output buffer
 * @param buffer_size size of output buffer
 * @returns number of characters written (excluding null terminator), or -1 on error
 */
int arrayToString(const int8_t *arr, uint8_t size, char *buffer, size_t buffer_size)
{
    if (buffer == NULL || buffer_size == 0)
    {
        return -1;
    }

    if (arr == NULL || size == 0)
    {
        if (buffer_size >= 3)
        {
            strcpy(buffer, "[]");
            return 2;
        }
        return -1;
    }

    size_t pos = 0;
    if (pos < buffer_size - 1)
    {
        buffer[pos++] = '[';
    }

    for (uint8_t i = 0; i < size && pos < buffer_size - 1; i++)
    {
        char num_buf[8];
        int len = snprintf(num_buf, sizeof(num_buf), "%d", arr[i]);

        for (int j = 0; j < len && pos < buffer_size - 1; j++)
        {
            buffer[pos++] = num_buf[j];
        }

        if (i < size - 1 && pos < buffer_size - 2)
        {
            buffer[pos++] = ',';
            buffer[pos++] = ' ';
        }
    }

    if (pos < buffer_size - 1)
    {
        buffer[pos++] = ']';
    }
    buffer[pos] = '\0';

    return (int)pos;
}

/**
 * @brief Verify heap property (max-heap) for array
 * @param arr array to verify
 * @param size size of array
 * @returns 1 if valid max-heap, 0 otherwise
 */
int isMaxHeap(const int8_t *arr, uint8_t size)
{
    if (arr == NULL || size <= 1)
    {
        return 1;
    }
    for (uint8_t i = 0; i < size; i++)
    {
        uint8_t left = 2 * i + 1;
        uint8_t right = 2 * i + 2;

        if (left < size && arr[i] < arr[left])
        {
            return 0;
        }
        if (right < size && arr[i] < arr[right])
        {
            return 0;
        }
    }
    return 1;
}
