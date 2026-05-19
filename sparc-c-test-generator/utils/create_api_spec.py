import sys
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

from clang.cindex import Config
Config.set_library_file("/usr/lib/llvm-14/lib/libclang.so")

from clang import cindex


def find_include_files(source_file: str) -> List[str]:
    """Extract all #include statements from a C file."""
    includes = []
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all #include statements (e.g. #include <stdio.h> or #include "myheader.h")
        include_pattern = r'#include\s+[<"]([^>"]+)[>"]'
        matches = re.findall(include_pattern, content)
        includes.extend(matches)
    except Exception as e:
        print(f"[Warning] Could not read file {source_file}: {e}", file=sys.stderr)
    
    return includes


def resolve_header_path(include_name: str, source_file: str, search_paths: List[str]) -> str:
    """Resolve the full path of an included header file."""
    source_dir = os.path.dirname(source_file)
    
    # Search paths in order of priority
    search_locations = [source_dir] + search_paths
    
    for search_dir in search_locations:
        potential_path = os.path.join(search_dir, include_name)
        if os.path.exists(potential_path):
            return os.path.abspath(potential_path)
    
    return None


def find_implementation_files(header_file: str) -> List[str]:
    """
        Find C implementation files that likely implement functions declared in the header.
        Suppose the header file is `myheader.h`, this function will look for:
        1. `myheader.c` in the same directory as `myheader.h`
        2. All `.c` files in the same directory as `myheader.h`
    """
    header_dir = os.path.dirname(header_file)
    header_name = os.path.splitext(os.path.basename(header_file))[0]
    
    implementation_files = []
    
    # Look for files with the same base name
    same_name_c = os.path.join(header_dir, f"{header_name}.c")
    if os.path.exists(same_name_c):
        implementation_files.append(same_name_c)
    
    # Look for all .c files in the same directory
    if os.path.exists(header_dir):
        for file in os.listdir(header_dir):
            if file.endswith('.c'):
                c_file = os.path.join(header_dir, file)
                if c_file not in implementation_files:
                    implementation_files.append(c_file)
    
    return implementation_files


def extract_functions_from_file(source_file: str, clang_args: List[str] = None, base_dir: str = None) -> List[Dict]:
    """Extract function information from a single C file."""
    if clang_args is None:
        clang_args = ['-x', 'c', '-std=c11']
    
    if base_dir is None:
        base_dir = os.getcwd()

    index = cindex.Index.create()

    try:
        tu = index.parse(source_file, args=clang_args)
    except cindex.TranslationUnitLoadError as e:
        print(f"[Warning] Failed to parse source file '{source_file}': {e}", file=sys.stderr)
        return []

    # Read the source file content to extract descriptions
    source_content = ""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_content = f.read()
        source_lines = source_content.split('\n')
    except Exception as e:
        print(f"[Warning] Could not read source file {source_file} for description extraction: {e}", file=sys.stderr)
        source_lines = []

    functions = []

    def extract_function_description(line_number: int) -> str:
        """Extract function description from C-style comments /* */ inside the function body."""
        if not source_content or line_number <= 0:
            return ""
        
        # Convert to 0-based line indexing
        target_line = line_number - 1
        
        # Look for the opening brace of the function to find where the function body starts
        function_start = -1
        function_end = -1
        
        # Find the opening brace after the function declaration
        for i in range(target_line, min(len(source_lines), target_line + 10)):
            if '{' in source_lines[i]:
                function_start = i
                break
        
        if function_start == -1:
            return ""
        
        # Find the matching closing brace for this function
        brace_count = 0
        for i in range(function_start, len(source_lines)):
            line = source_lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                function_end = i
                break
        
        if function_end == -1:
            function_end = min(len(source_lines), function_start + 50)  # Fallback limit
        
        # Extract the function body content
        function_body = '\n'.join(source_lines[function_start:function_end + 1])
        
        # Look for C-style comments /* */ inside the function body
        pattern = r'/\*(.*?)\*/'
        matches = re.findall(pattern, function_body, re.DOTALL)
        
        if matches:
            # Get the first description found in the function body
            description = matches[0].strip()
            
            # Clean up the description - normalize whitespace
            description = re.sub(r'\s+', ' ', description).strip()
            
            return description
        
        return ""

    def visit(node):
        if node.kind == cindex.CursorKind.FUNCTION_DECL:
            # Skip static functions (not global scope)
            if node.storage_class == cindex.StorageClass.STATIC:
                return
            
            # Only include functions with definitions (not just declarations)
            if not node.is_definition():
                return

            # Normalize the location path to be relative
            location_file = str(node.location.file) if node.location.file else source_file
            relative_location = normalize_path(location_file, base_dir)

            # Extract function description
            description = extract_function_description(node.location.line)

            func = {
                "name": node.spelling,
                "return_type": node.result_type.spelling,
                "parameters": [],
                "location": f"{relative_location}:{node.location.line}",
                "source_file": os.path.basename(source_file),
                "description": description
            }

            for c in node.get_children():
                if c.kind == cindex.CursorKind.PARM_DECL:
                    func["parameters"].append({
                        "name": c.spelling,
                        "type": c.type.spelling
                    })

            functions.append(func)

        # Recursively visit child nodes
        for child in node.get_children():
            visit(child)

    visit(tu.cursor)
    return functions


def normalize_path(file_path: str, base_dir: str = None) -> str:
    """Convert absolute path to relative path from base directory."""
    if base_dir is None:
        base_dir = os.getcwd()
    
    abs_path = os.path.abspath(file_path)
    abs_base = os.path.abspath(base_dir)
    
    try:
        return os.path.relpath(abs_path, abs_base)
    except ValueError:
        # If paths are on different drives (Windows), return the original path
        return file_path


def extract_all_functions(source_file: str, search_paths: List[str] = None, clang_args: List[str] = None) -> Dict:
    """Extract functions from a C file and all its dependencies."""
    if search_paths is None:
        search_paths = []
    
    if clang_args is None:
        clang_args = ['-x', 'c', '-std=c11']
    
    # Add common include paths
    source_dir = os.path.dirname(os.path.abspath(source_file))
    if source_dir not in search_paths:
        search_paths.append(source_dir)
    
    # Use current working directory as base for relative paths
    base_dir = os.getcwd()
    
    result = {
        "main_file": normalize_path(source_file, base_dir),
        "functions": [],
        "source_files": {},
        "headers_processed": [],
        "implementation_files": []
    }
    
    processed_files = set()
    
    # Normalize the main source file path
    normalized_source = normalize_path(source_file, base_dir)
    
    # First, extract functions from the main file
    main_functions = extract_functions_from_file(source_file, clang_args, base_dir)
    result["functions"].extend(main_functions)
    result["source_files"][normalized_source] = main_functions
    processed_files.add(os.path.abspath(source_file))
    
    # Find all includes in the main file
    includes = find_include_files(source_file)
    
    for include in includes:
        # Skip system headers (those in angle brackets typically)
        if include.startswith('/') or include in ['stdio.h', 'stdlib.h', 'string.h', 'math.h', 'assert.h']:
            continue
        
        # Resolve header path
        header_path = resolve_header_path(include, source_file, search_paths)
        if not header_path or not os.path.exists(header_path):
            print(f"[Warning] Could not find header file: {include}", file=sys.stderr)
            continue
        
        if header_path in result["headers_processed"]:
            continue
        
        result["headers_processed"].append(normalize_path(header_path, base_dir))
        
        # Find implementation files for this header
        impl_files = find_implementation_files(header_path)
        
        for impl_file in impl_files:
            if os.path.abspath(impl_file) in processed_files:
                continue
            
            normalized_impl = normalize_path(impl_file, base_dir)
            print(f"[+] Processing implementation file: {normalized_impl}")
            impl_functions = extract_functions_from_file(impl_file, clang_args, base_dir)
            
            if impl_functions:
                result["functions"].extend(impl_functions)
                result["source_files"][normalized_impl] = impl_functions
                result["implementation_files"].append(normalized_impl)
                processed_files.add(os.path.abspath(impl_file))
    
    return result


def extract_all_functions_from_folder(folder_path: str, output_dir: str = None, search_paths: List[str] = None, 
                                    clang_args: List[str] = None, recursive: bool = True) -> Dict[str, Dict]:
    """
    Extract functions from all C files in a folder.
    
    Args:
        folder_path: Path to the folder containing C files
        output_dir: Directory to save individual JSON files (optional)
        search_paths: Additional search paths for headers
        clang_args: Additional clang arguments
        recursive: Whether to search subdirectories recursively
    
    Returns:
        Dictionary mapping file paths to their extracted function data
    """
    if not os.path.exists(folder_path):
        print(f"[Error] Folder '{folder_path}' does not exist", file=sys.stderr)
        return {}
    
    if search_paths is None:
        search_paths = []
    
    if clang_args is None:
        clang_args = ['-x', 'c', '-std=c11']
    
    # Add folder to search paths
    abs_folder = os.path.abspath(folder_path)
    if abs_folder not in search_paths:
        search_paths.append(abs_folder)
    
    # Find all C files in the folder
    c_files = []
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.c'):
                    c_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(folder_path):
            if file.endswith('.c'):
                c_files.append(os.path.join(folder_path, file))
    
    if not c_files:
        print(f"[Warning] No C files found in {folder_path}", file=sys.stderr)
        return {}
    
    print(f"[+] Found {len(c_files)} C files in {folder_path}")
    
    results = {}
    
    for c_file in c_files:
        print(f"[+] Processing {c_file}...")
        try:
            result = extract_all_functions(c_file, search_paths, clang_args)
            relative_path = normalize_path(c_file, os.getcwd())
            results[relative_path] = result
            
            # Optionally save individual JSON files
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(c_file))[0]
                json_path = os.path.join(output_dir, f"{base_name}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"[+] Saved {json_path}")
            
        except Exception as e:
            print(f"[Error] Failed to process {c_file}: {e}", file=sys.stderr)
            continue
    
    return results



def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single file: python3 utils/extract_funcs_enhanced.py <source_file.c> <json_output_path> [search_path1] [search_path2] ...")
        print("  Folder mode: python3 utils/extract_funcs_enhanced.py --folder <folder_path> <output_dir> [search_path1] [search_path2] ...")
        print("\nSingle file mode:")
        print("  Extract functions from one C file and its dependencies")
        print("\nFolder mode:")
        print("  Extract functions from all C files in a folder")
        print("  Creates individual JSON files for each C file in output_dir")
        print("  Also creates a predefined functions as 'predefined_functions.json'")
        print("\nOptional search paths can be provided to help locate header files.")
        sys.exit(1)

    # Check if folder mode
    if sys.argv[1] == "--folder":
        if len(sys.argv) < 4:
            print("Folder mode requires: --folder <folder_path> <output_dir> [search_paths...]")
            sys.exit(1)
        
        folder_path = sys.argv[2]
        output_dir = sys.argv[3]
        search_paths = sys.argv[4:] if len(sys.argv) > 4 else []
        
        if not os.path.exists(folder_path):
            print(f"[Error] Folder '{folder_path}' does not exist", file=sys.stderr)
            sys.exit(1)
        
        print(f"[+] Extracting functions from all C files in {folder_path}...")
        results = extract_all_functions_from_folder(folder_path, output_dir, search_paths)
        
        if results:
            # Create predefined functions
            predefined_functions_path = os.path.join(output_dir, "predefined_functions.json")
            create_predefined_functions(results, predefined_functions_path)
            
            print(f"\n[Summary]")
            total_functions = sum(len(result["functions"]) for result in results.values())
            print(f"  Total files processed: {len(results)}")
            print(f"  Total functions extracted: {total_functions}")
            print(f"  Individual JSON files saved to: {output_dir}")
            print(f"  Predefined functions: {predefined_functions_path}")
        else:
            print("[Error] No results obtained from folder processing")
        
    else:
        # Single file mode (original functionality)
        source_path = sys.argv[1]
        json_path = sys.argv[2]
        search_paths = sys.argv[3:] if len(sys.argv) > 3 else []
        
        if not os.path.exists(source_path):
            print(f"[Error] Source file '{source_path}' does not exist", file=sys.stderr)
            sys.exit(1)
        
        print(f"[+] Analyzing {source_path} and its dependencies...")
        result = extract_all_functions(source_path, search_paths)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"[+] Extracted {len(result['functions'])} functions from {len(result['source_files'])} files")
        print(f"[+] Main file: {result['main_file']}")
        print(f"[+] Headers processed: {len(result['headers_processed'])}")
        print(f"[+] Implementation files: {len(result['implementation_files'])}")
        print(f"[+] Results saved to {json_path}")

        print("\n[Summary]")
        for source_file, functions in result['source_files'].items():
            print(f"  {os.path.basename(source_file)}: {len(functions)} functions")


if __name__ == "__main__":
    main()
