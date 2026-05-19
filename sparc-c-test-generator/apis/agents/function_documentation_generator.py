"""
Function Documentation Generator Agent
Generates comprehensive Doxygen-style documentation for C functions.
"""

import os
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from apis.gpt import GPT_Connection
from apis.prompts.function_documentation_prompt import (
    function_doc_sys_prompt_template,
    function_doc_user_prompt_template,
)
from pydantic import BaseModel
from typing import List as TypingList


class ParameterDoc(BaseModel):
    """Documentation for a single parameter."""
    name: str
    description: str


class StructuredFunctionDoc(BaseModel):
    """Structured representation of function documentation."""
    function_name: str
    brief: str
    details: str
    parameters: TypingList[ParameterDoc]
    return_description: str
    notes: TypingList[str]
    dependencies: TypingList[str]


class FunctionDocGenerator:
    """Agent responsible for generating detailed function documentation."""

    def __init__(self, model: str = None):
        """
        Initialize the Function Documentation Generator.

        Args:
            model: Model to use for generation. If None, uses the default for the provider.
        """
        self.gpt_connection = GPT_Connection(model=model)

    def _read_file_content(self, filepath: str) -> str:
        """
        Read content from a file.

        Args:
            filepath: Path to the file

        Returns:
            File content as string, or empty string if error
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Error: File not found: {filepath}")
            return ""
        except Exception as e:
            print(f"❌ Error reading file {filepath}: {e}")
            return ""

    def _load_json_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load JSON content from a file.

        Args:
            filepath: Path to the JSON file

        Returns:
            Parsed JSON as dictionary, or empty dict if error
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: JSON file not found: {filepath}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON from {filepath}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error loading JSON file {filepath}: {e}")
            return {}

    def _extract_function_code(self, atomic_file_content: str, function_name: str) -> str:
        """
        Extract just the target function code from the atomic file.

        Args:
            atomic_file_content: Full content of the atomic C file
            function_name: Name of the target function

        Returns:
            The function implementation code
        """
        # The atomic files contain the function and its dependencies
        # We need to extract just the target function
        lines = atomic_file_content.split('\n')

        # Find the start of the target function
        function_start = -1
        for i, line in enumerate(lines):
            # Look for function signature
            if function_name in line and '(' in line and '{' in line:
                function_start = i
                break
            elif function_name in line and '(' in line:
                # Function signature might span multiple lines
                for j in range(i, min(i + 5, len(lines))):
                    if '{' in lines[j]:
                        function_start = i
                        break

        if function_start == -1:
            # If we can't find it with the above method, return the whole content
            # This might happen if the function has a complex signature
            return atomic_file_content

        # Find the end of the function by counting braces
        brace_count = 0
        function_end = function_start
        in_function = False

        for i in range(function_start, len(lines)):
            line = lines[i]
            for char in line:
                if char == '{':
                    brace_count += 1
                    in_function = True
                elif char == '}':
                    brace_count -= 1
                    if in_function and brace_count == 0:
                        function_end = i
                        break
            if in_function and brace_count == 0:
                break

        # Extract the function code
        function_lines = lines[function_start:function_end + 1]
        return '\n'.join(function_lines)

    def generate_documentation(
        self,
        atomic_file_path: str,
        paths_file_path: str = None,  # Deprecated: no longer used
        function_name: str = None,
        required_functions: List[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 8192
    ) -> str:
        """
        Generate professional documentation for a C function.

        Args:
            atomic_file_path: Path to the atomic C file containing the function
            paths_file_path: Deprecated, no longer used (kept for backward compatibility)
            function_name: Name of the function to document
            required_functions: List of functions this function depends on
            temperature: GPT temperature for generation
            max_tokens: Maximum tokens for the response

        Returns:
            Generated Doxygen-style documentation string
        """
        # Note: paths_file_path is kept for backward compatibility but no longer used
        print(f"\n📝 Generating documentation for function: {function_name}")

        # Read the atomic file (includes function + dependency signatures)
        atomic_content = self._read_file_content(atomic_file_path)
        if not atomic_content:
            return f"// Error: Could not read atomic file {atomic_file_path}"

        # Use the full atomic file content - it includes dependency signatures
        function_code = atomic_content

        # Format required functions list
        req_funcs_str = ", ".join(required_functions) if required_functions else "None"

        # Build the prompts
        system_prompt = function_doc_sys_prompt_template

        user_prompt = function_doc_user_prompt_template.format(
            function_name=function_name,
            function_code=function_code,
            required_functions=req_funcs_str
        )

        # Generate documentation using GPT
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            documentation = self.gpt_connection.generate_chat_completion(
                messages=messages,
                temperature=temperature,
                context=f"function_documentation_{function_name}",
                max_tokens=max_tokens
            )

            print(f"✅ Successfully generated documentation for {function_name}")
            return documentation

        except Exception as e:
            print(f"❌ Error generating documentation for {function_name}: {e}")
            return f"// Error generating documentation: {str(e)}"

    def generate_structured_documentation(
        self,
        atomic_file_path: str,
        paths_file_path: str = None,  # Deprecated: no longer used
        function_name: str = None,
        required_functions: List[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ) -> Optional[StructuredFunctionDoc]:
        """
        Generate structured (JSON-friendly) documentation for a C function.

        Args:
            atomic_file_path: Path to the atomic C file containing the function
            paths_file_path: Deprecated, no longer used (kept for backward compatibility)
            function_name: Name of the function to document
            required_functions: List of functions this function depends on
            temperature: GPT temperature for generation
            max_tokens: Maximum tokens for the response

        Returns:
            StructuredFunctionDoc object with parsed documentation, or None if error
        """
        # Note: paths_file_path is kept for backward compatibility but no longer used
        print(f"\n📊 Generating structured documentation for function: {function_name}")

        # Read the atomic file (includes function + dependency signatures)
        atomic_content = self._read_file_content(atomic_file_path)
        if not atomic_content:
            return None

        # Use the full atomic file content - it includes dependency signatures
        function_code = atomic_content

        # Format required functions
        req_funcs_str = ", ".join(required_functions) if required_functions else "None"

        # Build structured prompt
        system_prompt = """You are a technical writer creating C function documentation.
Output valid JSON with this structure:
{
  "function_name": "name",
  "brief": "one-line description",
  "details": "2-3 sentence explanation of purpose and behavior",
  "parameters": [{"name": "param1", "description": "purpose and constraints"}, ...],
  "return_description": "what is returned, success/failure values",
  "notes": ["memory ownership note", "error handling note", ...],
  "dependencies": ["function1", "function2", ...]
}"""

        user_prompt = f"""Generate documentation for this C function:

**Function**: {function_name}

```c
{function_code}
```

**Dependencies**: {req_funcs_str}

Output only valid JSON."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            result = self.gpt_connection.generate_chat_completion(
                messages=messages,
                temperature=temperature,
                context=f"structured_doc_{function_name}",
                max_tokens=max_tokens,
                response_model=StructuredFunctionDoc
            )

            print(f"✅ Successfully generated structured documentation for {function_name}")
            return result

        except Exception as e:
            print(f"❌ Error generating structured documentation for {function_name}: {e}")
            return None

    def _process_single_function_doc(
        self,
        func_info: Dict[str, Any],
        atomic_dir: str,
        paths_dir: str,
        output_dir: str,
        temperature: float,
        batch_num: int,
        total_batches: int
    ) -> tuple[str, str, bool]:
        """
        Process documentation generation for a single function.

        Args:
            func_info: Function info dictionary with name and required_functions
            atomic_dir: Directory containing atomic C files
            paths_dir: Directory containing path JSON files
            output_dir: Directory to save documentation files
            temperature: GPT temperature for generation
            batch_num: Current batch number (for logging)
            total_batches: Total number of batches (for logging)

        Returns:
            Tuple of (function_name, documentation, success)
        """
        func_name = func_info.get("name")
        if not func_name:
            print("⚠️ Skipping function with no name")
            return "", "", False

        # Construct file paths
        atomic_file = os.path.join(atomic_dir, f"{func_name}.c")
        paths_file = os.path.join(paths_dir, f"{func_name}.json")

        # Check if files exist
        if not os.path.exists(atomic_file):
            print(f"⚠️ Skipping {func_name}: atomic file not found at {atomic_file}")
            return func_name, "", False

        if not os.path.exists(paths_file):
            print(f"⚠️ Skipping {func_name}: paths file not found at {paths_file}")
            return func_name, "", False

        # Generate documentation
        required_functions = func_info.get("required_functions", [])
        print(f"[Batch {batch_num}/{total_batches}] 📝 Processing: {func_name}")

        documentation = self.generate_documentation(
            atomic_file_path=atomic_file,
            paths_file_path=paths_file,
            function_name=func_name,
            required_functions=required_functions,
            temperature=temperature
        )

        # Save individual documentation file
        doc_file_path = os.path.join(output_dir, f"{func_name}_doc.txt")
        try:
            with open(doc_file_path, "w", encoding="utf-8") as f:
                f.write(documentation)
            print(f"[Batch {batch_num}/{total_batches}] 💾 Saved: {func_name} → {doc_file_path}")
        except Exception as e:
            print(f"❌ Error saving documentation for {func_name}: {e}")
            return func_name, documentation, False

        return func_name, documentation, True

    def generate_batch_documentation(
        self,
        function_list: List[Dict[str, Any]],
        atomic_dir: str,
        paths_dir: str,
        output_dir: str,
        temperature: float = 0.0,
        max_workers: int = 10
    ) -> Dict[str, str]:
        """
        Generate documentation for multiple functions in parallel batches.

        Args:
            function_list: List of dictionaries with function info
                          Each dict should have: name, required_functions (optional)
            atomic_dir: Directory containing atomic C files
            paths_dir: Directory containing path JSON files
            output_dir: Directory to save documentation files
            temperature: GPT temperature for generation
            max_workers: Maximum number of parallel workers (default: 10)

        Returns:
            Dictionary mapping function names to their documentation
        """
        total_functions = len(function_list)
        print(f"\n🚀 Generating documentation for {total_functions} functions")
        print(f"⚡ Using parallel processing with max {max_workers} workers")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        documentation_map = {}

        # Split functions into batches of max_workers size
        batch_size = max_workers
        total_batches = (total_functions + batch_size - 1) // batch_size  # Ceiling division

        print(f"📊 Processing in {total_batches} batch(es)")
        print("="*60)

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_functions)
            batch_functions = function_list[start_idx:end_idx]
            batch_num = batch_idx + 1

            print(f"\n🔄 Batch {batch_num}/{total_batches}: Processing functions {start_idx + 1}-{end_idx}")
            print("-"*60)

            # Process this batch in parallel
            with ThreadPoolExecutor(max_workers=min(len(batch_functions), max_workers)) as executor:
                # Submit all tasks for this batch
                future_to_func = {
                    executor.submit(
                        self._process_single_function_doc,
                        func_info,
                        atomic_dir,
                        paths_dir,
                        output_dir,
                        temperature,
                        batch_num,
                        total_batches
                    ): func_info.get("name", "unknown")
                    for func_info in batch_functions
                }

                # Collect results as they complete
                for future in as_completed(future_to_func):
                    func_name = future_to_func[future]
                    try:
                        result_name, documentation, success = future.result()
                        if success and result_name and documentation:
                            documentation_map[result_name] = documentation
                    except Exception as e:
                        print(f"❌ Exception while processing {func_name}: {e}")

            print(f"✅ Batch {batch_num}/{total_batches} complete: Generated {len([f for f in batch_functions if f.get('name') in documentation_map])}/{len(batch_functions)} docs")

        print("\n" + "="*60)

        # Save combined documentation
        combined_doc_path = os.path.join(output_dir, "all_functions_documented.json")
        try:
            with open(combined_doc_path, "w", encoding="utf-8") as f:
                json.dump(documentation_map, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved all documentation to {combined_doc_path}")
        except Exception as e:
            print(f"❌ Error saving combined documentation: {e}")

        print(f"✨ Documentation generation complete! Generated {len(documentation_map)}/{total_functions} documentation blocks")
        return documentation_map