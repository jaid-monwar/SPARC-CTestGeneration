#ifndef DS_ASCENDING_PRIORITY_QUEUE_H
#define DS_ASCENDING_PRIORITY_QUEUE_H

/* Node structure for the priority queue */
struct node
{
    int data;
    struct node *next;
};

/* Global pointers to front and rear of queue */
extern struct node *front, *rear;

/* ============================================
 * Core queue operations
 * ============================================ */

/* Initialize the queue to empty state */
void createqueue(void);

/* Check if queue is empty
 * Returns: 1 if empty, 0 otherwise */
int empty(void);

/* Insert an element into the queue
 * Returns: 0 on success, -1 on memory allocation failure */
int insert(int x);

/* Remove and return the minimum element from the queue
 * Parameters:
 *   result - pointer to store the removed minimum value (can be NULL)
 * Returns: 0 on success, -1 if queue is empty */
int removes(int *result);

/* Display queue contents to stdout */
void show(void);

/* Free all nodes and reset queue to empty state */
void destroyqueue(void);

/* ============================================
 * String-based alternatives for testing
 * ============================================ */

/* Get queue contents as a space-separated string
 * Parameters:
 *   buffer - destination buffer for the string
 *   buffer_size - size of the buffer
 * Returns: 0 on success, -1 on error or buffer overflow
 * Output: "empty" if queue is empty, "val1 val2 val3..." otherwise */
int show_to_string(char *buffer, int buffer_size);

/* ============================================
 * Utility functions for test assertions
 * ============================================ */

/* Get the number of nodes in the queue
 * Returns: number of nodes (0 if empty) */
int queue_size(void);

/* Check if a value exists in the queue
 * Returns: 1 if found, 0 if not found */
int queue_contains(int value);

/* Peek at the minimum value without removing it
 * Parameters:
 *   result - pointer to store the minimum value
 * Returns: 0 on success, -1 if queue is empty or result is NULL */
int queue_peek_min(int *result);

/* Get the value at a specific index (0-based, front to rear)
 * Parameters:
 *   index - 0-based index from front
 *   result - pointer to store the value
 * Returns: 0 on success, -1 if index out of bounds or result is NULL */
int queue_get_at(int index, int *result);

/* Get the front value without removing
 * Parameters:
 *   result - pointer to store the front value
 * Returns: 0 on success, -1 if queue is empty or result is NULL */
int queue_front_value(int *result);

/* Get the rear value without removing
 * Parameters:
 *   result - pointer to store the rear value
 * Returns: 0 on success, -1 if queue is empty or result is NULL */
int queue_rear_value(int *result);

/* Copy queue contents to an array (front to rear order)
 * Parameters:
 *   arr - destination array
 *   arr_size - maximum number of elements to copy
 * Returns: number of elements copied, -1 on error */
int queue_to_array(int *arr, int arr_size);

/* Check if the queue is in a valid internal state
 * Returns: 1 if valid, 0 if invalid (front/rear inconsistency) */
int queue_is_valid(void);

#endif /* DS_ASCENDING_PRIORITY_QUEUE_H */
