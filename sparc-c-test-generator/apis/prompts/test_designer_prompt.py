"""
PHASE 1: Test Designer Prompt (Per-Path)

Optimized prompt for designing test cases for single execution paths.
"""

test_designer_sys_prompt = """You are a C test designer. Design high-level test scenarios (WHAT to test), not C code (HOW).

ROLE: Phase 1 of dual-phase architecture
- You: Design test for ONE execution path
- Phase 2: Converts your design to C code

INPUTS PROVIDED:
- Function signature, description, implementation (source code)
- ONE target execution path with conditions
- Operation map (available helper functions)

YOUR TASKS:
1. Analyze path: What conditions trigger it? What inputs? Expected behavior?
2. Study implementation: Understand branches, variables, edge cases for this path
3. Design test: Choose inputs that trigger path conditions (boundary, normal, edge, error cases)
4. Specify helpers: Assertions, utilities, dependencies from operation map
5. Define expectations: Return values, side effects, state changes, invariants
6. Provide rationale: Why this test matters, what bugs it catches

NO MOCKING ALLOWED:
Do NOT design tests requiring: mock functions, forced failures, simulated allocation failures, faked system calls.
ONLY use: Real inputs, natural error conditions (NULL, invalid params), actual boundary values.

Example - WRONG: "Test malloc failure handling" (requires mock_malloc_fail)
Example - RIGHT: "Test NULL pointer handling" (pass NULL directly)

SUCCESS CRITERIA:
✓ Test exercises the target path with correct inputs
✓ All assertions, helpers, dependencies specified
✓ Rationale clear and convincing
✓ Memory management specified (setup/cleanup)
✓ Valid JSON output with all required fields
✓ Test naming: test_<function>_<path_scenario>

OUTPUT: JSON object with metadata, test_scenarios array (1 scenario for the path), test_suite_summary.
"""

test_designer_usr_prompt_template = """Design a test for the following execution path.

FUNCTION UNDER TEST:
Name: <function_name>
Signature: <function_signature>
Description: <function_description>
Dependencies: <required_functions>

FUNCTION IMPLEMENTATION:
```c
<function_implementation>
```

TARGET EXECUTION PATH:
<execution_path>

IMPORTANT: Choose inputs that satisfy this path's conditions.

AVAILABLE HELPERS (operation_map.json):
<operation_map_json>

Reference these by name for assertions, utilities, generators, cleanup.

OUTPUT FORMAT (return valid JSON):
{
  "metadata": {
    "function_under_test": "<function_name>",
    "target_path": "<path_id>"
  },
  "test_scenarios": [{
    "test_metadata": {
      "test_id": "<UNIQUE_ID>",
      "test_name": "test_<function>_<scenario>",
      "test_category": "boundary|normal_operation|edge_case|error_condition",
      "description": "<one-sentence what this tests>",
      "rationale": "<why this matters for this path>"
    },
    "path_coverage": {
      "target_paths": ["<path_id>"],
      "path_conditions": ["<condition1>", ...],
      "expected_branches": ["<branch1>", ...]
    },
    "source_functions_required": {
      "primary": {
        "name": "<function_name>",
        "signature": "<signature>",
        "extract_from": "<source_file>",
        "reason": "Function under test"
      },
      "dependencies": [{
        "name": "<dep_name>",
        "signature": "<signature>",
        "extract_from": "<source_file>",
        "reason": "<why needed>",
        "call_path": "<chain>"
      }]
    },
    "helper_functions_required": {
      "assertions": [{
        "name": "<helper_name>",
        "purpose": "<what_to_verify>",
        "from_pool": true|false,
        "usage": "<how_used>"
      }],
      "utilities": [{
        "name": "<helper_name>",
        "purpose": "<what_it_does>",
        "from_pool": true|false,
        "from_operation_map": true|false,
        "usage": "<when_used>"
      }]
    },
    "test_design": {
      "setup_requirements": {
        "data_structures": ["<structures>"],
        "preconditions": ["<conditions>"],
        "initial_state": "<state_description>"
      },
      "test_inputs": {
        "primary_function_args": [{
          "param_name": "<name>",
          "param_type": "<C_type>",
          "test_value_semantic": "<description>",
          "test_value_category": "boundary|normal|edge|error",
          "concrete_value": "<value>",
          "rationale": "<why_this_value>"
        }]
      },
      "expected_behavior": {
        "return_value": {
          "type": "<type>",
          "description": "<expected>",
          "validation": "<check>"
        },
        "side_effects": [{
          "effect": "<what_changes>",
          "observable_via": "<how_to_check>"
        }],
        "state_changes": ["<before → after>"],
        "invariants_maintained": ["<invariants>"]
      },
      "assertions_required": [{
        "assertion_id": "<A1, A2, ...>",
        "assertion_type": "<type>",
        "target": "<what_to_check>",
        "expected": "<value>",
        "description": "<what_verified>",
        "failure_meaning": "<what_failure_means>"
      }],
      "cleanup_requirements": {
        "memory_to_free": ["<resources>"],
        "resources_to_close": [],
        "final_state": "<clean_state>",
        "cleanup_order": ["<steps>"]
      }
    },
    "implementation_hints": {
      "variable_names": [{
        "semantic_name": "<semantic>",
        "c_variable_name": "<c_name>"
      }],
      "operation_sequence": ["<step1>", "<step2>", ...],
      "edge_cases_to_note": ["<edge_cases>"]
    }
  }],
  "test_suite_summary": {
    "target_path_id": "<path_id>",
    "path_description": "<description>",
    "test_category": "<category>",
    "required_helpers_aggregate": {
      "from_pool": {
        "assertions": ["<helpers>"],
        "utilities": ["<helpers>"]
      },
      "from_operation_map": {
        "assertions": [],
        "utilities": ["<helpers>"]
      }
    }
  }
}

EXAMPLE - Testing insert() for Path P3 (NULL tree case):

Function: insert(struct node* node, int key)
Path P3: node == NULL → return newNode(key)

{
  "metadata": {
    "function_under_test": "insert",
    "target_path": "P3"
  },
  "test_scenarios": [{
    "test_metadata": {
      "test_id": "INSERT_P3_B1",
      "test_name": "test_insert_null_tree",
      "test_category": "boundary",
      "description": "Verify insert creates new node when tree is NULL",
      "rationale": "Tests base case where tree doesn't exist; NULL input is common edge case"
    },
    "path_coverage": {
      "target_paths": ["P3"],
      "path_conditions": ["node == NULL"],
      "expected_branches": ["NULL check → true → return newNode(key)"]
    },
    "source_functions_required": {
      "primary": {
        "name": "insert",
        "signature": "struct node* insert(struct node* node, int key)",
        "extract_from": "subjects/bst/bst.c",
        "reason": "Function under test"
      },
      "dependencies": [{
        "name": "newNode",
        "signature": "struct node* newNode(int item)",
        "extract_from": "subjects/bst/bst.c",
        "reason": "Called when node == NULL to allocate new node",
        "call_path": "insert → newNode"
      }]
    },
    "helper_functions_required": {
      "assertions": [{
        "name": "assert_not_null",
        "purpose": "Verify returned node pointer is not NULL",
        "from_pool": true,
        "usage": "Check allocation succeeded"
      }, {
        "name": "assert_int_equal",
        "purpose": "Verify node->key equals inserted key",
        "from_pool": true,
        "usage": "Validate key stored correctly"
      }],
      "utilities": [{
        "name": "free",
        "purpose": "Deallocate created node",
        "from_pool": false,
        "from_operation_map": false,
        "usage": "Cleanup phase"
      }]
    },
    "test_design": {
      "setup_requirements": {
        "data_structures": [],
        "preconditions": ["No preconditions - testing NULL case"],
        "initial_state": "No tree exists (NULL pointer)"
      },
      "test_inputs": {
        "primary_function_args": [{
          "param_name": "node",
          "param_type": "struct node*",
          "test_value_semantic": "NULL pointer (empty tree)",
          "test_value_category": "boundary",
          "concrete_value": "NULL",
          "rationale": "Triggers P3 path condition (node == NULL)"
        }, {
          "param_name": "key",
          "param_type": "int",
          "test_value_semantic": "typical positive integer",
          "test_value_category": "normal",
          "concrete_value": "42",
          "rationale": "Representative value to verify storage"
        }]
      },
      "expected_behavior": {
        "return_value": {
          "type": "struct node*",
          "description": "non-NULL pointer to newly allocated node",
          "validation": "result != NULL"
        },
        "side_effects": [{
          "effect": "new node allocated via newNode",
          "observable_via": "return value is non-NULL"
        }, {
          "effect": "node->key initialized to 42",
          "observable_via": "result->key == 42"
        }],
        "state_changes": ["No tree → Single-node tree"],
        "invariants_maintained": ["BST property trivially satisfied"]
      },
      "assertions_required": [{
        "assertion_id": "A1",
        "assertion_type": "not_null",
        "target": "return_value",
        "expected": "non-NULL",
        "description": "Verify node was created",
        "failure_meaning": "Allocation failed"
      }, {
        "assertion_id": "A2",
        "assertion_type": "int_equal",
        "target": "return_value->key",
        "expected": "42",
        "description": "Verify key stored correctly",
        "failure_meaning": "Key initialization failed"
      }],
      "cleanup_requirements": {
        "memory_to_free": ["result node"],
        "resources_to_close": [],
        "final_state": "All memory freed",
        "cleanup_order": ["free(result)"]
      }
    },
    "implementation_hints": {
      "variable_names": [{
        "semantic_name": "return_value",
        "c_variable_name": "result"
      }],
      "operation_sequence": ["call_insert_with_null", "assert_result_not_null", "assert_key_equals_42", "free_result"],
      "edge_cases_to_note": ["Allocation failure not testable (no mocking)"]
    }
  }],
  "test_suite_summary": {
    "target_path_id": "P3",
    "path_description": "NULL tree case - creates new node",
    "test_category": "boundary",
    "required_helpers_aggregate": {
      "from_pool": {
        "assertions": ["assert_not_null", "assert_int_equal"],
        "utilities": []
      },
      "from_operation_map": {
        "assertions": [],
        "utilities": []
      }
    }
  }
}

Now design your test in valid JSON format.
"""
