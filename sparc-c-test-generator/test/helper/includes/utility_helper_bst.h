#ifndef UTILITY_HELPER_BST_H
#define UTILITY_HELPER_BST_H

// Includes from source file
#include <stdio.h>
#include "cJSON.h"
#include "../../include/bst/generated_header.h"

#include <stdlib.h>

// Function declarations
void run_test(void (*func)(), const char* name);
struct node * init_root(void);
void reset_root(struct node * * actual_root);
void cleanup_tree(struct node * * actual_root);
struct node * build_tree_from_json(cJSON * json);
struct node * load_golden_from_named_test_string(const char * testname);

#endif
