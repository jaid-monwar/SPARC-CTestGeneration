#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>


// Struct definitions
typedef struct node {
    int ID;
    int AT;
    int BT;
    int priority;
    int CT;
    int WT;
    int TAT;
    struct node * next;
} node;

// Function declarations
void insert(node * * root, int id, int at, int bt, int prior);
void delete(node * * root, int id);
void show_list(node * head);
int l_length(node * * root);
void update(node * * root, int id, int ct, int wt, int tat);
_Bool compare(node * a, node * b);
float calculate_ct(node * * root);
float calculate_tat(node * * root);
float calculate_wt(node * * root);
void test(void);

#endif
