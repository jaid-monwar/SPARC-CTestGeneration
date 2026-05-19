/**
 * @file
 * @brief Implementation of [merge
 * sort](https://en.wikipedia.org/wiki/Merge_sort) algorithm
 */
#include <stdio.h>
#include <stdlib.h>

/**
 * @addtogroup sorting Sorting algorithms
 * @{
 */
/** Swap two integer variables
 * @param [in,out] a pointer to first variable
 * @param [in,out] b pointer to second variable
 */
void swap(int *a, int *b)
{
    int t;
    t = *a;
    *a = *b;
    *b = t;
}

/**
 * @brief Perform merge of segments.
 *
 * @param a array to sort
 * @param l left index for merge
 * @param r right index for merge
 * @param n total number of elements in the array
 */
void merge(int *a, int l, int r, int n)
{
    int *b = (int *)malloc(n * sizeof(int)); /* dynamic memory must be freed */
    if (b == NULL)
    {
        printf("Can't Malloc! Please try again.");
        exit(EXIT_FAILURE);
    }
    int c = l;
    int p1, p2;
    p1 = l;
    p2 = ((l + r) / 2) + 1;
    while ((p1 < ((l + r) / 2) + 1) && (p2 < r + 1))
    {
        if (a[p1] <= a[p2])
        {
            b[c++] = a[p1];
            p1++;
        }
        else
        {
            b[c++] = a[p2];
            p2++;
        }
    }

    if (p2 == r + 1)
    {
        while ((p1 < ((l + r) / 2) + 1))
        {
            b[c++] = a[p1];
            p1++;
        }
    }
    else
    {
        while ((p2 < r + 1))
        {
            b[c++] = a[p2];
            p2++;
        }
    }

    for (c = l; c < r + 1; c++) a[c] = b[c];

    free(b);
}

/** Merge sort algorithm implementation
 * @param a array to sort
 * @param n number of elements in the array
 * @param l index to sort from
 * @param r index to sort till
 */
void merge_sort(int *a, int n, int l, int r)
{
    if (r - l == 1)
    {
        if (a[l] > a[r])
            swap(&a[l], &a[r]);
    }
    else if (l != r)
    {
        merge_sort(a, n, l, (l + r) / 2);
        merge_sort(a, n, ((l + r) / 2) + 1, r);
        merge(a, l, r, n);
    }

    /* no change if l == r */
}
/** @} */

/* ============================================================
 * Utility functions for testing
 * ============================================================ */

/**
 * @brief Check if an array is sorted in ascending order
 * @param arr array to check
 * @param n number of elements
 * @return 1 if sorted, 0 otherwise
 */
int is_sorted(int *arr, int n)
{
    if (arr == NULL || n <= 1)
        return 1;
    for (int i = 0; i < n - 1; i++)
    {
        if (arr[i] > arr[i + 1])
            return 0;
    }
    return 1;
}

/**
 * @brief Count elements in array (returns n if valid, -1 if NULL)
 * @param arr array to count
 * @param n expected number of elements
 * @return n if array is not NULL, -1 otherwise
 */
int array_count(int *arr, int n)
{
    if (arr == NULL)
        return -1;
    return n;
}

/**
 * @brief Create a copy of an array
 * @param src source array
 * @param n number of elements
 * @return newly allocated copy, or NULL on failure
 */
int *array_copy(int *src, int n)
{
    if (src == NULL || n <= 0)
        return NULL;
    int *copy = (int *)malloc(n * sizeof(int));
    if (copy == NULL)
        return NULL;
    for (int i = 0; i < n; i++)
        copy[i] = src[i];
    return copy;
}

/**
 * @brief Check if two arrays are equal
 * @param a first array
 * @param b second array
 * @param n number of elements
 * @return 1 if equal, 0 otherwise
 */
int arrays_equal(int *a, int *b, int n)
{
    if (a == NULL || b == NULL)
        return (a == b);
    for (int i = 0; i < n; i++)
    {
        if (a[i] != b[i])
            return 0;
    }
    return 1;
}

/**
 * @brief Find minimum value in array
 * @param arr array to search
 * @param n number of elements
 * @return minimum value, or 0 if array is NULL or empty
 */
int array_min(int *arr, int n)
{
    if (arr == NULL || n <= 0)
        return 0;
    int min = arr[0];
    for (int i = 1; i < n; i++)
    {
        if (arr[i] < min)
            min = arr[i];
    }
    return min;
}

/**
 * @brief Find maximum value in array
 * @param arr array to search
 * @param n number of elements
 * @return maximum value, or 0 if array is NULL or empty
 */
int array_max(int *arr, int n)
{
    if (arr == NULL || n <= 0)
        return 0;
    int max = arr[0];
    for (int i = 1; i < n; i++)
    {
        if (arr[i] > max)
            max = arr[i];
    }
    return max;
}

/**
 * @brief Search for a value in array
 * @param arr array to search
 * @param n number of elements
 * @param value value to find
 * @return index of first occurrence, or -1 if not found
 */
int array_search(int *arr, int n, int value)
{
    if (arr == NULL || n <= 0)
        return -1;
    for (int i = 0; i < n; i++)
    {
        if (arr[i] == value)
            return i;
    }
    return -1;
}

/**
 * @brief Count occurrences of a value in array
 * @param arr array to search
 * @param n number of elements
 * @param value value to count
 * @return number of occurrences
 */
int array_count_value(int *arr, int n, int value)
{
    if (arr == NULL || n <= 0)
        return 0;
    int count = 0;
    for (int i = 0; i < n; i++)
    {
        if (arr[i] == value)
            count++;
    }
    return count;
}

/**
 * @brief Create an array from a string of space-separated integers
 * @param str input string (e.g., "5 3 8 1 2")
 * @param n pointer to store the number of elements parsed
 * @return newly allocated array, or NULL on failure
 */
int *array_from_string(const char *str, int *n)
{
    if (str == NULL || n == NULL)
        return NULL;

    /* Count numbers in string */
    int count = 0;
    const char *p = str;
    while (*p)
    {
        while (*p == ' ') p++;
        if (*p == '\0') break;
        count++;
        while (*p && *p != ' ') p++;
    }

    if (count == 0)
    {
        *n = 0;
        return NULL;
    }

    int *arr = (int *)malloc(count * sizeof(int));
    if (arr == NULL)
    {
        *n = 0;
        return NULL;
    }

    p = str;
    for (int i = 0; i < count; i++)
    {
        while (*p == ' ') p++;
        arr[i] = atoi(p);
        while (*p && *p != ' ') p++;
    }

    *n = count;
    return arr;
}

/**
 * @brief Convert array to string representation
 * @param arr array to convert
 * @param n number of elements
 * @param buffer output buffer
 * @param buffer_size size of output buffer
 * @return pointer to buffer, or NULL on failure
 */
char *array_to_string(int *arr, int n, char *buffer, int buffer_size)
{
    if (arr == NULL || buffer == NULL || buffer_size <= 0)
        return NULL;

    buffer[0] = '\0';
    int offset = 0;

    for (int i = 0; i < n && offset < buffer_size - 1; i++)
    {
        int written = snprintf(buffer + offset, buffer_size - offset,
                               "%s%d", (i > 0 ? " " : ""), arr[i]);
        if (written < 0 || written >= buffer_size - offset)
            break;
        offset += written;
    }

    return buffer;
}

/**
 * @brief Free an array (wrapper for free)
 * @param arr array to free
 */
void array_free(int *arr)
{
    free(arr);
}
