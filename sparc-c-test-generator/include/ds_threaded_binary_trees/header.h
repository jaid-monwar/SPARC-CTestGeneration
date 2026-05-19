#ifndef DS_THREADED_BINARY_TREES_H
#define DS_THREADED_BINARY_TREES_H

#include <stdlib.h>

/**
 * Node, the basic data structure of the tree
 */
typedef struct Node
{
    int data;           /**< stores the number */
    struct Node *llink; /**< link to left child */
    struct Node *rlink; /**< link to right child */
} node;

/**
 * creates a new node
 * param[in] data value to be inserted
 * returns a pointer to the new node
 */
node *create_node(int data);

/**
 * inserts a node into the tree
 * param[in,out] root pointer to node pointer to the topmost node of the tree
 * param[in] data value to be inserted into the tree
 */
void insert_bt(node **root, int data);

/**
 * searches for the element
 * param[in] root node pointer to the topmost node of the tree
 * param[in] ele value searched for
 * returns 1 if element found, 0 otherwise
 */
int search(node *root, int ele);

/**
 * performs inorder traversal
 * param[in] curr node pointer to the topmost node of the tree
 */
void inorder_display(node *curr);

/**
 * performs postorder traversal
 * param[in] curr node pointer to the topmost node of the tree
 */
void postorder_display(node *curr);

/**
 * performs preorder traversal
 * param[in] curr node pointer to the topmost node of the tree
 */
void preorder_display(node *curr);

/**
 * deletion of a node from the tree
 * if the node isn't present in the tree, it takes no action.
 * param[in,out] root pointer to node pointer to the topmost node of the tree
 * param[in] ele value to be deleted from the tree
 */
void delete_bt(node **root, int ele);

/**
 * frees all nodes in the tree
 * param[in] root node pointer to the topmost node of the tree
 */
void free_tree(node *root);

#endif /* DS_THREADED_BINARY_TREES_H */
