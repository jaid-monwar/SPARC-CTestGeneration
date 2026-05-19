/**
 * @file ds_dynamic_stack.h
 * @brief Header file for Dynamic Stack implementation
 *
 * Dynamic Stack is a stack data structure whose capacity increases or
 * decreases in real time based on the operations performed on it.
 */

#ifndef DS_DYNAMIC_STACK_H
#define DS_DYNAMIC_STACK_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * @brief DArrayStack Structure of stack.
 */
typedef struct DArrayStack
{
    int capacity, top;  ///< to store capacity and top of the stack
    int *arrPtr;        ///< array pointer
} DArrayStack;

/**
 * @brief Create a Stack object
 *
 * @param cap Capacity of stack (must be > 0)
 * @return DArrayStack* Newly created stack object pointer, or NULL on failure
 */
DArrayStack *create_stack(int cap);

/**
 * @brief Expand the size of the stack by twice when full.
 *
 * @param ptr Stack pointer
 * @param cap Capacity of stack
 * @return DArrayStack* Modified stack, or NULL on failure
 */
DArrayStack *double_array(DArrayStack *ptr, int cap);

/**
 * @brief Shrink the size of stack by twice when capacity and size differ significantly.
 *
 * @param ptr Stack pointer
 * @param cap Capacity of stack
 * @return DArrayStack* Modified stack, or NULL on failure
 */
DArrayStack *shrink_array(DArrayStack *ptr, int cap);

/**
 * @brief Push an element onto the stack.
 *
 * @param ptr Stack pointer
 * @param data Value to be pushed onto stack
 * @return int Position of top pointer, or -1 on failure
 */
int push(DArrayStack *ptr, int data);

/**
 * @brief Pop an element from the stack.
 *
 * @param ptr Stack pointer
 * @param success Pointer to store success status (1 = success, 0 = failure), can be NULL
 * @return int Popped value, or 0 on failure (check success flag)
 */
int pop(DArrayStack *ptr, int *success);

/**
 * @brief Retrieve the element at the top of the stack without removing it.
 *
 * @param ptr Stack pointer
 * @param success Pointer to store success status (1 = success, 0 = failure), can be NULL
 * @return int Top of the stack, or 0 on failure (check success flag)
 */
int peek(DArrayStack *ptr, int *success);

/**
 * @brief Get the current capacity of the stack.
 *
 * @param ptr Stack pointer
 * @return int Current capacity of the stack, or -1 if ptr is NULL
 */
int show_capacity(DArrayStack *ptr);

/**
 * @brief Check whether the stack is empty.
 *
 * @param ptr Stack pointer
 * @return int 1 if empty or NULL, 0 if not empty
 */
int isempty(DArrayStack *ptr);

/**
 * @brief Get the size (number of elements) of the stack.
 *
 * @param ptr Stack pointer
 * @return int Size of stack, or 0 if ptr is NULL
 */
int stack_size(DArrayStack *ptr);

/**
 * @brief Free the entire stack and its internal array.
 *
 * @param ptr Stack pointer
 */
void free_stack(DArrayStack *ptr);

/**
 * @brief Get the element at a specific index in the stack (0 = bottom).
 *
 * @param ptr Stack pointer
 * @param index Index from bottom of stack
 * @param success Pointer to store success status (1 = success, 0 = failure), can be NULL
 * @return int Element at index, or 0 on failure
 */
int get_element_at(DArrayStack *ptr, int index, int *success);

/**
 * @brief Check if a value exists in the stack.
 *
 * @param ptr Stack pointer
 * @param value Value to search for
 * @return int 1 if found, 0 if not found or stack is NULL/empty
 */
int stack_contains(DArrayStack *ptr, int value);

/**
 * @brief Clear all elements from the stack without freeing it.
 *
 * @param ptr Stack pointer
 */
void clear_stack(DArrayStack *ptr);

/**
 * @brief Convert stack contents to a string representation.
 *
 * @param ptr Stack pointer
 * @param buffer Output buffer for the string
 * @param buffer_size Size of the output buffer
 * @return int Number of characters written (excluding null terminator), or -1 on error
 */
int stack_to_string(DArrayStack *ptr, char *buffer, int buffer_size);

/**
 * @brief Check if two stacks have equal contents.
 *
 * @param stack1 First stack pointer
 * @param stack2 Second stack pointer
 * @return int 1 if equal, 0 if not equal
 */
int stacks_equal(DArrayStack *stack1, DArrayStack *stack2);

/**
 * @brief Copy a stack to a new stack.
 *
 * @param src Source stack pointer
 * @return DArrayStack* New stack with copied contents, or NULL on failure
 */
DArrayStack *copy_stack(DArrayStack *src);

#endif /* DS_DYNAMIC_STACK_H */
