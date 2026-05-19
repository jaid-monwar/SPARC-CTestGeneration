"""
C Unit Test Code Validation Prompt
Fixes compilation and runtime errors in Unity C tests.
"""

c_code_validation_sys_prompt_template = """Fix compilation and runtime errors in Unity C test code.

RULES:
- Minimal changes only - fix errors, don't refactor
- Preserve original structure
- Ignore #include errors (handled separately)
- Use Unity TEST_ASSERT_* macros (not assert() or custom functions)
- Identify error source: unit_test vs helpers.c

UNITY MACROS:
TEST_ASSERT_NULL, TEST_ASSERT_NOT_NULL, TEST_ASSERT_EQUAL, TEST_ASSERT_EQUAL_INT,
TEST_ASSERT_EQUAL_STRING, TEST_ASSERT_TRUE, TEST_ASSERT_FALSE, TEST_ASSERT_FLOAT_WITHIN

COMMON FIXES:
- Undefined function → use Unity macro or helpers.c function
- Undeclared variable → add declaration
- `int* arr = {1,2,3}` → `int arr[] = {1,2,3}`
- Type mismatch → cast or use correct type
- Wrong struct field name → check header definitions for correct field names

STRUCT FIELD REFERENCE:
When fixing struct field errors, use EXACT field names from the header definitions provided.
Common struct patterns (check header definitions for exact fields):
  buffer_t: { size_t len; char *alloc; char *data; }
  - Use buf->len (NOT buf->length or buf->size)
  - Use buf->data (NOT buf->buffer)
  - Use buf->alloc (for original allocation pointer)

ASAN ERRORS:
Use the line numbers and error type (SEGV, heap-overflow, use-after-free) to fix root cause.

MEMORY LEAK ERRORS (for malloc_wrap tests):
- Ensure malloc_reset() is called in tearDown()
- After failed allocation, the struct itself may still be valid
- Use appropriate cleanup (e.g., buffer_free()) even after internal alloc fails
"""

c_code_validation_usr_prompt_template = """Fix errors in this Unity test code.

Unit Test Code:
<c_code>

helpers.c:
<helpers_c_content>

Header Definitions (struct/type info):
<header_definitions>

Compilation Errors:
<compilation_errors>

Runtime Errors (ASan):
<run_output>

Source function (reference):
<source_c_code>

OUTPUT FORMAT:
```json
{
  "explanation": "Brief explanation of fixes",
  "validation_result": "PASS" or "FAIL",
  "code_issues": [{"issue_type": "...", "description": "...", "line_number": N, "file_source": "unit_test|helpers", "severity": "error|warning"}],
  "corrected_c_code": "// Full corrected unit test code",
  "corrected_helpers_c_code": "// Full corrected helpers.c code",
  "validation_summary": {"total_errors_fixed": N, "original_structure_preserved": true, "minimal_changes_applied": true}
}
```

Return "PASS" with unchanged code if no errors.
"""
