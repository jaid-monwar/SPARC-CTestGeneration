#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


// Struct definitions
typedef struct DArrayStack {
    int capacity;
    int top;
    int * arrPtr;
} DArrayStack;

// Function declarations
DArrayStack * create_stack(int cap);
DArrayStack * double_array(DArrayStack * ptr, int cap);
DArrayStack * shrink_array(DArrayStack * ptr, int cap);
int push(DArrayStack * ptr, int data);
int pop(DArrayStack * ptr, int * success);
int peek(DArrayStack * ptr, int * success);
int show_capacity(DArrayStack * ptr);
int isempty(DArrayStack * ptr);
int stack_size(DArrayStack * ptr);
void free_stack(DArrayStack * ptr);
int get_element_at(DArrayStack * ptr, int index, int * success);
int stack_contains(DArrayStack * ptr, int value);
void clear_stack(DArrayStack * ptr);
int stack_to_string(DArrayStack * ptr, char * buffer, int buffer_size);
int stacks_equal(DArrayStack * stack1, DArrayStack * stack2);
DArrayStack * copy_stack(DArrayStack * src);

#endif
