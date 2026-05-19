import os
import json
from typing import List

from apis.gpt import GPT_Connection
from apis.formats.response_format import OperationMap, Path, SourceFunction
from apis.prompts.op_map_prompt import (
    op_map_sys_prompt_template,
    op_map_usr_prompt_template,
)


class OperationMapManager:
    def __init__(self, vector_db_manager):
        self.gpt_connection = GPT_Connection()
        self.vector_db_manager = vector_db_manager

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
        
    def _load_source_functions(self, source_functions_path: str) -> List[SourceFunction]:
        """
        Load source functions from a JSON file.
        """
        try:
            with open(source_functions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [SourceFunction(name=func["name"], paths=[Path(path_id=path["path_id"], path=path["path"]) for path in func["paths"]]) for func in data.get("source_functions", [])]
        except FileNotFoundError:
            print(f"Error: Source functions file not found: {source_functions_path}")
            return []
        except Exception as e:
            print(f"Error loading source functions from {source_functions_path}: {e}")
            return []

    def generate_operation_map_with_rag(
        self, source_filepath: str, header_filepaths: List[str], temperature: float = 0
    ) -> str:
        """
        Generate operation map using RAG with all helper functions as context.

        Args:
            source_filepath: Path to the source code file
            header_filepaths: Path to header file (str) or list of header file paths
            temperature: GPT temperature setting

        Returns:
            Generated operation map as JSON string
        """

        # Get all functions from the vector database instead of searching
        all_functions = self.vector_db_manager.get_all_functions()

        # Build context from all functions
        if all_functions:
            helper_context = f"Here are all {len(all_functions)} available helper functions you can use:\n\n"

            for i, func in enumerate(all_functions, 1):
                func_name = func.get("name") or func.get("function_name", "unknown")
                helper_context += f"{i}. {func_name}\n"

                if "description" in func and func["description"]:
                    helper_context += f"   Description: {func['description']}\n"

                if "return_type" in func:
                    helper_context += f"   Returns: {func['return_type']}\n"

                if "parameters" in func and func["parameters"]:
                    param_strs = []
                    for param in func["parameters"]:
                        if isinstance(param, dict):
                            param_strs.append(
                                f"{param.get('type', '')} {param.get('name', '')}"
                            )
                        else:
                            param_strs.append(str(param))
                    helper_context += f"   Parameters: {', '.join(param_strs)}\n"

                helper_context += "\n"
        else:
            helper_context = "No helper functions found in the knowledge base.\n"

        # Normalize header_filepaths to always be a list
        if isinstance(header_filepaths, str):
            header_filepaths = [header_filepaths]
        elif header_filepaths is None:
            header_filepaths = []

        # Collect content from all header files
        header_content = ""
        for i, header_filepath in enumerate(header_filepaths):
            if header_filepath and os.path.exists(header_filepath):
                content = self._get_source_code(header_filepath)
                if i > 0:
                    header_content += (
                        "\n\n"
                        + "=" * 50
                        + f"\n// Header file: {os.path.basename(header_filepath)}\n"
                        + "=" * 50
                        + "\n\n"
                    )
                header_content += content
            else:
                print(f"Warning: Header file not found: {header_filepath}")

        # Create the prompt template
        op_map_usr_prompt = op_map_usr_prompt_template.replace(
            "<source_code>", self._get_source_code(source_filepath)
        )
        op_map_usr_prompt = op_map_usr_prompt.replace("<header_file>", header_content)
        op_map_usr_prompt = op_map_usr_prompt.replace(
            "<helper_context>", helper_context.replace("\n", "\\n")
        )

        op_map_sys_prompt = op_map_sys_prompt_template

        print(f"Using {len(all_functions)} helper functions as context")

        op_map_response = self.gpt_connection.generate_chat_completion(
            messages=[
                {"role": "system", "content": op_map_sys_prompt},
                {"role": "user", "content": op_map_usr_prompt},
            ],
            temperature=temperature,
            response_model=OperationMap,
            context="operation_map_generation",
        )

        # Handle case where response is a dict (partial recovery from validation failure)
        if isinstance(op_map_response, dict):
            print("⚠️ Operation map returned as dict, attempting to convert to OperationMap")
            try:
                op_map_response = OperationMap.model_validate(op_map_response)
            except Exception as e:
                print(f"❌ Failed to convert dict to OperationMap: {e}")
                raise ValueError(f"Operation map generation failed: could not parse response. Error: {e}")

        if op_map_response is None:
            raise ValueError("Operation map generation failed: received None response")

        return op_map_response

    def operation_map_to_json_string(
        self, op_map_response: OperationMap, source_functions_path: str
    ) -> str:
        """
        Convert OperationMap response to JSON string format.

        Args:
            op_map_response: OperationMap response from GPT
            source_functions_path: Path to source_functions.json file

        Returns:
            JSON string representation of the operation map
        """
        # Load source functions and convert Pydantic models to dictionaries
        source_functions = self._load_source_functions(source_functions_path)
        source_functions_dict = [
            {
                "name": func.name,
                "paths": [
                    {"path_id": path.path_id, "path": path.path}
                    for path in func.paths
                ]
            }
            for func in source_functions
        ]

        function_info = {
            "dependency_analysis": {
                "source_functions": source_functions_dict,
                "planned_created_functions": [
                    {"name": func.name, "calls": func.calls}
                    for func in op_map_response.dependency_analysis.planned_created_functions
                ],
                "required_from_pool": op_map_response.dependency_analysis.required_from_pool,
            },
            "assertion_operations": {"searched_from_pool": [], "created": []},
            "utility_operations": {"searched_from_pool": [], "created": []},
        }

        # Get all functions from vector database for signature lookup
        all_functions = self.vector_db_manager.get_all_functions()
        func_lookup = {func.get("name"): func for func in all_functions}

        # Process assertion operations
        for func_name in op_map_response.assertion_operations.searched_from_pool:
            # Look up full signature from vector database
            func_info = func_lookup.get(func_name)
            if func_info and "parameters" in func_info:
                # Include full signature
                function_info["assertion_operations"]["searched_from_pool"].append(
                    {
                        "name": func_name,
                        "return_type": func_info.get("return_type", "void"),
                        "parameters": [
                            {"name": param.get("name", ""), "type": param.get("type", "")}
                            for param in func_info.get("parameters", [])
                        ],
                    }
                )
            else:
                # Fallback to name only if not found
                function_info["assertion_operations"]["searched_from_pool"].append(
                    {"name": func_name}
                )

        for func in op_map_response.assertion_operations.created:
            function_info["assertion_operations"]["created"].append(
                {
                    "name": func.name,
                    "description": func.description,
                    "return_type": func.return_type,
                    "parameters": [
                        {"name": param.name, "type": param.type}
                        for param in func.parameters
                    ],
                }
            )

        # Process utility operations
        for func_name in op_map_response.utility_operations.searched_from_pool:
            # Look up full signature from vector database
            func_info = func_lookup.get(func_name)
            if func_info and "parameters" in func_info:
                # Include full signature
                function_info["utility_operations"]["searched_from_pool"].append(
                    {
                        "name": func_name,
                        "return_type": func_info.get("return_type", "void"),
                        "parameters": [
                            {"name": param.get("name", ""), "type": param.get("type", "")}
                            for param in func_info.get("parameters", [])
                        ],
                    }
                )
            else:
                # Fallback to name only if not found
                function_info["utility_operations"]["searched_from_pool"].append(
                    {"name": func_name}
                )

        for func in op_map_response.utility_operations.created:
            function_info["utility_operations"]["created"].append(
                {
                    "name": func.name,
                    "description": func.description,
                    "return_type": func.return_type,
                    "parameters": [
                        {"name": param.name, "type": param.type}
                        for param in func.parameters
                    ],
                }
            )

        return json.dumps(function_info, indent=2, ensure_ascii=False)

    def load_operation_map_from_json(self, json_file_path: str) -> OperationMap:
        """
        Load operation map from a JSON file and convert it to OperationMap object.

        Args:
            json_file_path: Path to the JSON file containing operation map data

        Returns:
            OperationMap object reconstructed from JSON data
        """
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            from apis.formats.response_format import (
                OperationMap,
                OperationMapSection,
                Parameter,
                FunctionModel,
                DependencyAnalysis,
                PlannedFunction,
                SourceFunction,
                Path,
            )

            # Reconstruct dependency analysis
            dependency_data = json_data.get("dependency_analysis", {})
            planned_functions = []
            for planned_func in dependency_data.get("planned_created_functions", []):
                planned_functions.append(
                    PlannedFunction(
                        name=planned_func.get("name", ""),
                        calls=planned_func.get("calls", []),
                    )
                )

            # Reconstruct source_functions if present
            source_functions = None
            if dependency_data.get("source_functions"):
                source_functions = []
                for func_data in dependency_data.get("source_functions", []):
                    paths = [
                        Path(path_id=path.get("path_id"), path=path.get("path"))
                        for path in func_data.get("paths", [])
                    ]
                    source_func = SourceFunction(
                        name=func_data.get("name"),
                        paths=paths
                    )
                    source_functions.append(source_func)

            dependency_analysis = DependencyAnalysis(
                source_functions=source_functions,
                planned_created_functions=planned_functions,
                required_from_pool=dependency_data.get("required_from_pool", []),
            )

            # Reconstruct assertion operations
            assertion_searched_raw = json_data.get("assertion_operations", {}).get(
                "searched_from_pool", []
            )
            # Extract function names from dictionaries if needed
            assertion_searched = []
            for item in assertion_searched_raw:
                if isinstance(item, dict) and "name" in item:
                    assertion_searched.append(item["name"])
                elif isinstance(item, str):
                    assertion_searched.append(item)

            assertion_created = []

            for func_data in json_data.get("assertion_operations", {}).get(
                "created", []
            ):
                parameters = [
                    Parameter(name=param["name"], type=param["type"])
                    for param in func_data.get("parameters", [])
                ]
                func_info = FunctionModel(
                    name=func_data["name"],
                    description=func_data.get("description", ""),
                    return_type=func_data.get("return_type", "void"),
                    parameters=parameters,
                    code_block=func_data.get("code_block", ""),
                )
                assertion_created.append(func_info)

            assertion_ops = OperationMapSection(
                searched_from_pool=assertion_searched, created=assertion_created
            )

            # Reconstruct utility operations
            utility_searched_raw = json_data.get("utility_operations", {}).get(
                "searched_from_pool", []
            )
            # Extract function names from dictionaries if needed
            utility_searched = []
            for item in utility_searched_raw:
                if isinstance(item, dict) and "name" in item:
                    utility_searched.append(item["name"])
                elif isinstance(item, str):
                    utility_searched.append(item)
            utility_created = []

            for func_data in json_data.get("utility_operations", {}).get("created", []):
                parameters = [
                    Parameter(name=param["name"], type=param["type"])
                    for param in func_data.get("parameters", [])
                ]
                func_info = FunctionModel(
                    name=func_data["name"],
                    description=func_data.get("description", ""),
                    return_type=func_data.get("return_type", "void"),
                    parameters=parameters,
                    code_block=func_data.get("code_block", ""),
                )
                utility_created.append(func_info)

            utility_ops = OperationMapSection(
                searched_from_pool=utility_searched, created=utility_created
            )

            # Create and return OperationMap object
            operation_map = OperationMap(
                dependency_analysis=dependency_analysis,
                assertion_operations=assertion_ops,
                utility_operations=utility_ops,
            )

            print(f"Successfully loaded operation map from {json_file_path}")
            return operation_map

        except FileNotFoundError:
            print(f"Error: Operation map file not found: {json_file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in {json_file_path}: {e}")
            raise
        except Exception as e:
            print(f"Error loading operation map from {json_file_path}: {e}")
            raise

    def _find_function_definition_in_helpers(
        self, func_name: str, helper_functions_dir: str = "test/helper/functions"
    ) -> str:
        """
        Find the C function definition in helper function files.
        Also includes any #define statements from the same file.

        Args:
            func_name: Name of the function to find
            helper_functions_dir: Directory containing helper function files

        Returns:
            String containing the function definition with any #define statements from the same file, or None if not found
        """
        import glob
        import re

        # Search in all .c files in the helper functions directory
        pattern = os.path.join(helper_functions_dir, "*.c")
        c_files = glob.glob(pattern)

        for c_file in c_files:
            try:
                with open(c_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # First, extract all #define statements from the file
                file_lines = content.split("\n")
                file_defines = []
                for line in file_lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith("#define"):
                        file_defines.append(line)

                # Now look for the function name and extract everything until the matching brace
                lines = content.split("\n")
                func_start = None
                in_multiline_comment = False

                for i, line in enumerate(lines):
                    stripped = line.strip()

                    # Track multi-line comment state
                    # Handle /* and */ on the same line or across lines
                    if "/*" in line and "*/" in line:
                        # Comment starts and ends on same line, check position
                        pass  # Don't change state, but skip if function name is inside
                    elif "/*" in line:
                        in_multiline_comment = True
                    elif "*/" in line:
                        in_multiline_comment = False
                        continue  # Skip the closing comment line

                    # Skip lines inside multi-line comments
                    if in_multiline_comment:
                        continue

                    # Skip single-line comments and multi-line comment body lines
                    if stripped.startswith("//") or stripped.startswith("*"):
                        continue

                    # Look for function definition line (contains function name and opening parenthesis)
                    if func_name in line and "(" in line:
                        # Check if this is actually a function definition (not a call)
                        # Function definition should have the pattern: type func_name(params)
                        func_pattern = rf"\b{re.escape(func_name)}\s*\("
                        if re.search(func_pattern, line):
                            func_start = i
                            break

                if func_start is not None:
                    # Find the opening brace
                    brace_line = func_start
                    while brace_line < len(lines) and "{" not in lines[brace_line]:
                        brace_line += 1

                    if brace_line < len(lines):
                        # Count braces to find the end of the function
                        brace_count = 0
                        func_lines = []

                        for i in range(func_start, len(lines)):
                            line = lines[i]
                            func_lines.append(line)

                            # Count braces
                            brace_count += line.count("{")
                            brace_count -= line.count("}")

                            # If we've closed all braces, we're done
                            if brace_count == 0 and "{" in "\n".join(func_lines):
                                break

                        function_def = "\n".join(func_lines)

                        # Prepend #define statements from the same file to the function definition
                        if file_defines:
                            defines_block = "\n".join(file_defines)
                            function_def = defines_block + "\n\n" + function_def

                        # Clean up any triple quotes (docstrings) that might be in the function
                        function_def = re.sub(
                            r'"""[^"]*?"""', "", function_def, flags=re.DOTALL
                        )
                        function_def = re.sub(
                            r"\n\s*\n+", "\n", function_def
                        )  # Remove extra blank lines
                        function_def = function_def.strip()

                        print(
                            f"Found function '{func_name}' in {c_file} with {len(file_defines)} defines"
                        )
                        return function_def

            except Exception as e:
                print(f"Error reading {c_file}: {e}")
                continue

        print(f"Warning: Function '{func_name}' not found in helper files")
        return None

    def _extract_defines_from_code_block(self, code_block: str) -> List[str]:
        """
        Extract #define statements from a code block.

        Args:
            code_block: The code block to extract defines from

        Returns:
            List of #define statements
        """
        lines = code_block.split("\n")
        defines = []

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#define"):
                defines.append(line)

        return defines

    def _remove_includes_from_code_block(self, code_block: str) -> str:
        """
        Remove #include statements from a code block, but preserve #define statements.

        Args:
            code_block: The original code block

        Returns:
            Code block with #include statements removed but #define statements preserved
        """
        lines = code_block.split("\n")
        filtered_lines = []

        for line in lines:
            # Skip lines that are #include statements, but keep #define statements
            stripped_line = line.strip()
            if not stripped_line.startswith("#include"):
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def write_helper_functions_to_file(
        self,
        op_map_response: OperationMap,
        output_path: str = "helper.c",
        helper_functions_dir: str = "test/helper/functions",
        header_file_paths: List[str] = None,
    ) -> None:
        """
        Write all helper functions (both created and searched_from_pool) from OperationMap response to a C file.
        The searched_from_pool functions are retrieved from helper function files.

        Args:
            op_map_response: OperationMap response from GPT
            output_path: Path to save the C file
            helper_functions_dir: Directory containing helper function files
            header_file_paths: List of header file paths to include (optional)
        """
        c_content = []

        # Add header comment
        c_content.append("// Generated helper functions")
        c_content.append("// This file contains assertion and utility functions")
        c_content.append(
            "// Includes both created functions and functions from the helper pool"
        )
        c_content.append("")

        # Add common includes
        c_content.append("#include <stdio.h>")
        c_content.append("#include <stdlib.h>")
        c_content.append("#include <stdint.h>")
        c_content.append("#include <assert.h>")
        c_content.append("#include <string.h>")
        c_content.append("#include <math.h>")  # Add math.h for mathematical functions

        # Add header file includes if provided
        if header_file_paths:
            # Normalize to list if single string provided
            if isinstance(header_file_paths, str):
                header_file_paths = [header_file_paths]

            for header_file_path in header_file_paths:
                if header_file_path:
                    # Calculate relative path from output_path to header_file_path
                    output_dir = os.path.dirname(os.path.abspath(output_path))
                    header_abs_path = os.path.abspath(header_file_path)
                    relative_header_path = os.path.relpath(header_abs_path, output_dir)
                    c_content.append(f'#include "{relative_header_path}"')

        c_content.append("")

        # Collect all #define statements from helper functions
        all_defines = set()  # Use set to avoid duplicates

        # Collect defines from searched_from_pool assertion functions
        if op_map_response.assertion_operations.searched_from_pool:
            for func_name in op_map_response.assertion_operations.searched_from_pool:
                func_def = self._find_function_definition_in_helpers(
                    func_name, helper_functions_dir
                )
                if func_def:
                    defines = self._extract_defines_from_code_block(func_def)
                    print(f"Function definition for {func_name}: {func_def}")
                    all_defines.update(defines)

        # Collect defines from created assertion functions
        if op_map_response.assertion_operations.created:
            for func in op_map_response.assertion_operations.created:
                defines = self._extract_defines_from_code_block(func.code_block)
                all_defines.update(defines)

        # Collect defines from searched_from_pool utility functions
        if op_map_response.utility_operations.searched_from_pool:
            for func_name in op_map_response.utility_operations.searched_from_pool:
                func_def = self._find_function_definition_in_helpers(
                    func_name, helper_functions_dir
                )
                if func_def:
                    defines = self._extract_defines_from_code_block(func_def)
                    all_defines.update(defines)

        # Collect defines from created utility functions
        if op_map_response.utility_operations.created:
            for func in op_map_response.utility_operations.created:
                defines = self._extract_defines_from_code_block(func.code_block)
                all_defines.update(defines)

        # Add all collected defines to the file
        if all_defines:
            c_content.append("// ========== Defines from Helper Functions ==========")
            c_content.append("")
            for define in sorted(all_defines):  # Sort for consistency
                c_content.append(define)
            c_content.append("")

        # Add searched_from_pool assertion functions
        if op_map_response.assertion_operations.searched_from_pool:
            c_content.append(
                "// ========== Searched From Pool - Assertion Operations =========="
            )
            c_content.append("")

            for func_name in op_map_response.assertion_operations.searched_from_pool:
                func_def = self._find_function_definition_in_helpers(
                    func_name, helper_functions_dir
                )
                print(f"Function definition for {func_name}: {func_def}")
                if func_def:
                    c_content.append(f"// Function: {func_name} (from helper pool)")
                    # Remove #include statements from the function definition
                    clean_func_def = self._remove_includes_from_code_block(func_def)
                    c_content.append(clean_func_def)
                    c_content.append("")
                else:
                    c_content.append(
                        f"// Warning: Function {func_name} definition not found in helper files"
                    )
                    c_content.append("")

        # Add created assertion functions
        if op_map_response.assertion_operations.created:
            c_content.append("// ========== Created - Assertion Operations ==========")
            c_content.append("")

            for func in op_map_response.assertion_operations.created:
                # Add function comment
                c_content.append(f"// {func.description}")
                # Remove #include statements from the code block
                clean_code_block = self._remove_includes_from_code_block(
                    func.code_block
                )
                c_content.append(clean_code_block)
                c_content.append("")

        # Add searched_from_pool utility functions
        if op_map_response.utility_operations.searched_from_pool:
            c_content.append(
                "// ========== Searched From Pool - Utility Operations =========="
            )
            c_content.append("")

            for func_name in op_map_response.utility_operations.searched_from_pool:
                func_def = self._find_function_definition_in_helpers(
                    func_name, helper_functions_dir
                )
                if func_def:
                    c_content.append(f"// Function: {func_name} (from helper pool)")
                    # Remove #include statements from the function definition
                    clean_func_def = self._remove_includes_from_code_block(func_def)
                    c_content.append(clean_func_def)
                    c_content.append("")
                else:
                    c_content.append(
                        f"// Warning: Function {func_name} definition not found in helper files"
                    )
                    c_content.append("")

        # Add created utility functions
        if op_map_response.utility_operations.created:
            c_content.append("// ========== Created - Utility Operations ==========")
            c_content.append("")

            for func in op_map_response.utility_operations.created:
                # Add function comment
                c_content.append(f"// {func.description}")
                # Remove #include statements from the code block
                clean_code_block = self._remove_includes_from_code_block(
                    func.code_block
                )
                c_content.append(clean_code_block)
                c_content.append("")

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(c_content))

        # Count total functions
        total_created = len(op_map_response.assertion_operations.created) + len(
            op_map_response.utility_operations.created
        )
        total_searched = len(
            op_map_response.assertion_operations.searched_from_pool
        ) + len(op_map_response.utility_operations.searched_from_pool)
        total_functions = total_created + total_searched

        print(
            f"Generated helper file with {total_functions} functions ({total_created} created, {total_searched} from pool) saved to {output_path}"
        )

    def _extract_function_info_to_json(
        self, op_map_response: OperationMap, output_path: str = "function_info.json"
    ) -> None:
        """
        Extract function information from OperationMap response and save to JSON file.

        Args:
            op_map_response: OperationMap response from GPT
            output_path: Path to save the JSON file
        """
        function_info = {
            "dependency_analysis": {
                "source_functions": op_map_response.dependency_analysis.source_functions,
                "planned_created_functions": [
                    {"name": func.name, "calls": func.calls}
                    for func in op_map_response.dependency_analysis.planned_created_functions
                ],
                "required_from_pool": op_map_response.dependency_analysis.required_from_pool,
            },
            "assertion_operations": {"searched_from_pool": [], "created": []},
            "utility_operations": {"searched_from_pool": [], "created": []},
        }

        # Get all functions from vector database for signature lookup
        all_functions = self.vector_db_manager.get_all_functions()
        func_lookup = {func.get("name"): func for func in all_functions}

        # Process assertion operations
        for func_name in op_map_response.assertion_operations.searched_from_pool:
            # Look up full signature from vector database
            func_info = func_lookup.get(func_name)
            if func_info and "parameters" in func_info:
                # Include full signature
                function_info["assertion_operations"]["searched_from_pool"].append(
                    {
                        "name": func_name,
                        "return_type": func_info.get("return_type", "void"),
                        "parameters": [
                            {"name": param.get("name", ""), "type": param.get("type", "")}
                            for param in func_info.get("parameters", [])
                        ],
                    }
                )
            else:
                # Fallback to name only if not found
                function_info["assertion_operations"]["searched_from_pool"].append(
                    {"name": func_name}
                )

        for func in op_map_response.assertion_operations.created:
            function_info["assertion_operations"]["created"].append(
                {
                    "name": func.name,
                    "description": func.description,
                    "return_type": func.return_type,
                    "parameters": [
                        {"name": param.name, "type": param.type}
                        for param in func.parameters
                    ],
                }
            )

        # Process utility operations
        for func_name in op_map_response.utility_operations.searched_from_pool:
            # Look up full signature from vector database
            func_info = func_lookup.get(func_name)
            if func_info and "parameters" in func_info:
                # Include full signature
                function_info["utility_operations"]["searched_from_pool"].append(
                    {
                        "name": func_name,
                        "return_type": func_info.get("return_type", "void"),
                        "parameters": [
                            {"name": param.get("name", ""), "type": param.get("type", "")}
                            for param in func_info.get("parameters", [])
                        ],
                    }
                )
            else:
                # Fallback to name only if not found
                function_info["utility_operations"]["searched_from_pool"].append(
                    {"name": func_name}
                )

        for func in op_map_response.utility_operations.created:
            function_info["utility_operations"]["created"].append(
                {
                    "name": func.name,
                    "description": func.description,
                    "return_type": func.return_type,
                    "parameters": [
                        {"name": param.name, "type": param.type}
                        for param in func.parameters
                    ],
                }
            )

        # Ensure the dir path valid
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save to JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(function_info, f, indent=2, ensure_ascii=False)

        print(f"Function information saved to {output_path}")

    def process_operation_map_response(
        self,
        op_map_response: OperationMap,
        operation_map_path: str,
        helpers_c_path: str,
        helper_functions_dir: str = "test/helper/functions",
        header_file_paths: List[str] = None,
    ) -> None:
        """
        Process the OperationMap response and generate both JSON and C files.

        Args:
            op_map_response: OperationMap response from GPT
            operation_map_path: Path to save the operation map JSON file
            helpers_c_path: Path to save the helpers C file
            helper_functions_dir: Directory containing helper function files
            header_file_paths: List of header file paths to include
        """
        self._extract_function_info_to_json(op_map_response, operation_map_path)
        self.write_helper_functions_to_file(
            op_map_response, helpers_c_path, helper_functions_dir, header_file_paths
        )
