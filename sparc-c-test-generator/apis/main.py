import os
import json
import argparse

from apis.c_unit_test_generator import generate_c_test_code
from apis.formats.response_format import CCodeValidationResult
from apis.agents.test_specification_generator import TestSpecificationGenerator
from apis.token_calculator import get_token_calculator


def merge_function_doc_tokens(token_calculator, docs_token_file: str = "tmp/docs/token_calculator.json"):
    """
    Merge function documentation tokens from preprocessor step into the main token calculator.

    The preprocessor runs generate_function_docs.py which saves its tokens to tmp/docs/token_calculator.json.
    This function loads those tokens and merges them into the main token calculator.
    """
    if not os.path.exists(docs_token_file):
        print(f"ℹ️  No function documentation tokens found at {docs_token_file}")
        return

    try:
        with open(docs_token_file, "r", encoding="utf-8") as f:
            docs_data = json.load(f)

        # Extract function_documentation stats from the saved file
        by_step = docs_data.get("by_step", {})
        func_doc_stats = by_step.get("function_documentation", {})

        if func_doc_stats:
            input_tokens = func_doc_stats.get("input_tokens", 0)
            api_calls = func_doc_stats.get("api_calls", 0)

            if input_tokens > 0:
                # Manually add the tokens to the function_documentation category
                token_calculator.token_counts["function_documentation"]["input_tokens"] += input_tokens
                token_calculator.token_counts["function_documentation"]["calls"] += api_calls

                # Add a summary detail entry
                token_calculator.token_counts["function_documentation"]["details"].append({
                    "context": "function_documentation_merged_from_preprocessor",
                    "tokens": input_tokens,
                    "timestamp": docs_data.get("metadata", {}).get("end_time", ""),
                    "note": f"Merged {api_calls} API calls from preprocessor step"
                })

                print(f"✅ Merged function documentation tokens: {input_tokens:,} tokens from {api_calls} API calls")
        else:
            print(f"ℹ️  No function_documentation stats found in {docs_token_file}")

    except Exception as e:
        print(f"⚠️  Warning: Could not merge function documentation tokens: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate operation maps and test scenarios for C unit tests",
        epilog="""
            Examples:
            # Single header file:
            python3 main.py source.c --header_filepath header.h --predefined_functions_path functions.json
            
            # Multiple header files:
            python3 main.py source.c --header_filepath header1.h --header_filepath header2.h --predefined_functions_path functions.json
            
            # With additional options:
            python3 main.py source.c --header_filepath header.h --predefined_functions_path functions.json --output_path test/projects/bst --create_embed
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source_filepath", help="Path to the C source file")
    parser.add_argument(
        "--header_filepath",
        action="append",
        required=True,
        help="Path to a C header file (can be specified multiple times for multiple headers)",
    )
    parser.add_argument(
        "--predefined_functions_path",
        default="apis/function_pools/predefined_functions.json",
        help="Path to predefined_functions.json file (default: apis/function_pools/predefined_functions.json)",
    )
    parser.add_argument(
        "--create_embed",
        action="store_true",
        help="Create embeddings for predefined functions",
    )
    parser.add_argument(
        "--helper_functions_dir",
        default="test/helper/functions",
        help="Directory containing helper function C files (default: test/helper/functions)",
    )
    parser.add_argument(
        "--output_path",
        help="Output path for generated files"
    )
    parser.add_argument(
        "--skip_operation_map",
        action="store_true",
        help="Skip operation map generation (assumes operation_map.json already exists)",
    )
    parser.add_argument(
        "--skip_test_scenarios",
        action="store_true",
        help="Skip test scenarios generation (assumes test_scenarios.json already exists)",
    )
    parser.add_argument(
        "--skip_merge_complex",
        action="store_true",
        help="Skip merging to complex test scenarios (assumes complex_test_scenarios.json already exists)",
    )
    parser.add_argument(
        "--only_operation_map",
        action="store_true",
        help="Only run operation map generation and exit",
    )
    parser.add_argument(
        "--only_test_scenarios",
        action="store_true",
        help="Only run test scenarios generation and exit",
    )
    parser.add_argument(
        "--only_merge_complex",
        action="store_true",
        help="Only run merging to complex test scenarios and exit",
    )
    parser.add_argument(
        "--only_validation",
        action="store_true",
        help="Only run C code validation and exit",
    )
    parser.add_argument(
        "--per_function_generation",
        action="store_true",
        help="Generate, validate, and merge unit tests on a per-function basis",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=10,
        help="Maximum number of parallel workers for Phase 1 test generation (default: 10)",
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=3,
        help="Maximum validation iterations for fixing compilation errors (default: 3)",
    )
    parser.add_argument(
        "--architecture",
        type=str,
        choices=["multiagent", "monolithic"],
        default="multiagent",
        help="Test generation architecture: 'multiagent' (dual-phase: designer + coder) or 'monolithic' (single-phase: direct C code) (default: multiagent)",
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["gpt", "gemini", "openrouter", "deepseek"],
        default="gpt",
        help="LLM provider: 'gpt' for OpenAI, 'gemini' for Gemini, 'openrouter' for OpenRouter, 'deepseek' for DeepSeek (default: gpt)",
    )

    args = parser.parse_args()

    # Set the default LLM provider before creating any GPT_Connection instances
    from apis.gpt import set_default_provider
    set_default_provider(args.model)

    source_filepath = args.source_filepath
    header_file_paths = (
        args.header_filepath
    )  # This will be a list due to action='append'

    # Validate inputs
    if not header_file_paths:
        print(
            "❌ Error: At least one header file must be specified using --header_filepath"
        )
        exit(1)

    # Check if files exist
    if not os.path.exists(source_filepath):
        print(f"❌ Error: Source file does not exist: {source_filepath}")
        exit(1)

    missing_headers = [path for path in header_file_paths if not os.path.exists(path)]
    if missing_headers:
        print(f"❌ Error: The following header files do not exist:")
        for missing in missing_headers:
            print(f"  - {missing}")
        exit(1)

    predefined_functions_path = args.predefined_functions_path
    create_embeddings = args.create_embed
    output_path = args.output_path
    embedded_json_path = predefined_functions_path.replace(".json", "_embedded.json")

    subject_name = source_filepath.split("/")[-1].split(".")[0]
    print(f"Subject name: {subject_name}")
    print(f"Output directory: {output_path}")

    operation_map_path = f"{output_path}/operation_map.json"
    test_scenarios_path = f"{output_path}/test_scenarios.json"
    complex_test_scenarios_path = (
        f"{output_path}/complex_test_scenarios.json"
    )
    helpers_c_path = f"{output_path}/helpers.c"
    helpers_header_path = f"{output_path}/helpers.h"
    helper_functions_dir = "test/helper/functions"

    print(f"Using source file: {source_filepath}")
    print(f"Using header files: {', '.join(header_file_paths)}")
    print(f"Using embedded JSON path: {embedded_json_path}")
    print(f"Using predefined functions: {predefined_functions_path}")
    print(f"Create embeddings: {create_embeddings}")

    # Initialize the test specification generator
    test_generator = TestSpecificationGenerator()
    gpt_connection = test_generator.gpt_connection

    model_name = gpt_connection.model
    print(f"Using model: {model_name}")

    # Create embeddings for predefined functions if flag is set
    if create_embeddings:
        print("Creating embeddings for predefined functions...")
        gpt_connection.create_embeddings_for_json(
            predefined_functions_path,
            embedded_json_path,
        )

    # Initialize FAISS vector database
    # Check if the vector database already exists
    if test_generator.vector_db_manager.get_vector_db() is None:
        print("Initializing FAISS vector database...")
        test_generator.vector_db_manager.init_vector_db(
            embedded_json_path,
            index_type="flat",  # or "ivf" for larger datasets, "hnsw" for speed
            save_index=True,
            index_dir="apis/database",
        )

    # Load existing vector database
    test_generator.vector_db_manager.load_vector_db("apis/database")

    # Step 4a: Operation map generation with RAG
    if not args.skip_operation_map:
        print("\n=== STEP 4a: Operation Map Generation (RAG) ===")
        # source_functions = test_generator.op_map_manager.load_source_functions(
        #     source_functions_path=f"{output_path}/source_functions.json",
        # )
        # print(f"source functions: {source_functions}")
        operation_map = test_generator.op_map_manager.generate_operation_map_with_rag(
            source_filepath=source_filepath,
            header_filepaths=header_file_paths,
        )
        print("Generated operation map:")
        print(operation_map)

        # Process the operation map response to generate JSON and C files
        print("\nProcessing operation map response...")
        test_generator.op_map_manager.process_operation_map_response(
            operation_map,
            operation_map_path=operation_map_path,
            helpers_c_path=helpers_c_path,
            helper_functions_dir=helper_functions_dir,
            header_file_paths=header_file_paths,
        )

        # Generate helpers.h immediately after helpers.c is created
        # This is CRITICAL: validation in Step 4c requires helpers.h to exist
        if os.path.exists(helpers_c_path):
            print(f"\n🔧 Generating helpers.h from helpers.c...")
            try:
                from utils.gen_headers_clang import generate_header_clang
                generate_header_clang(helpers_c_path, helpers_header_path)
                print(f"✅ Generated {helpers_header_path}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to generate helpers.h: {e}")
        else:
            print(f"⚠️  Warning: helpers.c not found at {helpers_c_path}")

        op_map_json = test_generator.op_map_manager.operation_map_to_json_string(
            op_map_response=operation_map,
            source_functions_path=f"{output_path}/source_functions.json",
        )

        if args.only_operation_map:
            print("✅ Operation map generation completed! Exiting as requested.")
            exit(0)
    else:
        print("\n=== STEP 4a: Skipping Operation Map Generation ===")
        print(f"Loading existing operation map from: {operation_map_path}")
        try:
            operation_map = test_generator.op_map_manager.load_operation_map_from_json(
                operation_map_path
            )
            op_map_json = test_generator.op_map_manager.operation_map_to_json_string(
                op_map_response=operation_map,
                source_functions_path=f"{output_path}/source_functions.json",
            )
        except Exception as e:
            print(f"Error loading operation map: {e}")
            exit(1)

    # Step 4b: Test Generation (based on architecture choice)
    if not args.skip_test_scenarios:
        source_functions_path = f"{output_path}/source_functions.json"
        test_scenarios_dir = f"{output_path}/test_scenarios"

        if args.architecture == "monolithic":
            # Monolithic Architecture: Single-phase direct C code generation
            print("\n=== STEP 4b: Monolithic Test Generation ===")
            print("Architecture: Single-phase (direct C code generation)")

            from apis.agents.monolithic_test_generator import (
                MonolithicTestGenerator,
                wrap_test_files_for_compilation,
                merge_monolithic_tests,
            )

            # Generate tests directly as C code
            monolithic_generator = MonolithicTestGenerator()
            monolithic_test_files = monolithic_generator.generate_tests_for_all_functions(
                source_functions_path=source_functions_path,
                operation_map_json=op_map_json,
                output_dir=output_path,
                atomic_files_dir="tmp/function-files",
                temperature=0.0,
                max_workers=args.max_workers,
                header_files=header_file_paths,
            )

            # Wrap test files with includes and main() for compilation
            wrapped_test_files, test_to_function_map = wrap_test_files_for_compilation(
                test_files=monolithic_test_files,
                output_dir=output_path,
                header_files=header_file_paths,
                helpers_header_file=helpers_header_path,
                source_file_path=source_filepath,
            )

            # Validate each test file
            print("\n=== STEP 4c: Validate Monolithic Unit Tests ===")

            from apis.per_function_test_scenario_generator import validate_per_test_case_unit_tests

            # Build compile command template
            source_include_dir = os.path.dirname(source_filepath)

            # Collect all include directories (source dir + header dirs + output path for helpers.h)
            include_dirs = set()
            include_dirs.add(source_include_dir)
            include_dirs.add(output_path)  # For helpers.h
            for header_path in header_file_paths:
                header_dir = os.path.dirname(header_path)
                if header_dir:
                    include_dirs.add(header_dir)

            # Build include flags
            include_flags = " ".join(f'-I"{d}"' for d in include_dirs if d)

            # Unity framework paths
            unity_include = '-I"lib/unity"'
            unity_source = 'lib/unity/unity.c'

            # Malloc wrapper for testing allocation failures
            malloc_wrap_include = '-I"lib/malloc_wrap"'
            malloc_wrap_source = 'lib/malloc_wrap/malloc_wrap.c'
            malloc_wrap_flags = '-Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc'

            compile_command_template = (
                f'gcc -g -std=c99 -Wall -fsanitize=address -fno-omit-frame-pointer '
                f'{malloc_wrap_flags} {include_flags} {unity_include} {malloc_wrap_include} '
                '{unit_test_file} '
                f'{helpers_c_path} {unity_source} {malloc_wrap_source}'
            )

            # Find all source C files in source directory
            source_dir = os.path.dirname(source_filepath)
            import subprocess
            find_result = subprocess.run(
                ["find", source_dir, "-name", "*.c", "-type", "f"],
                capture_output=True,
                text=True
            )
            if find_result.returncode == 0:
                source_c_files = find_result.stdout.strip().split("\n")
                source_c_files = [f for f in source_c_files if f.strip()]
                compile_command_template += " " + " ".join(source_c_files)

            compile_command_template += " -o {unit_test_executable} -lm"

            validation_results = validate_per_test_case_unit_tests(
                unit_test_files=wrapped_test_files,
                test_to_function_map=test_to_function_map,
                helpers_c_path=helpers_c_path,
                function_files_dir="tmp/function-files",
                compile_command_template=compile_command_template,
                max_iterations=args.max_iterations,
                max_workers=args.max_workers,
            )

            # Merge validated tests into final unit_test.c
            print("\n=== STEP 4d: Merge Monolithic Unit Tests ===")

            unit_test_c_path = f"{output_path}/unit_test.c"
            merge_monolithic_tests(
                test_files=monolithic_test_files,
                validation_results=validation_results,
                output_path=unit_test_c_path,
                header_files=header_file_paths,
                helpers_header_file=helpers_header_path,
            )

            print(f"\n Monolithic test generation completed!")
            print(f"  Final unit test: {unit_test_c_path}")

        else:
            # Multiagent Architecture: Dual-Phase Test Generation (Designer + Coder)
            print("\n=== STEP 4b: Dual-Phase Test Generation ===")
            print("Architecture: Multiagent (designer + coder)")

            # Import dual-phase managers
            from apis.agents.test_designer import TestDesignerManager
            from apis.agents.test_coder import TestCoderManager

            # Paths
            test_designs_dir = f"{output_path}/designed_tests"

            # Step 4b Phase 1: Test Designer (Per-Path)
            print("\n--- STEP 4b Phase 1: Test Designer (Per-Path Parallel) ---")
            test_designer = TestDesignerManager()
            design_files = test_designer.design_tests_for_all_functions(
                source_functions_path=source_functions_path,
                operation_map_json=op_map_json,
                output_dir=test_designs_dir,
                atomic_files_dir="tmp/function-files",
                temperature=0.0,
                max_workers=args.max_workers
            )

            # Step 4b Phase 2: Test Coder
            print("\n--- STEP 4b Phase 2: Test Coder (Parallel) ---")
            test_coder = TestCoderManager()
            scenario_files = test_coder.generate_test_code_for_all_functions(
                source_functions_path=source_functions_path,
                test_designs_dir=test_designs_dir,
                operation_map_json=op_map_json,
                output_dir=test_scenarios_dir,
                function_files_dir="tmp/function-files",
                temperature=0.0,
                max_workers=args.max_workers
            )

    #     if args.only_test_scenarios:
    #         print("✅ Test scenarios generation completed! Exiting as requested.")
    #         exit(0)
    # else:
    #     print("\n=== STEP 2: Skipping Test Scenarios Generation ===")
    #     print(f"Using existing test scenarios from: {test_scenarios_path}")
    #     if not os.path.exists(test_scenarios_path):
    #         print(f"Error: Test scenarios file not found: {test_scenarios_path}")
    #         exit(1)

    # (monolithic already did validation and merging in Step 4b-4d above)
    if args.architecture == "monolithic":
        # For monolithic, we've already completed all steps above
        unit_test_c_path = f"{output_path}/unit_test.c"

        print(f"\nGenerated files (monolithic):")
        print(f"  - Operation map: {operation_map_path}")
        print(f"  - Helper functions: {helpers_c_path}")
        print(f"  - C unit tests: {unit_test_c_path}")
        print(f"  - Monolithic tests: {output_path}/monolithic/tests/")

        # Save token usage summary
        token_calculator = get_token_calculator()
        token_calculator.set_output_dir(output_path)
        merge_function_doc_tokens(token_calculator)
        token_calculator.print_summary()
        token_file = token_calculator.save(detailed=True)
        print(f"  - Token usage: {token_file}")

        print("\n Test generation completed (monolithic architecture)!")
        exit(0)

    # (Processing) Merge test scenarios and operation map into complex format
    # (Only for multiagent architecture)
    if not args.skip_merge_complex:
        print("\n=== (Processing) Merge to Complex Test Scenarios ===")
        test_generator.test_scenario_manager.merge_to_complex_test_scenarios(
            test_scenarios_dir=test_scenarios_dir,
            operation_map_path=operation_map_path,
            complex_test_scenarios_path=complex_test_scenarios_path,
            subject_name=subject_name,
            source_file_path=source_filepath,
            helpers_c_path=helpers_c_path,
        )

        if args.only_merge_complex:
            print("✅ Complex test scenarios merging completed! Exiting as requested.")
            exit(0)
    else:
        print("\n=== (Processing) Skipping Merge to Complex Test Scenarios ===")
        print(
            f"Using existing complex test scenarios from: {complex_test_scenarios_path}"
        )
        if not os.path.exists(complex_test_scenarios_path):
            print(
                f"Error: Complex test scenarios file not found: {complex_test_scenarios_path}"
            )
            exit(1)

    # Steps 4c-4d: C Code Generation and Validation
    print("\n=== STEPS 4c-4d: C Code Generation and Validation ===")
    unit_test_c_path = f"{output_path}/unit_test.c"

    # Check if per-function generation is requested
    if args.per_function_generation:
        print("\n🔀 Per-test-case generation mode enabled")
        print("Generating separate unit tests for each test case, validating, and merging...\n")

        # Import per-test-case generator
        from apis.per_function_test_scenario_generator import (
            generate_per_test_case_unit_tests,
            validate_per_test_case_unit_tests,
            merge_unit_test_files
        )

        # (Processing) Generate per-function complex test scenarios
        print("\n=== (Processing) Generate Per-Function Complex Test Scenarios ===")
        complex_scenarios_dir = f"{output_path}/complex_test_scenarios_per_function"

        complex_files = test_generator.test_scenario_manager.generate_per_function_complex_test_scenarios(
            test_scenarios_dir=test_scenarios_dir,
            operation_map_path=operation_map_path,
            output_dir=complex_scenarios_dir,
            subject_name=subject_name,
            source_file_path=source_filepath,
            helpers_c_path=helpers_c_path,
        )

        if not complex_files:
            print("✗ No complex test scenario files generated. Exiting.")
            exit(1)

        # (Processing) Generate per-test-case C unit tests
        print("\n=== (Processing) Generate Per-Test-Case C Unit Tests ===")
        # Generate unit tests in same directory as helpers for simpler include paths
        unit_tests_dir = output_path

        unit_test_files, test_to_function_map = generate_per_test_case_unit_tests(
            complex_scenarios_files=complex_files,
            header_files=header_file_paths,
            helpers_header_file=helpers_header_path,
            output_dir=unit_tests_dir,
            source_file_path=source_filepath,
        )

        # Step 4c: Validate each unit test
        print("\n=== STEP 4c: Validate Per-Test-Case Unit Tests ===")

        # Build compile command template with placeholders
        # {unit_test_file} will be replaced with actual unit test file path
        # {unit_test_executable} will be replaced with output executable path
        # Build template without f-string to avoid escaping issues
        source_include_dir = os.path.dirname(source_filepath)
        # Unity framework paths
        unity_include = '-I"lib/unity"'
        unity_source = 'lib/unity/unity.c'
        # Malloc wrapper for testing allocation failures
        malloc_wrap_include = '-I"lib/malloc_wrap"'
        malloc_wrap_source = 'lib/malloc_wrap/malloc_wrap.c'
        malloc_wrap_flags = '-Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc'
        # ASan flags for better debugging: -fsanitize=address catches NULL derefs, buffer overflows, use-after-free
        # -fno-omit-frame-pointer ensures accurate stack traces in error reports
        compile_command_template = f'gcc -g -std=c99 -Wall -fsanitize=address -fno-omit-frame-pointer {malloc_wrap_flags} -I"{source_include_dir}" {unity_include} {malloc_wrap_include} ' + '{unit_test_file} ' + f'{helpers_c_path} {unity_source} {malloc_wrap_source}'

        # Find all source C files in source directory
        source_dir = os.path.dirname(source_filepath)
        import subprocess
        find_result = subprocess.run(
            ["find", source_dir, "-name", "*.c", "-type", "f"],
            capture_output=True,
            text=True
        )
        if find_result.returncode == 0:
            source_c_files = find_result.stdout.strip().split("\n")
            source_c_files = [f for f in source_c_files if f.strip()]
            compile_command_template += " " + " ".join(source_c_files)

        compile_command_template += " -o {unit_test_executable} -lm"

        validation_results = validate_per_test_case_unit_tests(
            unit_test_files=unit_test_files,
            test_to_function_map=test_to_function_map,
            helpers_c_path=helpers_c_path,
            function_files_dir="tmp/function-files",
            compile_command_template=compile_command_template,
            max_iterations=args.max_iterations,
            max_workers=args.max_workers,
        )

        # Step 4d: Merge validated unit tests
        print("\n=== STEP 4d: Merge Validated Unit Tests ===")

        final_unit_test = merge_unit_test_files(
            unit_test_files=unit_test_files,
            validation_results=validation_results,
            output_path=unit_test_c_path,
            header_files=header_file_paths,
            helpers_header_file=helpers_header_path,
        )

        print(f"\n✓ Final merged unit test: {final_unit_test}")

    else:
        # Original monolithic generation
        with open(complex_test_scenarios_path, "r") as f:
            complex_test_data = json.load(f)

        # Generate C test code
        try:
            generated_c_code = generate_c_test_code(
                complex_test_data,
                source_filepath,
                header_file_paths,
                helpers_header_path,
                unit_test_c_path,
            )
            if generated_c_code is None:
                print("Code generation failed due to validation errors.")
                exit(1)
        except Exception as e:
            print(f"Error generating C test code: {e}")
            exit(1)

        # Create output directory if it doesn't exist
        unit_test_c_dir = os.path.dirname(unit_test_c_path)
        if unit_test_c_dir and not os.path.exists(unit_test_c_dir):
            os.makedirs(unit_test_c_dir)
            print(f"Created directory: {unit_test_c_dir}")

        # Write the generated code to file
        try:
            with open(unit_test_c_path, "w") as f:
                f.write(generated_c_code)
            print(f"\nGenerated C unit tests to {unit_test_c_path}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            exit(1)

    print(f"\nGenerated files:")
    print(f"  - Operation map: {operation_map_path}")
    print(f"  - Test scenarios: {test_scenarios_path}")
    print(f"  - Complex scenarios: {complex_test_scenarios_path}")
    print(f"  - Helper functions: {helpers_c_path}")
    print(f"  - C unit tests (original): {unit_test_c_path}")

    # Save token usage summary
    token_calculator = get_token_calculator()
    token_calculator.set_output_dir(output_path)

    # Merge function documentation tokens from preprocessor step
    merge_function_doc_tokens(token_calculator)

    token_calculator.print_summary()
    token_file = token_calculator.save(detailed=True)
    print(f"  - Token usage: {token_file}")

    print("\n✅ Test generation completed!")
