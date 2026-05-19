import os
import json
import glob
from typing import Any, Dict, List, Optional

from apis.gpt import GPT_Connection
from apis.formats.response_format import InputParam, TestScenarios, VariableDeclaration
from apis.prompts.test_scenario_generation_prompt import (
    test_scenario_sys_prompt_template,
    test_scenario_usr_prompt_template,
)

try:
    from clang.cindex import Index, CursorKind, TypeKind, Config

    # Set libclang path to llvm-20
    try:
        Config.set_library_file("/usr/lib/llvm-20/lib/libclang.so")
    except:
        # Fallback to llvm-18 or custom path
        try:
            Config.set_library_file("/usr/lib/llvm-18/lib/libclang.so.1")
        except:
            # Try custom LLVM build
            Config.set_library_file("/media/goat/Projects/Work/Jobs/UIUC/llvm-project/build/lib/libclang.so")

    CLANG_AVAILABLE = True
except ImportError:
    print("Warning: clang not available. Install with: pip install clang")
    CLANG_AVAILABLE = False


class TestScenariosManager:
    def __init__(self):
        self.gpt_connection = GPT_Connection()

    def _extract_source_functions(
        self, source_file_path: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract all functions from the source file being tested.

        Args:
            source_file_path: Path to the source C file

        Returns:
            Dictionary of function names to call template information
        """
        if not CLANG_AVAILABLE:
            print("Warning: clang not available, cannot extract source functions")
            return {}

        if not source_file_path or not os.path.exists(source_file_path):
            print(f"Warning: Source file not found: {source_file_path}")
            return {}

        try:
            index = Index.create()
            tu = index.parse(source_file_path)

            source_functions = {}

            # Get the absolute path of the source file for comparison
            abs_source_path = os.path.abspath(source_file_path)

            def pointer_depth(typ):
                depth = 0
                while typ.kind == TypeKind.POINTER:
                    depth += 1
                    typ = typ.get_pointee()
                return depth

            for cursor in tu.cursor.get_children():
                if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                    func_name = cursor.spelling

                    # Only include functions defined in the source file itself
                    if (
                        cursor.location.file
                        and os.path.abspath(str(cursor.location.file))
                        == abs_source_path
                    ):
                        call_args = []
                        input_params = []

                        for param in cursor.get_arguments():
                            pname = param.spelling
                            ptype = param.type
                            depth = pointer_depth(ptype)

                            # Add to input_params with type information
                            input_params.append({"name": pname, "type": ptype.spelling})

                            # For source functions, use placeholder syntax for call templates
                            call_args.append(f"{{{pname}}}")

                        call_template = f"{func_name}({', '.join(call_args)});"
                        source_functions[func_name] = {
                            "call_template": call_template,
                            "input_params": input_params,
                            "return_type": cursor.result_type.spelling,
                        }

            print(
                f"Extracted {len(source_functions)} functions from source file: {source_file_path}"
            )
            return source_functions

        except Exception as e:
            print(f"Error parsing source file with clang: {e}")
            return {}

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

    def generate_test_scenarios(
        self, source_filepath: str, op_map_json: str, temperature: float = 0.7
    ) -> TestScenarios:
        """
        Phase 1: Generate unit test scenarios based on the operation map.

        Args:
            source_filepath: Path to the C source file
            op_map_json: JSON string of the operation map
            temperature: GPT temperature setting

        Returns:
            Generated test scenarios as TestScenarios object
        """

        # Create the prompt template for Phase 1 - Generation
        test_scenario_usr_prompt = test_scenario_usr_prompt_template.replace(
            "<source_code>", self._get_source_code(source_filepath).replace("\n", "\\n")
        )
        test_scenario_usr_prompt = test_scenario_usr_prompt.replace(
            "<op_map_json>", op_map_json.replace("\n", "\\n")
        )

        test_scenario_sys_prompt = test_scenario_sys_prompt_template

        test_scenario_response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": test_scenario_sys_prompt},
                {"role": "user", "content": test_scenario_usr_prompt},
            ],
            temperature=temperature,
            response_model=TestScenarios,
            context="test_scenarios_generation",
            max_tokens=8192,  # Limit to 8K tokens to prevent hitting the 32K limit
        )

        return test_scenario_response

    def generate_test_scenarios_for_function(
        self, 
        source_filepath: str, 
        op_map_json: str, 
        function_name: str,
        function_paths: List[dict],
        temperature: float = 0.0
    ) -> TestScenarios:
        """
        Generate unit test scenarios for a specific function.

        Args:
            source_filepath: Path to the C source file
            op_map_json: JSON string of the operation map
            function_name: Name of the function to generate tests for
            function_paths: List of paths for this function from source_functions.json
            temperature: GPT temperature setting

        Returns:
            Generated test scenarios as TestScenarios object for the specific function
        """
        # Create function-specific context
        function_context = {
            "name": function_name,
            "paths": function_paths
        }
        
        function_context_json = json.dumps(function_context, indent=2)

        # Create the prompt template focused on this function
        test_scenario_usr_prompt = test_scenario_usr_prompt_template.replace(
            "<source_code>", self._get_source_code(source_filepath).replace("\n", "\\n")
        )
        test_scenario_usr_prompt = test_scenario_usr_prompt.replace(
            "<op_map_json>", op_map_json.replace("\n", "\\n")
        )
        
        # Add function-specific instruction
        function_instruction = f"\n\n**CRITICAL: Generate test scenarios ONLY for the function '{function_name}'.**\n"
        function_instruction += f"Function paths to cover:\n{function_context_json}\n"
        function_instruction += f"Generate multiple test scenarios to cover all different paths for this function.\n"
        
        test_scenario_usr_prompt += function_instruction

        test_scenario_sys_prompt = test_scenario_sys_prompt_template

        test_scenario_response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": test_scenario_sys_prompt},
                {"role": "user", "content": test_scenario_usr_prompt},
            ],
            temperature=temperature,
            response_model=TestScenarios,
            context=f"test_scenarios_generation_{function_name}",
            max_tokens=8192,  # Limit to 8K tokens to prevent hitting the 32K limit
        )

        return test_scenario_response

    def _convert_variable_declarations_to_dict(
        self, variable_declarations: Optional[List[VariableDeclaration]]
    ) -> List[Dict[str, Any]]:
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

    def generate_and_save_test_scenarios_per_function(
        self,
        source_filepath: str,
        source_functions_path: str,
        op_map_json: str,
        output_dir: str,
        temperature: float = 0.0
    ) -> None:
        """
        Generate test scenarios for each function separately and save to individual files.

        Args:
            source_filepath: Path to the C source file
            source_functions_path: Path to source_functions.json file
            op_map_json: JSON string of the operation map
            output_dir: Directory to save individual test scenario files
            temperature: GPT temperature setting
        """
        try:
            # Load source functions - optional, gracefully handle if file doesn't exist
            source_functions = []
            if os.path.exists(source_functions_path):
                with open(source_functions_path, "r", encoding="utf-8") as f:
                    source_functions_data = json.load(f)
                source_functions = source_functions_data.get("source_functions", [])
            else:
                print(f"Warning: {source_functions_path} not found. Will extract functions from operation map.")
                # Extract source functions from operation_map_json instead
                op_map_data = json.loads(op_map_json)
                source_functions = op_map_data.get("dependency_analysis", {}).get("source_functions", [])

            if not source_functions:
                print(f"Error: No source functions found in operation map or source_functions.json")
                return
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"Generating test scenarios for {len(source_functions)} functions...")
            
            # Generate test scenarios for each function
            for func_info in source_functions:
                func_name = func_info.get("name")
                func_paths = func_info.get("paths", [])
                
                if not func_name:
                    print("Warning: Function with no name found, skipping")
                    continue
                
                print(f"\nGenerating test scenarios for function: {func_name}")
                print(f"  - Paths to cover: {len(func_paths)}")
                
                # Generate test scenarios for this function
                test_scenarios = self.generate_test_scenarios_for_function(
                    source_filepath=source_filepath,
                    op_map_json=op_map_json,
                    function_name=func_name,
                    function_paths=func_paths,
                    temperature=temperature
                )
                
                # Save to individual file
                output_file = os.path.join(output_dir, f"{func_name}_test_scenarios.json")
                self.write_test_scenarios_to_json(test_scenarios, output_file)
                
            print(f"\n✓ All test scenarios generated and saved to {output_dir}")
            
        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in source_functions.json - {e}")
            raise
        except Exception as e:
            print(f"Error generating test scenarios per function: {e}")
            raise

    def write_test_scenarios_to_json(
        self, test_scenarios: TestScenarios, output_path: str = "test_scenarios.json"
    ) -> None:
        """
        Write TestScenarios response to a JSON file.

        Args:
            test_scenarios: TestScenarios response from GPT
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

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        # Write to JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scenarios_data, f, indent=2, ensure_ascii=False)

        print(f"Test scenarios saved to {output_path}")

    def test_scenarios_to_json_string(self, test_scenarios: TestScenarios) -> str:
        """
        Convert TestScenarios response to JSON string format.

        Args:
            test_scenarios: TestScenarios response from GPT

        Returns:
            JSON string representation of the test scenarios
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

        return json.dumps(scenarios_data, indent=2, ensure_ascii=False)

    def _generate_call_templates_from_file(
        self, helper_file_path: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate call templates from C helper file using clang static analysis.

        Args:
            helper_file_path: Path to the C helper file

        Returns:
            Dictionary of function names to call template information
        """
        if not CLANG_AVAILABLE:
            print("Warning: clang not available, falling back to simple templates")
            return {}

        try:
            index = Index.create()
            tu = index.parse(helper_file_path)

            call_templates = {}

            def pointer_depth(typ):
                depth = 0
                while typ.kind == TypeKind.POINTER:
                    depth += 1
                    typ = typ.get_pointee()
                return depth

            for cursor in tu.cursor.get_children():
                if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                    func_name = cursor.spelling
                    params = []
                    call_args = []
                    input_params = []

                    for param in cursor.get_arguments():
                        pname = param.spelling
                        ptype = param.type
                        depth = pointer_depth(ptype)

                        params.append(pname)

                        # Add to input_params with type information
                        input_params.append({"name": pname, "type": ptype.spelling})

                        # If pointer depth >= 2, pass address-of, else pass param directly
                        if depth >= 2:
                            call_args.append(f"&{{{pname}}}")
                        else:
                            call_args.append(f"{{{pname}}}")

                    call_template = f"{func_name}({', '.join(call_args)});"
                    call_templates[func_name] = {
                        "call_template": call_template,
                        "input_params": input_params,
                        "return_type": cursor.result_type.spelling,
                        "params": params,  # Keep for backward compatibility
                    }

            return call_templates

        except Exception as e:
            print(f"Error parsing C file with clang: {e}")
            return {}

    def _convert_steps_to_complex_format(self, steps: list) -> list:
        """
        Convert steps from test scenarios format to complex test scenarios format.
        Handles the new two-phase parameter system with variable_declarations and input_params.

        Args:
            steps: List of steps in test scenarios format

        Returns:
            List of steps in complex test scenarios format
        """
        converted_steps = []

        for step in steps:
            converted_step = {
                "op": step["op"],
                "input_params": step.get("input_params", {}),
                "return_params": step.get("return_params", []),
            }

            # Include variable_declarations if present
            if "variable_declarations" in step and step["variable_declarations"]:
                converted_step["variable_declarations"] = step["variable_declarations"]

            converted_steps.append(converted_step)

        return converted_steps

    def merge_to_complex_test_scenarios(
        self,
        test_scenarios_dir: str,
        operation_map_path: str,
        complex_test_scenarios_path: str = "complex_test_scenarios.json",
        subject_name: str = "subject",
        source_file_path: str = None,
        helpers_c_path: str = None,
    ) -> None:
        """
        Merge all test_scenarios JSON files from a directory and operation_map.json into complex_test_scenarios.json format.
        Matches the BST format with organized operation_map sections.
        Uses clang static analysis to generate accurate call templates from helpers.c
        Uses predefined_functions.json to get correct function signatures for searched_from_pool functions

        Args:
            test_scenarios_dir: Path to directory containing test_scenarios JSON files
            operation_map_path: Path to operation_map.json file
            complex_test_scenarios_path: Path to save the merged complex_test_scenarios.json
            subject_name: Name of the subject being tested
            source_file_path: Path to the source file (for meta information)
            helpers_c_path: Path to the helpers.c file for static analysis
        """
        try:
            # Load all test scenarios from directory
            all_test_scenarios = []
            if not os.path.isdir(test_scenarios_dir):
                print(f"Error: {test_scenarios_dir} is not a directory")
                return
            
            # Find all JSON files in the directory
            json_files = glob.glob(os.path.join(test_scenarios_dir, "*.json"))
            if not json_files:
                print(f"Warning: No JSON files found in {test_scenarios_dir}")
            
            print(f"Found {len(json_files)} JSON files in {test_scenarios_dir}")
            
            # Load and merge test scenarios from all files
            for json_file in sorted(json_files):
                print(f"Loading test scenarios from: {os.path.basename(json_file)}")
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    scenarios = data.get("test_scenarios", [])
                    all_test_scenarios.extend(scenarios)
                    print(f"  Loaded {len(scenarios)} test scenarios")
            
            print(f"Total test scenarios loaded: {len(all_test_scenarios)}")
            
            # Create a combined test_scenarios_data structure
            test_scenarios_data = {"test_scenarios": all_test_scenarios}

            # Load operation map
            with open(operation_map_path, "r", encoding="utf-8") as f:
                operation_map_data = json.load(f)

            # Generate call templates from helpers.c if available
            call_templates_from_file = {}
            if helpers_c_path and os.path.exists(helpers_c_path):
                print(f"Analyzing helpers.c file: {helpers_c_path}")
                call_templates_from_file = self._generate_call_templates_from_file(
                    helpers_c_path
                )
                print(
                    f"Generated {len(call_templates_from_file)} call templates from static analysis"
                )
            else:
                print("Error: helpers.c file not provided or does not exist")
                exit(1)

            # Extract functions from source file for function_operations
            source_functions = {}
            if source_file_path and os.path.exists(source_file_path):
                source_functions = self._extract_source_functions(source_file_path)
            else:
                print("Warning: Source file not provided or does not exist")

            # Create the complex test scenarios structure matching BST format
            complex_data = {
                "meta": {
                    "type": subject_name,
                    "source_file": source_file_path,
                    "ds_config": {"variable_name": f"test_{subject_name}"},
                },
                "operation_map": {
                    "function_operations": {},
                    "assertion_operations": {},
                    "utility_operations": {},
                },
                "test_scenarios": [],
            }

            # Populate function_operations with functions from source file
            complex_data["operation_map"]["function_operations"] = source_functions

            # Process assertion operations - created functions
            for func_info in operation_map_data.get("assertion_operations", {}).get(
                "created", []
            ):
                func_name = func_info["name"]

                # Use clang-generated template
                if func_name in call_templates_from_file:
                    template_info = call_templates_from_file[func_name]
                    call_template = template_info["call_template"]
                    input_params = template_info["input_params"]
                    return_type = template_info["return_type"]

                    complex_data["operation_map"]["assertion_operations"][func_name] = {
                        "call_template": call_template,
                        "input_params": input_params,
                        "return_type": return_type,
                    }

            # Process assertion operations - searched_from_pool functions
            for func_name_dict in operation_map_data.get(
                "assertion_operations", {}
            ).get("searched_from_pool", []):
                func_name = (
                    func_name_dict["name"]
                    if isinstance(func_name_dict, dict)
                    else func_name_dict
                )

                # Use clang-generated template if available
                if func_name in call_templates_from_file:
                    template_info = call_templates_from_file[func_name]
                    complex_data["operation_map"]["assertion_operations"][func_name] = {
                        "call_template": template_info["call_template"],
                        "input_params": template_info["input_params"],
                        "return_type": template_info["return_type"],
                    }

            # Process utility operations - created functions
            for func_info in operation_map_data.get("utility_operations", {}).get(
                "created", []
            ):
                func_name = func_info["name"]

                # Use clang-generated template if available
                if func_name in call_templates_from_file:
                    template_info = call_templates_from_file[func_name]
                    call_template = template_info["call_template"]
                    input_params = template_info["input_params"]
                    return_type = template_info["return_type"]

                    complex_data["operation_map"]["utility_operations"][func_name] = {
                        "call_template": call_template,
                        "input_params": input_params,
                        "return_type": return_type,
                    }

            # Process utility operations - searched_from_pool functions
            for func_name_dict in operation_map_data.get("utility_operations", {}).get(
                "searched_from_pool", []
            ):
                func_name = (
                    func_name_dict["name"]
                    if isinstance(func_name_dict, dict)
                    else func_name_dict
                )

                # Use clang-generated template if available
                if func_name in call_templates_from_file:
                    template_info = call_templates_from_file[func_name]
                    complex_data["operation_map"]["utility_operations"][func_name] = {
                        "call_template": template_info["call_template"],
                        "input_params": template_info["input_params"],
                        "return_type": template_info["return_type"],
                    }

            # Convert test scenarios to the complex format
            for scenario in test_scenarios_data.get("test_scenarios", []):
                test_scenario = {
                    "test_name": scenario["test_name"],
                    "setup": self._convert_steps_to_complex_format(
                        scenario.get("setup", [])
                    ),
                    "steps": self._convert_steps_to_complex_format(
                        scenario.get("steps", [])
                    ),
                    "cleanup": self._convert_steps_to_complex_format(
                        scenario.get("cleanup", [])
                    ),
                }
                complex_data["test_scenarios"].append(test_scenario)

            # Write merged data to file
            with open(complex_test_scenarios_path, "w", encoding="utf-8") as f:
                json.dump(complex_data, f, indent=2, ensure_ascii=False)

            print(
                f"Merged complex test scenarios saved to {complex_test_scenarios_path}"
            )

        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format - {e}")
        except Exception as e:
            print(f"Error merging files: {e}")

    def generate_per_function_complex_test_scenarios(
        self,
        test_scenarios_dir: str,
        operation_map_path: str,
        output_dir: str,
        subject_name: str = "subject",
        source_file_path: str = None,
        helpers_c_path: str = None,
    ) -> list:
        """
        Generate individual complex_test_scenarios_{function}.json for each function.

        Args:
            test_scenarios_dir: Path to directory containing test_scenarios JSON files
            operation_map_path: Path to operation_map.json file
            output_dir: Directory to save per-function complex test scenarios
            subject_name: Name of the subject being tested
            source_file_path: Path to the source file (for meta information)
            helpers_c_path: Path to the helpers.c file for static analysis

        Returns:
            List of generated complex test scenario file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)

            # Load operation map
            with open(operation_map_path, "r", encoding="utf-8") as f:
                operation_map_data = json.load(f)

            # Generate call templates from helpers.c
            call_templates_from_file = {}
            if helpers_c_path and os.path.exists(helpers_c_path):
                print(f"Analyzing helpers.c file: {helpers_c_path}")
                call_templates_from_file = self._generate_call_templates_from_file(
                    helpers_c_path
                )
                print(
                    f"Generated {len(call_templates_from_file)} call templates from static analysis"
                )

            # Extract functions from source file
            source_functions = {}
            if source_file_path and os.path.exists(source_file_path):
                source_functions = self._extract_source_functions(source_file_path)

            # Find all test scenario JSON files
            json_files = glob.glob(os.path.join(test_scenarios_dir, "*.json"))
            generated_files = []

            print(f"\nGenerating per-function complex test scenarios...")
            print(f"Found {len(json_files)} function test scenario files")

            for json_file in sorted(json_files):
                # Extract function name from filename (e.g., "deleteNode.json" -> "deleteNode")
                filename = os.path.basename(json_file)
                function_name = filename.replace(".json", "")

                print(f"\nProcessing function: {function_name}")

                # Load test scenarios for this function
                with open(json_file, "r", encoding="utf-8") as f:
                    test_scenarios_data = json.load(f)

                num_scenarios = len(test_scenarios_data.get("test_scenarios", []))
                print(f"  - Scenarios: {num_scenarios}")

                # Create complex test scenarios structure
                complex_data = {
                    "meta": {
                        "type": subject_name,
                        "source_file": source_file_path,
                        "function_name": function_name,
                        "ds_config": {"variable_name": f"test_{subject_name}"},
                    },
                    "operation_map": {
                        "function_operations": source_functions,
                        "assertion_operations": {},
                        "utility_operations": {},
                    },
                    "test_scenarios": [],
                }

                # Process assertion operations
                for func_info in operation_map_data.get("assertion_operations", {}).get("created", []):
                    func_name = func_info["name"]
                    if func_name in call_templates_from_file:
                        template_info = call_templates_from_file[func_name]
                        complex_data["operation_map"]["assertion_operations"][func_name] = {
                            "call_template": template_info["call_template"],
                            "input_params": template_info["input_params"],
                            "return_type": template_info["return_type"],
                        }

                for func_name_dict in operation_map_data.get("assertion_operations", {}).get("searched_from_pool", []):
                    func_name = func_name_dict["name"] if isinstance(func_name_dict, dict) else func_name_dict
                    if func_name in call_templates_from_file:
                        template_info = call_templates_from_file[func_name]
                        complex_data["operation_map"]["assertion_operations"][func_name] = {
                            "call_template": template_info["call_template"],
                            "input_params": template_info["input_params"],
                            "return_type": template_info["return_type"],
                        }

                # Process utility operations
                for func_info in operation_map_data.get("utility_operations", {}).get("created", []):
                    func_name = func_info["name"]
                    if func_name in call_templates_from_file:
                        template_info = call_templates_from_file[func_name]
                        complex_data["operation_map"]["utility_operations"][func_name] = {
                            "call_template": template_info["call_template"],
                            "input_params": template_info["input_params"],
                            "return_type": template_info["return_type"],
                        }

                for func_name_dict in operation_map_data.get("utility_operations", {}).get("searched_from_pool", []):
                    func_name = func_name_dict["name"] if isinstance(func_name_dict, dict) else func_name_dict
                    if func_name in call_templates_from_file:
                        template_info = call_templates_from_file[func_name]
                        complex_data["operation_map"]["utility_operations"][func_name] = {
                            "call_template": template_info["call_template"],
                            "input_params": template_info["input_params"],
                            "return_type": template_info["return_type"],
                        }

                # Convert test scenarios
                for scenario in test_scenarios_data.get("test_scenarios", []):
                    test_scenario = {
                        "test_name": scenario["test_name"],
                        "setup": self._convert_steps_to_complex_format(scenario.get("setup", [])),
                        "steps": self._convert_steps_to_complex_format(scenario.get("steps", [])),
                        "cleanup": self._convert_steps_to_complex_format(scenario.get("cleanup", [])),
                    }
                    complex_data["test_scenarios"].append(test_scenario)

                # Save to file
                output_path = os.path.join(output_dir, f"complex_test_scenarios_{function_name}.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(complex_data, f, indent=2, ensure_ascii=False)

                generated_files.append(output_path)
                print(f"  ✓ Saved: {output_path}")

            print(f"\n✓ Generated {len(generated_files)} per-function complex test scenario files")
            return generated_files

        except Exception as e:
            print(f"Error generating per-function complex test scenarios: {e}")
            import traceback
            traceback.print_exc()
            return []
