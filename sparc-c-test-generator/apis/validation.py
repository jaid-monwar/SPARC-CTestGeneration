import argparse
import os
from apis.agents.test_specification_generator import TestSpecificationGenerator
from apis.formats.response_format import CCodeValidationResult


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate and fix C code for unit tests",
        epilog="Examples:\n  python3 validation.py source.c --name bst --compile_command gcc -o out source.c --output_path test/projects/bst"
    )
    parser.add_argument("source_filepath", help="Path to the C source file")
    parser.add_argument(
        "--name",
        help="Name of the subject",
    )
    parser.add_argument(
        "--compile_command",
        type=str,
        help="Compilation command for the C source file"
    )
    parser.add_argument(
        "--output_path",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--function_files_dir",
        default="tmp/function-files",
        help="Directory containing per-function C files (default: tmp/function-files)",
    )
    args = parser.parse_args()

    source_filepath = args.source_filepath
    compile_command = args.compile_command
    output_path = args.output_path.rstrip("/")
    subject_name = args.name

    print(f"Output directory: {output_path}")

    unit_test_c_path = f"{output_path}/unit_test.c"
    helpers_c_path = f"{output_path}/helpers.c"
    
    test_generator = TestSpecificationGenerator()
    
    # Save the validated C code
    print("\n=== STEP 5: C Code Validation ===")
    # validated_c_path = f"{output_path}/unit_test_validated.c"
    validated_c_path = unit_test_c_path  # Overwrite the original unit test file

    # Validate and fix the generated C code
    # Note: For merged unit_test.c, function_files_dir won't provide per-function context
    # since the file is not named unit_test_<function>.c
    validated_c_code, validation_results = (
        test_generator.test_validator.validate_and_fix_c_code(
            unit_test_c_path=unit_test_c_path,
            validated_c_path=validated_c_path,
            helpers_c_path=helpers_c_path,
            function_files_dir=args.function_files_dir,
            compile_command=compile_command,
            temperature=0.0,
            max_iterations=3,
        )
    )

    # Create output directory if it doesn't exist
    validated_output_dir = os.path.dirname(validated_c_path)
    if validated_output_dir and not os.path.exists(validated_output_dir):
        os.makedirs(validated_output_dir)
        print(f"Created directory: {validated_output_dir}")

    # Write the validated C code to file
    try:
        with open(validated_c_path, "w") as f:
            f.write(validated_c_code)
        print(f"\nValidated C unit tests saved to {validated_c_path}")
    except Exception as e:
        print(f"Error writing to validated output file: {e}")

    print(f"✅ Validated C unit test code saved at: {validated_c_path}")

    # Print validation summary
    final_validation = validation_results.get("final_validation")
    if final_validation and isinstance(final_validation, CCodeValidationResult):
        final_status = validation_results.get("final_status", "UNKNOWN")
        if final_status == "PASS":
            print("🎉 C code validation PASSED - Ready for compilation!")
        else:
            print(f"⚠️  C code validation FAILED")
            final_compilation_errors = validation_results.get(
                "final_compilation_errors", ""
            )
            if final_compilation_errors:
                print(f"Compilation errors: {final_compilation_errors}")

        print(f"\nGenerated files:")
        print(f"  - C unit tests (validated): {validated_c_path}")