import os
import re
import signal
import tempfile
import subprocess
import threading
from typing import Any, Dict, List, Optional, Tuple

from apis.gpt import GPT_Connection
from apis.formats.response_format import CCodeValidationResult, SeverityLevel
from apis.prompts.test_validator_prompt import (
    c_code_validation_sys_prompt_template,
    c_code_validation_usr_prompt_template,
)


class TestValidator:
    def __init__(self):
        self.gpt_connection = GPT_Connection()

    @staticmethod
    def classify_failure(
        compile_errors: bool,
        compilation_output: str,
        run_failed: bool,
        run_output: str,
    ) -> str:
        """
        Classify the type of failure from compilation/runtime outputs.

        Returns one of: "none", "compilation", "assertion", "crash", "memory", "timeout"
        """
        if not compile_errors and not run_failed:
            return "none"

        if compile_errors:
            return "compilation"

        # Runtime failure classification
        if "Execution timed out" in run_output:
            return "timeout"

        # ASan memory errors
        if "AddressSanitizer" in run_output:
            return "memory"

        # Assertion failures
        lower_output = run_output.lower()
        if (
            "assertion failed" in lower_output
            or ("assert" in lower_output and "failed" in lower_output)
            or ("expected" in lower_output and "but got" in lower_output)
        ):
            return "assertion"

        # Signal-based crashes (segfault, abort, etc.)
        if "Segmentation fault" in run_output or "signal" in lower_output:
            return "crash"
        if "aborted" in lower_output or "SIGABRT" in run_output:
            return "crash"

        # Generic runtime failure
        return "crash"

    def _get_source_code(self, filepath: str) -> str:
        """
        Get the full source code content from a file.

        Args:
            filepath: Path to the source code file

        Returns:
            String containing the full source code content
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            return ""
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return ""

    def _get_header_definitions(self, unit_test_c_path: str) -> str:
        """
        Extract struct and type definitions from headers included in the test file.
        This helps the validator understand the correct field names for structs.

        Args:
            unit_test_c_path: Path to the unit test C file

        Returns:
            String containing relevant struct/typedef definitions
        """
        try:
            with open(unit_test_c_path, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            return "// No header definitions available"

        # Find local includes (not system includes like <stdio.h>)
        header_includes = re.findall(r'#include\s+"([^"]+\.h)"', content)

        definitions = []
        test_dir = os.path.dirname(os.path.abspath(unit_test_c_path))

        for header in header_includes:
            # Skip standard helper/test headers
            if header in ["unity.h", "helpers.h", "malloc_wrap.h"]:
                continue

            # Try to find the header file in various locations
            header_path = None
            search_dirs = [test_dir]

            # Add parent directories to search path (up to 5 levels)
            current_dir = test_dir
            for _ in range(5):
                current_dir = os.path.dirname(current_dir)
                if current_dir:
                    search_dirs.append(current_dir)
                    # Also check src subdirectory
                    src_dir = os.path.join(current_dir, "src")
                    if os.path.isdir(src_dir):
                        search_dirs.append(src_dir)

            for search_dir in search_dirs:
                candidate = os.path.join(search_dir, header)
                if os.path.exists(candidate):
                    header_path = candidate
                    break

            if header_path:
                try:
                    with open(header_path, "r", encoding="utf-8") as f:
                        header_content = f.read()

                    # Extract typedef struct definitions
                    # Pattern: typedef struct { ... } name;
                    struct_pattern = r'typedef\s+struct\s*\{[^}]+\}\s*\w+\s*;'
                    structs = re.findall(struct_pattern, header_content, re.DOTALL)

                    if structs:
                        definitions.append(f"// From {header}:")
                        for struct in structs:
                            # Clean up whitespace for readability
                            cleaned = re.sub(r'\s+', ' ', struct).strip()
                            definitions.append(cleaned)

                except Exception as e:
                    pass

        if definitions:
            return "\n".join(definitions)
        else:
            return "// No struct definitions found in headers"

    def _extract_includes_from_c_code(self, c_code: str) -> tuple[list[str], str]:
        """
        Extract #include statements from C code and return them separately.

        Args:
            c_code: Original C code with includes

        Returns:
            Tuple of (list of include lines, code without includes)
        """
        lines = c_code.split("\n")
        includes = []
        code_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#include"):
                includes.append(line)  # Keep original formatting/indentation
            else:
                code_lines.append(line)

        return includes, "\n".join(code_lines)

    def _restore_includes_to_c_code(self, includes: list[str], c_code: str) -> str:
        """
        Add #include statements back to the beginning of C code.

        Args:
            includes: List of include lines to add
            c_code: C code without includes

        Returns:
            Complete C code with includes at the top
        """
        if not includes:
            return c_code

        # Find the first non-empty, non-comment line to insert includes before
        lines = c_code.split("\n")
        insert_pos = 0

        # Skip initial empty lines and comments
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("//")
                and not stripped.startswith("/*")
            ):
                insert_pos = i
                break

        # Insert includes at the determined position
        result_lines = lines[:insert_pos] + includes + [""] + lines[insert_pos:]
        return "\n".join(result_lines)

    def _fix_c_code(
        self,
        unit_test_c_path: str,
        helpers_c_path: str,
        compilation_errors: str,
        run_output: str,
        source_file_path: str,
        temperature: float = 0.1,
    ) -> CCodeValidationResult:
        """
        Phase 2: Fix C code based on compilation errors.

        Args:
            unit_test_c_path: Path to the unit test C file
            helpers_c_path: Path to the helpers.c file
            compilation_errors: Compilation error messages
            run_output: Output from running the unit tests
            source_file_path: Path to the source file being tested (optional)
            temperature: GPT temperature setting

        Returns:
            CCodeValidationResult with validation results and corrected code if needed
        """

        # Read the unit test C code
        try:
            with open(unit_test_c_path, "r") as f:
                c_code = f.read()
        except FileNotFoundError:
            print(f"Error: Unit test file not found: {unit_test_c_path}")
            return CCodeValidationResult(
                validation_result="FAIL",
                code_issues=[],
                corrected_c_code="",
                validation_summary={
                    SeverityLevel.ERROR: f"Unit test file not found: {unit_test_c_path}"
                },
            )
        
        source_c_code = self._get_source_code(source_file_path) if source_file_path else ""

        # Get struct definitions from headers to help validator understand field names
        header_definitions = self._get_header_definitions(unit_test_c_path)

        print(f"🔍 Found compilation errors, attempting to fix...")

        # Read helpers content for the prompt
        try:
            with open(helpers_c_path, "r") as f:
                helpers_c_content = f.read()
        except FileNotFoundError:
            helpers_c_content = "// helpers.c not found"

        # Extract includes from both unit test and helpers code before sending to LLM
        # unit_test_includes, unit_test_code_no_includes = (
        #     self._extract_includes_from_c_code(c_code)
        # )
        # helpers_includes, helpers_code_no_includes = self._extract_includes_from_c_code(
        #     helpers_c_content
        # )

        # Create the prompt template for C code validation with actual errors (without includes)
        c_code_validation_usr_prompt = c_code_validation_usr_prompt_template.replace(
            "<c_code>", c_code.replace("\n", "\\n")
        )
        c_code_validation_usr_prompt = c_code_validation_usr_prompt.replace(
            "<compilation_errors>", compilation_errors.replace("\n", "\\n")
        )
        c_code_validation_usr_prompt = c_code_validation_usr_prompt.replace(
            "<run_output>", run_output.replace("\n", "\\n")
        )
        c_code_validation_usr_prompt = c_code_validation_usr_prompt.replace(
            "<header_definitions>", header_definitions.replace("\n", "\\n")
        )
        c_code_validation_usr_prompt = c_code_validation_usr_prompt.replace(
            "<helpers_c_content>", helpers_c_content.replace("\n", "\\n")
        )
        c_code_validation_usr_prompt = c_code_validation_usr_prompt.replace(
            "<source_c_code>", source_c_code.replace("\n", "\\n")
        )

        c_code_validation_sys_prompt = c_code_validation_sys_prompt_template

        validation_response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": c_code_validation_sys_prompt},
                {"role": "user", "content": c_code_validation_usr_prompt},
            ],
            temperature=temperature,
            response_model=CCodeValidationResult,
            context="c_code_validation",
        )

        # Handle case where response is a dict (partial recovery from validation failure)
        if isinstance(validation_response, dict):
            print("⚠️ Validation response returned as dict, attempting to convert")
            try:
                validation_response = CCodeValidationResult.model_validate(validation_response)
            except Exception as e:
                print(f"❌ Failed to convert dict to CCodeValidationResult: {e}")
                # Return a default failed result instead of crashing
                from apis.formats.response_format import CCodeValidationSummary
                return CCodeValidationResult(
                    explanation=f"LLM response parsing failed: {e}",
                    validation_result="FAIL",
                    code_issues=[],
                    corrected_c_code=None,
                    corrected_helpers_c_code=None,
                    validation_summary=CCodeValidationSummary(
                        summary="Failed to parse LLM response",
                        total_errors_fixed=0,
                        original_structure_preserved=False,
                        minimal_changes_applied=False,
                    ),
                )

        if validation_response is None:
            print("❌ Validation response is None, returning default failed result")
            from apis.formats.response_format import CCodeValidationSummary
            return CCodeValidationResult(
                explanation="LLM returned None response",
                validation_result="FAIL",
                code_issues=[],
                corrected_c_code=None,
                corrected_helpers_c_code=None,
                validation_summary=CCodeValidationSummary(
                    summary="LLM returned no response",
                    total_errors_fixed=0,
                    original_structure_preserved=False,
                    minimal_changes_applied=False,
                ),
            )

        # Restore includes to the corrected code if corrections were made
        # if validation_response.corrected_c_code:
        #     validation_response.corrected_c_code = self._restore_includes_to_c_code(
        #         unit_test_includes, validation_response.corrected_c_code
        #     )

        # if validation_response.corrected_helpers_c_code:
        #     validation_response.corrected_helpers_c_code = (
        #         self._restore_includes_to_c_code(
        #             helpers_includes, validation_response.corrected_helpers_c_code
        #         )
        #     )

        return validation_response

    def _try_compile_c_code_v0(
        self, unit_test_c_path: str, helpers_c_path: str, source_file_path: str = None
    ) -> tuple[SeverityLevel, str]:
        """
        Try to compile C code and return compilation severity and messages.
        Follows the same pattern as the shell script compilation.

        Args:
            unit_test_c_path: Path to the unit test C file
            helpers_c_path: Path to the actual helpers.c file
            source_file_path: Path to the source file being tested (optional)

        Returns:
            Tuple of (severity_level, compilation_output)
        """
        try:
            print("🔨 Compiling unit test (using validated C code)...")

            if os.path.exists(unit_test_c_path):
                print(f"Using unit test C file path: {unit_test_c_path}")
            else:
                print(f"❌ Error: No unit test C file found at {unit_test_c_path}")
                return SeverityLevel.ERROR, "Error: No unit test C file found"

            # Get the directory containing the main source file
            if source_file_path and os.path.exists(source_file_path):
                source_dir = os.path.dirname(source_file_path)

                # Find all .c files in the source directory
                find_cmd = ["find", source_dir, "-name", "*.c", "-type", "f"]
                find_result = subprocess.run(find_cmd, capture_output=True, text=True)

                if find_result.returncode == 0:
                    source_c_files = find_result.stdout.strip().split("\n")
                    source_c_files = [
                        f for f in source_c_files if f.strip()
                    ]  # Remove empty strings
                else:
                    source_c_files = []

                print(f"📁 Source directory: {source_dir}")
                print(f"📄 Source files: {' '.join(source_c_files)}")
            else:
                source_c_files = []
                print("No source file path provided or file doesn't exist")

            print(f"🔧 Unit test file: {unit_test_c_path}")

            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as temp_output:
                temp_output_path = temp_output.name

            # Build compilation command following the shell script pattern:
            # gcc "$UNIT_TEST_FILE" "$OUTPUT_DIR/$SUBJECT/helpers.c" $SOURCE_C_FILES -o "$OUTPUT_DIR/$SUBJECT/unit_test.o" -lm
            cmd = ["gcc", unit_test_c_path]

            # Add helpers.c if it exists
            if helpers_c_path and os.path.exists(helpers_c_path):
                cmd.append(helpers_c_path)

            # Add all source C files
            cmd.extend(source_c_files)

            # Add output path, math library, and warning flags to capture all warnings
            cmd.extend(["-o", temp_output_path, "-lm", "-Wall", "-Wextra"])

            print(f"Running compilation command: {' '.join(cmd)}")

            # Try to compile
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Clean up temp output file
            try:
                os.unlink(temp_output_path)
            except:
                pass

            # Combine stderr and stdout to capture both errors and warnings
            compilation_output = ""
            if result.stderr:
                compilation_output += result.stderr
            if result.stdout:
                compilation_output += result.stdout

            if result.returncode != 0:
                print(f"❌ Compilation failed with errors:")
                print(compilation_output)
                return SeverityLevel.ERROR, compilation_output
            elif compilation_output:
                # Compilation succeeded but has warnings
                print("⚠️  Compilation successful but with warnings:")
                print(compilation_output)
                return SeverityLevel.WARNING, compilation_output
            else:
                print("✅ Compilation successful with no errors or warnings!")
                return SeverityLevel.NOTE, ""  # No compilation errors or warnings

        except Exception as e:
            print(f"Warning: Could not attempt compilation: {e}")
            return SeverityLevel.WARNING, f"Compilation attempt failed: {str(e)}"

    def _try_compile_c_code(self, compile_command: str):
        try:
            result = subprocess.run(
                compile_command, shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Compilation successful!")
                return SeverityLevel.NOTE, ""
            else:
                print("❌ Compilation failed:")
                print(result.stderr)
                return SeverityLevel.ERROR, result.stderr
        except Exception as e:
            print(f"⚠️  Error occurred during compilation: {e}")
            return SeverityLevel.WARNING, str(e)

    def _try_run_unit_tests(self, executable_path: str) -> Tuple[bool, str]:
        """
        Try to run the compiled unit test executable and capture its output.

        Args:
            executable_path: Path to the compiled unit test executable

        Returns:
            Tuple of (success, output)
        """
        try:
            print(f"▶️  Running unit tests from executable: {executable_path}")

            if not os.path.exists(executable_path):
                print(f"❌ Error: Executable not found at {executable_path}")
                return False, "Error: Executable not found"

            result = subprocess.run(
                [executable_path], capture_output=True, text=True, timeout=10
            )

            output = result.stdout + "\n" + result.stderr

            # Check for assertion failures in output (even with returncode 0 in some cases)
            assertion_failed = (
                "Assertion failed" in output or
                "assert" in output.lower() and "failed" in output.lower() or
                "expected" in output.lower() and "but got" in output.lower()
            )

            if result.returncode == 0 and not assertion_failed:
                print("✅ Unit tests ran successfully!")
                print(output)
                return True, output
            elif assertion_failed:
                print("❌ Unit test assertion failed")
                print(output)
                return False, output
            elif result.returncode < 0:
                # Process was terminated by a signal
                sig = -result.returncode
                if sig == signal.SIGSEGV:
                    print("💥 Unit test crashed: Segmentation fault")
                elif sig == signal.SIGABRT:
                    print("💥 Unit test aborted (likely assertion failure)")
                else:
                    print(f"💥 Unit test terminated by signal {sig}")
                print(output)
                return False, output
            else:
                # Non-zero exit code, e.g., assertion failure with exit(1)
                print(f"❌ Unit tests failed with return code {result.returncode}")
                print(output)
                return False, output

        except subprocess.TimeoutExpired:
            print("❌ Error: Unit test execution timed out")
            return False, "Error: Execution timed out"
        except Exception as e:
            print(f"⚠️  Error occurred while running unit tests: {e}")
            return False, str(e)

    def validate_and_fix_c_code(
        self,
        unit_test_c_path: str,
        validated_c_path: str,
        helpers_c_path: str,
        function_files_dir: str = None,
        function_name: str = None,
        compile_command: str = None,
        temperature: float = 0.1,
        max_iterations: int = 1,
        helpers_lock: Optional[threading.Lock] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Validate and iteratively fix C unit test code until it compiles.

        Args:
            unit_test_c_path: Path to the unit test C file
            validated_c_path: Path to write the validated C file
            helpers_c_path: Path to helpers.c file
            function_files_dir: Path to directory containing per-function C files (e.g., tmp/function-files)
            function_name: Name of the function being tested (optional, used to find function file)
            compile_command: Compilation command for the C source file
            temperature: GPT temperature setting
            max_iterations: Maximum number of fix iterations
            helpers_lock: Optional threading lock for serializing writes to helpers.c during parallel validation

        Returns:
            Tuple of (final_c_code, validation_results)
        """

        all_validation_results = []
        iteration = 0

        print("🔍 Validating generated C unit test code...")

        # Determine the function-specific source file for context
        function_file_path = None
        if function_files_dir:
            # Use provided function_name, or try to extract from filename
            if not function_name:
                # Try to extract function name from unit_test_c_path (e.g., unit_test_partition.c -> partition)
                unit_test_filename = os.path.basename(unit_test_c_path)
                if unit_test_filename.startswith("unit_test_") and unit_test_filename.endswith(".c"):
                    function_name = unit_test_filename[len("unit_test_"):-len(".c")]

            if function_name:
                candidate_path = os.path.join(function_files_dir, f"{function_name}.c")
                if os.path.exists(candidate_path):
                    function_file_path = candidate_path
                    print(f"📄 Using function file: {function_file_path}")
                else:
                    print(f"⚠️  Function file not found: {candidate_path}")

        final_unit_test_c_path = unit_test_c_path
        severity_level, compilation_output = self._try_compile_c_code(
            compile_command=compile_command
        )
        executable_path = unit_test_c_path.split(".c")[0]
        run_success, run_output = self._try_run_unit_tests(executable_path)

        # Check if there are actual errors that prevent compilation (not just warnings)
        compile_errors = (
            severity_level == SeverityLevel.ERROR
            or severity_level == SeverityLevel.WARNING
        )
        run_failed = not run_success

        # Classify the initial failure type (before any fix iteration)
        initial_failure_type = self.classify_failure(
            compile_errors, compilation_output, run_failed, run_output
        )
        # Track failure type at each iteration
        iteration_failure_types = []

        while iteration < max_iterations and (compile_errors or run_failed):
            if compile_errors:
                print(f"Code has compilation errors: {compilation_output}")
            if run_failed:
                print(f"Unit tests failed to run: {run_output}")
            iteration += 1
            print(f"Try to fix the code...\nIteration {iteration}/{max_iterations}")

            # Validate current code
            validation_result = self._fix_c_code(
                final_unit_test_c_path,
                helpers_c_path,
                compilation_output,
                run_output,
                function_file_path,
                temperature,
            )

            all_validation_results.append(validation_result)

            # Apply corrections if available
            corrections_applied = False

            print(f"Explanation: {validation_result.explanation}")

            if validation_result.corrected_c_code:
                print(f"🔧 Applying fixes to unit test file...")

                # Write the corrected unit test code to the validated file
                try:
                    with open(validated_c_path, "w") as f:
                        f.write(validation_result.corrected_c_code)
                    print(f"Updated validated unit test file: {validated_c_path}")
                    final_unit_test_c_path = validated_c_path
                    corrections_applied = True
                except Exception as e:
                    print(f"Error writing corrected unit test code to file: {e}")
                    break

            if validation_result.corrected_helpers_c_code:
                print(f"🔧 Applying fixes to helpers file...")

                # Write the corrected helpers code back to the file
                # Use lock if provided to prevent race conditions during parallel validation
                try:
                    if helpers_lock:
                        with helpers_lock:
                            with open(helpers_c_path, "w") as f:
                                f.write(validation_result.corrected_helpers_c_code)
                    else:
                        with open(helpers_c_path, "w") as f:
                            f.write(validation_result.corrected_helpers_c_code)
                    print(f"Updated helpers file: {helpers_c_path}")
                    corrections_applied = True
                except Exception as e:
                    print(f"Error writing corrected helpers code to file: {e}")
                    break

            if corrections_applied:
                # Print issues found
                for issue in validation_result.code_issues:
                    file_type = (
                        "helpers.c"
                        if hasattr(issue, "file_source")
                        and issue.file_source == "helpers"
                        else "unit test"
                    )
                    severity = getattr(issue, "severity", SeverityLevel.ERROR)
                    severity_icon = (
                        "🚨"
                        if severity == SeverityLevel.ERROR
                        else "⚠️ " if severity == SeverityLevel.WARNING else "[i] "
                    )
                    print(
                        f"  - {severity_icon} Fixed {issue.issue_type} ({severity}) in {file_type}: {issue.description}"
                    )

                # After applying corrections, check if compilation passes
                severity_level, compilation_output = self._try_compile_c_code(
                    compile_command=compile_command
                )
                run_success, run_output = self._try_run_unit_tests(executable_path)
                compile_errors = (
                    severity_level == SeverityLevel.ERROR
                    or severity_level == SeverityLevel.WARNING
                )
                run_failed = not run_success

                # Track status after this iteration
                iter_failure = self.classify_failure(
                    compile_errors, compilation_output, run_failed, run_output
                )
                iteration_failure_types.append(iter_failure)
            else:
                print("❌ No corrections provided, stopping validation.")
                break

        # Read the final code from file
        try:
            with open(final_unit_test_c_path, "r") as f:
                final_c_code = f.read()
        except:
            final_c_code = ""

        # Check final compilation status based on severity level
        final_compilation_passed = severity_level != SeverityLevel.ERROR

        # Check final runtime test status
        final_runtime_passed = run_success

        # Final validation summary
        final_validation = (
            all_validation_results[-1] if all_validation_results else None
        )

        # Overall pass requires BOTH compilation and runtime success
        final_overall_passed = final_compilation_passed and final_runtime_passed

        if final_overall_passed:
            print("🎉 Final C code compiled and all tests passed!")
            if severity_level == SeverityLevel.WARNING:
                print(
                    f"Note: Compilation has warnings but no errors: {compilation_output}"
                )
        elif final_compilation_passed and not final_runtime_passed:
            print("⚠️  C code compiles but unit tests failed at runtime after maximum iterations.")
            if run_output:
                print(f"Final runtime errors: {run_output[:500]}")
        else:
            print("⚠️  C code still has compilation issues after maximum iterations.")
            if compilation_output:
                print(f"Final compilation errors: {compilation_output}")

        return final_c_code, {
            "final_validation": final_validation,
            "all_iterations": all_validation_results,
            "total_iterations": len(all_validation_results),
            "final_status": "PASS" if final_overall_passed else "FAIL",
            "final_compilation_output": compilation_output,
            "final_runtime_output": run_output,
            "compilation_passed": final_compilation_passed,
            "runtime_passed": final_runtime_passed,
            "initial_failure_type": initial_failure_type,
            "iteration_failure_types": iteration_failure_types,
        }
