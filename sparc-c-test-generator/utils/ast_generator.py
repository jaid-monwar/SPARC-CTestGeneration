#!/usr/bin/env python3
"""
C AST Generator using Tree-sitter

This script takes a directory path as input, finds all C files in that directory,
and generates Abstract Syntax Trees (ASTs) using tree-sitter-c parser.
The ASTs are saved as JSON files with the naming convention: {c_file_name}_ast.json

Usage:
    python ast_generator.py <directory_path>

Example:
    python ast_generator.py ../subjects/bst/
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try different import strategies for tree-sitter
parser_setup_success = False
language = None
parser = None

# Method 1: Try tree-sitter-languages (works with 1.8.0 - 1.10.2)
try:
    from tree_sitter_languages import get_language, get_parser
    language = get_language('c')
    parser = get_parser('c')
    parser_setup_success = True
    print("✓ Successfully loaded C parser using tree-sitter-languages")
except Exception as e:
    print(f"tree-sitter-languages failed: {e}")

# Method 2: Try tree-sitter 0.23+ with tree_sitter_c module
if not parser_setup_success:
    try:
        import tree_sitter_c
        from tree_sitter import Parser, Language
        
        # tree-sitter 0.23+ API
        language_capsule = tree_sitter_c.language()
        
        # Try with name argument (0.23+)
        try:
            language = Language(language_capsule, "c")
            parser = Parser(language)
            parser_setup_success = True
            print("✓ Successfully loaded C parser using tree-sitter-c (0.23+ API)")
        except TypeError:
            # Try without name argument
            try:
                language = Language(language_capsule)
                parser = Parser(language)
                parser_setup_success = True
                print("✓ Successfully loaded C parser using tree-sitter-c (legacy API)")
            except Exception as e2:
                print(f"tree-sitter-c legacy API failed: {e2}")
    except Exception as e:
        print(f"tree-sitter-c module failed: {e}")

# Method 2: Try standard tree-sitter with manual language loading
if not parser_setup_success:
    try:
        import tree_sitter
        from tree_sitter import Language, Parser

        # Try to load from pre-built library
        try:
            language = Language.build_library('c.so', ['tree-sitter-c'])
            parser = Parser()
            parser.set_language(language)
            parser_setup_success = True
            print("✓ Successfully loaded C parser using manual build")
        except Exception as e:
            print(f"Manual build failed: {e}")

    except ImportError:
        print("tree-sitter not available")

if not parser_setup_success:
    print("\n❌ Could not set up tree-sitter C parser.")
    print("Please try one of the following:")
    print("1. pip install tree-sitter tree-sitter-languages")
    print("2. Check compatibility between tree-sitter and tree-sitter-languages versions")
    print("3. Try downgrading: pip install tree-sitter==0.20.4 tree-sitter-languages==1.8.0")
    sys.exit(1)


class ASTGenerator:
    def __init__(self):
        """Initialize the AST generator with C language parser."""
        self.parser = parser
        self.language = language

    def node_to_dict(self, node) -> Dict[str, Any]:
        """Convert a tree-sitter node to a dictionary representation."""
        result = {
            'type': node.type,
            'start_point': {
                'row': node.start_point[0],
                'column': node.start_point[1]
            },
            'end_point': {
                'row': node.end_point[0],
                'column': node.end_point[1]
            },
            'start_byte': node.start_byte,
            'end_byte': node.end_byte,
            'is_named': node.is_named,
            'is_missing': node.is_missing,
            'has_changes': node.has_changes,
            'has_error': node.has_error,
            'is_error': node.is_error
        }

        # Add text content for leaf nodes or small nodes
        if len(node.children) == 0 or (node.end_byte - node.start_byte) < 200:
            try:
                if hasattr(node, 'text') and node.text:
                    result['text'] = node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text)
                else:
                    result['text'] = ''
            except (UnicodeDecodeError, AttributeError):
                result['text'] = '<unparseable>'

        # Add children recursively
        if node.children:
            result['children'] = [self.node_to_dict(child) for child in node.children]

        return result

    def parse_c_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a C file and return its AST as a dictionary."""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()

            # Parse the source code
            tree = self.parser.parse(source_code)

            # Convert to dictionary
            ast_dict = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'language': 'c',
                'parser_version': "tree-sitter with tree-sitter-languages",
                'source_size_bytes': len(source_code),
                'has_error': tree.root_node.has_error,
                'root_node': self.node_to_dict(tree.root_node)
            }

            return ast_dict

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def find_c_files(self, directory: str) -> List[str]:
        """Find all C files in the given directory."""
        c_files = []

        # Only process .c files (skip .h header files)
        patterns = ['*.c']

        for pattern in patterns:
            search_pattern = os.path.join(directory, pattern)
            c_files.extend(glob.glob(search_pattern))

            # Also search recursively
            recursive_pattern = os.path.join(directory, '**', pattern)
            c_files.extend(glob.glob(recursive_pattern, recursive=True))

        # Remove duplicates and sort
        c_files = sorted(list(set(c_files)))

        return c_files

    def generate_ast_for_directory(self, path: str, output_dir: Optional[str] = None) -> None:
        """Generate AST files for C file(s). Accepts a single file or directory."""
        # Use tree-sitter directory as output if not specified
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))

        # Check if path is a file or directory
        if os.path.isfile(path):
            # Single file mode
            if not path.endswith('.c'):
                print(f"❌ Error: File '{path}' is not a C file.")
                return
            c_files = [path]
            print(f"🔍 Single file mode: {path}")
        elif os.path.isdir(path):
            # Directory mode
            print(f"🔍 Searching for C files in: {path}")
            c_files = self.find_c_files(path)
        else:
            print(f"❌ Error: Path '{path}' does not exist.")
            return

        if not c_files:
            print("❌ No C files found in the directory.")
            return

        print(f"📁 Found {len(c_files)} C files:")
        for file_path in c_files:
            print(f"  - {file_path}")

        print(f"\n🚀 Generating ASTs...")
        print(f"📂 Output directory: {output_dir}")

        success_count = 0
        for i, file_path in enumerate(c_files, 1):
            print(f"\n[{i}/{len(c_files)}] Processing: {os.path.basename(file_path)}")

            # Parse the file
            ast = self.parse_c_file(file_path)

            if ast is None:
                print("  ❌ FAILED to parse")
                continue

            # Generate output filename
            base_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_filename = f"{name_without_ext}.json"
            output_path = os.path.join(output_dir, output_filename)

            # Save AST as JSON
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(ast, f, indent=2, ensure_ascii=False)
                print(f"  ✅ SUCCESS - AST saved to: {output_filename}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ FAILED to save: {e}")

        print(f"\n🎉 AST generation completed!")
        print(f"✅ Successfully processed: {success_count}/{len(c_files)} files")
        print(f"📂 Output files saved in: {output_dir}")

        # List generated files
        print(f"\n📋 Generated AST files:")
        ast_files = glob.glob(os.path.join(output_dir, "*.json"))
        for ast_file in sorted(ast_files):
            print(f"  - {os.path.basename(ast_file)}")


def main():
    """Main function to handle command line arguments and execute AST generation."""
    parser_args = argparse.ArgumentParser(
        description="Generate ASTs for C files using tree-sitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ast_generator.py ../subjects/bst/
  python ast_generator.py ../subjects/rgba/src/
  python ast_generator.py /path/to/c/source/files/
  python ast_generator.py ../subjects/bst/ --output-dir ./output/
        """
    )

    parser_args.add_argument(
        'path',
        help='C source file or directory path containing C files to parse'
    )

    parser_args.add_argument(
        '--output-dir', '-o',
        help='Output directory for AST JSON files (default: current tree-sitter directory)',
        default=None
    )

    parser_args.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser_args.parse_args()

    print("🌳 C AST Generator using Tree-sitter")
    print("=" * 50)

    # Initialize AST generator
    generator = ASTGenerator()

    # Generate ASTs
    generator.generate_ast_for_directory(args.path, args.output_dir)


if __name__ == "__main__":
    main()