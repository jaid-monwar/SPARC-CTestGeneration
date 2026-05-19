#!/usr/bin/env python3
"""
Preprocessor Script - Orchestrates AST generation and function extraction

This script automates the preprocessing pipeline:
1. Generate AST from C source files using ast_generator.py
2. Extract function files from AST using create_atomic_files.py
3. Generate CFG DOT/SVG files for each function
4. Extract execution paths from CFGs

Usage:
    python scripts/preprocessor.py <source_directory>

Example:
    python scripts/preprocessor.py subjects/qsort/
    python scripts/preprocessor.py subjects/bst/
"""

import argparse
import os
import sys
import subprocess
import glob
import json


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n[SUCCESS] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error during {description}")
        print(f"Exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during {description}: {e}")
        return False


def main():
    """Main function to orchestrate the preprocessing pipeline."""
    parser = argparse.ArgumentParser(
        description="Preprocess C source files: Generate AST and extract function files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/preprocessor.py subjects/qsort/
  python scripts/preprocessor.py subjects/bst/ --verbose
  python scripts/preprocessor.py subjects/rgba/src/ --clean
  python scripts/preprocessor.py subjects/qsort/ --skip-cfg

This script will:
  1. Generate AST files in tmp/ast/
  2. Extract function files in tmp/function-files/
  3. Generate CFG DOT and SVG files in tmp/cfg/dot and tmp/cfg/svg
  4. Extract unique paths to tmp/paths/ (deletes detailed JSON files)

Use --skip-cfg to skip steps 3 and 4.
        """
    )

    parser.add_argument(
        'source_path',
        help='C source file or directory containing C source files to process'
    )

    parser.add_argument(
        '--ast-dir',
        default='tmp/ast',
        help='Output directory for AST files (default: tmp/ast)'
    )

    parser.add_argument(
        '--function-dir',
        default='tmp/function-files',
        help='Output directory for function files (default: tmp/function-files)'
    )

    parser.add_argument(
        '--cfg-dot-dir',
        default='tmp/cfg/dot',
        help='Output directory for CFG DOT files (default: tmp/cfg/dot)'
    )

    parser.add_argument(
        '--cfg-svg-dir',
        default='tmp/cfg/svg',
        help='Output directory for CFG SVG files (default: tmp/cfg/svg)'
    )

    parser.add_argument(
        '--paths-dir',
        default='tmp/paths',
        help='Output directory for path JSON files (default: tmp/paths)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean output directories before processing'
    )

    parser.add_argument(
        '--skip-cfg',
        action='store_true',
        help='Skip CFG generation and path extraction steps'
    )

    parser.add_argument(
        '--model',
        choices=['gpt', 'gemini', 'openrouter', 'deepseek'],
        default='gpt',
        help='LLM provider for function documentation: gpt for OpenAI, gemini for Gemini, openrouter for OpenRouter, deepseek for DeepSeek (default: gpt)'
    )

    args = parser.parse_args()

    # Validate source path (file or directory)
    source_path = os.path.abspath(args.source_path)
    
    if os.path.isfile(source_path):
        # Single file mode: use the directory containing the file
        source_file = source_path
        source_dir = os.path.dirname(source_path)
        single_file_mode = True
        print(f"[INFO] Single file mode: processing only {os.path.basename(source_file)}")
    elif os.path.isdir(source_path):
        # Directory mode: process all .c files
        source_file = None
        source_dir = source_path
        single_file_mode = False
    else:
        print(f"[ERROR] Source path '{args.source_path}' does not exist")
        sys.exit(1)
    ast_dir = os.path.abspath(args.ast_dir)
    function_dir = os.path.abspath(args.function_dir)
    cfg_dot_dir = os.path.abspath(args.cfg_dot_dir)
    cfg_svg_dir = os.path.abspath(args.cfg_svg_dir)
    paths_dir = os.path.abspath(args.paths_dir)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("C Source Preprocessor Pipeline")
    print("="*60)
    print(f"Source directory:    {source_dir}")
    print(f"AST output:          {ast_dir}")
    print(f"Function files:      {function_dir}")
    if not args.skip_cfg:
        print(f"CFG DOT output:      {cfg_dot_dir}")
        print(f"CFG SVG output:      {cfg_svg_dir}")
        print(f"Paths output:        {paths_dir}")
    print(f"Project root:        {project_root}")
    print("="*60)

    # Clean directories if requested
    if args.clean:
        print("\n[*] Cleaning output directories...")
        import shutil
        dirs_to_clean = [ast_dir, function_dir]
        if not args.skip_cfg:
            dirs_to_clean.extend([cfg_dot_dir, cfg_svg_dir, paths_dir])
        for dir_path in dirs_to_clean:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                print(f"  Removed: {dir_path}")

    # Create output directories
    os.makedirs(ast_dir, exist_ok=True)
    os.makedirs(function_dir, exist_ok=True)
    if not args.skip_cfg:
        os.makedirs(cfg_dot_dir, exist_ok=True)
        os.makedirs(cfg_svg_dir, exist_ok=True)
        os.makedirs(paths_dir, exist_ok=True)
    print(f"\n[SUCCESS] Output directories ready")

    # Step 3a.1: Generate AST
    ast_generator_script = os.path.join(project_root, 'utils', 'ast_generator.py')

    if not os.path.isfile(ast_generator_script):
        print(f"[ERROR] ast_generator.py not found at {ast_generator_script}")
        sys.exit(1)

    # In single file mode, pass the specific file; otherwise pass the directory
    ast_input = source_file if single_file_mode else source_dir
    
    ast_cmd = [
        sys.executable,
        ast_generator_script,
        ast_input,
        '--output-dir', ast_dir
    ]

    if args.verbose:
        ast_cmd.append('--verbose')

    success = run_command(ast_cmd, "Step 3a.1: AST Generation")

    if not success:
        print("\n[ERROR] Pipeline failed at AST generation step")
        sys.exit(1)

    # Find generated AST files
    ast_files = glob.glob(os.path.join(ast_dir, "*.json"))

    if not ast_files:
        print(f"\n[ERROR] No AST files found in {ast_dir}")
        print("Expected files matching pattern: *.json")
        sys.exit(1)

    print(f"\n[*] Found {len(ast_files)} AST file(s):")
    for ast_file in ast_files:
        print(f"  - {os.path.basename(ast_file)}")

    # Step 3a.2: Extract function files from each AST file
    extractor_script = os.path.join(project_root, 'utils', 'create_atomic_files.py')

    if not os.path.isfile(extractor_script):
        print(f"[ERROR] create_atomic_files.py not found at {extractor_script}")
        sys.exit(1)

    all_success = True

    for i, ast_file in enumerate(ast_files, 1):
        print(f"\n{'='*60}")
        print(f"Step 3a.2.{i}: Extracting functions from {os.path.basename(ast_file)}")
        print(f"{'='*60}")

        extract_cmd = [
            sys.executable,
            extractor_script,
            ast_file,
            '--output-dir', function_dir
        ]

        if args.verbose:
            extract_cmd.append('--verbose')

        success = run_command(
            extract_cmd,
            f"Function extraction from {os.path.basename(ast_file)}"
        )

        if not success:
            all_success = False
            print(f"[WARNING] Failed to extract functions from {os.path.basename(ast_file)}")

    # Count generated function files
    function_files = glob.glob(os.path.join(function_dir, "*.c"))

    # Step 3a.3: Generate CFG for each function (if not skipped)
    if not args.skip_cfg and function_files:
        print(f"\n{'='*60}")
        print(f"Step 3a.3: CFG Generation")
        print(f"{'='*60}")

        render_script = os.path.join(project_root, 'cfg-tool', 'render_function.py')

        if not os.path.isfile(render_script):
            print(f"[WARNING] render_function.py not found at {render_script}")
            print("Skipping CFG generation")
        else:
            cfg_success_count = 0

            for i, func_file in enumerate(function_files, 1):
                # Extract function name from filename (remove .c extension)
                func_name = os.path.splitext(os.path.basename(func_file))[0]

                print(f"\n[{i}/{len(function_files)}] Generating CFG for function: {func_name}")

                # Output paths
                dot_output = os.path.join(cfg_dot_dir, f"{func_name}.dot")
                svg_output = os.path.join(cfg_svg_dir, f"{func_name}.svg")

                # Build command (always use --verbose for proper path extraction)
                cfg_cmd = [
                    sys.executable,
                    render_script,
                    func_file,
                    func_name,
                    '--dot', dot_output,
                    '--out', svg_output,
                    '--verbose'  # Always enable verbose to include code in node labels
                ]

                success = run_command(
                    cfg_cmd,
                    f"CFG generation for {func_name}"
                )

                if success:
                    cfg_success_count += 1
                else:
                    print(f"[WARNING] Failed to generate CFG for {func_name}")

            print(f"\n[*] CFG generation completed: {cfg_success_count}/{len(function_files)} functions")

    # Step 3a.4: Extract paths from CFG DOT files (if not skipped)
    if not args.skip_cfg and function_files:
        print(f"\n{'='*60}")
        print(f"Step 3a.4: Path Extraction")
        print(f"{'='*60}")

        extract_paths_script = os.path.join(project_root, 'cfg-tool', 'extract_cfg_paths.py')

        if not os.path.isfile(extract_paths_script):
            print(f"[WARNING] extract_cfg_paths.py not found at {extract_paths_script}")
            print("Skipping path extraction")
        else:
            # Find all DOT files
            dot_files = glob.glob(os.path.join(cfg_dot_dir, "*.dot"))

            if not dot_files:
                print("[WARNING] No DOT files found for path extraction")
            else:
                path_success_count = 0

                for i, dot_file in enumerate(dot_files, 1):
                    func_name = os.path.splitext(os.path.basename(dot_file))[0]

                    print(f"\n[{i}/{len(dot_files)}] Extracting paths for: {func_name}")

                    # Build command
                    path_cmd = [
                        sys.executable,
                        extract_paths_script,
                        dot_file
                    ]

                    success = run_command(
                        path_cmd,
                        f"Path extraction for {func_name}"
                    )

                    if success:
                        # Move the generated JSON files to paths directory
                        base_name = os.path.splitext(os.path.basename(dot_file))[0]

                        # Move simplified JSON
                        src_json = os.path.join(cfg_dot_dir, f"{base_name}.json")
                        dst_json = os.path.join(paths_dir, f"{base_name}.json")
                        if os.path.exists(src_json):
                            os.rename(src_json, dst_json)

                        # Delete detailed JSON
                        detailed_json = os.path.join(cfg_dot_dir, f"{base_name}_detailed.json")
                        if os.path.exists(detailed_json):
                            os.remove(detailed_json)
                            if args.verbose:
                                print(f"  Deleted: {detailed_json}")

                        path_success_count += 1
                    else:
                        print(f"[WARNING] Failed to extract paths for {func_name}")

                print(f"\n[*] Path extraction completed: {path_success_count}/{len(dot_files)} files")

    # Step 3a.5: Create source_functions.json
    print(f"\n{'='*60}")
    print(f"Step 3a.5: Create source_functions.json")
    print(f"{'='*60}")

    # Extract subject name from source directory
    def extract_subject_name(source_dir):
        """Extract subject name handling src subdirs and version suffixes"""
        basename = os.path.basename(source_dir.rstrip('/'))

        # If basename is 'src', go up one level
        if basename.lower() == 'src':
            parent_dir = os.path.dirname(source_dir.rstrip('/'))
            basename = os.path.basename(parent_dir)

        # Remove version suffixes: -0.4.0, -1.0, -v2, etc.
        import re
        basename = re.sub(r'-v?\d+(\.\d+)*', '', basename)

        return basename

    subject_name = extract_subject_name(source_dir)

    # Determine output directory for source_functions.json
    test_output_dir = os.path.join(project_root, 'test', 'projects', subject_name)
    os.makedirs(test_output_dir, exist_ok=True)

    # Find the main source file
    source_files = glob.glob(os.path.join(source_dir, "*.c"))
    if not source_files:
        print(f"[WARNING] No C source files found in {source_dir}")
        main_source_file = ""
    else:
        # Use the first .c file or try to match subject name
        main_source_file = source_files[0]
        for src_file in source_files:
            if subject_name in os.path.basename(src_file):
                main_source_file = src_file
                break

    if main_source_file:
        # Use the enhanced script that includes dependency tracking
        create_source_functions_script = os.path.join(project_root, 'scripts', 'create_source_functions_json_with_deps.py')

        if not os.path.isfile(create_source_functions_script):
            # Fall back to regular script if enhanced version not found
            create_source_functions_script = os.path.join(project_root, 'scripts', 'create_source_functions_json.py')
            print(f"[INFO] Using regular create_source_functions_json.py (without dependency tracking)")

        if not os.path.isfile(create_source_functions_script):
            print(f"[WARNING] create_source_functions_json script not found")
            print("Skipping source_functions.json creation")
        else:
            # Get the AST file for the subject
            # First try to find any AST file that matches the subject name
            possible_ast_files = glob.glob(os.path.join(ast_dir, "*.json"))
            ast_file_path = None

            for ast_file in possible_ast_files:
                basename = os.path.basename(ast_file)
                # Try exact match first, then partial match
                if basename == f"{subject_name}.json" or subject_name in basename:
                    ast_file_path = ast_file
                    break

            # If no match, use the first AST file (if any)
            if not ast_file_path and possible_ast_files:
                ast_file_path = possible_ast_files[0]
                print(f"[INFO] Using AST file: {os.path.basename(ast_file_path)}")

            if not ast_file_path:
                print(f"[WARNING] No AST file found in {ast_dir}")
                print("Cannot create source_functions.json with dependencies")
                ast_file_path = ""  # Set to empty string to avoid None issues

            # Use different command based on which script we're using
            if 'with_deps' in create_source_functions_script and ast_file_path:
                create_cmd = [
                    sys.executable,
                    create_source_functions_script,
                    subject_name,
                    test_output_dir,
                    paths_dir,
                    ast_file_path  # Enhanced version uses AST file directly
                ]
            else:
                create_cmd = [
                    sys.executable,
                    create_source_functions_script,
                    subject_name,
                    test_output_dir,
                    paths_dir,
                    main_source_file,
                    '--ast-dir', ast_dir
                ]

            if args.verbose:
                create_cmd.append('--verbose')

            success = run_command(
                create_cmd,
                f"Creating source_functions.json for {subject_name}"
            )

            if success:
                print(f"[SUCCESS] Created source_functions.json in {test_output_dir}")

                # Step 3b: Generate function documentation and update source_functions.json
                print(f"\n{'='*60}")
                print(f"Step 3b: Generate Function Documentation")
                print(f"{'='*60}")

                generate_docs_script = os.path.join(project_root, 'scripts', 'generate_function_docs.py')

                if not os.path.isfile(generate_docs_script):
                    print(f"[WARNING] generate_function_docs.py not found at {generate_docs_script}")
                    print("Skipping function documentation generation")
                else:
                    # Create docs output directory
                    docs_output_dir = os.path.join(project_root, 'tmp', 'docs')
                    os.makedirs(docs_output_dir, exist_ok=True)

                    # Generate documentation
                    docs_cmd = [
                        sys.executable,
                        generate_docs_script,
                        subject_name,
                        '--function-dir', function_dir,
                        '--paths-dir', paths_dir,
                        '--ast-dir', ast_dir,
                        '--output-dir', docs_output_dir,
                        '--model', args.model
                    ]

                    if args.verbose:
                        docs_cmd.append('--verbose')

                    success = run_command(
                        docs_cmd,
                        f"Generating function documentation for {subject_name}"
                    )

                    # Always attempt to merge if all_functions_documented.json exists
                    # Update source_functions.json with documentation from all_functions_documented.json
                    print(f"\n[*] Updating source_functions.json with documentation...")

                    try:
                        # Load the all_functions_documented.json file
                        all_docs_file = os.path.join(docs_output_dir, 'all_functions_documented.json')

                        if not os.path.exists(all_docs_file):
                            print(f"[WARNING] Documentation file not found: {all_docs_file}")
                            if success:
                                print(f"[WARNING] Documentation generation reported success but file is missing")
                        else:
                                # Load the documentation
                                with open(all_docs_file, 'r', encoding='utf-8') as f:
                                    all_docs = json.load(f)

                                # Load the source_functions.json
                                source_functions_file = os.path.join(test_output_dir, 'source_functions.json')
                                with open(source_functions_file, 'r', encoding='utf-8') as f:
                                    source_functions_data = json.load(f)

                                # Update each function with its description
                                functions_updated = 0
                                for func in source_functions_data.get('source_functions', []):
                                    func_name = func.get('name')
                                    if func_name and func_name in all_docs:
                                        # Get the ENTIRE documentation text from all_functions_documented.json
                                        description = all_docs[func_name]

                                        # Add description right after name by reconstructing the dict
                                        func_data_with_desc = {}
                                        for key, value in func.items():
                                            func_data_with_desc[key] = value
                                            if key == 'name':
                                                func_data_with_desc['description'] = description

                                        # Update the function data
                                        func.clear()
                                        func.update(func_data_with_desc)
                                        functions_updated += 1
                                        # For multi-line descriptions, only show first line in console
                                        first_line = description.split('\n')[0][:60] if description else ""
                                        print(f"  Updated {func_name}: {first_line}...")
                                    elif func_name:
                                        print(f"  Warning: No documentation found for {func_name} in all_functions_documented.json")

                                # Save the updated source_functions.json
                                with open(source_functions_file, 'w', encoding='utf-8') as f:
                                    json.dump(source_functions_data, f, indent=2)

                                print(f"[SUCCESS] Updated {functions_updated} function(s) with documentation")
                                print(f"[SUCCESS] source_functions.json updated with descriptions")

                    except Exception as e:
                        print(f"[ERROR] Failed to update source_functions.json with documentation: {e}")
                        import traceback
                        traceback.print_exc()
            else:
                print(f"[ERROR] Failed to create source_functions.json")
    else:
        print("[WARNING] No source file found, skipping source_functions.json creation")

    # Summary
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)

    # Count generated files
    func_files = glob.glob(os.path.join(function_dir, "*.c"))
    dot_files = glob.glob(os.path.join(cfg_dot_dir, "*.dot")) if not args.skip_cfg else []
    svg_files = glob.glob(os.path.join(cfg_svg_dir, "*.svg")) if not args.skip_cfg else []
    path_files = glob.glob(os.path.join(paths_dir, "*.json")) if not args.skip_cfg else []

    print(f"\n[*] AST files generated:      {len(ast_files)}")
    print(f"[*] Function files:           {len(func_files)}")
    if not args.skip_cfg:
        print(f"[*] CFG DOT files:            {len(dot_files)}")
        print(f"[*] CFG SVG files:            {len(svg_files)}")
        print(f"[*] Path JSON files:          {len(path_files)}")

    print(f"\nOutput locations:")
    print(f"   AST files:         {ast_dir}")
    print(f"   Function files:    {function_dir}")
    if not args.skip_cfg:
        print(f"   CFG DOT files:     {cfg_dot_dir}")
        print(f"   CFG SVG files:     {cfg_svg_dir}")
        print(f"   Path JSON files:   {paths_dir}")

    if func_files:
        print(f"\nGenerated function files:")
        for func_file in sorted(func_files):
            print(f"   - {os.path.basename(func_file)}")

    if all_success:
        print("\n[SUCCESS] Preprocessing pipeline completed successfully!")
        return 0
    else:
        print("\n[WARNING] Preprocessing pipeline completed with warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
