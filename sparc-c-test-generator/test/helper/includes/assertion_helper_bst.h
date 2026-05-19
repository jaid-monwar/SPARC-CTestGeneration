#ifndef ASSERTION_HELPER_BST_H
#define ASSERTION_HELPER_BST_H

// Includes from source file
#include <assert.h>
#include <stdio.h>
#include "../../include/bst/generated_header.h"

#include <stdlib.h>

// Function declarations
void assert_root_null(struct node * actual_root);
void assert_root_key(struct node * actual_root, int expected_key);
void assert_left_child_null(struct node * actual_root);
void assert_right_child_null(struct node * actual_root);
void assert_tree_equal(struct node * actual_root, struct node * expected_root);

#endif
