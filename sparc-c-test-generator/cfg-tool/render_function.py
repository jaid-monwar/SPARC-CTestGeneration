#!/usr/bin/env python3
"""
CFG Renderer - Python port of render-function.ts

Generate Control Flow Graphs from C source code.
"""
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.file_parsing.file_parsing import get_language, iter_functions
from src.parser_loader.parser_loader import initialize_parser
from src.control_flow.cfg import extract_function_name, get_wasm_path
from src.cfg_helper import build_cfg
from src.control_flow.render import graph_to_dot
from src.control_flow.colors import (
    get_dark_color_scheme,
    get_light_color_scheme,
    deserialize_color_list,
    list_to_scheme
)


def get_func_def(source_code: str, func) -> str:
    """Get the function definition (signature)"""
    body = func.child_by_field_name("body")
    if not body:
        raise ValueError("No function body")

    func_def = source_code[func.start_byte:body.start_byte]
    # Normalize whitespace
    func_def = ' '.join(func_def.split())
    return func_def


def get_color_scheme(colors: str):
    """Get the color scheme from the colors argument"""
    if not colors or colors == "dark":
        return get_dark_color_scheme()
    elif colors == "light":
        return get_light_color_scheme()
    else:
        # Load from file
        color_file = Path(colors)
        if not color_file.exists():
            raise FileNotFoundError(f"Color file not found: {colors}")

        with open(color_file, 'r') as f:
            color_list = deserialize_color_list(f.read())
        return list_to_scheme(color_list)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Control Flow Graph from C source code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python render_function.py bst.c insert --verbose --dot insert.dot --out insert.svg
  python render_function.py main.c myFunction --colors light --simplify
        """
    )

    parser.add_argument("file", help="Source file to parse")
    parser.add_argument("function", help="Function name to generate CFG for")
    parser.add_argument("--verbose", action="store_true",
                        help="Show code contents in graph nodes")
    parser.add_argument("--dot", help="Output DOT file path")
    parser.add_argument("--out", help="Output SVG file path")
    parser.add_argument("--simplify", action="store_true",
                        help="Simplify CFG by collapsing trivial paths")
    parser.add_argument("--flatSwitch", dest="flat_switch", action="store_true", default=True,
                        help="Flatten switch statements (default: true)")
    parser.add_argument("--no-flatSwitch", dest="flat_switch", action="store_false",
                        help="Don't flatten switch statements")
    parser.add_argument("--colors", default="dark",
                        help="Color scheme: 'light', 'dark', or path to color file (default: dark)")
    parser.add_argument("--language", help="Force specific language (only C is supported)")

    args = parser.parse_args()

    # Read source file
    source_file = Path(args.file)
    if not source_file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    with open(source_file, 'r') as f:
        source_code = f.read()

    # Determine language
    if args.language:
        language = args.language
    else:
        try:
            language = get_language(args.file)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    print(f"Language: {language}")

    # Initialize parser
    wasm_path = get_wasm_path(language)
    print(f"Loading parser from: {wasm_path}")
    try:
        ts_parser, ts_language = initialize_parser(language, wasm_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Make sure to copy the parser WASM files to the parsers/ directory", file=sys.stderr)
        return 1

    # Find the function
    target_function = None
    for func in iter_functions(source_code, language, ts_parser):
        func_name = extract_function_name(language, func)
        if func_name == args.function:
            target_function = func
            break

    if not target_function:
        print(f"Error: Function '{args.function}' not found in {args.file}", file=sys.stderr)
        print("Available functions:", file=sys.stderr)
        for func in iter_functions(source_code, language, ts_parser):
            func_name = extract_function_name(language, func)
            if func_name:
                print(f"  - {func_name}", file=sys.stderr)
        return 1

    print(f"Found function: {args.function}")

    # Build CFG
    print("Building CFG...")
    cfg = build_cfg(
        target_function,
        language,
        simplify=args.simplify,
        flat_switch=args.flat_switch,
        ts_language=ts_language
    )
    print(f"CFG nodes: {len(cfg.graph.nodes())}, edges: {len(cfg.graph.edges())}")

    # Get color scheme
    try:
        color_scheme = get_color_scheme(args.colors)
    except Exception as e:
        print(f"Error loading color scheme: {e}", file=sys.stderr)
        return 1

    # Generate DOT
    print("Generating DOT...")
    dot_content = graph_to_dot(cfg, verbose=args.verbose, color_scheme=color_scheme)

    # Write DOT file if requested
    if args.dot:
        dot_file = Path(args.dot)
        with open(dot_file, 'w') as f:
            f.write(dot_content)
        print(f"DOT file written to: {args.dot}")

    # Generate SVG (always, like TypeScript version)
    print("Generating SVG...")
    try:
        import graphviz
        src = graphviz.Source(dot_content)

        if args.out:
            # Write to file
            output_file = Path(args.out)
            output_format = output_file.suffix[1:] if output_file.suffix else 'svg'
            src.render(output_file.stem, directory=output_file.parent, format=output_format, cleanup=True)
            print(f"SVG file written to: {args.out}")
        else:
            # Write to stdout (like TypeScript version)
            svg_output = src.pipe(format='svg')
            sys.stdout.buffer.write(svg_output)
    except ImportError:
        print("Error: graphviz package not installed. Install with: pip install graphviz", file=sys.stderr)
        if not args.dot:
            print("DOT content:", file=sys.stderr)
            print(dot_content)
        return 1
    except Exception as e:
        print(f"Error generating SVG: {e}", file=sys.stderr)
        return 1

    if args.out or args.dot:
        print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
