import sys
import os
import re
from clang.cindex import Index, CursorKind, TypeKind, TranslationUnit, Config

# Set libclang path - search for available versions
def _find_libclang():
    """Find the libclang library on the system."""
    paths = [
        "/usr/lib/llvm-18/lib/libclang.so.1",
        "/usr/lib/llvm-18/lib/libclang.so",
        "/usr/lib/llvm-20/lib/libclang.so",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

_libclang_path = _find_libclang()
if _libclang_path:
    Config.set_library_file(_libclang_path)


# Convert relative paths to work from the output file location
def convert_include_path(include_path, output_path):
    if not include_path:
        return include_path

    # Case 1: already relative (starts with ./ or ../)
    if include_path.startswith("./") or include_path.startswith("../"):
        return include_path

    # Case 2: header in same directory or system header
    if "/" not in include_path:
        return include_path

    # Case 3: path includes subdirectories → make relative to output
    output_dir = os.path.dirname(output_path)
    rel_path = os.path.relpath(include_path, output_dir)
    return rel_path


def extract_includes(source_path, output_path):
    """Extract #include directives from source and convert paths relative to output."""

    includes = []
    seen_includes = set()
    source_dir = os.path.dirname(source_path)

    print(f"[i] Extracting includes from {source_path} to {output_path}")

    try:
        with open(source_path, "r") as f:
            content = f.read()

        include_pattern = r'^\s*#\s*include\s*[<"][^>"]+[>"]'
        matches = re.findall(include_pattern, content, re.MULTILINE)

        for match in matches:
            cleaned_include = match.strip()

            # System includes with <...> stay as-is
            if cleaned_include.startswith("#include <"):
                new_include = cleaned_include

            # Local includes with "..." may need conversion
            elif '"' in cleaned_include:
                include_file = cleaned_include.split('"')[1]

                # Build full path relative to source file
                full_include_path = os.path.join(source_dir, include_file)

                # Convert path relative to output file
                converted_path = convert_include_path(full_include_path, output_path)
                new_include = f'#include "{converted_path}"'
                print(f"[i] Converted include: {include_file} -> {converted_path}")
            else:
                new_include = cleaned_include

            # Add unique includes
            if new_include not in seen_includes:
                includes.append(new_include)
                seen_includes.add(new_include)

    except Exception as e:
        print(f"[!] Warning: Could not extract includes from {source_path}: {e}")

    return includes


def get_type_string(t):
    if t.kind == TypeKind.POINTER:
        pointee = get_type_string(t.get_pointee())
        if t.get_pointee().kind == TypeKind.FUNCTIONPROTO:
            # This is a function pointer, format it properly
            ret_type = get_type_string(t.get_pointee().get_result())
            param_types = [get_type_string(p) for p in t.get_pointee().argument_types()]
            return f"{ret_type} (*)({', '.join(param_types)})"
        else:
            return pointee + " *"
    elif t.kind == TypeKind.FUNCTIONPROTO:
        ret_type = get_type_string(t.get_result())
        param_types = [get_type_string(p) for p in t.argument_types()]
        return f"{ret_type} (*)({', '.join(param_types)})"
    elif t.kind == TypeKind.CONSTANTARRAY:
        # Handle array types properly
        element_type = get_type_string(t.get_array_element_type())
        return f"{element_type}"
    else:
        return t.spelling


def extract_functions(cursor, functions, source_path):
    if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
        if cursor.location.file and cursor.location.file.name == source_path:
            # Check if the function is static by examining the source text
            # Check if the main function, if so, skip it
            if cursor.spelling == "main":
                print(f"[i] Skipping main function: {cursor.spelling}")
                return
            # This is a workaround since cursor.storage_class doesn't always work correctly
            # source_range = cursor.extent
            # try:
            #     with open(source_path, 'r') as f:
            #         lines = f.readlines()
            #         start_line = source_range.start.line - 1  # Convert to 0-based
            #         if start_line < len(lines):
            #             line_content = lines[start_line].strip()
            #             if line_content.startswith('static'):
            #                 print(f"[i] Skipping static function: {cursor.spelling}")
            #                 # Recurse and return without adding this function
            #                 for child in cursor.get_children():
            #                     extract_functions(child, functions, source_path)
            #                 return
            # except Exception as e:
            #     print(f"[!] Warning: Could not check if function {cursor.spelling} is static: {e}")

            ret_type = get_type_string(cursor.result_type)
            name = cursor.spelling
            params = []

            for arg in cursor.get_arguments():
                arg_type = arg.type
                arg_name = arg.spelling or "param"

                # --- Arrays ---
                if arg_type.kind == TypeKind.CONSTANTARRAY:
                    elem_type = get_type_string(arg_type.get_array_element_type())
                    size = arg_type.get_array_size()
                    params.append(f"{elem_type} {arg_name}[{size}]")

                elif arg_type.kind == TypeKind.INCOMPLETEARRAY:
                    elem_type = get_type_string(arg_type.get_array_element_type())
                    params.append(f"{elem_type} {arg_name}[]")

                # --- Function pointers ---
                elif (
                    arg_type.kind == TypeKind.POINTER
                    and arg_type.get_pointee().kind == TypeKind.FUNCTIONPROTO
                ):
                    pointee = arg_type.get_pointee()
                    ret = get_type_string(pointee.get_result())
                    args = ", ".join(
                        get_type_string(a) for a in pointee.argument_types()
                    )
                    params.append(f"{ret} (*{arg_name})({args})")

                # --- Default case ---
                else:
                    params.append(f"{get_type_string(arg_type)} {arg_name}")

            functions.append((ret_type, name, params))

    # Recurse
    for child in cursor.get_children():
        extract_functions(child, functions, source_path)


def extract_typedefs(cursor, typedefs):
    if cursor.kind == CursorKind.TYPEDEF_DECL:
        if cursor.underlying_typedef_type.kind == TypeKind.RECORD:
            typedefs.append(cursor)

    for child in cursor.get_children():
        extract_typedefs(child, typedefs)


def extract_macros(cursor, macros, source_file):
    if cursor.kind == CursorKind.MACRO_DEFINITION:
        # Only include macros from the file itself
        loc = cursor.location
        if loc.file and loc.file.name == source_file:
            macros.append(cursor.spelling)
    for child in cursor.get_children():
        extract_macros(child, macros, source_file)


def extract_structs(cursor, structs, source_path, typedef_name=None):
    """Extract struct definitions from the source file, excluding static structs.
    
    Args:
        cursor: The clang cursor to examine
        structs: List to append (struct_cursor, typedef_name) tuples
        source_path: Path to source file
        typedef_name: If inside a typedef, this is the typedef name
    """
    # Check for typedef declarations - get the typedef name for nested structs
    if cursor.kind == CursorKind.TYPEDEF_DECL:
        typedef_name = cursor.spelling
        # Continue to process children with the typedef name
        for child in cursor.get_children():
            extract_structs(child, structs, source_path, typedef_name)
        return
    
    if cursor.kind == CursorKind.STRUCT_DECL and cursor.is_definition():
        # Only include structs defined in the source file (not included headers)
        if cursor.location.file and str(cursor.location.file).endswith(source_path):
            struct_name = cursor.spelling
            if struct_name:
                # Check if this struct is declared as static by examining the source
                source_range = cursor.extent
                try:
                    with open(source_path, "r") as f:
                        lines = f.readlines()
                        start_line = source_range.start.line - 1  # Convert to 0-based
                        if start_line < len(lines):
                            # Check this line and a few lines before for "static"
                            for i in range(
                                max(0, start_line - 2), min(len(lines), start_line + 1)
                            ):
                                line_content = lines[i].strip()
                                if (
                                    "static" in line_content
                                    and "struct" in line_content
                                ):
                                    print(f"[i] Skipping static struct: {struct_name}")
                                    return  # Skip this struct
                except Exception as e:
                    print(
                        f"[!] Warning: Could not check if struct {struct_name} is static: {e}"
                    )

                # Store both the cursor and the typedef name (if any)
                structs.append((cursor, typedef_name))

    for child in cursor.get_children():
        extract_structs(child, structs, source_path, typedef_name)


def format_struct_definition(struct_cursor, typedef_name=None):
    """Format a struct definition for the header file.

    Outputs as 'typedef struct tag { ... } typedef_name;' to ensure the type
    can be used both as 'struct tag' and as 'typedef_name'.
    
    Args:
        struct_cursor: The clang cursor for the struct
        typedef_name: The typedef name (e.g., 'stdout_capture_t'), if different from struct tag
    """
    struct_tag = struct_cursor.spelling  # e.g., 'stdout_capture'
    # Use typedef_name if provided, otherwise use struct tag as the type name
    type_alias = typedef_name if typedef_name else struct_tag
    
    lines = [f"typedef struct {struct_tag} {{"]

    for field in struct_cursor.get_children():
        if field.kind == CursorKind.FIELD_DECL:
            field_type = get_type_string(field.type)
            field_name = field.spelling
            lines.append(f"    {field_type} {field_name};")

    lines.append(f"}} {type_alias};")
    return "\n".join(lines)


def generate_header_guard_name(out_path):
    """Generate a header guard name based on the output file path."""
    # Get the filename without extension
    filename = os.path.splitext(os.path.basename(out_path))[0]

    # Convert to uppercase and replace non-alphanumeric characters with underscores
    header_guard = re.sub(r"[^A-Z0-9]", "_", filename.upper())

    # Add _H suffix
    header_guard += "_H"

    return header_guard


def generate_header_clang(source_path, out_path):
    # Create the directory if it doesn't exist
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
        print(f"[+] Created directory: {out_dir}")

    # Generate header guard name from output path
    header_guard = generate_header_guard_name(out_path)

    # Extract includes from the source file
    includes = extract_includes(source_path, out_path)

    index = Index.create()
    tu = index.parse(
        source_path,
        args=[
            "-I/usr/include",
            "-I/usr/include/x86_64-linux-gnu",
            "-I/usr/include/X11",
        ],
        options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    )

    # for d in tu.diagnostics:
    #     print("CLANG DIAG:", d)

    functions = []
    typedefs = []
    macros = []
    structs = []

    extract_functions(tu.cursor, functions, source_path)
    extract_typedefs(tu.cursor, typedefs)
    extract_macros(tu.cursor, macros, source_path)
    extract_structs(tu.cursor, structs, source_path)

    with open(out_path, "w") as f:
        f.write(f"#ifndef {header_guard}\n#define {header_guard}\n\n")

        # Write extracted includes from the source file
        if includes:
            f.write("// Includes from source file\n")
            for include in includes:
                f.write(f"{include}\n")
            f.write("\n")

        # Write standard includes if not already present
        standard_includes = ["#include <stdio.h>", "#include <stdlib.h>"]
        for std_include in standard_includes:
            if not any(std_include in inc for inc in includes):
                f.write(f"{std_include}\n")
        f.write("\n")

        # Write struct definitions first (deduplicated by struct tag name)
        # Prefer typedef versions over bare struct versions
        if structs:
            f.write("// Struct definitions\n")
            # Build a dict: struct_tag -> (cursor, typedef_name)
            # If same struct appears twice, prefer the one with typedef_name
            struct_map = {}
            for struct_cursor, typedef_name in structs:
                struct_tag = struct_cursor.spelling
                if struct_tag:
                    if struct_tag not in struct_map:
                        struct_map[struct_tag] = (struct_cursor, typedef_name)
                    elif typedef_name and not struct_map[struct_tag][1]:
                        # New one has typedef_name, old one doesn't - prefer new
                        struct_map[struct_tag] = (struct_cursor, typedef_name)
            
            for struct_tag, (struct_cursor, typedef_name) in struct_map.items():
                struct_def = format_struct_definition(struct_cursor, typedef_name)
                f.write(f"{struct_def}\n\n")

        # Write typedefs
        if typedefs:
            f.write("// Typedefs\n")
            for td in typedefs:
                f.write(f"// typedef: {td.spelling}\n")
            f.write("\n")

        if macros:
            print("[+] Extracted macros:")
            for macro in macros:
                print(f"    #define {macro}")
            f.write("// Macros\n")
            for macro in macros:
                f.write(f"#define {macro}\n")

        # Write function declarations
        if functions:
            f.write("// Function declarations\n")
            for ret_type, name, params in functions:
                param_str = ", ".join(params) if params else "void"
                f.write(f"{ret_type} {name}({param_str});\n")

        f.write("\n#endif\n")

    print(f"[+] Header generated at {out_path}")
    if includes:
        print(f"[+] Extracted {len(includes)} include directives from source file")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 utils/gen_headers_clang.py input.c [output.h]")
        print("If output.h is not provided, defaults to include/generated_header.h")
        sys.exit(1)

    source_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "src/include/generated_header.h"

    generate_header_clang(source_file, output_file)
