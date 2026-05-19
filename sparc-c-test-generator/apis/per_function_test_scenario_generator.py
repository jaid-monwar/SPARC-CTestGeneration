#!/usr/bin/env python3
"""
Per-Test-Case Test Generator
Generates, validates, and merges unit tests on a per-test-case basis.

This script:
1. Generates per-function complex_test_scenarios_{function}.json files
2. Generates individual unit test files for EACH test case (e.g., unit_test_swap_same_pointer.c)
3. Validates each test case file independently (max 3 iterations)
4. Merges all validated unit tests into final unit_test.c
"""

import os
import sys
import json
import argparse
import threading
from typing import List, Dict, Optional, Tuple
# Note: Parallel processing disabled to avoid race conditions when fixing helpers.c
# from concurrent.futures import ThreadPoolExecutor, as_completed
from apis.c_unit_test_generator import generate_single_test_c_code
from apis.agents.test_specification_generator import TestSpecificationGenerator


def generate_per_test_case_unit_tests(
    complex_scenarios_files: List[str],
    header_files: List[str],
    helpers_header_file: str,
    output_dir: str,
    source_file_path: str,
) -> Tuple[List[str], Dict[str, str]]:
    """
    Generate individual unit test C files for EACH test case.

    Args:
        complex_scenarios_files: List of per-function complex test scenario JSON files
        header_files: List of header file paths
        helpers_header_file: Path to helpers header file
        output_dir: Directory to save unit test files
        source_file_path: Path to source file being tested

    Returns:
        Tuple of:
        - List of generated unit test file paths
        - Dict mapping test file path to function name (for function-files lookup)
    """
    generated_files = []
    test_to_function_map = {}  # Maps test file path to function name
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print("GENERATING PER-TEST-CASE UNIT TESTS")
    print(f"{'='*60}")

    total_tests = 0
    for complex_file in complex_scenarios_files:
        # Extract function name from filename
        filename = os.path.basename(complex_file)
        function_name = filename.replace("complex_test_scenarios_", "").replace(".json", "")

        # Load complex test scenarios
        with open(complex_file, "r") as f:
            complex_test_data = json.load(f)

        operation_map = complex_test_data.get("operation_map", {})
        test_scenarios = complex_test_data.get("test_scenarios", [])
        num_tests = len(test_scenarios)
        total_tests += num_tests

        print(f"\n📦 Function: {function_name} ({num_tests} test cases)")

        for i, test_scenario in enumerate(test_scenarios):
            test_name = test_scenario.get("test_name", f"test_{i}")

            # Generate output path using the test_name directly
            # test_name already includes function name (e.g., unit_test_swap_same_pointer)
            output_path = os.path.join(output_dir, f"{test_name}.c")

            # Generate C test code for this single test case
            generated_c_code = generate_single_test_c_code(
                test_scenario,
                operation_map,
                source_file_path,
                header_files,
                helpers_header_file,
                output_path,
            )

            if generated_c_code:
                # Write to file
                with open(output_path, "w") as f:
                    f.write(generated_c_code)

                generated_files.append(output_path)
                test_to_function_map[output_path] = function_name
                print(f"  [{i+1}/{num_tests}] ✓ {test_name}.c")
            else:
                print(f"  [{i+1}/{num_tests}] ✗ Failed to generate {test_name}.c")

    print(f"\n{'='*60}")
    print(f"✓ Generated {len(generated_files)}/{total_tests} unit test files")
    print(f"{'='*60}")

    return generated_files, test_to_function_map


# Keep old function for backward compatibility
def generate_per_function_unit_tests(
    complex_scenarios_files: List[str],
    header_files: List[str],
    helpers_header_file: str,
    output_dir: str,
    source_file_path: str,
) -> List[str]:
    """
    Generate individual unit test C files for each function (LEGACY - per function).
    Use generate_per_test_case_unit_tests() for per-test-case generation.
    """
    generated_files, _ = generate_per_test_case_unit_tests(
        complex_scenarios_files,
        header_files,
        helpers_header_file,
        output_dir,
        source_file_path,
    )
    return generated_files


def _validate_single_unit_test(
    unit_test_path: str,
    helpers_c_path: str,
    function_files_dir: str,
    function_name: str,
    compile_command_template: str,
    max_iterations: int,
    test_generator: TestSpecificationGenerator,
    helpers_lock: Optional[threading.Lock] = None,
) -> tuple[str, bool, str, dict]:
    """
    Validate a single unit test file.

    Args:
        unit_test_path: Path to unit test file
        helpers_c_path: Path to helpers.c file
        function_files_dir: Path to directory containing per-function C files
        function_name: Name of the function being tested (for function-files lookup)
        compile_command_template: Template for compilation command
        max_iterations: Maximum validation iterations
        test_generator: TestSpecificationGenerator instance
        helpers_lock: Optional threading lock for serializing writes to helpers.c

    Returns:
        Tuple of (unit_test_path, success, error_message, validation_info)
    """
    test_name = os.path.basename(unit_test_path).replace(".c", "")

    print(f"🔍 Validating: {test_name}")
    print(f"   Function: {function_name} | File: {unit_test_path}")

    # Build compile command for this specific unit test
    compile_command = compile_command_template.replace("{unit_test_file}", unit_test_path)

    # Replace output executable name (in same directory as unit test)
    output_dir = os.path.dirname(unit_test_path)
    output_executable = os.path.join(output_dir, test_name)
    compile_command = compile_command.replace("{unit_test_executable}", output_executable)

    # Validate and fix the unit test
    try:
        validated_c_code, validation_info = (
            test_generator.test_validator.validate_and_fix_c_code(
                unit_test_c_path=unit_test_path,
                validated_c_path=unit_test_path,  # Overwrite original
                helpers_c_path=helpers_c_path,
                function_files_dir=function_files_dir,
                function_name=function_name,
                compile_command=compile_command,
                temperature=0.0,
                max_iterations=max_iterations,
                helpers_lock=helpers_lock,
            )
        )

        final_status = validation_info.get("final_status", "UNKNOWN")
        iterations = validation_info.get("total_iterations", 0)

        if final_status == "PASS":
            print(f"   ✓ {test_name}: Validation PASSED after {iterations} iteration(s)")
            return unit_test_path, True, "", validation_info
        else:
            final_errors = validation_info.get("final_compilation_output", "")
            error_msg = final_errors[:500] if final_errors else "Unknown error"
            print(f"   ✗ {test_name}: Validation FAILED after {iterations} iteration(s)")
            return unit_test_path, False, error_msg, validation_info

    except Exception as e:
        print(f"   ✗ {test_name}: Validation error: {e}")
        return unit_test_path, False, str(e), {
            "total_iterations": 0,
            "final_status": "FAIL",
            "initial_failure_type": "compilation",
            "iteration_failure_types": [],
        }


def validate_per_test_case_unit_tests(
    unit_test_files: List[str],
    test_to_function_map: Dict[str, str],
    helpers_c_path: str,
    function_files_dir: str,
    compile_command_template: str,
    max_iterations: int = 3,
    max_workers: int = 10,  # noqa: ARG001 - Kept for API compatibility, but ignored
) -> Dict[str, bool]:
    """
    Validate each unit test file independently with sequential processing.

    Note: Validation is done sequentially to avoid race conditions when multiple
    LLM calls try to fix helpers.c simultaneously. The max_workers parameter is
    kept for API compatibility but is ignored.

    Args:
        unit_test_files: List of unit test file paths
        test_to_function_map: Dict mapping test file path to function name
        helpers_c_path: Path to helpers.c file
        function_files_dir: Path to directory containing per-function C files
        compile_command_template: Template for compilation command
        max_iterations: Maximum validation iterations per file
        max_workers: Ignored (kept for API compatibility)

    Returns:
        Dictionary mapping file paths to validation success status
    """
    validation_results = {}
    validation_details = {}  # Stores full validation_info per test
    test_generator = TestSpecificationGenerator()

    total_tests = len(unit_test_files)

    print(f"\n{'='*60}")
    print("VALIDATING PER-TEST-CASE UNIT TESTS")
    print(f"{'='*60}")
    print(f"🔄 Sequential mode: Validating {total_tests} unit tests one at a time")
    print(f"📝 This avoids race conditions when fixing helpers.c")
    print()

    # Process unit tests sequentially
    for idx, unit_test_path in enumerate(unit_test_files):
        test_name = os.path.basename(unit_test_path).replace(".c", "")
        function_name = test_to_function_map.get(unit_test_path, "unknown")

        print(f"🔍 [{idx + 1}/{total_tests}] Validating: {test_name}")
        print(f"   Function: {function_name}")

        try:
            _, success, error_msg, validation_info = _validate_single_unit_test(
                unit_test_path=unit_test_path,
                helpers_c_path=helpers_c_path,
                function_files_dir=function_files_dir,
                function_name=function_name,
                compile_command_template=compile_command_template,
                max_iterations=max_iterations,
                test_generator=test_generator,
                helpers_lock=None,  # No lock needed for sequential processing
            )
            validation_results[unit_test_path] = success
            validation_details[unit_test_path] = validation_info

            status_icon = "✅" if success else "❌"
            print(f"   {status_icon} {test_name} {'passed' if success else 'failed'}")

            if not success and error_msg:
                print(f"       Error: {error_msg[:200]}...")

        except Exception as exc:
            print(f"   ❌ {test_name} generated an exception: {exc}")
            validation_results[unit_test_path] = False
            validation_details[unit_test_path] = {
                "total_iterations": 0,
                "final_status": "FAIL",
                "initial_failure_type": "compilation",
                "iteration_failure_types": [],
            }

        print()

    # --- Collect detailed metrics ---
    total_before_validation = total_tests
    total_passed = sum(1 for v in validation_results.values() if v)
    total_failed = total_before_validation - total_passed

    # Tests that needed repair = had initial failure (initial_failure_type != "none")
    tests_needed_repair = 0
    tests_repaired_successfully = 0
    fixed_after_iteration = {}  # iteration_number -> count
    fixed_failure_types = {"compilation": 0, "assertion": 0, "crash": 0, "memory": 0, "timeout": 0}

    for path, info in validation_details.items():
        initial_failure = info.get("initial_failure_type", "none")
        total_iterations = info.get("total_iterations", 0)
        final_status = info.get("final_status", "FAIL")

        if initial_failure != "none":
            tests_needed_repair += 1

            if final_status == "PASS":
                tests_repaired_successfully += 1
                # Which iteration fixed it?
                fixed_after_iteration[total_iterations] = fixed_after_iteration.get(total_iterations, 0) + 1
                # Track the initial failure type that was repaired
                if initial_failure in fixed_failure_types:
                    fixed_failure_types[initial_failure] += 1

    # Tests that passed without any iteration (compiled and ran on first try)
    tests_passed_initially = total_passed - tests_repaired_successfully

    # --- Print detailed metrics ---
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"  Total tests generated (before validation):     {total_before_validation}")
    print(f"  Tests passed initially (no repair needed):     {tests_passed_initially}")
    print(f"  Tests that required repair:                    {tests_needed_repair}")
    print(f"  Tests repaired successfully:                   {tests_repaired_successfully}")
    print(f"  Tests added to final unit_test.c:              {total_passed}")
    print(f"  Tests dropped (validation failed):             {total_failed}")
    print()
    print("  Repair iterations breakdown:")
    max_iter = max(fixed_after_iteration.keys()) if fixed_after_iteration else 0
    for i in range(1, max(max_iter + 1, max_iterations + 1)):
        count = fixed_after_iteration.get(i, 0)
        print(f"    Fixed after iteration {i}:                    {count}")
    print()
    print("  Repaired failure types:")
    for ftype, count in fixed_failure_types.items():
        print(f"    {ftype:.<40s} {count}")
    print(f"{'='*60}")

    # --- Save metrics to validation_metrics.json ---
    # Determine output path from the first test file path
    if unit_test_files:
        # Navigate up from monolithic/tests/<func>/file.c to project dir
        sample_path = unit_test_files[0]
        # Find the project output dir (contains monolithic/ or is the parent of test files)
        output_dir = sample_path
        for _ in range(5):  # Walk up to find the project dir
            output_dir = os.path.dirname(output_dir)
            if os.path.exists(os.path.join(output_dir, "source_functions.json")):
                break

        metrics = {
            "total_tests_before_validation": total_before_validation,
            "total_tests_in_final_unit_test": total_passed,
            "tests_passed_initially": tests_passed_initially,
            "tests_needed_repair": tests_needed_repair,
            "tests_repaired_successfully": tests_repaired_successfully,
            "tests_dropped": total_failed,
            "fixed_after_iteration": {str(k): v for k, v in sorted(fixed_after_iteration.items())},
            "max_iterations_configured": max_iterations,
            "repaired_failure_types": fixed_failure_types,
            "per_test_details": {},
        }

        # Per-test detail (serializable subset)
        for path, info in validation_details.items():
            test_name = os.path.basename(path).replace(".c", "")
            metrics["per_test_details"][test_name] = {
                "passed": validation_results.get(path, False),
                "total_iterations": info.get("total_iterations", 0),
                "initial_failure_type": info.get("initial_failure_type", "none"),
                "final_status": info.get("final_status", "FAIL"),
            }

        metrics_path = os.path.join(output_dir, "validation_metrics.json")
        try:
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)
            print(f"\n  Validation metrics saved to: {metrics_path}")
        except Exception as e:
            print(f"\n  Warning: Could not save validation metrics: {e}")

    return validation_results


# Backward-compatible alias
def validate_per_function_unit_tests(
    unit_test_files: List[str],
    helpers_c_path: str,
    function_files_dir: str,
    compile_command_template: str,
    max_iterations: int = 3,
    max_workers: int = 10,
) -> Dict[str, bool]:
    """
    Validate each unit test file independently (LEGACY - assumes per-function naming).
    Use validate_per_test_case_unit_tests() for per-test-case validation with function mapping.
    """
    # Build a simple test_to_function_map by extracting function name from filename
    # This assumes old naming convention: unit_test_<function>.c
    test_to_function_map = {}
    for unit_test_path in unit_test_files:
        filename = os.path.basename(unit_test_path)
        if filename.startswith("unit_test_") and filename.endswith(".c"):
            function_name = filename[len("unit_test_"):-len(".c")]
            test_to_function_map[unit_test_path] = function_name

    return validate_per_test_case_unit_tests(
        unit_test_files=unit_test_files,
        test_to_function_map=test_to_function_map,
        helpers_c_path=helpers_c_path,
        function_files_dir=function_files_dir,
        compile_command_template=compile_command_template,
        max_iterations=max_iterations,
        max_workers=max_workers,
    )


def merge_unit_test_files(
    unit_test_files: List[str],
    validation_results: Dict[str, bool],
    output_path: str,
    header_files: List[str],
    helpers_header_file: str,
) -> str:
    """
    Merge all validated unit test files into a single unit_test.c file.

    Args:
        unit_test_files: List of unit test file paths
        validation_results: Dictionary of validation results
        output_path: Path to save merged file
        header_files: List of header file paths
        helpers_header_file: Path to helpers header file

    Returns:
        Path to merged file
    """
    print(f"\n{'='*60}")
    print("MERGING UNIT TEST FILES")
    print(f"{'='*60}")

    # Collect all test functions and their calls
    all_test_functions = []
    all_test_calls = []

    for unit_test_path in unit_test_files:
        # Skip failed validations
        test_name = os.path.basename(unit_test_path).replace(".c", "")
        if not validation_results.get(unit_test_path, False):
            print(f"  ⚠ Skipping {test_name} (validation failed)")
            continue

        print(f"  + Including {test_name}")

        # Read the unit test file
        with open(unit_test_path, "r") as f:
            content = f.read()

        # Extract test functions (everything between includes and main())
        # Split by "int main()" to separate functions from main
        parts = content.split("int main()")

        if len(parts) >= 2:
            # Get the function definitions part (before main)
            functions_part = parts[0]

            # Remove the header section (everything before the first "void unit_test_")
            if "void unit_test_" in functions_part:
                functions_part = "void unit_test_" + functions_part.split("void unit_test_", 1)[1]
                all_test_functions.append(functions_part.rstrip())

            # Extract test function calls from main()
            main_part = parts[1]
            # Find function calls (lines with "unit_test_" followed by "();")
            import re
            calls = re.findall(r'^\s+(unit_test_\w+\(\);)', main_part, re.MULTILINE)
            all_test_calls.extend(calls)

    # Generate the merged file header
    from apis.c_unit_test_generator import create_c_test_header, extract_globals, generate_externs

    merged_content = create_c_test_header(
        header_files,
        helpers_header_file,
        output_path
    )

    # Add extern declarations
    merged_content += "\n"
    # Use first successful unit test file's source to extract globals
    source_file_path = None
    for unit_test_path in unit_test_files:
        if validation_results.get(unit_test_path, False):
            # Extract source path from complex scenarios
            break

    if source_file_path and os.path.exists(source_file_path):
        globals_info = extract_globals(source_file_path)
        extern_code = generate_externs(globals_info)
        merged_content += extern_code

    merged_content += "\n"

    # Add all test functions
    merged_content += "\n".join(all_test_functions)
    merged_content += "\n\n"

    # Add main function
    merged_content += "int main() {\n"
    merged_content += "    printf(\"Starting all generated unit tests...\\n\\n\");\n"
    for call in all_test_calls:
        merged_content += f"    {call}\n"
    merged_content += "    printf(\"All generated tests completed successfully!\\n\");\n"
    merged_content += "    return 0;\n"
    merged_content += "}\n"

    # Write merged file
    with open(output_path, "w") as f:
        f.write(merged_content)

    print(f"\n  ✓ Merged file saved: {output_path}")
    print(f"  ✓ Total test functions: {len(all_test_calls)}")
    print(f"{'='*60}")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate, validate, and merge per-function unit tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("source_filepath", help="Path to the C source file")
    parser.add_argument("--test_scenarios_dir", required=True, help="Directory containing test_scenarios JSON files")
    parser.add_argument("--operation_map", required=True, help="Path to operation_map.json")
    parser.add_argument("--header_filepath", action="append", required=True, help="Path to header file (can specify multiple)")
    parser.add_argument("--helpers_header", required=True, help="Path to helpers.h file")
    parser.add_argument("--helpers_c", required=True, help="Path to helpers.c file")
    parser.add_argument("--output_dir", required=True, help="Output directory for all generated files")
    parser.add_argument("--subject_name", default="subject", help="Name of the subject being tested")
    parser.add_argument("--compile_command", required=True, help="Template for compilation command")
    parser.add_argument("--max_iterations", type=int, default=3, help="Maximum validation iterations per file")
    parser.add_argument("--function_files_dir", default="tmp/function-files", help="Directory containing per-function C files (default: tmp/function-files)")

    args = parser.parse_args()

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories
    complex_scenarios_dir = os.path.join(output_dir, "complex_test_scenarios_per_function")
    unit_tests_dir = os.path.join(output_dir, "unit_tests")

    print(f"\n{'='*60}")
    print("PER-TEST-CASE TEST GENERATION PIPELINE")
    print(f"{'='*60}")
    print(f"Source file: {args.source_filepath}")
    print(f"Test scenarios: {args.test_scenarios_dir}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")

    # Initialize test generator
    test_generator = TestSpecificationGenerator()

    # (Processing) Generate per-function complex test scenarios
    print(f"\n{'='*60}")
    print("(Processing) GENERATE PER-FUNCTION COMPLEX TEST SCENARIOS")
    print(f"{'='*60}")

    complex_files = test_generator.test_scenario_manager.generate_per_function_complex_test_scenarios(
        test_scenarios_dir=args.test_scenarios_dir,
        operation_map_path=args.operation_map,
        output_dir=complex_scenarios_dir,
        subject_name=args.subject_name,
        source_file_path=args.source_filepath,
        helpers_c_path=args.helpers_c,
    )

    if not complex_files:
        print("✗ No complex test scenario files generated. Exiting.")
        return 1

    # (Processing) Generate per-test-case C unit tests
    print(f"\n{'='*60}")
    print("(Processing) GENERATE PER-TEST-CASE C UNIT TESTS")
    print(f"{'='*60}")

    unit_test_files, test_to_function_map = generate_per_test_case_unit_tests(
        complex_scenarios_files=complex_files,
        header_files=args.header_filepath,
        helpers_header_file=args.helpers_header,
        output_dir=unit_tests_dir,
        source_file_path=args.source_filepath,
    )

    # Step 4c: Validate each unit test
    print(f"\n{'='*60}")
    print("STEP 4c: VALIDATE PER-TEST-CASE UNIT TESTS")
    print(f"{'='*60}")

    validation_results = validate_per_test_case_unit_tests(
        unit_test_files=unit_test_files,
        test_to_function_map=test_to_function_map,
        helpers_c_path=args.helpers_c,
        function_files_dir=args.function_files_dir,
        compile_command_template=args.compile_command,
        max_iterations=args.max_iterations,
    )

    # Step 4d: Merge validated unit tests
    print(f"\n{'='*60}")
    print("STEP 4d: MERGE VALIDATED UNIT TESTS")
    print(f"{'='*60}")

    final_unit_test = merge_unit_test_files(
        unit_test_files=unit_test_files,
        validation_results=validation_results,
        output_path=os.path.join(output_dir, "unit_test.c"),
        header_files=args.header_filepath,
        helpers_header_file=args.helpers_header,
    )

    print(f"\n{'='*60}")
    print("✓ PER-TEST-CASE TEST GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Final unit test: {final_unit_test}")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
