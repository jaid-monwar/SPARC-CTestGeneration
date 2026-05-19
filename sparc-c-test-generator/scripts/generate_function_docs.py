#!/usr/bin/env python3
"""
Generate comprehensive Doxygen documentation for C functions

This script orchestrates the documentation generation process:
1. Reads atomic function files from tmp/function-files/
2. Reads execution paths from tmp/paths/
3. Extracts function dependencies from AST
4. Generates detailed documentation for each function

Usage:
    python scripts/generate_function_docs.py <subject_name> [options]

Examples:
    python scripts/generate_function_docs.py bst
    python scripts/generate_function_docs.py qsort --output-dir docs/generated
    python scripts/generate_function_docs.py insert --single-function
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apis.agents.function_documentation_generator import FunctionDocGenerator
from apis.token_calculator import get_token_calculator


class DependencyExtractor:
    """Extract function dependencies from the AST"""

    def __init__(self, ast_data: Dict):
        self.ast_data = ast_data
        self.functions = {}  # function_name -> function_node
        self.dependencies = {}  # function_name -> set of dependencies

    def extract_dependencies(self) -> Dict[str, List[str]]:
        """
        Extract function dependencies from the AST.
        Returns a dict mapping function_name -> list of required function names.
        """
        root_node = self.ast_data.get('root_node', {})

        # First pass: Find all function definitions
        self._find_all_functions(root_node)

        # Second pass: Analyze dependencies for each function
        for func_name, func_node in self.functions.items():
            deps = set()
            self._find_function_calls(func_node, deps)
            self.dependencies[func_name] = sorted(list(deps))

        return self.dependencies

    def _find_all_functions(self, node: Dict):
        """Recursively find all function definitions in the AST."""
        if node.get('type') == 'function_definition':
            func_name = self._extract_function_name(node)
            if func_name:
                self.functions[func_name] = node

        # Recursively search children
        for child in node.get('children', []):
            self._find_all_functions(child)

    def _extract_function_name(self, func_node: Dict) -> Optional[str]:
        """Extract the function name from a function_definition node."""
        for child in func_node.get('children', []):
            name = self._find_identifier_in_declarator(child)
            if name:
                return name
        return None

    def _find_identifier_in_declarator(self, node: Dict) -> Optional[str]:
        """Find the identifier in a declarator node."""
        if node.get('type') == 'identifier':
            return node.get('text', '')

        if node.get('type') in ['function_declarator', 'pointer_declarator']:
            for child in node.get('children', []):
                name = self._find_identifier_in_declarator(child)
                if name:
                    return name

        return None

    def _find_function_calls(self, node: Dict, deps: Set[str]):
        """Find all function calls within a function body."""
        if node.get('type') == 'call_expression':
            for child in node.get('children', []):
                if child.get('type') == 'identifier':
                    called_func = child.get('text', '')
                    # Only track calls to user-defined functions
                    if called_func in self.functions:
                        deps.add(called_func)
                    break

        # Recursively search all children
        for child in node.get('children', []):
            self._find_function_calls(child, deps)


def load_ast_file(subject_name: str, ast_dir: str) -> Dict:
    """
    Load the AST file for a subject.

    Args:
        subject_name: Name of the subject (e.g., 'bst', 'qsort')
        ast_dir: Directory containing AST files

    Returns:
        AST data as dictionary
    """
    # Try different possible AST file names
    possible_files = [
        f"{subject_name}_c_ast.json",
        f"{subject_name}.json",
        f"{subject_name}_ast.json"
    ]

    for filename in possible_files:
        ast_file = os.path.join(ast_dir, filename)
        if os.path.exists(ast_file):
            print(f"📂 Loading AST from: {ast_file}")
            try:
                with open(ast_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error loading AST file: {e}")
                return {}

    print(f"❌ No AST file found for subject '{subject_name}' in {ast_dir}")
    print(f"   Looked for: {', '.join(possible_files)}")
    return {}


def get_available_functions(function_dir: str, paths_dir: str) -> List[str]:
    """
    Get list of available functions based on function files and paths.

    Args:
        function_dir: Directory containing function C files
        paths_dir: Directory containing path JSON files

    Returns:
        List of function names that have both function and path files
    """
    if not os.path.exists(function_dir):
        print(f"⚠️ Function files directory not found: {function_dir}")
        return []

    if not os.path.exists(paths_dir):
        print(f"⚠️ Paths directory not found: {paths_dir}")
        return []

    # Get functions that have both function files and path files
    func_files = {f[:-2] for f in os.listdir(function_dir) if f.endswith('.c')}
    path_files = {f[:-5] for f in os.listdir(paths_dir) if f.endswith('.json')}

    available_functions = sorted(func_files & path_files)

    if not available_functions:
        print("⚠️ No functions found with both function and path files")
    else:
        print(f"✅ Found {len(available_functions)} functions with complete data")

    return available_functions


def main():
    """Main function to orchestrate documentation generation."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive Doxygen documentation for C functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_function_docs.py bst
  python scripts/generate_function_docs.py qsort --output-dir docs/generated
  python scripts/generate_function_docs.py bst --single-function insert
  python scripts/generate_function_docs.py bst --model gpt-4o-mini

This script will:
  1. Load atomic function files from tmp/function-files/
  2. Load execution paths from tmp/paths/
  3. Extract function dependencies from AST in tmp/ast/
  4. Generate detailed Doxygen documentation for each function
  5. Save documentation to the output directory
        """
    )

    parser.add_argument(
        'subject',
        help='Subject name (e.g., bst, qsort) or function name if --single-function'
    )

    parser.add_argument(
        '--single-function',
        metavar='FUNCTION_NAME',
        help='Generate documentation for a single function only'
    )

    parser.add_argument(
        '--function-dir',
        default='tmp/function-files',
        help='Directory containing function files (default: tmp/function-files)'
    )

    parser.add_argument(
        '--paths-dir',
        default='tmp/paths',
        help='Directory containing path JSON files (default: tmp/paths)'
    )

    parser.add_argument(
        '--ast-dir',
        default='tmp/ast',
        help='Directory containing AST JSON files (default: tmp/ast)'
    )

    parser.add_argument(
        '--output-dir',
        default='tmp/docs',
        help='Output directory for generated documentation (default: tmp/docs)'
    )

    parser.add_argument(
        '--model',
        choices=['gpt', 'gemini', 'openrouter', 'deepseek'],
        default='gpt',
        help='LLM provider: gpt for OpenAI gpt-4.1, gemini for Gemini 2.5 Flash, openrouter for OpenRouter, deepseek for DeepSeek (default: gpt)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.0,
        help='GPT temperature for generation (default: 0.3)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Set the default LLM provider before creating any GPT_Connection instances
    from apis.gpt import set_default_provider
    set_default_provider(args.model)

    # Get absolute paths
    function_dir = os.path.abspath(args.function_dir)
    paths_dir = os.path.abspath(args.paths_dir)
    ast_dir = os.path.abspath(args.ast_dir)
    output_dir = os.path.abspath(args.output_dir)

    print("\n" + "="*60)
    print("🚀 C Function Documentation Generator")
    print("="*60)
    print(f"Subject:        {args.subject}")
    print(f"Function files: {function_dir}")
    print(f"Path files:     {paths_dir}")
    print(f"AST files:      {ast_dir}")
    print(f"Output:         {output_dir}")
    print(f"Model:          {args.model}")
    print(f"Temperature:    {args.temperature}")
    print("="*60)

    # Load AST and extract dependencies
    ast_data = load_ast_file(args.subject, ast_dir)
    dependencies = {}

    if ast_data:
        extractor = DependencyExtractor(ast_data)
        dependencies = extractor.extract_dependencies()
        print(f"📊 Extracted dependencies for {len(dependencies)} functions")
        if args.verbose and dependencies:
            print("\nFunction Dependencies:")
            for func, deps in dependencies.items():
                if deps:
                    print(f"  {func} → {', '.join(deps)}")
                else:
                    print(f"  {func} → (no dependencies)")
    else:
        print("⚠️ Proceeding without dependency information")

    # Initialize documentation generator (uses default provider set above)
    doc_generator = FunctionDocGenerator()

    # Prepare function list
    if args.single_function:
        # Single function mode
        function_list = [{
            "name": args.single_function,
            "required_functions": dependencies.get(args.single_function, [])
        }]
        print(f"\n📝 Generating documentation for single function: {args.single_function}")
    else:
        # Get all available functions
        available_functions = get_available_functions(function_dir, paths_dir)

        if not available_functions:
            print("\n❌ No functions available for documentation generation")
            sys.exit(1)

        # Build function list with dependencies
        function_list = []
        for func_name in available_functions:
            function_list.append({
                "name": func_name,
                "required_functions": dependencies.get(func_name, [])
            })

        print(f"\n📝 Preparing to generate documentation for {len(function_list)} functions")

    # Generate documentation
    if len(function_list) == 1:
        # Single function - use direct generation
        func_info = function_list[0]
        func_name = func_info["name"]
        func_file = os.path.join(function_dir, f"{func_name}.c")
        paths_file = os.path.join(paths_dir, f"{func_name}.json")

        if not os.path.exists(func_file):
            print(f"❌ Function file not found: {func_file}")
            sys.exit(1)

        if not os.path.exists(paths_file):
            print(f"❌ Paths file not found: {paths_file}")
            sys.exit(1)

        documentation = doc_generator.generate_documentation(
            atomic_file_path=func_file,
            paths_file_path=paths_file,
            function_name=func_name,
            required_functions=func_info["required_functions"],
            temperature=args.temperature
        )

        # Save documentation
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{func_name}_doc.txt")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(documentation)
            print(f"\n✅ Documentation saved to: {output_file}")
            print("\n" + "="*60)
            print("Generated Documentation:")
            print("="*60)
            print(documentation)
        except Exception as e:
            print(f"❌ Error saving documentation: {e}")
            sys.exit(1)

    else:
        # Batch generation
        doc_map = doc_generator.generate_batch_documentation(
            function_list=function_list,
            atomic_dir=function_dir,
            paths_dir=paths_dir,
            output_dir=output_dir,
            temperature=args.temperature
        )

        if doc_map:
            print(f"\n✅ Successfully generated documentation for {len(doc_map)} functions")
            print(f"📁 Documentation files saved in: {output_dir}")

            # Print summary
            print("\n" + "="*60)
            print("Generation Summary:")
            print("="*60)
            for func_name in sorted(doc_map.keys()):
                doc_file = os.path.join(output_dir, f"{func_name}_doc.txt")
                print(f"  ✓ {func_name} → {doc_file}")
        else:
            print("\n❌ No documentation was generated")
            sys.exit(1)

    print("\n✨ Documentation generation complete!")

    # Save token usage for function documentation step
    token_calculator = get_token_calculator()
    token_calculator.set_output_dir(output_dir)
    token_calculator.print_summary()
    token_file = token_calculator.save(detailed=True)
    print(f"📊 Token usage saved to: {token_file}")


if __name__ == "__main__":
    main()