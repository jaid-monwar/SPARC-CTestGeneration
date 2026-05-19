/**
 * @file
 * @brief [Patience Sort](https://en.wikipedia.org/wiki/Patience_sorting)
 * @details From Wikipedia:
 * In computer science, patience sorting is a sorting algorithm inspired by, and named after, the card game patience.
 * Given an array of n elements from some totally ordered domain, consider this array as a collection of cards and simulate the patience sorting game.
 * When the game is over, recover the sorted sequence by repeatedly picking off the minimum visible card;
 * in other words, perform a k-way merge of the p piles, each of which is internally sorted.
 * @author [CascadingCascade](https://github.com/CascadingCascade)
 */

#include <assert.h> /// for assertions
#include <stdio.h> /// for IO operations
#include <stdlib.h> /// for memory management

/**
 * @brief Sorts the target array by dividing it into a variable number of internally sorted piles then merge the piles
 * @param array pointer to the array to be sorted
 * @param length length of the target array
 * @returns 0 on success, -1 on error (null array, invalid length, or allocation failure)
 */
int patienceSort(int *array, int length) {
    // Validate input
    if (array == NULL || length < 0) {
        return -1;
    }

    // Handle edge cases
    if (length <= 1) {
        return 0;  // Already sorted
    }

    // An array of pointers used to store each pile
    int* *piles = (int* *) malloc(sizeof(int*) * length);
    if (piles == NULL) {
        return -1;
    }

    for (int i = 0; i < length; ++i) {
        piles[i] = malloc(sizeof(int) * length);
        if (piles[i] == NULL) {
            // Clean up previously allocated piles
            for (int j = 0; j < i; ++j) {
                free(piles[j]);
            }
            free(piles);
            return -1;
        }
    }

    // pileSizes keep track of the indices of each pile's topmost element, hence 0 means only one element
    // Note how calloc() is used to initialize the sizes of all piles to zero
    int *pileSizes = (int*) calloc(length, sizeof(int));
    if (pileSizes == NULL) {
        for (int i = 0; i < length; ++i) {
            free(piles[i]);
        }
        free(piles);
        return -1;
    }

    // This initializes the first pile, note how using an array of pointers allowed us to access elements through two subscripts
    // The first subscript indicates which pile we are accessing, the second subscript indicates the location being accessed in that pile
    piles[0][0] = array[0];
    int pileCount = 1;

    for (int i = 1; i < length; ++i) {
        // This will be used to keep track whether an element has been added to an existing pile
        int flag = 1;

        for (int j = 0; j < pileCount; ++j) {
            if(piles[j][pileSizes[j]] > array[i]) {
                // We have found a pile this element can be added to
                piles[j][pileSizes[j] + 1] = array[i];
                pileSizes[j]++;
                flag--;
                break;
            }
        }

        if(flag) {
            // The element in question can not be added to any existing piles, creating a new pile
            piles[pileCount][0] = array[i];
            pileCount++;
        }
    }

    // This will keep track of the minimum value of all 'exposed' elements and which pile that value is from
    int min, minLocation;

    for (int i = 0; i < length; ++i) {
        // Since there's no guarantee the first pile will be depleted slower than other piles,
        // Example: when all elements are equal, in that case the first pile will be depleted immediately
        // We can't simply initialize min to the top most element of the first pile,
        // this loop finds a value to initialize min to.
        for (int j = 0; j < pileCount; ++j) {
            if(pileSizes[j] < 0) {
                continue;
            }
            min = piles[j][pileSizes[j]];
            minLocation = j;
            break;
        }

        for (int j = 0; j < pileCount; ++j) {
            if(pileSizes[j] < 0) {
                continue;
            }
            if(piles[j][pileSizes[j]] < min) {
                min = piles[j][pileSizes[j]];
                minLocation = j;
            }
        }

        array[i] = min;
        pileSizes[minLocation]--;
    }

    // Deallocate memory
    free(pileSizes);
    for (int i = 0; i < length; ++i) {
        free(piles[i]);
    }
    free(piles);

    return 0;
}

/**
 * @brief Check if an array is sorted in ascending order
 * @param array pointer to the array to check
 * @param length length of the array
 * @returns 1 if sorted in ascending order, 0 otherwise
 */
int isSorted(int *array, int length) {
    if (array == NULL || length < 0) {
        return 0;
    }
    if (length <= 1) {
        return 1;
    }
    for (int i = 0; i < length - 1; ++i) {
        if (array[i] > array[i + 1]) {
            return 0;
        }
    }
    return 1;
}

/**
 * @brief Check if an array is sorted in descending order
 * @param array pointer to the array to check
 * @param length length of the array
 * @returns 1 if sorted in descending order, 0 otherwise
 */
int isSortedDescending(int *array, int length) {
    if (array == NULL || length < 0) {
        return 0;
    }
    if (length <= 1) {
        return 1;
    }
    for (int i = 0; i < length - 1; ++i) {
        if (array[i] < array[i + 1]) {
            return 0;
        }
    }
    return 1;
}

/**
 * @brief Count occurrences of a value in an array
 * @param array pointer to the array
 * @param length length of the array
 * @param value value to count
 * @returns count of occurrences, or -1 on error
 */
int countOccurrences(int *array, int length, int value) {
    if (array == NULL || length < 0) {
        return -1;
    }
    int count = 0;
    for (int i = 0; i < length; ++i) {
        if (array[i] == value) {
            count++;
        }
    }
    return count;
}

/**
 * @brief Find the minimum value in an array
 * @param array pointer to the array
 * @param length length of the array
 * @param result pointer to store the minimum value
 * @returns 0 on success, -1 on error
 */
int findMin(int *array, int length, int *result) {
    if (array == NULL || length <= 0 || result == NULL) {
        return -1;
    }
    *result = array[0];
    for (int i = 1; i < length; ++i) {
        if (array[i] < *result) {
            *result = array[i];
        }
    }
    return 0;
}

/**
 * @brief Find the maximum value in an array
 * @param array pointer to the array
 * @param length length of the array
 * @param result pointer to store the maximum value
 * @returns 0 on success, -1 on error
 */
int findMax(int *array, int length, int *result) {
    if (array == NULL || length <= 0 || result == NULL) {
        return -1;
    }
    *result = array[0];
    for (int i = 1; i < length; ++i) {
        if (array[i] > *result) {
            *result = array[i];
        }
    }
    return 0;
}

/**
 * @brief Check if two arrays have the same elements (same multiset)
 * @param array1 pointer to first array
 * @param array2 pointer to second array
 * @param length length of both arrays
 * @returns 1 if same elements, 0 otherwise
 */
int haveSameElements(int *array1, int *array2, int length) {
    if (array1 == NULL || array2 == NULL || length < 0) {
        return 0;
    }
    if (length == 0) {
        return 1;
    }

    // Create a copy of array2 to mark elements as "used"
    int *temp = (int*) malloc(sizeof(int) * length);
    if (temp == NULL) {
        return 0;
    }
    int *used = (int*) calloc(length, sizeof(int));
    if (used == NULL) {
        free(temp);
        return 0;
    }

    for (int i = 0; i < length; ++i) {
        temp[i] = array2[i];
    }

    for (int i = 0; i < length; ++i) {
        int found = 0;
        for (int j = 0; j < length; ++j) {
            if (!used[j] && array1[i] == temp[j]) {
                used[j] = 1;
                found = 1;
                break;
            }
        }
        if (!found) {
            free(temp);
            free(used);
            return 0;
        }
    }

    free(temp);
    free(used);
    return 1;
}

/**
 * @brief Copy an array to a new allocated array
 * @param array pointer to the source array
 * @param length length of the array
 * @returns pointer to the copy, or NULL on error
 */
int* copyArray(int *array, int length) {
    if (array == NULL || length <= 0) {
        return NULL;
    }
    int *copy = (int*) malloc(sizeof(int) * length);
    if (copy == NULL) {
        return NULL;
    }
    for (int i = 0; i < length; ++i) {
        copy[i] = array[i];
    }
    return copy;
}

/**
 * @brief Compare two arrays for equality
 * @param array1 pointer to first array
 * @param array2 pointer to second array
 * @param length length of both arrays
 * @returns 1 if equal, 0 otherwise
 */
int arraysEqual(int *array1, int *array2, int length) {
    if (array1 == NULL || array2 == NULL || length < 0) {
        return 0;
    }
    for (int i = 0; i < length; ++i) {
        if (array1[i] != array2[i]) {
            return 0;
        }
    }
    return 1;
}

/**
 * @brief Format array as string for debugging (writes to provided buffer)
 * @param array pointer to the array
 * @param length length of the array
 * @param buffer output buffer
 * @param bufferSize size of the output buffer
 * @returns 0 on success, -1 on error
 */
int arrayToString(int *array, int length, char *buffer, int bufferSize) {
    if (buffer == NULL || bufferSize <= 0) {
        return -1;
    }
    if (array == NULL || length <= 0) {
        snprintf(buffer, bufferSize, "[]");
        return 0;
    }

    int pos = 0;
    pos += snprintf(buffer + pos, bufferSize - pos, "[");

    for (int i = 0; i < length && pos < bufferSize - 1; ++i) {
        if (i > 0) {
            pos += snprintf(buffer + pos, bufferSize - pos, ", ");
        }
        pos += snprintf(buffer + pos, bufferSize - pos, "%d", array[i]);
    }

    if (pos < bufferSize - 1) {
        snprintf(buffer + pos, bufferSize - pos, "]");
    }

    return 0;
}
