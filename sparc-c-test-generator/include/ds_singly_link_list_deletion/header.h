/*
 * Singly Linked List with Deletion Operations - Header File
 *
 * This module provides a singly linked list implementation with insertion
 * and deletion operations at arbitrary positions.
 */
#ifndef DS_SINGLY_LINK_LIST_DELETION_H
#define DS_SINGLY_LINK_LIST_DELETION_H

#include <stddef.h>

/* Node structure for singly linked list */
struct node
{
    int info;
    struct node *link;
};

/* Core Functions */

/*
 * Create a new node with given data
 * Returns: pointer to new node, or NULL on allocation failure
 */
struct node *createnode(int data);

/*
 * Insert a node at a given position (1-indexed)
 * Parameters:
 *   head - pointer to head pointer of the list
 *   pos  - position to insert (1 = first position)
 *   data - value to insert
 * Returns: 0 on success, -1 on failure
 */
int insert(struct node **head, int pos, int data);

/*
 * Delete a node at a given position (1-indexed)
 * Parameters:
 *   head - pointer to head pointer of the list
 *   pos  - position to delete (1 = first position)
 * Returns: 0 on success, -1 on failure
 */
int deletion(struct node **head, int pos);

/*
 * Display list values to stdout
 * Parameters:
 *   head - head pointer of the list
 */
void viewlist(struct node *head);

/* String-based Alternatives */

/*
 * Write list contents to a string buffer
 * Parameters:
 *   head        - head pointer of the list
 *   buffer      - destination buffer
 *   buffer_size - size of buffer
 * Returns: number of characters written, or -1 on error
 */
int viewlist_to_string(struct node *head, char *buffer, size_t buffer_size);

/* Utility Functions for Test Assertions */

/*
 * Count the number of nodes in the list
 * Returns: number of nodes (0 for empty list)
 */
int count_nodes(struct node *head);

/*
 * Search for a value in the list
 * Returns: position (1-indexed) if found, 0 if not found
 */
int search(struct node *head, int value);

/*
 * Get the value at a given position (1-indexed)
 * Parameters:
 *   head      - head pointer of the list
 *   pos       - position to get (1 = first position)
 *   value_out - pointer to store the value
 * Returns: 0 on success, -1 on failure
 */
int get_at_position(struct node *head, int pos, int *value_out);

/*
 * Check if the list is empty
 * Returns: 1 if empty, 0 otherwise
 */
int is_empty(struct node *head);

/*
 * Get the head (first element) value
 * Parameters:
 *   head      - head pointer of the list
 *   value_out - pointer to store the value
 * Returns: 0 on success, -1 on failure (empty list)
 */
int get_head(struct node *head, int *value_out);

/*
 * Get the tail (last element) value
 * Parameters:
 *   head      - head pointer of the list
 *   value_out - pointer to store the value
 * Returns: 0 on success, -1 on failure (empty list)
 */
int get_tail(struct node *head, int *value_out);

/*
 * Free all nodes in the list
 * Parameters:
 *   head - pointer to head pointer (will be set to NULL)
 */
void free_list(struct node **head);

/*
 * Append a value at the end of the list
 * Parameters:
 *   head - pointer to head pointer of the list
 *   data - value to append
 * Returns: 0 on success, -1 on failure
 */
int append(struct node **head, int data);

/*
 * Prepend a value at the beginning of the list
 * Parameters:
 *   head - pointer to head pointer of the list
 *   data - value to prepend
 * Returns: 0 on success, -1 on failure
 */
int prepend(struct node **head, int data);

/*
 * Create a list from an array
 * Parameters:
 *   arr  - array of integers
 *   size - number of elements in array
 * Returns: pointer to new list head, or NULL on failure
 */
struct node *create_from_array(int *arr, int size);

/*
 * Convert list to array
 * Parameters:
 *   head     - head pointer of the list
 *   arr      - destination array
 *   max_size - maximum number of elements to copy
 * Returns: number of elements copied, or -1 on error
 */
int to_array(struct node *head, int *arr, int max_size);

#endif /* DS_SINGLY_LINK_LIST_DELETION_H */
