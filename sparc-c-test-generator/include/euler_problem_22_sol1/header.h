/**
 * \file header.h
 * \brief Header file for Project Euler Problem 22 solution
 *
 * Provides functions for sorting names alphabetically and calculating
 * name scores based on position in sorted order.
 */
#ifndef EULER_PROBLEM_22_SOL1_H
#define EULER_PROBLEM_22_SOL1_H

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
void shell_sort(char data[][MAX_NAME_LEN], int LEN);

/**
 * Alphabetical sorting using 'lazy sort' algorithm (bubble sort variant)
 * @param data 2D array of strings to sort
 * @param LEN number of strings in the array
 */
void lazy_sort(char data[][MAX_NAME_LEN], int LEN);

/**
 * Parse names from a CSV-formatted string (e.g., "\"ALICE\",\"BOB\",\"CHARLIE\"")
 * String-based alternative to file parsing for testability.
 * @param input CSV-formatted string with quoted names
 * @param names output 2D array to store parsed names
 * @param max_names maximum number of names to parse
 * @return number of names parsed, or -1 on error
 */
int parse_names_from_string(const char *input, char names[][MAX_NAME_LEN], int max_names);

/**
 * Calculate the alphabetic score of a single name
 * Each letter contributes its position (A=1, B=2, ..., Z=26)
 * @param name the name string (uppercase letters expected)
 * @return the alphabetic score of the name, or 0 if name is NULL
 */
long calculate_name_score(const char *name);

/**
 * Calculate the weighted score for a name at a given position
 * @param name the name string
 * @param position 1-based position in the sorted list
 * @return name_score * position, or 0 on error
 */
long calculate_weighted_score(const char *name, int position);

/**
 * Calculate the total score for all names (Problem 22 solution)
 * @param names array of sorted names
 * @param count number of names
 * @return sum of all weighted scores
 */
long calculate_total_score(char names[][MAX_NAME_LEN], int count);

/**
 * Check if an array of strings is sorted alphabetically
 * @param data array of strings
 * @param len number of strings
 * @return 1 if sorted in ascending order, 0 otherwise
 */
int is_sorted(char data[][MAX_NAME_LEN], int len);

/**
 * Count the number of non-empty names in an array
 * @param data array of strings
 * @param max_len maximum number of entries to check
 * @return number of non-empty strings
 */
int count_names(char data[][MAX_NAME_LEN], int max_len);

/**
 * Find a name in the array and return its index
 * @param data array of strings
 * @param len number of strings
 * @param name name to search for
 * @return index of the name (0-based), or -1 if not found
 */
int find_name(char data[][MAX_NAME_LEN], int len, const char *name);

/**
 * Copy a name into the names array at a specific index
 * @param data array of strings
 * @param index position to copy to
 * @param name name to copy
 * @param max_entries maximum entries in the array
 * @return 0 on success, -1 on error
 */
int set_name(char data[][MAX_NAME_LEN], int index, const char *name, int max_entries);

/**
 * Initialize/clear all names in an array
 * @param data array of strings to clear
 * @param len number of entries to clear
 */
void clear_names(char data[][MAX_NAME_LEN], int len);

#endif /* EULER_PROBLEM_22_SOL1_H */
