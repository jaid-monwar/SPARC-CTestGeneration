"""
Test Scenario Generation Prompt Template
This prompt focuses on generating clean, well-structured test scenarios based on core C unit testing principles.
"""

test_scenario_sys_prompt_template = """
## CORE RULES:
1. **test_name**: Clear C function name with "unit_test_" prefix (e.g., `unit_test_rgba_from_string_comprehensive`)
2. **Operations only**: Use ONLY ops from the operation map - NO exceptions!
3. **Parameter names matching**: All keys in `input_params` MUST match operation map parameter names exactly
4. **Type matching CRITICAL**: Variable declaration types MUST match operation map expected types exactly
   - If operation expects `rgba_t`, declare `rgba_t` (not `uint32_t`)
   - If operation expects `char *`, declare `char *` (not `char[20]`)
   - If operation expects `size_t`, use `size_t` (not `int`)
5. **NO MEANINGLESS NULL VALUES**: 
   - ❌ NEVER declare `int* values = NULL` if the function expects actual data
   - ✅ CORRECT: `int* values = {50, 30, 20, 70, 60}` or `char* buffer = "test_string"`
   - ❌ NEVER pass NULL pointers to functions that need real data
6. **Assertions required**: Every test MUST verify results with assertion operations
   - **ALWAYS PREFER helper assertion functions from the operation map** (e.g., `helper_assert_quadtree_search`, `helper_assert_quadtree_insert`, `helper_assert_quadtree_free`)
   - **For pointer comparisons**: Use `assert(pointer == NULL)` or `assert(pointer != NULL)` - NEVER use `assert_int_equal`
   - **For double/float comparisons**: Use `assert(fabs(actual - expected) < 0.001)` or similar - NEVER use `assert_int_equal`
   - **For integer comparisons**: Use `assert_int_equal(actual, expected)` only if available in operation map
   - **CRITICAL**: Only use assertion operations that exist in the operation map - check before using!
7. **Variable consistency**: Same variable names throughout each test
8. **NO DUPLICATE OPERATIONS**: Each function should only be called once per test scenario
   - **SETUP**: For complex data preparation using utility operations (like `create_test_array`, `init_test_buffer`) OR variables needed by multiple steps
   - **STEPS**: Main function calls + assertions to verify results (can declare variables used in this section)
   - **CLEANUP**: Resource cleanup only (like `free_test_data`, `cleanup_buffer`) (can declare variables used in this section)
   - **VARIABLE PLACEMENT PRINCIPLE**: Declare variables in the operation step where they are first used (setup, steps, or cleanup)
   - **SIMPLE TESTS**: If no complex setup needed, leave setup empty and put variable declarations in the steps that use them
9. **Expected values MANDATORY**: Every assertion MUST include concrete expected values
10. **Focus on MAXIMUM LINE COVERAGE STRATEGY:**
  - **Identify PUBLIC interface functions** that call multiple internal helper functions
  - **Prioritize testing functions that provide maximum line coverage** (e.g., a main function that calls 4 internal helpers covers more lines than testing each helper separately)
  - **Multiple test cases per function**: Design different inputs to trigger all code branches
  - **List all the source function names** but prioritize comprehensive tests for high-coverage functions
  - **Comprehensive scenarios**: Single test function should exercise various internal paths
  - **Example**: `rgba_from_string` with hex, rgb, rgba, and named inputs covers 4 internal functions

**CRITICAL VALIDATION**: Before outputting JSON, verify EVERY "op" field exists in the operation map!
**ASSERTION VALIDATION**: Always check the operation map for available assertion functions (helper_assert_*, assert_int_equal, etc.) before using standard assert()

**REMEMBER**: This format completely solves the pointer parameter problem:
- Declaration: `short ok = 0;` (declares the actual variable)
- Usage: `&ok` (passes address to function expecting `short*`)

🚨 CRITICAL: UNIQUE TEST NAMING 🚨
**IMPORTANT: Test function names MUST be unique and not conflict with helper function names**
- Use prefix "unit_test_" for all test function names 
- Examples: "unit_test_rgba_from_string_hex", "unit_test_bst_insert_basic", "unit_test_qsort_array"

🚨 CRITICAL: TWO-PHASE PARAMETER SYSTEM 🚨
Pattern: SETUP → STEPS → CLEANUP

**IMPORTANT: AVOID DUPLICATE OPERATIONS & DECLARE VARIABLES WHERE USED**
- **SETUP**: For variable declarations and data preparation that are needed across multiple steps
- **STEPS**: Main function calls being tested + assertions to verify results (can include variable declarations for variables used in that step)
- **CLEANUP**: Memory cleanup, resource deallocation (can include variable declarations for cleanup variables)
- **VARIABLE DECLARATION PRINCIPLE**: Declare variables in the operation step where they are first used - whether that's in setup, steps, or cleanup

**DO NOT** repeat the same function call in both setup and steps! Declare variables in the step that actually uses them.
**DO NOT** use operations that does not include in the operation map.
**CRITICAL**: Never use standard library functions (malloc, free, printf, etc.) as operations - they are NOT in the operation map!

🚨 **OPERATION MAP VALIDATION** 🚨
- **ONLY use operations listed in the provided operation_map**
- **Standard library functions are NOT operations** (malloc, free, printf, strcpy, etc.)
- **If you need memory allocation**, declare variables with `malloc()` in variable_declarations, don't use malloc as an operation
- **If you need cleanup**, use utility operations from the operation map like `cleanup_buffer`, `free_memory`, etc.

### Phase 1: Variable Declarations
```json
"variable_declarations": [
  {
    "name": "ok",
    "type": "short", 
    "value": "0",
    "comment": "Status flag for parsing operation"
  },
  {
    "name": "color_str", 
    "type": "const char*", 
    "value": "\"#FF5733\"",
    "comment": "Input color string to parse"
  }
]
```

### Phase 2: Function Call Usage  
```json
"input_params": {
  "str": "color_str",
  "ok": "&ok"
}
```

## CRITICAL ADVANTAGES OF FORMAT:
- **Solves Pointer Problems**: Can declare `short ok = 0;` but pass `&ok` to function
- **Clear Separation**: Declaration type vs usage type are explicit
- **Better Documentation**: Comments explain variable purposes  
- **Flexible Usage**: Same variable can be used differently in different contexts

## PARAMETER FORMAT EXAMPLES

### Example 1: Basic Function Testing Pattern
```json
{
  "test_name": "unit_test_quadtree_insert_valid",
  "setup": [
    {
      "op": "quadtree_new",
      "variable_declarations": [
        {
          "name": "tree",
          "type": "quadtree_t*",
          "value": "NULL",
          "comment": "Quadtree structure"
        }
      ],
      "input_params": {
        "minx": "0.0",
        "miny": "0.0", 
        "maxx": "10.0",
        "maxy": "10.0"
      },
      "return_params": ["tree"]
    }
  ],
  "steps": [
    {
      "op": "quadtree_insert",
      "variable_declarations": [
        {
          "name": "point_x",
          "type": "double",
          "value": "5.0",
          "comment": "X coordinate to insert"
        },
        {
          "name": "point_y", 
          "type": "double",
          "value": "5.0",
          "comment": "Y coordinate to insert"
        },
        {
          "name": "key",
          "type": "void*",
          "value": "NULL",
          "comment": "Key for the point"
        }
      ],
      "input_params": {
        "tree": "tree",
        "x": "point_x",
        "y": "point_y",
        "key": "key"
      },
      "return_params": ["result"]
    },
    {
      "op": "assert_int_equal",
      "input_params": {
        "actual": "result",
        "expected": "1"
      },
      "return_params": []
    }
  ],
  "cleanup": [
    {
      "op": "quadtree_free",
      "input_params": {
        "tree": "tree"
      },
      "return_params": []
    }
  ]
}
```

### Example 2: Correct Variable Declaration Placement
```json
{
  "test_name": "unit_test_rgba_from_string_hex",
  "setup": [],
  "steps": [
    {
      "op": "rgba_from_string",
      "variable_declarations": [
        {
          "name": "color_str",
          "type": "const char*", 
          "value": "\"#FF5733\"",
          "comment": "Input color string to parse"
        },
        {
          "name": "parse_status",
          "type": "short",
          "value": "0", 
          "comment": "Status flag for parsing operation"
        }
      ],
      "input_params": {
        "str": "color_str",
        "ok": "&parse_status"
      },
      "return_params": ["result"]
    },
    {
      "op": "assert_uint32_equal",
      "input_params": {
        "actual": "result",
        "expected": "0xFF5733FF"
      },
      "return_params": []
    }
  ],
  "cleanup": []
}
```

### Example 3: CORRECT Pattern - Array/Pointer Variable Declarations
```json
{
  "steps": [
    {
      "op": "helper_build_tree",  
      "variable_declarations": [
        {
          "name": "values",
          "type": "int*",
          "value": "{50, 30, 20, 70, 60}",  // ✅ CORRECT: Array with actual test values
          "comment": "Array of values to insert into tree"
        },
        {
          "name": "size",
          "type": "int", 
          "value": "5",
          "comment": "Number of elements in array"
        }
      ],
      "input_params": {
        "values": "values",
        "size": "size" 
      },
      "return_params": ["tree"]
    }
  ],
  "cleanup": [
    {
      "op": "cleanup_test_array",  // ✅ CORRECT: Use cleanup operations from operation_map
      "input_params": {
        "array": "values"
      },
      "return_params": []
    }
  ]
}
```

### Example 4: CORRECT Pattern - Memory Management Through Variable Declarations
```json
{
  "steps": [
    {
      "op": "rgba_to_string",  
      "variable_declarations": [
        {
          "name": "buf",
          "type": "char*",
          "value": "malloc(20)",  // ✅ CORRECT: malloc in variable declaration, not as operation
          "comment": "Buffer for string representation"
        }
      ],
      "input_params": {
        "rgba": "rgba_obj",
        "buf": "buf",
        "len": "20"
      },
      "return_params": []
    }
  ],
  "cleanup": [
    {
      "op": "cleanup_memory",  // ✅ CORRECT: Use cleanup operations from operation_map
      "input_params": {
        "buffer": "buf"
      },
      "return_params": []
    }
  ]
}
```
"""


test_scenario_usr_prompt_template = """
You are generating **unit test scenarios** for C source code.

Below is the C source file to be tested, **IMPORTANT** please carefully examine this file to understand how it works, you are going to generate unit tests for it:
<source_code>

Below is the operation map for the source code:
<op_map_json>

Your Tasks:
1. Generate comprehensive unit tests using only operations in the operation map. Maximize code coverage and test all edge cases. Use diverse and realistic values; avoid NULL pointers or invalid runtime-dependent values if possible.
2. Each generated unit test **must call at least one function from the actual source code**.
3. Do not generate tests that only call helper/assertion functions.
4. **Do NOT redeclare global variables** locally. If a global variable is used in the source code, access it via `extern` in the unit test.
5. If a source function depends on runtime resources (e.g., `resize()`, X11), **mock its behavior**:
    - Update the globals, buffers, or outputs the function would affect.
    - The function call itself must still appear in the test.
6. For each test, clearly separate:
   - Setup: utility operations and variable declarations needed before main steps.
   - Steps: main function calls + assertions.
   - Cleanup: freeing resources or buffers.
7. Verify every 'op' used exists in the operation map.
8. Include concrete expected values for every assertion.


### IMPORTANT REMINDERS:
- Helpers/assertions should only be used to **check results**, never as a replacement for calling source functions.
- Avoid empty tests (no function calls or no assertions).

## EACH OPERATION STEP STRUCTURE:
```json
{
  "op": "function_name_from_operation_map",
  "variable_declarations": [
    {
      "name": "variable_name",
      "type": "C_type", 
      "value": "initial_value",
      "comment": "optional_description"
    }
  ],
  "input_params": {
    "param_name_from_op_map": "how_to_use_variable"
  },
  "return_params": ["return_variable_name"]
}
```

## JSON SCHEMA:
```json
{
  "test_name": "string - C function name",
  "setup": [
    {
      "op": "string - operation from operation map",
      "variable_declarations": [
        {"name": "var_name", "type": "C_type", "value": "initial_value", "comment": "description"}
      ],
      "input_params": {
        "param_name_from_op_map": "variable_or_literal"
      },
      "return_params": ["return_variable_name"]
    }
  ],
  "steps": [
    {
      "op": "string - main function call + assertion operations",
      "variable_declarations": [
        {"name": "var_name", "type": "C_type", "value": "initial_value", "comment": "description"}
      ],
      "input_params": {
        "param_name_from_op_map": "variable_or_literal"
      },
      "return_params": ["return_variable_name"]
    }
  ],
  "cleanup": [
    {
      "op": "string - cleanup operations",
      "variable_declarations": [],
      "input_params": {
        "param_name_from_op_map": "variable_or_literal"
      },
      "return_params": []
    }
  ]
}
```


**Output only valid JSON. No explanations.**
"""
