"""
Phase 1: Test Designer Manager

Generates high-level test designs based on:
- Function metadata from source_functions.json
- Single execution path from CFG analysis (per-path prompting)
- Function implementation from atomic files
- Operation map with available helpers
"""

import os
import json
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from apis.gpt import GPT_Connection
from apis.formats.response_format import TestDesigns, TestDesign, EnhancedTestDesigns
from apis.prompts.test_designer_prompt import (
    test_designer_sys_prompt,
    test_designer_usr_prompt_template,
)


class TestDesignerManager:
    """Manages Phase 1: Test Design generation (per-path prompting)"""

    def __init__(self):
        self.gpt_connection = GPT_Connection()

    def _read_function_implementation(self, function_name: str, atomic_files_dir: str = "tmp/function-files") -> str:
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
            print(f"⚠️  Warning: Function file not found: {function_file_path}")
            return ""

        try:
            with open(function_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"⚠️  Error reading function file {function_file_path}: {e}")
            return ""

    def design_test_for_path(
        self,
        function_name: str,
        function_info: Dict[str, Any],
        path_info: Dict[str, Any],
        function_implementation: str,
        operation_map_json: str,
        temperature: float = 0.0,
        use_enhanced_format: bool = True,
    ) -> Any:
        """
        Design a test for a specific execution path using LLM.

        Args:
            function_name: Name of the function to design test for
            function_info: Dictionary containing function metadata from source_functions.json
                           {
                               "name": str,
                               "signature": str,
                               "description": str,
                               "paths": List[dict],
                               "required_functions": List[str]
                           }
            path_info: Dictionary containing single path information
                       {
                           "path_id": str,
                           "path": str,
                           "conditions": str (optional),
                           ...
                       }
            function_implementation: Source code of the function from atomic files
            operation_map_json: JSON string of the operation map
            temperature: GPT temperature setting
            use_enhanced_format: If True, use EnhancedTestDesigns format with rich metadata

        Returns:
            EnhancedTestDesigns or TestDesigns object (containing single test design)
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
        usr_prompt = test_designer_usr_prompt_template.replace(
            "<function_name>", function_name
        )
        usr_prompt = usr_prompt.replace("<function_signature>", function_signature)
        usr_prompt = usr_prompt.replace("<function_description>", function_description)
        usr_prompt = usr_prompt.replace("<execution_path>", path_text)  # Single path
        usr_prompt = usr_prompt.replace("<function_implementation>", function_implementation)
        usr_prompt = usr_prompt.replace("<required_functions>", required_funcs_text)
        usr_prompt = usr_prompt.replace(
            "<operation_map_json>", operation_map_json.replace("\n", "\\n")
        )

        # Select response model based on format preference
        response_model = EnhancedTestDesigns if use_enhanced_format else TestDesigns
        max_tokens = 8192

        # Call GPT to generate test design for this path
        print(f"  🎨 [{path_id}] Designing test for path")

        test_design_response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": test_designer_sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            temperature=temperature,
            response_model=response_model,
            context=f"test_designer_{function_name}_{path_id}",
            max_tokens=max_tokens,
        )

        if use_enhanced_format:
            num_tests = len(test_design_response.test_scenarios)
            print(f"  ✅ [{path_id}] Generated {num_tests} test design(s)")
        else:
            num_tests = len(test_design_response.test_designs)
            print(f"  ✅ [{path_id}] Generated {num_tests} test design(s)")

        return test_design_response

    def save_test_designs(
        self, test_designs: Any, output_path: str, path_info: Dict[str, Any] = None
    ) -> None:
        """
        Save test designs to JSON file.

        Args:
            test_designs: TestDesigns or EnhancedTestDesigns object
            output_path: Path to save the JSON file
            path_info: Optional execution path data to inject into each test scenario
        """
        # Check if enhanced format
        if isinstance(test_designs, EnhancedTestDesigns):
            # Save the full enhanced model as JSON using model_dump()
            designs_data = test_designs.model_dump()

            # Inject execution_path data into each test scenario if provided
            if path_info is not None:
                for scenario in designs_data.get("test_scenarios", []):
                    scenario["execution_path"] = {
                        "path_id": path_info.get("path_id", ""),
                        "path": path_info.get("path", ""),
                    }
        else:
            # Simple format - only save test names and descriptions
            designs_data = {
                "test_designs": [
                    {
                        "test_name": design.test_name,
                        "test_description": design.test_description,
                    }
                    for design in test_designs.test_designs
                ]
            }

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(designs_data, f, indent=2, ensure_ascii=False)

        if isinstance(test_designs, EnhancedTestDesigns):
            print(f"  💾 Test designs saved to {output_path}")
        else:
            print(f"  💾 Test designs saved to {output_path}")

    def _merge_path_designs_to_function_file(
        self,
        func_name: str,
        path_design_files: List[str],
        output_dir: str,
    ) -> str:
        """
        Merge all path design files for a function into a single merged file.

        Args:
            func_name: Function name
            path_design_files: List of individual path design file paths
            output_dir: Base output directory

        Returns:
            Path to merged file
        """
        merged_data = {
            "metadata": None,
            "test_scenarios": [],
            "test_suite_summary": None
        }

        # Read and merge all path design files
        for path_file in path_design_files:
            with open(path_file, "r", encoding="utf-8") as f:
                design_data = json.load(f)

            # Use first file's metadata
            if merged_data["metadata"] is None:
                merged_data["metadata"] = design_data.get("metadata", {})
                if "target_path" in merged_data["metadata"]:
                    merged_data["metadata"]["target_path"] = "all_paths"

            # Append test scenarios
            test_scenarios = design_data.get("test_scenarios", [])
            merged_data["test_scenarios"].extend(test_scenarios)

        # Create summary
        merged_data["test_suite_summary"] = {
            "function_name": func_name,
            "total_tests": len(merged_data["test_scenarios"]),
            "total_paths": len(path_design_files)
        }

        # Save merged file
        merged_path = os.path.join(output_dir, f"{func_name}.json")
        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)

        print(f"  📦 Merged {len(path_design_files)} path designs into {func_name}.json")
        return merged_path

    def _process_single_path(
        self,
        func_name: str,
        func_info: Dict[str, Any],
        path_info: Dict[str, Any],
        function_implementation: str,
        operation_map_json: str,
        output_dir: str,
        temperature: float,
        use_enhanced_format: bool,
    ) -> Tuple[str, str, str]:
        """
        Process a single path: design test and save to file.

        Args:
            func_name: Function name
            func_info: Function metadata dictionary
            path_info: Single path metadata dictionary
            function_implementation: Source code of the function
            operation_map_json: JSON string of operation map
            output_dir: Directory to save test design files
            temperature: GPT temperature
            use_enhanced_format: If True, use comprehensive test design format

        Returns:
            Tuple of (function_name, path_id, output_file_path)
        """
        path_id = path_info.get("path_id", "P1")

        # Design test for this path
        test_design = self.design_test_for_path(
            function_name=func_name,
            function_info=func_info,
            path_info=path_info,
            function_implementation=function_implementation,
            operation_map_json=operation_map_json,
            temperature=temperature,
            use_enhanced_format=use_enhanced_format,
        )

        # Create function subdirectory
        func_subdir = os.path.join(output_dir, func_name)
        os.makedirs(func_subdir, exist_ok=True)

        # Extract test_name from response
        if use_enhanced_format:
            test_name = test_design.test_scenarios[0].test_metadata.test_name
        else:
            test_name = test_design.test_designs[0].test_name

        # Handle filename collisions
        individual_filename = f"{test_name}.json"
        individual_path = os.path.join(func_subdir, individual_filename)

        # Check for collision and append suffix if needed
        counter = 1
        while os.path.exists(individual_path):
            individual_filename = f"{test_name}_{counter}.json"
            individual_path = os.path.join(func_subdir, individual_filename)
            counter += 1

        # Save individual file to subdirectory (with path_info for Test Coder)
        self.save_test_designs(test_design, individual_path, path_info=path_info)

        return func_name, path_id, individual_path

    def design_tests_for_all_functions(
        self,
        source_functions_path: str,
        operation_map_json: str,
        output_dir: str,
        atomic_files_dir: str = "tmp/function-files",
        temperature: float = 0.0,
        use_enhanced_format: bool = True,
        max_workers: int = 10,
    ) -> Dict[str, List[str]]:
        """
        Design tests for all execution paths across all functions with parallel processing.

        This method iterates through each function, then through each execution path,
        and generates a test design for each path independently.

        Args:
            source_functions_path: Path to source_functions.json
            operation_map_json: JSON string of operation map
            output_dir: Directory to save test design files
            atomic_files_dir: Directory containing atomic function files
            temperature: GPT temperature
            use_enhanced_format: If True, use comprehensive test design format
            max_workers: Maximum number of parallel workers (default: 10)

        Returns:
            Dictionary mapping function names to list of their individual test design file paths
            Note: Merged files are also created at {output_dir}/{function_name}.json for Test Coder compatibility
        """
        # Load source functions
        with open(source_functions_path, "r", encoding="utf-8") as f:
            source_functions_data = json.load(f)

        source_functions = source_functions_data.get("source_functions", [])

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        design_files = {}  # {function_name: [path1_file, path2_file, ...]}

        # Count total paths across all functions
        total_paths = sum(len(func.get("paths", [])) for func in source_functions)
        total_funcs = len(source_functions)

        format_type = "comprehensive" if use_enhanced_format else "simple"

        print(f"\n🎨 PHASE 1: Per-Path Test Design Generation ({format_type} format)")
        print(f"📊 Total functions: {total_funcs}")
        print(f"📊 Total execution paths: {total_paths}")
        print(f"⚡ Parallel mode: Processing up to {max_workers} paths at a time")
        print()

        # Prepare all path tasks (function_name, func_info, path_info)
        all_path_tasks = []
        for func_info in source_functions:
            func_name = func_info.get("name")
            if not func_name:
                print("⚠️  Warning: Function with no name found, skipping")
                continue

            paths = func_info.get("paths", [])
            if not paths:
                print(f"⚠️  Warning: Function '{func_name}' has no execution paths, skipping")
                continue

            # Read function implementation once per function
            function_implementation = self._read_function_implementation(func_name, atomic_files_dir)
            if not function_implementation:
                print(f"⚠️  Warning: Could not read implementation for '{func_name}', skipping")
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

        print(f"📦 Total batches: {num_batches}")
        print()

        completed_count = 0
        for batch_num in range(num_batches):
            start_idx = batch_num * max_workers
            end_idx = min(start_idx + max_workers, len(all_path_tasks))
            batch_tasks = all_path_tasks[start_idx:end_idx]
            batch_size = len(batch_tasks)

            print(f"{'=' * 70}")
            print(f"📦 BATCH {batch_num + 1}/{num_batches}: Processing paths {start_idx + 1}-{end_idx}")
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
                        use_enhanced_format,
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
                        returned_func_name, returned_path_id, output_path = future.result()

                        # Track files per function
                        if returned_func_name not in design_files:
                            design_files[returned_func_name] = []
                        design_files[returned_func_name].append(output_path)

                        batch_completed += 1
                        completed_count += 1
                        print(f"   [{batch_completed}/{batch_size}] ✅ {returned_func_name}::{returned_path_id} completed")
                    except Exception as exc:
                        print(f"   ❌ {func_name}::{path_id} generated an exception: {exc}")
                        import traceback
                        traceback.print_exc()

            print(f"✅ Batch {batch_num + 1} completed: {batch_completed}/{batch_size} paths processed")
            print()

        # Merge path designs into function files for Test Coder compatibility
        print(f"\n📦 Merging path designs into function files...")
        merged_files = {}
        for func_name, path_files in design_files.items():
            merged_path = self._merge_path_designs_to_function_file(
                func_name=func_name,
                path_design_files=path_files,
                output_dir=output_dir
            )
            merged_files[func_name] = merged_path

        print(f"✅ Created {len(merged_files)} merged function files")
        print()

        print(f"{'=' * 70}")
        print(f"✅ PHASE 1 COMPLETE: Test designs generated for {completed_count}/{total_paths} paths")
        print(f"📁 Functions processed: {len(design_files)}/{total_funcs}")
        print(f"📁 Individual files: {completed_count} | Merged files: {len(merged_files)}")
        print(f"{'=' * 70}")

        return design_files
