#!/usr/bin/env python3
"""
Function Extractor from Tree-sitter AST

This script takes a Tree-sitter AST JSON file as input and generates independent
C files for each function found in the AST. Each generated file contains:
- The target function's full implementation
- Forward declarations (signatures) for dependency functions
- Required struct definitions

This minimal format is optimized for both CFG generation and LLM context.

Usage:
    python create_atomic_files.py <ast_file.json>

Example:
    python create_atomic_files.py bst.json
    python create_atomic_files.py bst.json --output-dir tmp/function-files
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class FunctionExtractor:
    def __init__(self, ast_data: Dict[str, Any]):
        """Initialize the extractor with parsed AST data."""
        self.ast_data = ast_data
        self.functions = {}  # function_name -> function_node
        self.structs = {}    # struct_name -> struct_node
        self.includes = []   # list of include statements
        self.dependencies = {}  # function_name -> set of dependencies
        self.source_code = ""

        # Load source code if available
        if 'file_path' in ast_data:
            try:
                with open(ast_data['file_path'], 'r') as f:
                    self.source_code = f.read()
            except FileNotFoundError:
                print(f"Warning: Source file {ast_data['file_path']} not found")

        self._parse_ast()
        self._analyze_dependencies()

    def _parse_ast(self):
        """Parse the AST and extract functions, structs, and includes."""
        root_node = self.ast_data['root_node']
        self._traverse_node(root_node)

    def _traverse_node(self, node: Dict[str, Any]):
        """Recursively traverse AST nodes to find functions, structs, and includes."""
        node_type = node.get('type', '')

        if node_type == 'function_definition':
            self._extract_function(node)
        elif node_type == 'struct_specifier':
            self._extract_struct(node)
        elif node_type == 'preproc_include':
            self._extract_include(node)

        # Recursively traverse children
        for child in node.get('children', []):
            self._traverse_node(child)

    def _extract_function(self, node: Dict[str, Any]):
        """Extract function information from function_definition node."""
        func_name = self._get_function_name(node)
        if func_name:
            self.functions[func_name] = node
            print(f"Found function: {func_name}")

    def _get_function_name(self, func_node: Dict[str, Any]) -> Optional[str]:
        """Extract function name from function_definition node."""
        # Navigate through the function definition structure
        for child in func_node.get('children', []):
            if child.get('type') == 'pointer_declarator':
                # For functions returning pointers
                return self._get_name_from_declarator(child)
            elif child.get('type') == 'function_declarator':
                # For functions not returning pointers
                return self._get_name_from_declarator(child)
            elif 'function_declarator' in str(child):
                # Recursive search in complex structures
                name = self._find_function_name_recursive(child)
                if name:
                    return name
        return None

    def _get_name_from_declarator(self, declarator: Dict[str, Any]) -> Optional[str]:
        """Extract function name from declarator node."""
        for child in declarator.get('children', []):
            if child.get('type') == 'function_declarator':
                return self._get_name_from_declarator(child)
            elif child.get('type') == 'identifier':
                return child.get('text', '')
        return None

    def _find_function_name_recursive(self, node: Dict[str, Any]) -> Optional[str]:
        """Recursively search for function name in nested structures."""
        if node.get('type') == 'identifier':
            return node.get('text', '')

        for child in node.get('children', []):
            if child.get('type') == 'function_declarator':
                name = self._find_function_name_recursive(child)
                if name:
                    return name
            elif child.get('type') == 'identifier':
                return child.get('text', '')
        return None

    def _extract_struct(self, node: Dict[str, Any]):
        """Extract struct information from struct_specifier node."""
        struct_name = self._get_struct_name(node)
        if struct_name and self._has_field_declaration_list(node):
            self.structs[struct_name] = node
            print(f"Found struct: {struct_name}")

    def _get_struct_name(self, struct_node: Dict[str, Any]) -> Optional[str]:
        """Extract struct name from struct_specifier node."""
        for child in struct_node.get('children', []):
            if child.get('type') == 'type_identifier':
                return child.get('text', '')
        return None

    def _has_field_declaration_list(self, struct_node: Dict[str, Any]) -> bool:
        """Check if struct has field declarations (not just a forward declaration)."""
        for child in struct_node.get('children', []):
            if child.get('type') == 'field_declaration_list':
                return True
        return False

    def _extract_include(self, node: Dict[str, Any]):
        """Extract include statement from preproc_include node."""
        include_text = node.get('text', '').strip()
        if include_text:
            self.includes.append(include_text)
            print(f"Found include: {include_text}")

    def _analyze_dependencies(self):
        """Analyze function dependencies by examining function bodies."""
        for func_name, func_node in self.functions.items():
            deps = set()

            # Find function calls in the function body
            self._find_function_calls(func_node, deps)

            # Find struct usage
            self._find_struct_usage(func_node, deps)

            self.dependencies[func_name] = deps
            print(f"Dependencies for {func_name}: {deps}")

    def _find_function_calls(self, node: Dict[str, Any], deps: Set[str]):
        """Find function calls within a node."""
        if node.get('type') == 'call_expression':
            # Get the function name being called
            for child in node.get('children', []):
                if child.get('type') == 'identifier':
                    called_func = child.get('text', '')
                    if called_func in self.functions:
                        deps.add(called_func)
                    break

        # Recursively search children
        for child in node.get('children', []):
            self._find_function_calls(child, deps)

    def _find_struct_usage(self, node: Dict[str, Any], deps: Set[str]):
        """Find struct usage within a node."""
        if node.get('type') == 'struct_specifier':
            struct_name = self._get_struct_name(node)
            if struct_name and struct_name in self.structs:
                deps.add(struct_name)

        # Also check for type_identifier that might reference structs
        if node.get('type') == 'type_identifier':
            type_name = node.get('text', '')
            if type_name in self.structs:
                deps.add(type_name)

        # Recursively search children
        for child in node.get('children', []):
            self._find_struct_usage(child, deps)

    def _get_node_text(self, node: Dict[str, Any]) -> str:
        """Extract text content from AST node using byte positions."""
        if not self.source_code:
            return node.get('text', '')

        start_byte = node.get('start_byte', 0)
        end_byte = node.get('end_byte', 0)

        if start_byte < end_byte <= len(self.source_code):
            return self.source_code[start_byte:end_byte]

        return node.get('text', '')

    def _get_all_dependencies(self, func_name: str, visited: Set[str] = None) -> Set[str]:
        """Get all dependencies recursively (including transitive dependencies)."""
        if visited is None:
            visited = set()

        if func_name in visited:
            return set()

        visited.add(func_name)
        all_deps = set()

        # Add direct dependencies
        direct_deps = self.dependencies.get(func_name, set())
        all_deps.update(direct_deps)

        # Add transitive dependencies for functions
        for dep in direct_deps:
            if dep in self.functions:  # It's a function dependency
                transitive_deps = self._get_all_dependencies(dep, visited.copy())
                all_deps.update(transitive_deps)

        return all_deps

    def generate_function_files(self, output_dir: str = "function_files"):
        """Generate C files for each function.

        Each file contains:
        - Full implementation of the TARGET function only
        - Forward declarations (signatures) for dependency functions
        - Required struct definitions

        This minimal format is optimized for both CFG generation and LLM context.
        """
        os.makedirs(output_dir, exist_ok=True)

        for func_name in self.functions:
            self._generate_function_file(func_name, output_dir)

        print(f"\n✅ Generated {len(self.functions)} function files in '{output_dir}' directory")

    def _generate_function_file(self, func_name: str, output_dir: str):
        """Generate a C file with target function + dependency signatures only."""
        filename = f"{func_name}.c"
        filepath = os.path.join(output_dir, filename)

        # Get all dependencies for this function
        all_deps = self._get_all_dependencies(func_name)

        content = []

        # Add header comment
        content.append("// C program for the function called " + func_name)
        content.append("// Contains target function implementation and dependency signatures")
        content.append("")

        # Add includes
        for include in self.includes:
            content.append(include)
        if self.includes:
            content.append("")

        # Add required structs (full definitions needed for type info)
        struct_deps = [dep for dep in all_deps if dep in self.structs]
        for struct_name in struct_deps:
            struct_code = self._get_node_text(self.structs[struct_name])
            content.append(struct_code + ";")
            content.append("")

        # Add forward declarations for dependency functions (signatures only)
        func_deps = [dep for dep in all_deps if dep in self.functions]
        if func_deps:
            content.append("// Forward declarations for dependency functions")
            for dep_func_name in func_deps:
                if dep_func_name != func_name:  # Don't add signature for target function
                    signature = self._get_function_signature(self.functions[dep_func_name])
                    content.append(signature)
            content.append("")

        # Add target function (full implementation)
        content.append("// Target function implementation")
        func_code = self._get_node_text(self.functions[func_name])
        content.append(func_code)
        content.append("")

        # Write the file
        with open(filepath, 'w') as f:
            f.write('\n'.join(content))

        dep_count = len([d for d in all_deps if d in self.functions and d != func_name])
        print(f"Generated: {filename} ({dep_count} dependency signatures)")

    def _topological_sort_functions(self, func_list: List[str]) -> List[str]:
        """Simple topological sort to order functions based on dependencies."""
        result = []
        remaining = set(func_list)

        while remaining:
            # Find functions with no dependencies in the remaining set
            no_deps = []
            for func in remaining:
                func_deps = self.dependencies.get(func, set())
                # Check if all dependencies are either resolved or not in remaining set
                if not (func_deps & remaining - {func}):
                    no_deps.append(func)

            if not no_deps:
                # Circular dependency or unresolved - just add remaining in order
                no_deps = list(remaining)

            # Add to result and remove from remaining
            for func in no_deps:
                if func in remaining:
                    result.append(func)
                    remaining.remove(func)

        return result

    def _get_function_signature(self, func_node: Dict[str, Any]) -> str:
        """Extract function signature (declaration) from function_definition node.

        Returns a forward declaration like: 'void swap(int* a, int* b);'
        """
        func_text = self._get_node_text(func_node)

        # Find the opening brace that starts the function body
        brace_depth = 0
        body_start = -1

        for i, char in enumerate(func_text):
            if char == '{':
                if brace_depth == 0:
                    body_start = i
                    break
                brace_depth += 1
            elif char == ')':
                # After closing paren of parameters, look for the brace
                pass

        if body_start > 0:
            # Get everything before the body and add semicolon
            signature = func_text[:body_start].strip()
            return signature + ";"

        # Fallback: return full text if we can't parse it
        return func_text

    def print_analysis(self):
        """Print analysis results."""
        print("\n" + "="*50)
        print("ANALYSIS RESULTS")
        print("="*50)

        print(f"\nIncludes found: {len(self.includes)}")
        for include in self.includes:
            print(f"  - {include}")

        print(f"\nStructs found: {len(self.structs)}")
        for struct_name in self.structs:
            print(f"  - {struct_name}")

        print(f"\nFunctions found: {len(self.functions)}")
        for func_name in self.functions:
            deps = self.dependencies.get(func_name, set())
            print(f"  - {func_name}: {deps}")


def main():
    """Main function to handle command line arguments and execute extraction."""
    parser = argparse.ArgumentParser(
        description="Extract functions from Tree-sitter AST and generate independent C files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_atomic_files.py bst.json
  python create_atomic_files.py rgba.json --output-dir tmp/function-files
  python create_atomic_files.py quadtree.json --verbose
        """
    )

    parser.add_argument(
        'ast_file',
        help='Path to the AST JSON file to process'
    )

    parser.add_argument(
        '--output-dir', '-o',
        default='function_files',
        help='Output directory for function files (default: function_files)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Check if AST file exists
    if not os.path.isfile(args.ast_file):
        print(f"❌ Error: AST file '{args.ast_file}' not found.")
        sys.exit(1)

    print(f"🔍 Processing AST file: {args.ast_file}")
    print(f"📂 Output directory: {args.output_dir}")

    try:
        # Load and parse AST
        with open(args.ast_file, 'r') as f:
            ast_data = json.load(f)

        # Create extractor and process
        extractor = FunctionExtractor(ast_data)

        if args.verbose:
            extractor.print_analysis()

        # Generate function files (target + dependency signatures)
        extractor.generate_function_files(args.output_dir)

        print(f"\n🎉 Extraction completed successfully!")
        print(f"📁 Function files: '{args.output_dir}'")

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in AST file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()