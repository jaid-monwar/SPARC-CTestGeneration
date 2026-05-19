/**
 * \file
 * \brief [Problem 22](https://projecteuler.net/problem=22) solution
 * \author [Krishna Vedala](https://github.com/kvedala)
 *
 * Modified for testability - main() removed, string-based parsing added
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NAMES 6000  /**< Maximum number of names to store */
#define MAX_NAME_LEN 20 /**< Maximum length of each name */

/**
 * Alphabetical sorting using 'shell sort' algorithm
 * @param data 2D array of strings to sort
 * @param LEN number of strings in the array
 */
void shell_sort(char data[][MAX_NAME_LEN], int LEN)
{
    if (data == NULL || LEN <= 0)
        return;

    const int gaps[] = {701, 301, 132, 57, 23, 10, 4, 1};
    const int gap_len = 8;
    int i, j, g;

    for (g = 0; g < gap_len; g++)
    {
        int gap = gaps[g];
        for (i = gap; i < LEN; i++)
        {
            char tmp_buffer[MAX_NAME_LEN];
            strcpy(tmp_buffer, data[i]);

            for (j = i; j >= gap && strcmp(data[j - gap], tmp_buffer) > 0;
                 j -= gap)
                strcpy(data[j], data[j - gap]);
            strcpy(data[j], tmp_buffer);
        }
    }
}

/**
 * Alphabetical sorting using 'lazy sort' algorithm (bubble sort variant)
 * @param data 2D array of strings to sort
 * @param LEN number of strings in the array
 */
void lazy_sort(char data[][MAX_NAME_LEN], int LEN)
{
    if (data == NULL || LEN <= 0)
        return;

    int i, j;
    for (i = 0; i < LEN; i++)
    {
        for (j = i + 1; j < LEN; j++)
        {
            if (strcmp(data[i], data[j]) > 0)
            {
                char tmp_buffer[MAX_NAME_LEN];
                strcpy(tmp_buffer, data[i]);
                strcpy(data[i], data[j]);
                strcpy(data[j], tmp_buffer);
            }
        }
    }
}

/**
 * Parse names from a CSV-formatted string (e.g., "\"ALICE\",\"BOB\",\"CHARLIE\"")
 * String-based alternative to file parsing for testability.
 * @param input CSV-formatted string with quoted names
 * @param names output 2D array to store parsed names
 * @param max_names maximum number of names to parse
 * @return number of names parsed, or -1 on error
 */
int parse_names_from_string(const char *input, char names[][MAX_NAME_LEN], int max_names)
{
    if (input == NULL || names == NULL || max_names <= 0)
        return -1;

    int count = 0;
    const char *ptr = input;

    while (*ptr != '\0' && count < max_names)
    {
        /* Skip whitespace and commas */
        while (*ptr == ' ' || *ptr == ',' || *ptr == '\n' || *ptr == '\r')
            ptr++;

        if (*ptr == '\0')
            break;

        /* Expect opening quote */
        if (*ptr != '"')
        {
            ptr++;
            continue;
        }
        ptr++; /* skip opening quote */

        /* Copy name until closing quote */
        int i = 0;
        while (*ptr != '\0' && *ptr != '"' && i < MAX_NAME_LEN - 1)
        {
            names[count][i++] = *ptr++;
        }
        names[count][i] = '\0';

        if (*ptr == '"')
            ptr++; /* skip closing quote */

        if (i > 0) /* only count non-empty names */
            count++;
    }

    return count;
}

/**
 * Calculate the alphabetic score of a single name
 * Each letter contributes its position (A=1, B=2, ..., Z=26)
 * @param name the name string (uppercase letters expected)
 * @return the alphabetic score of the name, or 0 if name is NULL
 */
long calculate_name_score(const char *name)
{
    if (name == NULL)
        return 0;

    long score = 0;
    for (int j = 0; name[j] != '\0'; j++)
    {
        char c = name[j];
        /* Handle both uppercase and lowercase */
        if (c >= 'A' && c <= 'Z')
            score += c - 'A' + 1;
        else if (c >= 'a' && c <= 'z')
            score += c - 'a' + 1;
    }
    return score;
}

/**
 * Calculate the weighted score for a name at a given position
 * @param name the name string
 * @param position 1-based position in the sorted list
 * @return name_score * position, or 0 on error
 */
long calculate_weighted_score(const char *name, int position)
{
    if (name == NULL || position <= 0)
        return 0;

    return calculate_name_score(name) * position;
}

/**
 * Calculate the total score for all names (Problem 22 solution)
 * @param names array of sorted names
 * @param count number of names
 * @return sum of all weighted scores
 */
long calculate_total_score(char names[][MAX_NAME_LEN], int count)
{
    if (names == NULL || count <= 0)
        return 0;

    long sum_score = 0;
    for (int i = 0; i < count; i++)
    {
        sum_score += calculate_weighted_score(names[i], i + 1);
    }
    return sum_score;
}

/**
 * Check if an array of strings is sorted alphabetically
 * @param data array of strings
 * @param len number of strings
 * @return 1 if sorted in ascending order, 0 otherwise
 */
int is_sorted(char data[][MAX_NAME_LEN], int len)
{
    if (data == NULL || len <= 0)
        return 1; /* empty or NULL considered sorted */

    for (int i = 0; i < len - 1; i++)
    {
        if (strcmp(data[i], data[i + 1]) > 0)
            return 0;
    }
    return 1;
}

/**
 * Count the number of non-empty names in an array
 * @param data array of strings
 * @param max_len maximum number of entries to check
 * @return number of non-empty strings
 */
int count_names(char data[][MAX_NAME_LEN], int max_len)
{
    if (data == NULL || max_len <= 0)
        return 0;

    int count = 0;
    for (int i = 0; i < max_len; i++)
    {
        if (data[i][0] != '\0')
            count++;
        else
            break; /* assume names are contiguous */
    }
    return count;
}

/**
 * Find a name in the array and return its index
 * @param data array of strings
 * @param len number of strings
 * @param name name to search for
 * @return index of the name (0-based), or -1 if not found
 */
int find_name(char data[][MAX_NAME_LEN], int len, const char *name)
{
    if (data == NULL || len <= 0 || name == NULL)
        return -1;

    for (int i = 0; i < len; i++)
    {
        if (strcmp(data[i], name) == 0)
            return i;
    }
    return -1;
}

/**
 * Copy a name into the names array at a specific index
 * @param data array of strings
 * @param index position to copy to
 * @param name name to copy
 * @param max_entries maximum entries in the array
 * @return 0 on success, -1 on error
 */
int set_name(char data[][MAX_NAME_LEN], int index, const char *name, int max_entries)
{
    if (data == NULL || name == NULL || index < 0 || index >= max_entries)
        return -1;

    strncpy(data[index], name, MAX_NAME_LEN - 1);
    data[index][MAX_NAME_LEN - 1] = '\0';
    return 0;
}

/**
 * Initialize/clear all names in an array
 * @param data array of strings to clear
 * @param len number of entries to clear
 */
void clear_names(char data[][MAX_NAME_LEN], int len)
{
    if (data == NULL || len <= 0)
        return;

    for (int i = 0; i < len; i++)
    {
        data[i][0] = '\0';
    }
}
