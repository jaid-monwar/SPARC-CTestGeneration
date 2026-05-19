#ifndef DS_MIN_HEAP_H
#define DS_MIN_HEAP_H

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>

/* Min-heap structure */
typedef struct min_heap
{
    int *p;     /* Pointer to heap array */
    int size;   /* Allocated capacity */
    int count;  /* Number of elements */
} Heap;

/* ==================== CORE HEAP OPERATIONS ==================== */

/* Creates a min_heap structure and returns a pointer to the struct */
Heap *create_heap(void);

/* Pushes an element downwards in the heap to find its correct position */
void down_heapify(Heap *heap, int index);

/* Pushes an element upwards in the heap to find its correct position */
void up_heapify(Heap *heap, int index);

/* Inserts an element in the heap */
void push(Heap *heap, int x);

/* Removes the top element from the heap */
void pop(Heap *heap);

/* Returns the top element of the heap or returns INT_MIN if heap is empty */
int top(Heap *heap);

/* Checks if heap is empty (returns 1 if empty, 0 otherwise) */
int empty(Heap *heap);

/* Returns the number of elements in the heap */
int heap_size(Heap *heap);

/* ==================== UTILITY FUNCTIONS FOR TESTING ==================== */

/* Frees all memory associated with the heap */
void destroy_heap(Heap *heap);

/* Checks if a value exists in the heap (returns 1 if found, 0 otherwise) */
int heap_contains(Heap *heap, int value);

/* Returns the element at the given index (INT_MIN if invalid index) */
int heap_get_at(Heap *heap, int index);

/* Verifies the min-heap property (returns 1 if valid, 0 otherwise) */
int verify_min_heap_property(Heap *heap);

/* Converts heap contents to a string for testing (caller must free) */
char *heap_to_string(Heap *heap);

/* Creates a heap from an array of integers */
Heap *heap_from_array(int *arr, int n);

/* Returns the allocated capacity of the heap */
int heap_capacity(Heap *heap);

/* Clears all elements from the heap without destroying it */
void heap_clear(Heap *heap);

/* Returns the second minimum element (or INT_MIN if less than 2 elements) */
int heap_second_min(Heap *heap);

#endif /* DS_MIN_HEAP_H */
