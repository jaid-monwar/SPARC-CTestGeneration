"""
Monolithic Test Generator

Single-phase test generation that directly produces C test code.
Combines the functionality of Test Designer and Test Coder into one step.

Features:
- Generates C test code directly (no intermediate JSON)
- One test per execution path
- Parallel processing (10 workers by default)
- Individual test validation (max 3 iterations)
- Automatic merging into final unit_test.c
"""

import os
import re
import json
import threading
from typing import Any, Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from apis.gpt import GPT_Connection
from apis.prompts.monolithic_test_prompt import (
    monolithic_test_sys_prompt,
    monolithic_test_usr_prompt_template,
)

# Set up libclang for parsing C headers
try:
    from clang.cindex import Index, CursorKind, Config

    # Try to set libclang path (same as gen_headers_clang.py)
    try:
        Config.set_library_file("/usr/lib/llvm-20/lib/libclang.so")
    except:
        try:
            Config.set_library_file("/usr/lib/llvm-18/lib/libclang.so.1")
        except:
            pass  # Use default libclang path

    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False


def extract_public_function_names(header_files: List[str]) -> set:
    """
    Extract function names declared in header files using libclang.

    These are the public API functions that should have tests generated.
    Functions not declared in headers (internal/static) should be skipped.

    Args:
        header_files: List of paths to header files

    Returns:
        Set of function names declared in the headers
    """
    public_functions = set()

    if not CLANG_AVAILABLE:
        print("  [Warning] libclang not available, falling back to regex parsing")
        return _extract_public_function_names_regex(header_files)

    for header_path in header_files:
        if not os.path.exists(header_path):
            continue

        try:
            index = Index.create()
            # Parse header as C code
            tu = index.parse(
                header_path,
                args=['-x', 'c', '-std=c11'],
                options=0x01  # CXTranslationUnit_DetailedPreprocessingRecord
            )

            # Walk the AST to find function declarations
            for cursor in tu.cursor.get_children():
                if cursor.kind == CursorKind.FUNCTION_DECL:
                    # Only include if location is in this header file
                    if cursor.location.file and str(cursor.location.file) == header_path:
                        public_functions.add(cursor.spelling)

        except Exception as e:
            print(f"  [Warning] Could not parse header {header_path} with clang: {e}")
            # Fallback to regex for this file
            public_functions.update(_extract_public_function_names_regex([header_path]))

    return public_functions


def _extract_public_function_names_regex(header_files: List[str]) -> set:
    """
    Fallback regex-based extraction for when libclang is not available.
    """
    public_functions = set()

    for header_path in header_files:
        if not os.path.exists(header_path):
            continue

        try:
            with open(header_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Match function declarations: return_type function_name(params);
            pattern = r'^\s*(?:extern\s+)?(?:static\s+)?(?:inline\s+)?(?:\w+[\s\*]+)+(\w+)\s*\([^)]*\)\s*;'
            matches = re.findall(pattern, content, re.MULTILINE)
            public_functions.update(matches)

        except Exception as e:
            print(f"  [Warning] Could not read header {header_path}: {e}")

    return public_functions


class MonolithicTestGenerator:
    """
    Monolithic test generator that directly produces C test code.

    This combines the functionality of TestDesignerManager and TestCoderManager
    into a single agent that outputs compilable C code directly.
    """

    def __init__(self):
        self.gpt_connection = GPT_Connection()

    def _read_function_implementation(
        self, function_name: str, atomic_files_dir: str = "tmp/function-files"
    ) -> str:
        """
        Read the function implementation from atomic files.

        Args:
            function_name: Name of the function
            atomic_files_dir: Directory containing atomic function files

        Returns:
            String containing the function implementation
        """
        function_file_path = os.path.join(atomic_files_dir, f"{function_name}.c")

        if not os.path.exists(function_file_path):
            print(f"  Warning: Function file not found: {function_file_path}")
            return ""

        try:
            with open(function_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"  Error reading function file {function_file_path}: {e}")
            return ""

    def _extract_test_name_from_code(self, c_code: str) -> str:
        """
        Extract the test function name from generated C code.

        Args:
            c_code: Generated C test code

        Returns:
            Extracted test name or a default name
        """
        # Look for void unit_test_*(...) pattern
        match = re.search(r'void\s+(unit_test_\w+)\s*\(', c_code)
        if match:
            return match.group(1)
        return "unit_test_unknown"

    def _sanitize_test_name(self, test_name: str) -> str:
        """
        Sanitize test name to be a valid C function identifier and filename.

        Args:
            test_name: Original test name

        Returns:
            Sanitized test name
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', test_name)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized

    def generate_test_for_path(
        self,
        function_name: str,
        function_info: Dict[str, Any],
        path_info: Dict[str, Any],
        function_implementation: str,
        operation_map_json: str,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate C test code for a specific execution path.

        Args:
            function_name: Name of the function to test
            function_info: Dictionary containing function metadata
            path_info: Dictionary containing single path information
            function_implementation: Source code of the function
            operation_map_json: JSON string of the operation map
            temperature: GPT temperature setting

        Returns:
            Generated C test code as string
        """
        # Extract function information
        function_signature = function_info.get("signature", "")
        function_description = function_info.get("description", "")
        required_functions = function_info.get("required_functions", [])

        # Format single path for the prompt
        path_id = path_info.get("path_id", "P1")
        path_description = path_info.get("path", "")
        path_text = f"Path {path_id}: {path_description}"

        # Format required functions
        required_funcs_text = ", ".join(required_functions) if required_functions else "None"

        # Create the prompt
        usr_prompt = monolithic_test_usr_prompt_template.replace(
            "<function_name>", function_name
        )
        usr_prompt = usr_prompt.replace("<function_signature>", function_signature)
        usr_prompt = usr_prompt.replace("<function_description>", function_description)
        usr_prompt = usr_prompt.replace("<execution_path>", path_text)
        usr_prompt = usr_prompt.replace("<function_implementation>", function_implementation)
        usr_prompt = usr_prompt.replace("<required_functions>", required_funcs_text)
        usr_prompt = usr_prompt.replace(
            "<operation_map_json>", operation_map_json.replace("\n", "\\n")
        )

        # Call GPT to generate C test code directly (no response_model = raw text)
        print(f"  [{path_id}] Generating C test code...")

        response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": monolithic_test_sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            temperature=temperature,
            response_model=None,  # Get raw text, not structured output
            context=f"monolithic_test_{function_name}_{path_id}",
            max_tokens=4096,
        )

        # Extract the C code from response
        c_code = response.strip()

        # Remove markdown code blocks if present
        if c_code.startswith("```c"):
            c_code = c_code[4:]
        elif c_code.startswith("```"):
            c_code = c_code[3:]
        if c_code.endswith("```"):
            c_code = c_code[:-3]
        c_code = c_code.strip()

        test_name = self._extract_test_name_from_code(c_code)
        print(f"  [{path_id}] Generated: {test_name}")

        return c_code

    def _process_single_path(
        self,
        func_name: str,
        func_info: Dict[str, Any],
        path_info: Dict[str, Any],
        function_implementation: str,
        operation_map_json: str,
        output_dir: str,
        temperature: float,
    ) -> Tuple[str, str, str, str]:
        """
        Process a single path: generate C test code and save to file.

        Args:
            func_name: Function name
            func_info: Function metadata dictionary
            path_info: Single path metadata dictionary
            function_implementation: Source code of the function
            operation_map_json: JSON string of operation map
            output_dir: Base directory for monolithic output
            temperature: GPT temperature

        Returns:
            Tuple of (function_name, path_id, test_name, output_file_path)
        """
        path_id = path_info.get("path_id", "P1")

        # Generate C test code for this path
        c_code = self.generate_test_for_path(
            function_name=func_name,
            function_info=func_info,
            path_info=path_info,
            function_implementation=function_implementation,
            operation_map_json=operation_map_json,
            temperature=temperature,
        )

        # Extract test name from generated code
        test_name = self._extract_test_name_from_code(c_code)
        test_name = self._sanitize_test_name(test_name)

        # Create function subdirectory: monolithic/tests/{function_name}/
        func_tests_dir = os.path.join(output_dir, "monolithic", "tests", func_name)
        os.makedirs(func_tests_dir, exist_ok=True)

        # Handle filename collisions
        output_filename = f"{test_name}.c"
        output_path = os.path.join(func_tests_dir, output_filename)

        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{test_name}_{counter}.c"
            output_path = os.path.join(func_tests_dir, output_filename)
            counter += 1

        # Save the C test code
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(c_code)

        print(f"  [{path_id}] Saved: {output_path}")

        return func_name, path_id, test_name, output_path

    def generate_tests_for_all_functions(
        self,
        source_functions_path: str,
        operation_map_json: str,
        output_dir: str,
        atomic_files_dir: str = "tmp/function-files",
        temperature: float = 0.0,
        max_workers: int = 10,
        header_files: List[str] = None,
    ) -> Dict[str, List[str]]:
        """
        Generate C tests for all execution paths across all functions with parallel processing.

        Args:
            source_functions_path: Path to source_functions.json
            operation_map_json: JSON string of operation map
            output_dir: Base output directory
            atomic_files_dir: Directory containing atomic function files
            temperature: GPT temperature
            max_workers: Maximum number of parallel workers (default: 10)
            header_files: List of header file paths (filters to only test public functions)

        Returns:
            Dictionary mapping function names to list of their generated test file paths
        """
        # Load source functions
        with open(source_functions_path, "r", encoding="utf-8") as f:
            source_functions_data = json.load(f)

        source_functions = source_functions_data.get("source_functions", [])

        # Filter to only public functions if header files are provided
        public_functions = None
        if header_files:
            public_functions = extract_public_function_names(header_files)
            if public_functions:
                original_count = len(source_functions)
                source_functions = [
                    f for f in source_functions
                    if f.get("name") in public_functions
                ]
                filtered_count = original_count - len(source_functions)
                if filtered_count > 0:
                    print(f"  [Filter] Skipping {filtered_count} internal functions (not in public headers)")

        # Create output directory
        monolithic_dir = os.path.join(output_dir, "monolithic", "tests")
        os.makedirs(monolithic_dir, exist_ok=True)

        test_files = {}  # {function_name: [path1_file, path2_file, ...]}

        # Count total paths across all functions
        total_paths = sum(len(func.get("paths", [])) for func in source_functions)
        total_funcs = len(source_functions)

        print(f"\n{'=' * 70}")
        print("MONOLITHIC TEST GENERATION")
        print(f"{'=' * 70}")
        print(f"Total functions: {total_funcs}")
        print(f"Total execution paths: {total_paths}")
        print(f"Parallel mode: Processing up to {max_workers} paths at a time")
        print()

        # Prepare all path tasks
        all_path_tasks = []
        for func_info in source_functions:
            func_name = func_info.get("name")
            if not func_name:
                print("  Warning: Function with no name found, skipping")
                continue

            paths = func_info.get("paths", [])
            if not paths:
                print(f"  Warning: Function '{func_name}' has no execution paths, skipping")
                continue

            # Read function implementation once per function
            function_implementation = self._read_function_implementation(
                func_name, atomic_files_dir
            )
            if not function_implementation:
                print(f"  Warning: Could not read implementation for '{func_name}', skipping")
                continue

            # Add each path as a separate task
            for path_info in paths:
                all_path_tasks.append({
                    "func_name": func_name,
                    "func_info": func_info,
                    "path_info": path_info,
                    "function_implementation": function_implementation,
                })

        # Process paths in batches
        num_batches = (len(all_path_tasks) + max_workers - 1) // max_workers

        print(f"Total batches: {num_batches}")
        print()

        completed_count = 0
        for batch_num in range(num_batches):
            start_idx = batch_num * max_workers
            end_idx = min(start_idx + max_workers, len(all_path_tasks))
            batch_tasks = all_path_tasks[start_idx:end_idx]
            batch_size = len(batch_tasks)

            print(f"{'=' * 70}")
            print(f"BATCH {batch_num + 1}/{num_batches}: Processing paths {start_idx + 1}-{end_idx}")
            print(f"{'=' * 70}")

            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit all paths in this batch
                future_to_task = {
                    executor.submit(
                        self._process_single_path,
                        task["func_name"],
                        task["func_info"],
                        task["path_info"],
                        task["function_implementation"],
                        operation_map_json,
                        output_dir,
                        temperature,
                    ): task
                    for task in batch_tasks
                }

                # Process completed tasks as they finish
                batch_completed = 0
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    func_name = task["func_name"]
                    path_id = task["path_info"].get("path_id", "P?")

                    try:
                        returned_func_name, returned_path_id, test_name, output_path = future.result()

                        # Track files per function
                        if returned_func_name not in test_files:
                            test_files[returned_func_name] = []
                        test_files[returned_func_name].append(output_path)

                        batch_completed += 1
                        completed_count += 1
                        print(f"   [{batch_completed}/{batch_size}] {returned_func_name}::{returned_path_id} -> {test_name}")
                    except Exception as exc:
                        print(f"   {func_name}::{path_id} generated an exception: {exc}")
                        import traceback
                        traceback.print_exc()

            print(f"Batch {batch_num + 1} completed: {batch_completed}/{batch_size} paths processed")
            print()

        print(f"{'=' * 70}")
        print(f"MONOLITHIC TEST GENERATION COMPLETE")
        print(f"Generated tests for {completed_count}/{total_paths} paths")
        print(f"Functions processed: {len(test_files)}/{total_funcs}")
        print(f"{'=' * 70}")

        return test_files


def create_complete_test_file(
    test_code: str,
    function_name: str,
    test_name: str,
    header_files: List[str],
    helpers_header_file: str,
    source_file_path: str,
) -> str:
    """
    Create a complete, compilable C test file from a test function.
    Supports both Unity-style tests (complete files) and legacy tests (function only).

    Args:
        test_code: The generated test function code
        function_name: Name of the function being tested
        test_name: Name of the test function
        header_files: List of header file paths
        helpers_header_file: Path to helpers header file
        source_file_path: Path to source file being tested

    Returns:
        Complete C test file content
    """
    # Check if this is a Unity-style complete test file
    is_unity_test = '#include "unity.h"' in test_code or "#include <unity.h>" in test_code
    has_main = "int main(" in test_code or "int main(void)" in test_code

    if is_unity_test and has_main:
        # Unity test already complete - just add source headers after unity.h
        additional_includes = []

        # Add source headers
        for header in header_files:
            header_name = os.path.basename(header)
            include_line = f'#include "{header_name}"'
            if include_line not in test_code:
                additional_includes.append(include_line)

        # Add helpers header
        if helpers_header_file:
            helpers_name = os.path.basename(helpers_header_file)
            include_line = f'#include "{helpers_name}"'
            if include_line not in test_code:
                additional_includes.append(include_line)

        if additional_includes:
            # Insert additional includes after unity.h
            includes_str = "\n".join(additional_includes)
            if '#include "unity.h"' in test_code:
                test_code = test_code.replace(
                    '#include "unity.h"',
                    f'#include "unity.h"\n{includes_str}'
                )
            elif "#include <unity.h>" in test_code:
                test_code = test_code.replace(
                    "#include <unity.h>",
                    f"#include <unity.h>\n{includes_str}"
                )

        return test_code

    # Legacy mode: wrap test function with includes and main()
    includes = []
    includes.append("#include <stdio.h>")
    includes.append("#include <stdlib.h>")
    includes.append("#include <string.h>")
    includes.append("#include <assert.h>")

    # Add source headers
    for header in header_files:
        header_name = os.path.basename(header)
        includes.append(f'#include "{header_name}"')

    # Add helpers header
    if helpers_header_file:
        helpers_name = os.path.basename(helpers_header_file)
        includes.append(f'#include "{helpers_name}"')

    includes_str = "\n".join(includes)

    # Create complete file
    complete_file = f"""{includes_str}

{test_code}

int main() {{
    printf("Running {test_name}...\\n");
    {test_name}();
    printf("{test_name} PASSED\\n");
    return 0;
}}
"""
    return complete_file


def wrap_test_files_for_compilation(
    test_files: Dict[str, List[str]],
    output_dir: str,
    header_files: List[str],
    helpers_header_file: str,
    source_file_path: str,
) -> Tuple[List[str], Dict[str, str]]:
    """
    Wrap raw test function files with includes and main() for compilation.

    Args:
        test_files: Dict mapping function names to list of test file paths
        output_dir: Base output directory
        header_files: List of header file paths
        helpers_header_file: Path to helpers header file
        source_file_path: Path to source file being tested

    Returns:
        Tuple of:
        - List of wrapped test file paths ready for validation
        - Dict mapping test file path to function name
    """
    wrapped_files = []
    test_to_function_map = {}

    print(f"\n{'=' * 70}")
    print("WRAPPING TEST FILES FOR COMPILATION")
    print(f"{'=' * 70}")

    for func_name, file_paths in test_files.items():
        for test_file_path in file_paths:
            # Read the raw test function
            with open(test_file_path, "r", encoding="utf-8") as f:
                test_code = f.read()

            # Extract test name from file path
            test_name = os.path.basename(test_file_path).replace(".c", "")

            # Create complete test file
            complete_file = create_complete_test_file(
                test_code=test_code,
                function_name=func_name,
                test_name=test_name,
                header_files=header_files,
                helpers_header_file=helpers_header_file,
                source_file_path=source_file_path,
            )

            # Overwrite the file with wrapped version
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(complete_file)

            wrapped_files.append(test_file_path)
            test_to_function_map[test_file_path] = func_name

            print(f"  Wrapped: {os.path.basename(test_file_path)}")

    print(f"\nWrapped {len(wrapped_files)} test files")
    print(f"{'=' * 70}")

    return wrapped_files, test_to_function_map


def merge_monolithic_tests(
    test_files: Dict[str, List[str]],
    validation_results: Dict[str, bool],
    output_path: str,
    header_files: List[str],
    helpers_header_file: str,
) -> str:
    """
    Merge all validated monolithic test files into a single unit_test.c file.

    Args:
        test_files: Dict mapping function names to list of test file paths
        validation_results: Dictionary of validation results
        output_path: Path to save merged file
        header_files: List of header file paths
        helpers_header_file: Path to helpers header file

    Returns:
        Path to merged file
    """
    print(f"\n{'=' * 70}")
    print("MERGING MONOLITHIC TEST FILES")
    print(f"{'=' * 70}")

    # Collect all test functions and their RUN_TEST calls
    all_test_functions = []
    all_test_names = []
    uses_malloc_wrap = False  # Track if any test uses malloc_wrap

    for func_name, file_paths in test_files.items():
        for test_file_path in file_paths:
            # Skip failed validations
            test_name = os.path.basename(test_file_path).replace(".c", "")
            if not validation_results.get(test_file_path, False):
                print(f"  Skipping {test_name} (validation failed)")
                continue

            print(f"  + Including {test_name}")

            # Read the test file
            with open(test_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if this test uses malloc_wrap
            if 'malloc_wrap.h' in content or 'malloc_fail_' in content or 'malloc_reset' in content:
                uses_malloc_wrap = True

            # Extract test function (between includes and main())
            parts = content.split("int main(")

            if len(parts) >= 2:
                functions_part = parts[0]

                # Extract the test function - look for void unit_test_* or void test_*
                if "void unit_test_" in functions_part:
                    # Extract from "void unit_test_" to end of functions_part
                    func_code = "void unit_test_" + functions_part.split("void unit_test_", 1)[1]
                    func_code = func_code.rstrip()
                    all_test_functions.append(func_code)

                    # Extract function name for RUN_TEST
                    # Parse "void unit_test_something(void)" to get "unit_test_something"
                    func_name_part = func_code.split("(")[0]  # "void unit_test_something"
                    actual_func_name = func_name_part.replace("void ", "").strip()
                    all_test_names.append(actual_func_name)

                elif "void test_" in functions_part:
                    # Fallback for test_* naming
                    func_code = "void test_" + functions_part.split("void test_", 1)[1]
                    func_code = func_code.rstrip()
                    all_test_functions.append(func_code)

                    func_name_part = func_code.split("(")[0]
                    actual_func_name = func_name_part.replace("void ", "").strip()
                    all_test_names.append(actual_func_name)

    # Generate the merged file with Unity framework
    includes = []
    includes.append('#include "unity.h"')

    for header in header_files:
        header_name = os.path.basename(header)
        includes.append(f'#include "{header_name}"')

    if helpers_header_file:
        helpers_name = os.path.basename(helpers_header_file)
        includes.append(f'#include "{helpers_name}"')

    # Add malloc_wrap.h if any test uses it
    if uses_malloc_wrap:
        includes.append('#include "malloc_wrap.h"')
        print(f"  [i] Adding malloc_wrap.h (used by one or more tests)")

    includes_str = "\n".join(includes)

    # Build RUN_TEST calls
    run_test_calls = "\n".join([f"    RUN_TEST({name});" for name in all_test_names])

    # Generate tearDown - include malloc_reset() if any test uses malloc_wrap
    if uses_malloc_wrap:
        teardown_body = "malloc_reset();"
    else:
        teardown_body = ""

    merged_content = f"""{includes_str}

void setUp(void) {{ }}
void tearDown(void) {{ {teardown_body} }}

{chr(10).join(all_test_functions)}

int main(void) {{
    UNITY_BEGIN();
{run_test_calls}
    return UNITY_END();
}}
"""

    # Write merged file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(merged_content)

    print(f"\n  Merged file saved: {output_path}")
    print(f"  Total test functions: {len(all_test_names)}")
    print(f"{'=' * 70}")

    return output_path
