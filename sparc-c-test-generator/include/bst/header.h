#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdio.h>
#include <stdlib.h>


// Struct definitions
struct node {
    int key;
    struct node * left;
    struct node * right;
};

// Function declarations
struct node * newNode(int item);
void inorder(struct node * root);
struct node * insert(struct node * node, int key);
struct node * minValueNode(struct node * node);
struct node * deleteNode(struct node * root, int key);

#endif
