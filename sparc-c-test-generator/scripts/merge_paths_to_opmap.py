#!/usr/bin/env python3
"""
Merge Path Data into Operation Map

This script reads path JSON files from tmp/paths/ directory and merges them
into the operation_map.json file under dependency_analysis.source_functions.

Usage:
    python scripts/merge_paths_to_opmap.py <operation_map.json> <paths_directory>

Example:
    python scripts/merge_paths_to_opmap.py test/projects/bst/operation_map.json tmp/paths/
"""

import argparse
import json
import os
import sys
from pathlib import Path


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


def load_paths_from_directory(paths_dir):
    """Load all path JSON files from a directory."""
    paths_data = {}

    if not os.path.isdir(paths_dir):
        print(f"[ERROR] Paths directory does not exist: {paths_dir}")
        return paths_data

    # Find all JSON files in the paths directory
    json_files = list(Path(paths_dir).glob("*.json"))

    if not json_files:
        print(f"[WARNING] No path JSON files found in {paths_dir}")
        return paths_data

    print(f"\n[*] Loading {len(json_files)} path file(s) from {paths_dir}")

    for json_file in json_files:
        # Function name is the filename without extension
        func_name = json_file.stem

        data = load_json_file(json_file)
        if data and 'paths' in data:
            # Extract just the paths array (remove path_id, keep path_id and path)
            paths_data[func_name] = [
                {
                    "path_id": path.get("path_id"),
                    "path": path.get("path")
                }
                for path in data['paths']
            ]
            print(f"  ✓ Loaded {len(paths_data[func_name])} path(s) for function: {func_name}")
        else:
            print(f"  ✗ Failed to load paths from: {json_file.name}")

    return paths_data


def merge_paths_into_opmap(opmap_data, paths_data):
    """Merge path data into operation map's source_functions."""

    # Ensure dependency_analysis exists
    if 'dependency_analysis' not in opmap_data:
        print("[WARNING] 'dependency_analysis' not found in operation map, creating it")
        opmap_data['dependency_analysis'] = {}

    # Ensure source_functions exists
    if 'source_functions' not in opmap_data['dependency_analysis']:
        print("[INFO] 'source_functions' not found, creating it")
        opmap_data['dependency_analysis']['source_functions'] = []

    # Get or initialize source_functions as a list
    source_functions = opmap_data['dependency_analysis']['source_functions']

    # If source_functions is None, initialize as empty list
    if source_functions is None:
        source_functions = []
        opmap_data['dependency_analysis']['source_functions'] = source_functions

    # Create a mapping of existing functions for quick lookup
    existing_funcs = {func['name']: func for func in source_functions if isinstance(func, dict) and 'name' in func}

    # Track statistics
    added_count = 0
    updated_count = 0

    # Merge paths for each function
    for func_name, paths in paths_data.items():
        if func_name in existing_funcs:
            # Update existing function with paths
            existing_funcs[func_name]['paths'] = paths
            updated_count += 1
            print(f"  ✓ Updated paths for existing function: {func_name}")
        else:
            # Add new function entry with paths
            new_func = {
                "name": func_name,
                "paths": paths
            }
            source_functions.append(new_func)
            added_count += 1
            print(f"  ✓ Added new function with paths: {func_name}")

    print(f"\n[*] Merge summary: {updated_count} updated, {added_count} added")

    return opmap_data


def main():
    """Main function to merge paths into operation map."""
    parser = argparse.ArgumentParser(
        description="Merge path data from JSON files into operation_map.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/merge_paths_to_opmap.py test/projects/bst/operation_map.json tmp/paths/
  python scripts/merge_paths_to_opmap.py test/projects/qsort/operation_map.json tmp/paths/ --backup
        """
    )

    parser.add_argument(
        'operation_map',
        help='Path to the operation_map.json file to update'
    )

    parser.add_argument(
        'paths_directory',
        help='Directory containing path JSON files'
    )

    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create a backup of the original operation_map.json'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.isfile(args.operation_map):
        print(f"[ERROR] Operation map file not found: {args.operation_map}")
        sys.exit(1)

    if not os.path.isdir(args.paths_directory):
        print(f"[ERROR] Paths directory not found: {args.paths_directory}")
        sys.exit(1)

    print("="*60)
    print("Path Merger - Integrating CFG Paths into Operation Map")
    print("="*60)
    print(f"Operation Map: {args.operation_map}")
    print(f"Paths Dir:     {args.paths_directory}")
    print("="*60)

    # Create backup if requested
    if args.backup:
        backup_path = f"{args.operation_map}.backup"
        try:
            import shutil
            shutil.copy2(args.operation_map, backup_path)
            print(f"\n[*] Backup created: {backup_path}")
        except Exception as e:
            print(f"[WARNING] Failed to create backup: {e}")

    # Load operation map
    print(f"\n[*] Loading operation map...")
    opmap_data = load_json_file(args.operation_map)
    if opmap_data is None:
        sys.exit(1)

    # Load paths from directory
    paths_data = load_paths_from_directory(args.paths_directory)

    if not paths_data:
        print("\n[WARNING] No path data loaded, operation map will not be modified")
        sys.exit(0)

    # Merge paths into operation map
    print(f"\n[*] Merging paths into operation map...")
    updated_opmap = merge_paths_into_opmap(opmap_data, paths_data)

    # Save updated operation map
    print(f"\n[*] Saving updated operation map...")
    if save_json_file(args.operation_map, updated_opmap):
        print(f"[SUCCESS] Operation map updated successfully: {args.operation_map}")
        return 0
    else:
        print(f"[ERROR] Failed to save updated operation map")
        return 1


if __name__ == "__main__":
    sys.exit(main())
