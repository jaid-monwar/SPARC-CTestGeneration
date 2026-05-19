"""
Phase 2: Test Coder Manager

Generates concrete C test code based on:
- Test designs from Phase 1
- Function source code from function files (minimal: target + dependency signatures)
- Operation map with helper function signatures
- Execution paths
"""

import os
import json
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from apis.gpt import GPT_Connection
from apis.formats.response_format import TestScenarios
from apis.prompts.test_coder_prompt import (
    test_coder_sys_prompt,
    test_coder_usr_prompt_template,
)


class TestCoderManager:
    """Manages Phase 2: Test Code generation"""

    def __init__(self):
        self.gpt_connection = GPT_Connection()

    def _read_function_file(self, function_name: str, function_files_dir: str = "tmp/function-files") -> str:
        """
        Read the source code for a function from function files.

        Function files contain target function implementation + dependency signatures only
        (more efficient than atomic files which include full dependency implementations).

        Args:
            function_name: Name of the function
            function_files_dir: Directory containing minimal function C files

        Returns:
            Source code as string
        """
        function_file_path = os.path.join(function_files_dir, f"{function_name}.c")

        if not os.path.exists(function_file_path):
            print(f"⚠️  Warning: Function file not found: {function_file_path}")
            return f"// Source code for {function_name} not found"

        try:
            with open(function_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"⚠️  Error reading function file {function_file_path}: {e}")
            return f"// Error reading source code for {function_name}"

    def generate_test_code_for_single_scenario(
        self,
        function_name: str,
        function_signature: str,
        function_source_code: str,
        single_test_design: Dict[str, Any],
        execution_path: Dict[str, Any],
        operation_map_json: str,
        temperature: float = 0.0,
    ) -> TestScenarios:
        """
        Generate C test code for a single test scenario.

        Args:
            function_name: Name of the function
            function_signature: Function signature string
            function_source_code: Source code of the function
            single_test_design: Single test design object (one element from test_scenarios array)
            execution_path: Single execution path for this test scenario
            operation_map_json: JSON string of operation map
            temperature: GPT temperature

        Returns:
            TestScenarios object with single generated test scenario
        """
        # Format single execution path
        path_id = execution_path.get("path_id", "P1")
        path_description = execution_path.get("path", "")
        path_text = f"Path {path_id}: {path_description}"

        # Wrap single test design in the expected format
        single_design_data = {
            "test_scenarios": [single_test_design]
        }
        test_designs_json = json.dumps(single_design_data, indent=2)

        # Create the prompt
        usr_prompt = test_coder_usr_prompt_template.replace(
            "<function_name>", function_name
        )
        usr_prompt = usr_prompt.replace("<function_signature>", function_signature)
        usr_prompt = usr_prompt.replace(
            "<function_source_code>", function_source_code.replace("\n", "\\n")
        )
        usr_prompt = usr_prompt.replace(
            "<test_designs_json>", test_designs_json.replace("\n", "\\n")
        )
        usr_prompt = usr_prompt.replace("<execution_path>", path_text)
        usr_prompt = usr_prompt.replace(
            "<operation_map_json>", operation_map_json.replace("\n", "\\n")
        )

        # Call GPT to generate test code for this single scenario
        test_scenarios_response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": test_coder_sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            temperature=temperature,
            response_model=TestScenarios,
            context=f"test_coder_{function_name}_single",
            max_tokens=8192,
        )

        return test_scenarios_response

    def generate_test_code_for_function(
        self,
        function_name: str,
        function_info: Dict[str, Any],
        test_designs_path: str,
        operation_map_json: str,
        function_files_dir: str = "tmp/function-files",
        temperature: float = 0.0,
        output_path: str = None,
    ) -> TestScenarios:
        """
        Generate C test code for a function based on test designs.
        Processes each test scenario individually with progress indication.

        Args:
            function_name: Name of the function
            function_info: Dictionary containing function metadata from source_functions.json
            test_designs_path: Path to test designs JSON file from Phase 1
            operation_map_json: JSON string of operation map
            function_files_dir: Directory containing minimal function C files
            temperature: GPT temperature
            output_path: Path to save test scenarios incrementally (optional)

        Returns:
            TestScenarios object with all generated C test code
        """
        # Load test designs
        try:
            with open(test_designs_path, "r", encoding="utf-8") as f:
                test_designs_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: Test designs file not found: {test_designs_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in test designs file: {e}")
            raise

        # Extract test scenarios array
        test_design_scenarios = test_designs_data.get("test_scenarios", [])
        total_scenarios = len(test_design_scenarios)

        if total_scenarios == 0:
            print(f"⚠️  Warning: No test scenarios found in {test_designs_path}")
            return TestScenarios(test_scenarios=[])

        print(f"💻 Generating C test code for function: {function_name} ({total_scenarios} scenarios)")

        # Read function source code from function files (minimal: target + signatures)
        function_source_code = self._read_function_file(function_name, function_files_dir)

        # Extract function information
        function_signature = function_info.get("signature", "")

        # Accumulate all generated test scenarios
        all_generated_scenarios = []

        # Process each test scenario individually
        for idx, single_design in enumerate(test_design_scenarios, 1):
            test_name = single_design.get("test_metadata", {}).get("test_name", f"test_{idx}")
            print(f"  [{idx}/{total_scenarios}] Processing: {test_name}")

            # Extract execution_path from the test design (injected by Test Designer)
            execution_path = single_design.get("execution_path", {})
            if not execution_path:
                # Fallback: try to get path from path_coverage if execution_path not found
                path_coverage = single_design.get("path_coverage", {})
                target_paths = path_coverage.get("target_paths", [])
                if target_paths:
                    execution_path = {"path_id": target_paths[0], "path": ""}
                else:
                    execution_path = {"path_id": f"P{idx}", "path": ""}

            try:
                # Generate code for this single test scenario
                single_scenario_response = self.generate_test_code_for_single_scenario(
                    function_name=function_name,
                    function_signature=function_signature,
                    function_source_code=function_source_code,
                    single_test_design=single_design,
                    execution_path=execution_path,
                    operation_map_json=operation_map_json,
                    temperature=temperature,
                )

                # Extract generated scenarios (should be 1, but handle multiple)
                generated_scenarios = single_scenario_response.test_scenarios
                if generated_scenarios:
                    all_generated_scenarios.extend(generated_scenarios)
                    print(f"  ✅ [{idx}/{total_scenarios}] Generated test code for: {test_name}")

                    # Save incrementally if output path provided
                    if output_path:
                        self._save_incremental(all_generated_scenarios, output_path)
                else:
                    print(f"  ⚠️  [{idx}/{total_scenarios}] No test code generated for: {test_name}")

            except Exception as e:
                print(f"  ❌ [{idx}/{total_scenarios}] Failed to generate test code for: {test_name}")
                print(f"     Error: {e}")
                # Skip this scenario and continue with the next one
                continue

        print(f"✅ Generated {len(all_generated_scenarios)}/{total_scenarios} test scenarios for {function_name}")

        # Return all accumulated scenarios
        return TestScenarios(test_scenarios=all_generated_scenarios)

    def _save_incremental(self, test_scenarios_list: List[Any], output_path: str) -> None:
        """
        Save test scenarios incrementally to avoid data loss.

        Args:
            test_scenarios_list: List of TestScenario objects
            output_path: Path to save the JSON file
        """
        # Convert to dictionary format
        scenarios_data = {"test_scenarios": []}

        for scenario in test_scenarios_list:
            scenario_dict = {
                "test_name": scenario.test_name,
                "setup": [],
                "steps": [],
                "cleanup": [],
            }

            # Convert setup steps
            for step in scenario.setup:
                step_dict = {
                    "op": step.op,
                    "variable_declarations": self._convert_variable_declarations_to_dict(
                        step.variable_declarations
                    ),
                    "input_params": step.input_params,
                    "return_params": step.return_params,
                }
                scenario_dict["setup"].append(step_dict)

            # Convert main steps
            for step in scenario.steps:
                step_dict = {
                    "op": step.op,
                    "variable_declarations": self._convert_variable_declarations_to_dict(
                        step.variable_declarations
                    ),
                    "input_params": step.input_params,
                    "return_params": step.return_params,
                }
                scenario_dict["steps"].append(step_dict)

            # Convert cleanup steps
            for step in scenario.cleanup:
                step_dict = {
                    "op": step.op,
                    "variable_declarations": self._convert_variable_declarations_to_dict(
                        step.variable_declarations
                    ),
                    "input_params": step.input_params,
                    "return_params": step.return_params,
                }
                scenario_dict["cleanup"].append(step_dict)

            scenarios_data["test_scenarios"].append(scenario_dict)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scenarios_data, f, indent=2, ensure_ascii=False)

    def _convert_variable_declarations_to_dict(self, variable_declarations) -> List[Dict[str, Any]]:
        """Convert VariableDeclaration objects to dictionary format."""
        if not variable_declarations:
            return []

        result = []
        for var_decl in variable_declarations:
            var_dict = {
                "name": var_decl.name,
                "type": var_decl.type,
                "value": var_decl.value,
            }
            if var_decl.comment:
                var_dict["comment"] = var_decl.comment
            result.append(var_dict)
        return result

    def save_test_scenarios(
        self, test_scenarios: TestScenarios, output_path: str
    ) -> None:
        """
        Save test scenarios to JSON file.

        Args:
            test_scenarios: TestScenarios object
            output_path: Path to save the JSON file
        """
        # Convert TestScenarios to dictionary format
        scenarios_data = {"test_scenarios": []}

        for scenario in test_scenarios.test_scenarios:
            scenario_dict = {
                "test_name": scenario.test_name,
                "setup": [],
                "steps": [],
                "cleanup": [],
            }

            # Convert setup steps
            for step in scenario.setup:
                step_dict = {
                    "op": step.op,
                    "variable_declarations": self._convert_variable_declarations_to_dict(
                        step.variable_declarations
                    ),
                    "input_params": step.input_params,  # Already a dictionary
                    "return_params": step.return_params,
                }
                scenario_dict["setup"].append(step_dict)

            # Convert main steps
            for step in scenario.steps:
                step_dict = {
                    "op": step.op,
                    "variable_declarations": self._convert_variable_declarations_to_dict(
                        step.variable_declarations
                    ),
                    "input_params": step.input_params,  # Already a dictionary
                    "return_params": step.return_params,
                }
                scenario_dict["steps"].append(step_dict)

            # Convert cleanup steps
            for step in scenario.cleanup:
                step_dict = {
                    "op": step.op,
                    "variable_declarations": self._convert_variable_declarations_to_dict(
                        step.variable_declarations
                    ),
                    "input_params": step.input_params,  # Already a dictionary
                    "return_params": step.return_params,
                }
                scenario_dict["cleanup"].append(step_dict)

            scenarios_data["test_scenarios"].append(scenario_dict)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scenarios_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Test scenarios saved to {output_path}")

    def _process_single_function_code_generation(
        self,
        func_info: Dict[str, Any],
        test_designs_dir: str,
        operation_map_json: str,
        output_dir: str,
        function_files_dir: str,
        temperature: float,
    ) -> tuple[str, str]:
        """
        Process a single function: generate C test code and save to file.

        Args:
            func_info: Function metadata dictionary
            test_designs_dir: Directory containing test design JSON files
            operation_map_json: JSON string of operation map
            output_dir: Directory to save test scenario files
            function_files_dir: Directory containing minimal function C files
            temperature: GPT temperature

        Returns:
            Tuple of (function_name, output_file_path)
        """
        func_name = func_info.get("name")
        if not func_name:
            print("⚠️  Warning: Function with no name found, skipping")
            return None, None

        # Path to test designs for this function
        test_designs_path = os.path.join(test_designs_dir, f"{func_name}.json")

        if not os.path.exists(test_designs_path):
            print(f"⚠️  Warning: Test designs not found for {func_name}, skipping")
            return None, None

        # Prepare output path for incremental saving
        output_path = os.path.join(output_dir, f"{func_name}.json")

        # Generate test code for this function (with incremental saving)
        test_scenarios = self.generate_test_code_for_function(
            function_name=func_name,
            function_info=func_info,
            test_designs_path=test_designs_path,
            operation_map_json=operation_map_json,
            function_files_dir=function_files_dir,
            temperature=temperature,
            output_path=output_path,
        )

        # Final save to ensure all scenarios are persisted
        self.save_test_scenarios(test_scenarios, output_path)

        return func_name, output_path

    def generate_test_code_for_all_functions(
        self,
        source_functions_path: str,
        test_designs_dir: str,
        operation_map_json: str,
        output_dir: str,
        function_files_dir: str = "tmp/function-files",
        temperature: float = 0.0,
        max_workers: int = 10,
    ) -> Dict[str, str]:
        """
        Generate C test code for all functions based on their test designs with parallel processing.

        Args:
            source_functions_path: Path to source_functions.json
            test_designs_dir: Directory containing test design JSON files
            operation_map_json: JSON string of operation map
            output_dir: Directory to save test scenario files
            function_files_dir: Directory containing minimal function C files
            temperature: GPT temperature
            max_workers: Maximum number of parallel workers (default: 10)

        Returns:
            Dictionary mapping function names to their test scenario file paths
        """
        # Load source functions
        with open(source_functions_path, "r", encoding="utf-8") as f:
            source_functions_data = json.load(f)

        source_functions = source_functions_data.get("source_functions", [])

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        scenario_files = {}

        total_funcs = len(source_functions)
        num_batches = (total_funcs + max_workers - 1) // max_workers  # Ceiling division

        print(f"\n💻 PHASE 2: Generating C test code for {total_funcs} functions...")
        print(f"⚡ Parallel mode: Processing up to {max_workers} functions at a time")
        print(f"📦 Batches: {num_batches} batch(es) will be processed")
        print()

        # Process functions in batches
        for batch_num in range(num_batches):
            start_idx = batch_num * max_workers
            end_idx = min(start_idx + max_workers, total_funcs)
            batch_functions = source_functions[start_idx:end_idx]
            batch_size = len(batch_functions)

            print(f"{'=' * 70}")
            print(f"📦 BATCH {batch_num + 1}/{num_batches}: Processing functions {start_idx + 1}-{end_idx}")
            print(f"{'=' * 70}")

            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit all functions in this batch
                future_to_func = {
                    executor.submit(
                        self._process_single_function_code_generation,
                        func_info,
                        test_designs_dir,
                        operation_map_json,
                        output_dir,
                        function_files_dir,
                        temperature,
                    ): func_info.get("name", f"unknown_{i}")
                    for i, func_info in enumerate(batch_functions)
                }

                # Process completed tasks as they finish
                completed = 0
                for future in as_completed(future_to_func):
                    func_name_submitted = future_to_func[future]
                    try:
                        func_name, output_path = future.result()
                        if func_name and output_path:
                            scenario_files[func_name] = output_path
                            completed += 1
                            print(f"   [{completed}/{batch_size}] ✅ {func_name} completed")
                    except Exception as exc:
                        print(f"   ❌ {func_name_submitted} generated an exception: {exc}")

            print(f"✅ Batch {batch_num + 1} completed: {completed}/{batch_size} functions processed")
            print()

        print(f"{'=' * 70}")
        print(f"✅ PHASE 2 COMPLETE: C test code generated for {len(scenario_files)}/{total_funcs} functions")
        print(f"{'=' * 70}")
        return scenario_files
