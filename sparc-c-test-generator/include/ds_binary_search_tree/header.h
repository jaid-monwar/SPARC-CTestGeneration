/**
 * @file header.h
 * @brief Header file for the binary search tree implementation.
 */
#ifndef DS_BINARY_SEARCH_TREE_H
#define DS_BINARY_SEARCH_TREE_H

#include <stdio.h>
#include <stdlib.h>

/** Node, the basic data structure in the tree */
typedef struct node
{
    struct node *left;  /**< left child */
    struct node *right; /**< right child */
    int data;           /**< data of the node */
} node;

/**
 * @brief Creates a new node with the given data.
 * @param data data to store in a new node
 * @returns new node with the provided data
 */
node *newNode(int data);

/**
 * @brief Inserts a new node with the given data into the tree.
 * @param root pointer to parent node
 * @param data value to store in the new node
 * @returns pointer to parent node
 */
node *insert(node *root, int data);

/**
 * @brief Finds the node with the maximum key in the subtree.
 * @param root pointer to parent node
 * @returns pointer to node with maximum key
 */
node *getMax(node *root);

/**
 * @brief Deletes a node with the given data from the tree.
 * @param root pointer to parent node
 * @param data value to search for and delete
 * @returns pointer to parent node
 */
node *delete(node *root, int data);

/**
 * @brief Searches for a node with the given data in the tree.
 * @param root pointer to parent node
 * @param data value to search for
 * @returns 1 if value was found, 0 otherwise
 */
int find(node *root, int data);

/**
 * @brief Calculates the height of the tree.
 * @param root pointer to parent node
 * @returns height of the tree
 */
int height(node *root);

/**
 * @brief Frees all nodes in the tree.
 * @param root pointer to parent node
 */
void purge(node *root);

/**
 * @brief Performs in-order traversal and prints node data.
 * @param root pointer to parent node
 */
void inOrder(node *root);

#endif /* DS_BINARY_SEARCH_TREE_H */
