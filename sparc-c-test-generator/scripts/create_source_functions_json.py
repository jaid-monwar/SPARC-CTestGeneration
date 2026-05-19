#!/usr/bin/env python3
"""
Create source_functions.json from path JSON files

This script reads path JSON files from tmp/paths/ directory and creates
a source_functions.json file for a specific subject. It also extracts
function signatures from AST JSON files if available.

Usage:
    python scripts/create_source_functions_json.py <subject_name> <output_dir> <paths_dir> <source_file>

Example:
    python scripts/create_source_functions_json.py qsort test/projects/qsort tmp/paths subjects/qsort/qsort.c
    python scripts/create_source_functions_json.py qsort test/projects/qsort tmp/paths subjects/qsort/qsort.c --ast-dir tmp/ast
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Import the signature extraction module
try:
    from extract_function_signatures import load_ast_and_extract_signatures
except ImportError:
    # Try relative import
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from extract_function_signatures import load_ast_and_extract_signatures


def extract_function_names_from_source(source_file):
    """
    Extract function names from the source C file.
    Simple heuristic: look for lines that match function definitions.
    """
    function_names = []

    if not os.path.exists(source_file):
        print(f"Warning: Source file not found: {source_file}")
        return function_names

    with open(source_file, 'r') as f:
        content = f.read()

    # Simple heuristic: find function definitions
    # This is a basic implementation - could be improved
    import re
    # Match patterns like: type function_name(...) {
    pattern = r'^\s*(?:static\s+)?(?:inline\s+)?(?:\w+[\s\*]+)+(\w+)\s*\([^)]*\)\s*\{'
    matches = re.findall(pattern, content, re.MULTILINE)
    function_names = [match for match in matches if not match.startswith('_')]

    return function_names


def load_paths_from_directory(paths_dir, subject_functions, signatures_map=None):
    """
    Load path JSON files from directory, filtering by subject functions.

    Args:
        paths_dir: Directory containing path JSON files
        subject_functions: List of function names to include (from source file)
        signatures_map: Optional dictionary mapping function names to signatures

    Returns:
        List of source function dictionaries with paths and signatures
    """
    source_functions = []

    if not os.path.isdir(paths_dir):
        print(f"[ERROR] Paths directory does not exist: {paths_dir}")
        return source_functions

    # Find all JSON files in the paths directory
    json_files = list(Path(paths_dir).glob("*.json"))

    if not json_files:
        print(f"[WARNING] No path JSON files found in {paths_dir}")
        return source_functions

    print(f"\n[*] Loading path files from {paths_dir}")
    print(f"[*] Filtering for functions: {', '.join(subject_functions)}")

    for json_file in json_files:
        # Function name is the filename without extension
        func_name = json_file.stem

        # Skip if not in subject functions list
        if subject_functions and func_name not in subject_functions:
            print(f"  ⊘ Skipping {func_name} (not in source file)")
            continue

        data = load_json_file(json_file)
        if data and 'paths' in data:
            # Create source function entry
            source_func = {
                "name": func_name,
                "paths": data['paths']
            }

            # Add signature if available
            if signatures_map and func_name in signatures_map:
                source_func["signature"] = signatures_map[func_name]
                print(f"  ✓ Loaded {len(data['paths'])} path(s) for function: {func_name}")
                print(f"    Signature: {signatures_map[func_name]}")
            else:
                print(f"  ✓ Loaded {len(data['paths'])} path(s) for function: {func_name}")
                print(f"    Warning: No signature found")

            source_functions.append(source_func)
        else:
            print(f"  ✗ Failed to load paths from: {json_file.name}")

    return source_functions


def load_json_file(filepath):
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {filepath}: {e}")
        return None


def save_json_file(filepath, data):
    """Save data to a JSON file with pretty formatting."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save {filepath}: {e}")
        return False


def main():
    """Main function to create source_functions.json"""
    parser = argparse.ArgumentParser(
        description="Create source_functions.json from path JSON files with function signatures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create_source_functions_json.py qsort test/projects/qsort tmp/paths subjects/qsort/qsort.c
  python scripts/create_source_functions_json.py bst test/projects/bst tmp/paths subjects/bst/bst.c --ast-dir tmp/ast
        """
    )

    parser.add_argument(
        'subject_name',
        help='Name of the subject (e.g., qsort, bst)'
    )

    parser.add_argument(
        'output_dir',
        help='Output directory where source_functions.json will be created'
    )

    parser.add_argument(
        'paths_dir',
        help='Directory containing path JSON files'
    )

    parser.add_argument(
        'source_file',
        help='Path to the C source file to extract function names'
    )

    parser.add_argument(
        '--ast-dir',
        default=None,
        help='Directory containing AST JSON files (default: tmp/ast)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    print("="*60)
    print("Source Functions JSON Creator")
    print("="*60)
    print(f"Subject:     {args.subject_name}")
    print(f"Output dir:  {args.output_dir}")
    print(f"Paths dir:   {args.paths_dir}")
    print(f"Source file: {args.source_file}")
    if args.ast_dir:
        print(f"AST dir:     {args.ast_dir}")
    print("="*60)

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Extract function names from source file
    print(f"\n[*] Extracting function names from {args.source_file}...")
    subject_functions = extract_function_names_from_source(args.source_file)

    if not subject_functions:
        print("[WARNING] No functions found in source file")
        print("[INFO] Will include all path files from paths directory")
    else:
        print(f"[SUCCESS] Found {len(subject_functions)} function(s): {', '.join(subject_functions)}")

    # Extract function signatures from AST if available
    signatures_map = {}
    if args.ast_dir:
        print(f"\n[*] Extracting function signatures from AST...")
        # Get the source filename without extension
        source_basename = os.path.basename(args.source_file)
        source_name = os.path.splitext(source_basename)[0]

        # Look for AST file
        ast_file = os.path.join(args.ast_dir, f"{source_name}.json")

        if os.path.exists(ast_file):
            print(f"[*] Loading AST from {ast_file}")
            signatures_map = load_ast_and_extract_signatures(ast_file)
            if signatures_map:
                print(f"[SUCCESS] Extracted {len(signatures_map)} function signature(s)")
                for func_name, signature in sorted(signatures_map.items()):
                    print(f"  - {func_name}: {signature}")
            else:
                print("[WARNING] No function signatures extracted from AST")
        else:
            print(f"[WARNING] AST file not found: {ast_file}")
            print("[INFO] Proceeding without function signatures")

    # Load paths for subject functions
    source_functions = load_paths_from_directory(args.paths_dir, subject_functions, signatures_map)

    if not source_functions:
        print("\n[WARNING] No source functions loaded")
        return 1

    # Create source_functions.json structure
    output_data = {
        "source_functions": source_functions
    }

    # Save to file
    output_file = os.path.join(args.output_dir, "source_functions.json")
    print(f"\n[*] Saving source_functions.json...")

    if save_json_file(output_file, output_data):
        print(f"[SUCCESS] Created {output_file}")
        print(f"[INFO] Included {len(source_functions)} function(s)")
        for func in source_functions:
            num_paths = len(func.get('paths', []))
            print(f"  - {func['name']}: {num_paths} path(s)")
        return 0
    else:
        print(f"[ERROR] Failed to save {output_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
