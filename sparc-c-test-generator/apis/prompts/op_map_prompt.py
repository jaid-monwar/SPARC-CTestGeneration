"""
Operation Map Prompt Template
This prompt focuses on generating a clear and concise operation map for C functions.
"""

op_map_sys_prompt_template = """
🚨 CRITICAL RULES - VIOLATION = IMMEDIATE REJECTION 🚨
1. **NO DUPLICATE NAMES**: Never create functions with same names as source code
2. **NO HARDCODED VALUES**: All data must come from parameters, never {50, 30, 20}
3. **PARAMETERIZED ONLY**: Every function must accept explicit parameters
4. **NO PLACEHOLDER CODE**: Every function must contain COMPLETE, WORKING C code - NO TODO comments, NO placeholder comments like "// Perform operation", NO functions that only malloc/free without doing actual work
5. **NO PRIVATE FUNCTIONS**: Never call functions that are NOT declared in the header file. Functions with trailing underscores (like `node_contains_`, `get_quadrant_`) are typically private/static and FORBIDDEN


##⚠️ MANDATORY WORKFLOW ⚠️:

1. **Analyze the C source code and header file**: 
   - **Note**: Source function names and their paths are pre-defined and will be loaded from source_functions.json - you do NOT need to generate them
   - **Extract all public function declarations** from the header file - these are the ONLY functions you can call from the source code
   - **FORBIDDEN**: Never call functions not declared in the header file (private/static functions like `node_contains_`, `get_quadrant_`)
2. **Focus on BASIC helpers only**: Create only fundamental assertion and utility helpers that provide NEW functionality. Do NOT create:
   - Wrapper functions that just call existing helpers
   - Complete test functions that combine multiple operations
   - Functions that duplicate existing functionality
3. Carefully separate operations into two categories:
   - **assertion_operations**: Include BASIC assertion functions for validating specific conditions.
   - **utility_operations**: Include BASIC utility functions for fundamental setup/init functions, cleanup functions, or reset functions.
    Important:
    - Do not place assertion-type functions under utility_operations.
    - Do not place utility-type functions under assertion_operations.
4. For each category:
   - If there are existing helper functions that are relevant for unit testing (either as dependencies OR as useful operations for test scenarios), list all the **names** in `"searched_from_pool"` **ONLY if they do NOT conflict with source code function names**.
   - **CRITICAL: Before adding ANY function name to "searched_from_pool", verify it does NOT match ANY function name in the source C code being tested.**
   - **Include in searched_from_pool**:
     a. Functions that your created functions will call (dependencies)
     b. Functions that would be useful for test scenarios even if not called by created functions
     c. Any assertion or utility functions relevant to testing the source code
   - If no perfect match exists for needed functionality, define a **new helper** in `"created"` with:
     - `"name"`: The function name you're creating. **🚨 CRITICAL RULE 🚨** Please use prefix "helper_" for all helper functions to avoid conflicts with source code function names.
     - `"description"`: Clear explanation of the helper's purpose
     - `"return_type"`: C return type (e.g., `void`, `int`, `struct node *`)
     - `"parameters"`: List of objects with `"name"` and `"type"`
     - `"code_block"`: The complete, compilable C implementation of the helper function. **🚨 MANDATORY: MUST CONTAIN ACTUAL WORKING CODE 🚨** - NO PLACEHOLDER COMMENTS! Include all necessary declarations and statements so that the function can be compiled and run as-is. 
       **FORBIDDEN PATTERNS**:
       ❌ `// TODO: implement this` 
       ❌ `// Perform some operation`
       ❌ `// Call some_function(...)`
       ❌ Functions with only malloc/free and no actual logic
       **REQUIRED**: Every function must contain complete, functional C code that actually performs the described operation.
   - **🚨 CRITICAL DEPENDENCY RULE 🚨**: If your created function calls ANY other function (like `assert_array_equal`, `malloc`, custom helpers, etc.), you MUST ensure those functions are available by:
     1. **For standard library functions** (malloc, printf, etc.): Include appropriate headers in your code_block
     2. **For helper pool functions** (assert_array_equal, etc.): Add them to `"searched_from_pool"` 
     3. **For source code functions**: ONLY call functions that are declared in the header file - never call private/static functions
     4. **Example**: If you create a function that calls `assert_array_equal`, you MUST include `assert_array_equal` in the `"searched_from_pool"` section, otherwise compilation will fail with "undefined reference" errors.
   - **🚨 HEADER FILE VALIDATION 🚨**: Before calling ANY function from the source code, verify it exists in the header file:
     - ✅ **ALLOWED**: `insert(root, key)` (if declared in header)
     - ❌ **FORBIDDEN**: `node_contains_(root, point)` (private function with underscore)
     - ❌ **FORBIDDEN**: `get_quadrant_(root, point)` (private function with underscore)
     - ❌ **FORBIDDEN**: Any function not declared in the header file
   - Only generate new helper functions in `"created"` if no existing function in available helper functions performs the same or a highly similar task. **PREFER REUSING existing helpers over creating new ones**. If an equivalent function already exists, reuse it instead of creating a new one.
   - **AVOID WRAPPER FUNCTIONS**: Do not create functions that simply call existing helpers without adding significant new functionality.
   - **FOCUS ON GAPS**: Only create helpers that fill genuine functionality gaps not covered by existing helper pool functions.
   - **CRITICAL CONFLICT RESOLUTION**: If a helper function from the pool has the same name as a source code function, do NOT include it in "searched_from_pool". Instead, create a new function in "created" with a different name that performs the same functionality.
   - **STRICT NAMING REQUIREMENT**: Before finalizing any function name in `"created"` or `"searched_from_pool"`, verify it does NOT match any function name from the source code or helper functions. This is mandatory to prevent compilation conflicts.
4. **MANDATORY DEPENDENCY MANAGEMENT**:
   - **Create dependency_analysis section** with these 2 required fields:
     - **"planned_created_functions"**: For each function you plan to create, list:
       - `"name"`: The function name you're creating
       - `"calls"`: Array of ALL functions it will call (including `malloc`, `printf`, `assert_array_equal`, etc.)
     - **"required_from_pool"**: List ALL helper pool functions needed by your created functions
   - **Note**: "source_functions" will be automatically loaded from source_functions.json and merged - you do NOT need to generate it
   
   - **Dependency validation rules**:
     - **Scan every `"created"` function** for external function calls
     - **For each function call**, determine if it's:
       - Standard library (`malloc`, `printf`) → Include proper #includes in code_block
       - Helper pool function (`assert_array_equal`) → Add to "required_from_pool"
       - Source code function (`insert`, `newNode`) → ONLY allowed if declared in header file, list in "calls"
       - Private/static function (`node_contains_`, `get_quadrant_`) → ❌ FORBIDDEN - causes compilation errors
     - **CRITICAL**: Every function in "required_from_pool" MUST appear in "searched_from_pool" sections
     - **HEADER VALIDATION**: Every source code function call must be verified against the header file declarations
     - **NOTE**: "searched_from_pool" can include MORE functions than "required_from_pool" - include any helper pool functions that are relevant for unit testing, even if not directly called by created functions
     - **Compilation will fail** with "undefined reference" errors if dependencies are missing

5. Include all possible operations that are necessary for generating **complete** test scenarios later.
6. Make sure the operations are comprehensive enough to write complete test scenarios for all functions in the source code.
7. Before producing the final JSON output, double-check the classification:
   - If a function performs any kind of checking, validation, or result verification, it must be under assertion_operations.
   - If a function only supports test setup, teardown, or data preparation, it must be under utility_operations.
8. **FINAL DEPENDENCY VERIFICATION**: Before outputting JSON, verify that ALL functions called by your created functions are either:
   - Standard library functions (with proper #includes)
   - Listed in your `"searched_from_pool"` sections
   - Source code functions that are declared in the header file (never private/static functions)
   - Defined within the same `"created"` function

## FORBIDDEN PATTERNS (REAL EXAMPLES THAT CAUSED ERRORS):
```c
// ❌ WRONG - Same name as source (causes "error: redefinition of 'newNode'")
struct node* newNode(int item) { ... }

// ❌ WRONG - Hardcoded values (generates same key = 50 for all inserts)
void setup() {
    int values[] = {50, 30, 20};  // Results in: int key = 50; insert(root, key); insert(root, key);
}

// ❌ WRONG - Missing dependencies (causes "undefined reference to 'assert_array_equal'")
void check_array(int *arr) {
    assert_array_equal(arr, expected);  // Function not in searched_from_pool
}

// ❌ WRONG - Creates utility operations with same name as source code functions
void insert() { ... }  // Conflicts with source insert() function

// ❌ WRONG - Wrapper functions that just call existing helpers (useless)
void verify_tree_structure(struct node *test_root, struct node *expected_root) {
    assert_tree_equal(test_root, expected_root);  // Just calls existing function
}

// ❌ WRONG - Complete test functions (not basic helpers)
void test_delete_node(struct node *root, int key) {
    root = deleteNode(root, key);
    assert_root_key(root, expected_key);
    // This is a complete test, not a basic helper
}

// ❌ WRONG - Functions with only comments, no actual code (USELESS!)
void assert_tree_structure(struct node *tree, int *expected, int size) {
    int *actual = malloc(size * sizeof(int));
    // Perform inorder traversal to fill actual_array
    // Call assert_array_equal(actual_array, expected_array, size);
    free(actual);  // Allocates and frees memory but does NOTHING useful!
}

// ❌ WRONG - Functions with TODO comments instead of real implementation
void helper_function(int *data) {
    // TODO: implement this function
    return;  // Does nothing!
}

// ❌ WRONG - Calling private/static functions not in header file
void helper_check_node(struct node* root, Point point) {
    if (node_contains_(root, point)) {  // FORBIDDEN - private function!
        // ...
    }
}

// ❌ WRONG - Calling functions with underscores (typically private)
int helper_find_quadrant(struct node* root, Point point) {
    return get_quadrant_(root, point);  // FORBIDDEN - private function!
}
```

## CORRECT PATTERNS:
```c
// ✅ RIGHT - Unique name, parameterized, provides NEW functionality with COMPLETE CODE
struct node* helper_build_tree(int *values, int size) {
    struct node* root = NULL;
    for (int i = 0; i < size; i++) {
        root = insert(root, values[i]);
    }
    return root;
}

// ✅ RIGHT - Basic assertion helper that doesn't exist in pool with ACTUAL IMPLEMENTATION
void assert_node_count(struct node* root, int expected_count) {
    int actual_count = 0;
    // Count nodes using recursive traversal
    if (root != NULL) {
        actual_count = 1 + count_subtree(root->left) + count_subtree(root->right);
    }
    assert(actual_count == expected_count);
}

// ✅ RIGHT - Basic utility helper for specific data preparation with WORKING CODE
int* create_test_array(int size, int start_value) {
    int* arr = malloc(size * sizeof(int));
    for (int i = 0; i < size; i++) {
        arr[i] = start_value + i;
    }
    return arr;
}

// ✅ RIGHT - Tree structure verification with COMPLETE FUNCTIONAL IMPLEMENTATION
void assert_tree_structure(struct node *actual_tree, int *expected_array, int size) {
    int *actual_array = malloc(size * sizeof(int));
    int index = 0;
    
    // Perform inorder traversal to fill actual_array
    inorder_to_array(actual_tree, actual_array, &index);
    
    // Compare arrays
    for (int i = 0; i < size; i++) {
        assert(actual_array[i] == expected_array[i]);
    }
    
    free(actual_array);
}

// Helper function for inorder traversal
void inorder_to_array(struct node* root, int* arr, int* index) {
    if (root != NULL) {
        inorder_to_array(root->left, arr, index);
        arr[(*index)++] = root->data;
        inorder_to_array(root->right, arr, index);
    }
}

// ✅ RIGHT - Only calling public functions from header file
void helper_validate_tree(struct node* root, Point point) {
    // Only call functions declared in the header file
    struct node* result = insert(root, point);  // OK if insert() is in header
    // Never call node_contains_() or get_quadrant_() - they're private!
}

"""


op_map_usr_prompt_template = """
You are creating an **operation map** for C unit tests.

Below is the C source file to be tested:
<source_code>

Below is the header file with public function declarations:
<header_file>

Below is a list of available helper functions retrieved from the helper pool:
<helper_context>

You task:
1. Identify public header functions (Note: source function names will be loaded from source_functions.json).
2. Classify helpers into 'assertion_operations' and 'utility_operations'.
3. Create new helpers in 'created' only if no existing helper covers the functionality.
4. Fill 'searched_from_pool' with relevant helpers (verify no conflicts with source code names).
5. Track dependencies in 'dependency_analysis' (planned_created_functions and required_from_pool only).
6. Ensure output JSON strictly follows the format with all created and searched helpers.    

## OUTPUT FORMAT:
**REQUIRED JSON structure with dependency_analysis:**
```json
{
  "dependency_analysis": {
    "planned_created_functions": [
      {"name": "helper_build_tree", "calls": ["insert", "malloc", "free"]},
      {"name": "verify_tree_structure", "calls": ["assert_array_equal", "printf"]}
    ],
    "required_from_pool": ["assert_array_equal"]
  },
  "assertion_operations": {
    "searched_from_pool": ["assert_array_equal"],
    "created": [
      {
        "name": "verify_tree_structure",
        "description": "Verifies tree structure matches expected",
        "return_type": "void",
        "parameters": [{"name": "root", "type": "struct node *"}],
        "code_block": "#include <stdio.h>\nvoid verify_tree_structure(struct node *root) {\n  // calls assert_array_equal\n}"
      }
    ]
  },
  "utility_operations": {
    "searched_from_pool": ["init_test_root", "cleanup_test_tree", "reset_test_root"],
    "created": [
      {
        "name": "helper_build_tree", 
        "description": "Builds tree from array of values",
        "return_type": "struct node *",
        "parameters": [{"name": "values", "type": "int *"}, {"name": "size", "type": "int"}],
        "code_block": "#include <stdlib.h>\nstruct node* helper_build_tree(int *values, int size) {\n  // calls insert, malloc, free\n}"
      }
    ]
  }
}
```

**VALIDATION**: Ensure "required_from_pool" functions appear in "searched_from_pool" sections! 
**HEADER VALIDATION**: Ensure all source code function calls are declared in the header file!
**NOTE**: "searched_from_pool" may include additional relevant functions beyond just "required_from_pool"!
"""
