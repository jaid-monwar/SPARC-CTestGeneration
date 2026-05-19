import json
import textwrap
import os
import re
from tqdm import tqdm

# libclang integration for better type analysis
try:
    from clang.cindex import Index, TranslationUnit, TypeKind, CursorKind, Config

    # Set libclang path - try in order of preference
    libclang_loaded = False
    libclang_paths = [
        "/usr/lib/llvm-18/lib/libclang.so.1",  # Most common on Ubuntu
        "/usr/lib/llvm-20/lib/libclang.so.1",
        "/usr/lib/llvm-20/lib/libclang.so",
        "/usr/lib/llvm-18/lib/libclang.so",
        "/media/goat/Projects/Work/Jobs/UIUC/llvm-project/build/lib/libclang.so"
    ]

    for path in libclang_paths:
        try:
            if os.path.exists(path):
                Config.set_library_file(path)
                libclang_loaded = True
                break
        except:
            continue

    if not libclang_loaded:
        # Try without explicit path - let system find it
        pass

    LIBCLANG_AVAILABLE = True
except ImportError:
    LIBCLANG_AVAILABLE = False
    print(
        "Warning: libclang not available. Falling back to string-based type detection."
    )
    print("To install libclang: pip install libclang")

# --- C Test Templates ---

C_TEST_FUNCTION_TEMPLATE = textwrap.dedent(
    """
void {test_name}() {{
    printf("Running {test_name}...\\n");

{declarations}
{setup_code}
{test_steps_code}
{cleanup_code}
    printf("{test_name} passed.\\n");
}}
"""
)

C_MAIN_TEMPLATE = textwrap.dedent(
    """
int main() {{
    printf("Starting all generated unit tests...\\n\\n");
{run_test_calls}
    printf("All generated tests completed successfully!\\n");
    return 0;
}}
"""
)

# --- Helper Functions ---


def init_libclang():
    """Initialize libclang with proper configuration."""
    if not LIBCLANG_AVAILABLE:
        return False

    try:
        # Try to set libclang library path if needed
        # This might be required on some systems
        import clang.cindex

        # Common libclang library locations
        possible_paths = [
            "/usr/lib/llvm-14/lib/libclang.so.1",
            "/usr/lib/llvm-13/lib/libclang.so.1",
            "/usr/lib/llvm-12/lib/libclang.so.1",
            "/usr/lib/x86_64-linux-gnu/libclang-14.so.1",
            "/usr/lib/x86_64-linux-gnu/libclang-13.so.1",
            "/usr/local/lib/libclang.dylib",  # macOS
            "/opt/homebrew/lib/libclang.dylib",  # macOS with Homebrew
        ]

        # Try to find and set the library
        for path in possible_paths:
            if os.path.exists(path):
                clang.cindex.conf.set_library_file(path)
                break

        return True

    except Exception as e:
        print(f"Warning: Failed to initialize libclang: {e}")
        return False


def is_standard_library_function(op_name):
    """Check if the operation name is a standard library function that should not be treated as an operation."""
    standard_library_functions = {
        # Memory management
        "malloc",
        "calloc",
        "realloc",
        "free",
        # String functions
        "strlen",
        "strcpy",
        "strncpy",
        "strcmp",
        "strncmp",
        "strcat",
        "strncat",
        "strchr",
        "strrchr",
        "strstr",
        "strtok",
        "sprintf",
        "sscanf",
        # I/O functions
        "printf",
        "fprintf",
        "sprintf",
        "scanf",
        "fscanf",
        "sscanf",
        "fopen",
        "fclose",
        "fread",
        "fwrite",
        "fgets",
        "fputs",
        # Math functions
        "abs",
        "fabs",
        "sqrt",
        "pow",
        "sin",
        "cos",
        "tan",
        "log",
        "exp",
        # Other common functions
        "exit",
        "abort",
        "atexit",
        "system",
        "getenv",
        "qsort",
        "bsearch",
        "rand",
        "srand",
        "time",
        "memcpy",
        "memmove",
        "memset",
        "memcmp",
    }
    return op_name in standard_library_functions


def get_operation_info(op_name, operation_map):
    """Get operation information from the operation map."""
    # Check all operation types
    for op_type in [
        "function_operations",
        "assertion_operations",
        "utility_operations",
    ]:
        if op_type in operation_map and op_name in operation_map[op_type]:
            return operation_map[op_type][op_name]
    return None


def analyze_type_with_clang(type_string):
    """
    Use libclang to analyze a C type string and determine if it's a string type.
    Returns a tuple (is_string, type_info).
    """
    if not LIBCLANG_AVAILABLE:
        return None, None

    try:
        # Create a minimal C code snippet to analyze the type
        test_code = f"""
        #include <stdio.h>
        #include <stdlib.h>
        #include <string.h>
        
        void test_function({type_string} param) {{
            // This function is just for type analysis
        }}
        """

        # Create clang index and parse the code
        index = Index.create()

        # Parse the code as a translation unit
        tu = index.parse("temp.c", unsaved_files=[("temp.c", test_code)])

        # Find the function parameter
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.PARM_DECL and cursor.spelling == "param":
                param_type = cursor.type

                # Check various string type conditions
                is_string = False
                type_info = {
                    "kind": param_type.kind,
                    "spelling": param_type.spelling,
                    "is_pointer": param_type.kind == TypeKind.POINTER,
                    "pointee_kind": None,
                }

                # Check if it's a pointer type
                if param_type.kind == TypeKind.POINTER:
                    pointee_type = param_type.get_pointee()
                    type_info["pointee_kind"] = pointee_type.kind

                    # Check if it points to char
                    if (
                        pointee_type.kind == TypeKind.CHAR_S
                        or pointee_type.kind == TypeKind.CHAR_U
                    ):
                        is_string = True
                    # Check for const char
                    # elif pointee_type.spelling in ['char', 'const char', 'signed char', 'unsigned char']:
                    #     is_string = True

                # Check for single char type
                elif (
                    param_type.kind == TypeKind.CHAR_S
                    or param_type.kind == TypeKind.CHAR_U
                ):
                    is_string = True

                return is_string, type_info

        return False, None

    except Exception as e:
        print(f"Warning: clang analysis failed for type '{type_string}': {e}")
        return None, None


def is_string_type(param_type):
    """
    Determine if a parameter type is a string type using libclang when available,
    falling back to robust string analysis.
    """
    if not param_type:
        return False

    # Try libclang analysis first
    if LIBCLANG_AVAILABLE:
        is_string, type_info = analyze_type_with_clang(param_type)
        if is_string is not None:
            return is_string

    return False


def extract_globals(file_path, include_dirs=None):
    if LIBCLANG_AVAILABLE:
        import clang.cindex

        index = clang.cindex.Index.create()
        args = []
        if include_dirs:
            args = [f"-I{inc}" for inc in include_dirs]
        tu = index.parse(file_path, args=args)

        globals_list = []

        def visit(node):
            # Only top-level global variables
            if node.kind == clang.cindex.CursorKind.VAR_DECL:
                if (
                    node.semantic_parent.kind
                    == clang.cindex.CursorKind.TRANSLATION_UNIT
                ):
                    globals_list.append(
                        {"name": node.spelling, "type": node.type.spelling}
                    )
            for child in node.get_children():
                visit(child)

        visit(tu.cursor)
    return globals_list


def generate_externs(globals_list):
    lines = ["// Automatically extracted global variables"]
    for g in globals_list:
        global_declaration = convert_type_to_c_declaration(g['type'], g['name'], None)
        lines.append(f"extern {global_declaration}")
    return "\n".join(lines)


def convert_type_to_c_declaration(param_type, param_name, param_value):
    """Convert parameter type and value to C declaration."""
    # Handle array types like int[5], float[10], char[20]
    array_match = re.match(r"(.+)\[(\d+)\]$", param_type)
    if array_match:
        base_type = array_match.group(1).strip()
        size = array_match.group(2)
        if param_value:
            # Remove surrounding braces if present
            array_values = param_value.strip()
            if array_values.startswith("{") and array_values.endswith("}"):
                array_values = array_values[1:-1]
            return f"{base_type} {param_name}[{size}] = {{{array_values}}};"
        else:
            return f"{base_type} {param_name}[{size}];"

    # Handle array types (any type ending with *)
    if param_type.endswith(" *"):
        if not param_value or param_value == "NULL":
            return f"{param_type} {param_name} = NULL;"
        else:
            return f"{param_type} {param_name} = {param_value};"

    # Handle pointer types without initialization
    if param_type.endswith(" *") and (not param_value or param_value == "NULL"):
        return f"{param_type} {param_name} = NULL;"

    # Use improved string type detection
    if is_string_type(param_type) and param_value:
        # Check if the value already has quotes (either single or double)
        # Also check if it contains a function call pattern (function_name(...))
        function_call_pattern = r"\w+\s*\([^)]*\)"
        if not (
            (param_value.startswith('"') and param_value.endswith('"'))
            or (param_value.startswith("'") and param_value.endswith("'"))
            or re.search(function_call_pattern, param_value)
        ):
            # Add double quotes for string literals
            param_value = f'"{param_value}"'

    # Handle pointer types with initialization
    if param_type.endswith(" *"):
        return f"{param_type} {param_name} = {param_value};"

    # Handle regular types with values
    if param_value:
        return f"{param_type} {param_name} = {param_value};"

    # Handle types without initialization (just declaration)
    return f"{param_type} {param_name};"


def process_step(step, operation_map, declared_variables):
    """Process a single step and return the generated code and any new declarations."""
    op_name = step["op"]
    variable_declarations = step.get("variable_declarations", [])
    input_params_raw = step.get("input_params", [])
    return_params = step.get("return_params", [])
    print(f"Processing step {step}")  # Debugging output

    # Convert input_params to dictionary format for the two-phase system
    input_params = {}
    if isinstance(input_params_raw, dict):
        # Format: {'str': 'color_str', 'ok': '&ok'}
        for param_name, param_usage in input_params_raw.items():
            if param_name:
                input_params[param_name] = param_usage

    # Get operation info
    op_info = get_operation_info(op_name, operation_map)
    if not op_info:
        # Check if it's a standard library function and handle it gracefully
        if is_standard_library_function(op_name):
            # Create a synthetic operation info for standard library functions
            op_info = {
                "call_template": "{}({})",  # Generic template that will be filled in
                "return_type": "void",  # Default, can be overridden by return_params
                "description": f"Standard library function {op_name}",
            }
        else:
            return (
                f"    // Error: Operation '{op_name}' not found in operation map\n",
                [],
            )

    declarations = []

    # Handle variable declarations for this step (new two-phase system)
    for var_decl in variable_declarations:
        var_name = var_decl["name"]
        var_type = var_decl["type"]
        var_value = var_decl["value"]
        var_comment = var_decl.get("comment", "")

        if var_name not in declared_variables:
            comment_text = f" // {var_comment}" if var_comment else ""
            declaration = convert_type_to_c_declaration(var_type, var_name, var_value)
            declarations.append(f"    {declaration}{comment_text}")
            declared_variables.add(var_name)

    # Handle return variable declarations - pre-declare if new
    if return_params:
        return_var = return_params[0]
        return_type = op_info.get("return_type", "void")
        if return_var not in declared_variables and return_type != "void":
            declarations.append(f"    {return_type} {return_var};")
            declared_variables.add(return_var)

    # Generate the function call using new format
    function_call = generate_function_call(op_info, input_params, return_params)

    # Format the function call properly
    if return_params and len(return_params) > 0:
        return_var = return_params[0]
        code = f"    {return_var} = {function_call};\n"
    else:
        code = f"    {function_call};\n"

    return code, declarations


def generate_function_call(op_info, input_params, return_params):
    """Generate the C function call based on operation info and parameters."""
    call_template = op_info["call_template"]

    # Handle standard library functions with generic template
    if call_template == "{}({})":
        # Extract function name from description or deduce from context
        func_name = (
            op_info.get("description", "").split()[-1]
            if op_info.get("description")
            else "unknown"
        )

        # Build parameter list from input_params
        if input_params:
            param_list = ", ".join(input_params.values())
            call_template = f"{func_name}({param_list})"
        else:
            call_template = f"{func_name}()"
    else:
        # Find all parameters in the template (anything between {})
        import re

        param_pattern = r"\{([^}]+)\}"
        template_params = re.findall(param_pattern, call_template)

        # Replace each parameter found in the template
        input_param_values = list(input_params.values())
        for i, param_name in enumerate(template_params):
            if param_name in input_params:
                # Use the usage specification from input_params
                param_usage = input_params[param_name]
                call_template = call_template.replace(f"{{{param_name}}}", param_usage)
            elif i < len(input_param_values):
                # Parameter name doesn't match, but we have values in sequence - use by position
                param_usage = input_param_values[i]
                call_template = call_template.replace(f"{{{param_name}}}", param_usage)
            else:
                # Parameter not found in input_params and no more values available
                print(
                    f"input_params: {input_params}, template_params: {template_params}"
                )
                print(
                    f"Warning: Parameter '{param_name}' expected in template but not found in input_params"
                )
                call_template = call_template.replace(
                    f"{{{param_name}}}", f"/* MISSING: {param_name} */"
                )

    # Remove the semicolon from call template since we'll add it back when formatting
    if call_template.endswith(";"):
        call_template = call_template[:-1]

    return call_template


def create_c_test_header(header_files, helpers_header_file, output_file_path):
    """Generate the C header part for the test file with all necessary includes.

    Args:
        header_files: Single header file path (str) or list of header file paths
        helpers_header_file: Path to helpers header file
        output_file_path: Path where the test file will be written

    Returns:
        String containing all necessary includes
    """

    # Normalize header_files to always be a list
    if isinstance(header_files, str):
        header_files = [header_files]
    elif header_files is None:
        header_files = []

    # Convert relative paths to work from the output file location
    def convert_include_path(include_path, output_path):
        if not include_path:
            return include_path

        # Calculate the relative path from output directory to the include file
        output_dir = os.path.dirname(output_path)

        # If the include path is already relative, convert it properly
        if not os.path.isabs(include_path):
            # Calculate how many levels deep the output file is from the project root
            depth = len([p for p in output_dir.split("/") if p and p != "."])
            prefix = "../" * depth
            return prefix + include_path

        return include_path

    # Convert paths
    converted_helpers_file = convert_include_path(helpers_header_file, output_file_path)

    # Essential system includes that must always be present
    essential_includes = [
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <stdint.h>",
        "#include <assert.h>",
        "#include <string.h>",
    ]

    # Extract additional includes from all header files
    additional_includes = []
    converted_header_files = []

    for header_file in header_files:
        if not header_file:
            continue

        # Convert the header file path
        converted_header_file = convert_include_path(header_file, output_file_path)
        converted_header_files.append(converted_header_file)

        try:
            with open(header_file, "r") as f:
                header_content = f.read()

            # Find all #include statements in the header file
            import re

            include_pattern = r'^\s*#include\s+[<"][^>"]+[>"]'
            includes_found = re.findall(include_pattern, header_content, re.MULTILINE)

            for include in includes_found:
                include = include.strip()
                # Only add if it's not already in essential includes and not already added
                if (
                    include not in essential_includes
                    and include not in additional_includes
                ):
                    additional_includes.append(include)

        except Exception as e:
            print(f"Warning: Could not read header file {header_file}: {e}")

    # Build the complete header
    header_lines = []
    header_lines.extend(essential_includes)

    if additional_includes:
        header_lines.append("")  # Add blank line
        header_lines.append("// Additional includes from header files")
        header_lines.extend(additional_includes)

    if converted_header_files:
        header_lines.append("")  # Add blank line
        header_lines.append("// Include the header files")
        for converted_header_file in converted_header_files:
            header_lines.append(f'#include "{converted_header_file}"')

    header_lines.append("")
    header_lines.append("// Include test helpers")
    header_lines.append(f'#include "{converted_helpers_file}"')
    header_lines.append("")

    return "\n".join(header_lines)


def validate_test_scenarios(test_scenarios, operation_map):
    """Validate test scenarios for common issues before generating code."""
    validation_errors = []

    for i, test_scenario in enumerate(test_scenarios):
        test_name = test_scenario.get("test_name", f"test_{i}")

        # Check all steps in setup, steps, and cleanup
        all_steps = []
        all_steps.extend(test_scenario.get("setup", []))
        all_steps.extend(test_scenario.get("steps", []))
        all_steps.extend(test_scenario.get("cleanup", []))

        for step in all_steps:
            op_name = step.get("op")
            if not op_name:
                continue

            # Check for missing operations in operation map (but allow standard library functions)
            if not get_operation_info(
                op_name, operation_map
            ) and not is_standard_library_function(op_name):
                validation_errors.append(
                    f"Test '{test_name}': Operation '{op_name}' not found in operation map."
                )

    return validation_errors


def generate_single_test_c_code(
    test_scenario,
    operation_map,
    source_file_path,
    header_files,
    helpers_header_file,
    output_file_path,
):
    """Generate C test code for a single test scenario.

    Args:
        test_scenario: Single test scenario dict with test_name, setup, steps, cleanup
        operation_map: Operation map for resolving operations
        source_file_path: Path to the source file being tested
        header_files: Header files to include
        helpers_header_file: Path to helpers header file
        output_file_path: Path where the test file will be written

    Returns:
        Generated C code as a string
    """
    test_name = test_scenario.get("test_name")
    if not test_name:
        print("Error: Test scenario must have a 'test_name' field.")
        return None

    # Track declared variables across the entire test function
    declared_variables = set()

    # Collect all declarations and code
    all_declarations = []
    setup_code = ""
    test_steps_code = ""
    cleanup_code = ""

    # Process setup steps
    setup_steps = test_scenario.get("setup", [])
    for step in setup_steps:
        code, declarations = process_step(step, operation_map, declared_variables)
        all_declarations.extend(declarations)
        setup_code += code

    # Process main test steps
    test_steps = test_scenario.get("steps", [])
    for step in test_steps:
        code, declarations = process_step(step, operation_map, declared_variables)
        all_declarations.extend(declarations)
        test_steps_code += code

    # Process cleanup steps
    cleanup_steps = test_scenario.get("cleanup", [])
    for step in cleanup_steps:
        code, declarations = process_step(step, operation_map, declared_variables)
        all_declarations.extend(declarations)
        cleanup_code += code

    # Combine all declarations at the top
    declarations_code = "\n".join(all_declarations)
    if declarations_code:
        declarations_code += "\n"

    # Generate the test function
    test_function = C_TEST_FUNCTION_TEMPLATE.format(
        test_name=test_name,
        declarations=declarations_code,
        setup_code=setup_code,
        test_steps_code=test_steps_code,
        cleanup_code=cleanup_code,
    )

    # Assemble the final C test file
    final_c_code = create_c_test_header(
        header_files, helpers_header_file, output_file_path
    )

    # Add extern declarations
    final_c_code += "\n"
    globals_info = extract_globals(source_file_path)
    extern_code = generate_externs(globals_info)
    final_c_code += extern_code
    final_c_code += "\n"

    # Add the single test function
    final_c_code += test_function

    # Add main function that calls just this test
    run_test_calls = f"    {test_name}();"
    final_c_code += C_MAIN_TEMPLATE.format(run_test_calls=run_test_calls)

    return final_c_code


def generate_c_test_code(
    complex_test_data,
    source_file_path,
    header_files,
    helpers_header_file,
    output_file_path,
):
    """Generate C test code from complex test scenarios JSON data."""

    # Extract data from JSON
    meta = complex_test_data.get("meta", {})
    operation_map = complex_test_data.get("operation_map", {})
    test_scenarios = complex_test_data.get("test_scenarios", [])

    # Validate test scenarios before generating code
    validation_errors = validate_test_scenarios(test_scenarios, operation_map)
    if validation_errors:
        print("Validation errors found in test scenarios:")
        for error in validation_errors:
            print(f"  - {error}")
        print("Please fix these issues before generating tests.")

    all_test_functions = []
    run_test_calls = []

    for test_scenario in tqdm(test_scenarios, desc="Generating C test cases"):
        test_name = test_scenario.get("test_name")
        if not test_name:
            print("Error: Each test scenario must have a 'test_name' field.")
            continue

        # Track declared variables across the entire test function
        declared_variables = set()

        # Collect all declarations and code
        all_declarations = []
        setup_code = ""
        test_steps_code = ""
        cleanup_code = ""

        # Process setup steps
        setup_steps = test_scenario.get("setup", [])
        for step in setup_steps:
            code, declarations = process_step(step, operation_map, declared_variables)
            all_declarations.extend(declarations)
            setup_code += code

        # Process main test steps
        test_steps = test_scenario.get("steps", [])
        for step in test_steps:
            code, declarations = process_step(step, operation_map, declared_variables)
            all_declarations.extend(declarations)
            test_steps_code += code

        # Process cleanup steps
        cleanup_steps = test_scenario.get("cleanup", [])
        for step in cleanup_steps:
            code, declarations = process_step(step, operation_map, declared_variables)
            all_declarations.extend(declarations)
            cleanup_code += code

        # Combine all declarations at the top
        declarations_code = "\n".join(all_declarations)
        if declarations_code:
            declarations_code += "\n"

        # Add the test function to the list
        all_test_functions.append(
            C_TEST_FUNCTION_TEMPLATE.format(
                test_name=test_name,
                declarations=declarations_code,
                setup_code=setup_code,
                test_steps_code=test_steps_code,
                cleanup_code=cleanup_code,
            )
        )
        run_test_calls.append(f"    {test_name}();")

    # Assemble the final C test file
    final_c_code = create_c_test_header(
        header_files, helpers_header_file, output_file_path
    )
    # Add extern declarations
    final_c_code += "\n"
    globals_info = extract_globals(source_file_path)
    extern_code = generate_externs(globals_info)
    final_c_code += extern_code
    final_c_code += "\n"

    final_c_code += "\n".join(all_test_functions)
    final_c_code += C_MAIN_TEMPLATE.format(run_test_calls="\n".join(run_test_calls))

    return final_c_code


# --- Main Execution ---
if __name__ == "__main__":
    import sys

    # Initialize libclang if available
    if LIBCLANG_AVAILABLE:
        libclang_ready = init_libclang()
        if libclang_ready:
            print("libclang initialized successfully for enhanced type analysis.")
        else:
            print("libclang initialization failed, using fallback type detection.")

    if len(sys.argv) < 5:
        print(
            "Usage: python3 apis/c_unit_test_generator.py <complex_test_scenarios.json> <header_file.h> <helpers.h> <output_file.c>"
        )
        print("Example:")
        print(
            "  python3 apis/c_unit_test_generator.py complex_test_scenarios.json header.h helpers.h output.c"
        )
        sys.exit(1)

    json_file = sys.argv[1]  # complex_test_scenarios.json file
    header_file = sys.argv[2]  # header file (.h)
    helpers_header_file = sys.argv[3]  # helpers.h file
    output_file = sys.argv[4]  # Output C file

    # Load test data from the specified JSON file
    try:
        with open(json_file, "r") as f:
            complex_test_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_file}': {e}")
        sys.exit(1)

    # Validate JSON structure
    required_keys = ["meta", "operation_map", "test_scenarios"]
    for key in required_keys:
        if key not in complex_test_data:
            print(f"Error: Missing required key '{key}' in {json_file}")
            sys.exit(1)

    # Generate C test code
    try:
        generated_c_code = generate_c_test_code(
            complex_test_data, header_file, helpers_header_file, output_file
        )
        if generated_c_code is None:
            print("Code generation failed due to validation errors.")
            sys.exit(1)
    except Exception as e:
        print(f"Error generating C test code: {e}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Write the generated code to file
    try:
        with open(output_file, "w") as f:
            f.write(generated_c_code)
        print(f"\nGenerated C unit tests to {output_file}")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        sys.exit(1)

    # Print compilation instructions
    source_file = complex_test_data["meta"].get("source_file", "source.c")
    object_file = output_file.replace(".c", ".o")
    helpers_file = helpers_header_file.replace(".h", ".c")
    print("\nTo compile and run:")
    print(
        f"1. Compile: gcc {output_file} {helpers_file} {source_file} -o {object_file}"
    )
    print(f"2. Run: ./{object_file}")

    print("\nGenerated test structure:")
    test_count = len(complex_test_data.get("test_scenarios", []))
    print(f"  - {test_count} test functions")
    print(f"  - Source file: {source_file}")
    print(f"  - Header file: {header_file}")
    print(f"  - Helpers file: {helpers_file}")
    print(f"  - Output file: {output_file}")
