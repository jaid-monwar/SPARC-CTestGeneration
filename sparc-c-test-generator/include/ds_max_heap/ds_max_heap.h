#ifndef DS_MAX_HEAP_H
#define DS_MAX_HEAP_H

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct max_heap
{
    int *p;
    int size;
    int count;
} Heap;

/* Core heap operations */
Heap *create_heap(Heap *heap); /*Creates a max_heap structure and returns a
                                  pointer to the struct*/
void down_heapify(Heap *heap, int index); /*Pushes an element downwards in the
                                             heap to find its correct position*/
void up_heapify(Heap *heap, int index); /*Pushes an element upwards in the heap
                                           to find its correct position*/
void push(Heap *heap, int x);           /*Inserts an element in the heap*/
void pop(Heap *heap); /*Removes the top element from the heap*/
int top(Heap *heap); /*Returns the top element of the heap or returns INT_MIN if
                        heap is empty*/
int empty(Heap *heap); /*Checks if heap is empty*/
int size(Heap *heap);  /*Returns the size of heap*/

/* Utility functions for test assertions */
void destroy_heap(Heap *heap); /*Frees heap memory and cleans up*/
int get_element_at(Heap *heap, int index); /*Returns element at given index*/
int is_valid_max_heap(Heap *heap); /*Checks if heap satisfies max-heap property*/
int get_capacity(Heap *heap); /*Returns the current capacity of the heap*/
int contains(Heap *heap, int value); /*Checks if a value exists in the heap*/
int heap_to_array(Heap *heap, int *arr, int arr_size); /*Copies heap to array*/
Heap *create_heap_from_array(int *arr, int arr_size); /*Creates heap from array*/
int heap_to_string(Heap *heap, char *buffer, int buffer_size); /*Heap to string*/

#endif /* DS_MAX_HEAP_H */
