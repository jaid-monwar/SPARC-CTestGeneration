/**
 * @file ds_segment_tree.h
 * @brief Header file for segment trees with point updates
 * @details
 * This header provides the interface for segment tree operations.
 * Segment trees allow range-based queries in O(log N) time and
 * point updates in O(log N) time.
 */

#ifndef DS_SEGMENT_TREE_H
#define DS_SEGMENT_TREE_H

#include <stddef.h>  /* for size_t */

/**
 * Function pointer type for combining two data elements
 * @param a pointer to first data
 * @param b pointer to second data
 * @param result pointer to memory location where result is stored
 */
typedef void (*combine_function)(const void *a, const void *b, void *result);

/**
 * Structure holding all data required by a segment tree
 */
typedef struct segment_tree
{
    void *root;               /**< the root of formed segment tree */
    void *identity;           /**< identity element for combine function */
    size_t elem_size;         /**< size in bytes of each data element */
    size_t length;            /**< total size of array which segment tree represents */
    combine_function combine; /**< function to combine two nodes' data */
} segment_tree;

/* Core segment tree operations */

/**
 * Initializes a segment tree from an array
 * @param arr the array data upon which segment tree is built
 * @param elem_size size of each element in segment tree
 * @param len total number of elements in array
 * @param identity the identity element for combine_function
 * @param func the combine_function used to build segment tree
 * @returns pointer to segment tree, or NULL on failure
 */
segment_tree *segment_tree_init(void *arr, size_t elem_size, size_t len,
                                void *identity, combine_function func);

/**
 * Builds a segment tree (assumes leaves already contain data)
 * @param tree pointer to segment tree to be built
 */
void segment_tree_build(segment_tree *tree);

/**
 * Updates the element at given index and propagates changes
 * @param tree pointer to segment tree
 * @param index the index whose element is to be updated (0-based)
 * @param val pointer to value that is to be set at given index
 */
void segment_tree_update(segment_tree *tree, size_t index, void *val);

/**
 * Query the segment tree for a range [l, r]
 * @param tree pointer to segment tree
 * @param l the start of range (0-based, inclusive)
 * @param r the end of range (0-based, inclusive)
 * @param res pointer to memory where result of query is stored
 */
void segment_tree_query(segment_tree *tree, long long l, long long r, void *res);

/**
 * Frees all heap memory acquired by segment tree
 * @param tree pointer to segment tree
 */
void segment_tree_dispose(segment_tree *tree);

/**
 * Prints the segment tree (for int data type)
 * @param tree pointer to segment tree
 */
void segment_tree_print_int(segment_tree *tree);

/* Common combine functions */

/**
 * Combine function for minimum (Range Minimum Query)
 * @param a pointer to integer a
 * @param b pointer to integer b
 * @param c pointer where minimum of a and b is stored
 */
void combine_minimum(const void *a, const void *b, void *c);

/**
 * Combine function for maximum (Range Maximum Query)
 * @param a pointer to integer a
 * @param b pointer to integer b
 * @param c pointer where maximum of a and b is stored
 */
void combine_maximum(const void *a, const void *b, void *c);

/**
 * Combine function for sum (Range Sum Query)
 * @param a pointer to integer a
 * @param b pointer to integer b
 * @param c pointer where sum of a and b is stored
 */
void combine_sum(const void *a, const void *b, void *c);

/* Utility functions for testing */

/**
 * Get the length of the array represented by the segment tree
 * @param tree pointer to segment tree
 * @returns length of the array, or 0 if tree is NULL
 */
size_t segment_tree_get_length(segment_tree *tree);

/**
 * Get the element size of the segment tree
 * @param tree pointer to segment tree
 * @returns element size in bytes, or 0 if tree is NULL
 */
size_t segment_tree_get_elem_size(segment_tree *tree);

/**
 * Get the total number of nodes in the segment tree
 * @param tree pointer to segment tree
 * @returns total number of nodes (2*length - 1), or 0 if tree is NULL
 */
size_t segment_tree_get_node_count(segment_tree *tree);

/**
 * Get the value at a specific index in the original array
 * @param tree pointer to segment tree
 * @param index the index in the original array (0-based)
 * @param result pointer to memory where result is stored
 * @returns 0 on success, -1 on failure
 */
int segment_tree_get_element(segment_tree *tree, size_t index, void *result);

/**
 * Get the root value of the segment tree
 * @param tree pointer to segment tree
 * @param result pointer to memory where result is stored
 * @returns 0 on success, -1 on failure
 */
int segment_tree_get_root_value(segment_tree *tree, void *result);

/**
 * Check if segment tree is valid (properly initialized)
 * @param tree pointer to segment tree
 * @returns 1 if valid, 0 if invalid or NULL
 */
int segment_tree_is_valid(segment_tree *tree);

/**
 * Get the identity element value
 * @param tree pointer to segment tree
 * @param result pointer to memory where identity is stored
 * @returns 0 on success, -1 on failure
 */
int segment_tree_get_identity(segment_tree *tree, void *result);

/**
 * Perform a safe query with bounds checking
 * @param tree pointer to segment tree
 * @param l the start of range (0-based, inclusive)
 * @param r the end of range (0-based, inclusive)
 * @param res pointer to memory where result of query is stored
 * @returns 0 on success, -1 on failure (invalid range or NULL)
 */
int segment_tree_query_safe(segment_tree *tree, size_t l, size_t r, void *res);

/**
 * Perform a safe update with bounds checking
 * @param tree pointer to segment tree
 * @param index the index to update (0-based)
 * @param val pointer to value to set at index
 * @returns 0 on success, -1 on failure (out of bounds or NULL)
 */
int segment_tree_update_safe(segment_tree *tree, size_t index, void *val);

#endif /* DS_SEGMENT_TREE_H */
