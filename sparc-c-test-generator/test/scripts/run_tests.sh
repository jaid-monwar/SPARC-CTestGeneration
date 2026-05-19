#!/bin/bash

# Unit Test Generation and Execution Script
# This script generates and runs unit tests for different subjects

set -e  # Exit on any error

# Check if subject parameter is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a subject name"
    echo "Usage: $0 <subject> [output_dir] [operations] [create_embed] [architecture] [per_function] [model] [max_workers] [max_iterations]"
    echo ""
    echo "Examples:"
    echo "  $0 bst"
    echo "  $0 bst test/projects"
    echo "  $0 bst test/projects all"
    echo "  $0 bst test/projects all false multiagent true"
    echo "  $0 qsort test/projects all false monolithic true"
    echo "  $0 buffer test/projects all false monolithic true gemini"
    echo "  $0 buffer test/projects all false monolithic true gemini 1"
    echo ""
    echo "Supported subjects with their header files:"
    echo "  bst         - subjects/bst/bst.c (no header)"
    echo "  qsort       - subjects/qsort/qsort.c (no header)"
    echo "  quadtree    - subjects/quadtree-0.1.0/src/quadtree.c (no header)"
    echo "  rgba        - subjects/rgba/src/rgba.c (no header)"
    echo "  buffer      - subjects/buffer-0.4.0/src/buffer.c + buffer.h"
    echo "  small-buffer - subjects/buffer/src/buffer.c + buffer.h (minimal test subject)"
    echo "  genann      - subjects/genann/src/genann.c + genann.h"
    echo "  grabc       - subjects/grabc/grabc.c (no header)"
    echo "  url_parser  - subjects/url_parser/url.c (no header)"
    echo "  xzoom       - subjects/xzoom/xzoom.c (no header)"
    echo ""
    echo "Operations (supports: all, N+, N-M, or comma-separated):"
    echo "  1 - Step 1: Extract helper functions from helper pool"
    echo "  2 - Step 2: Generate header files"
    echo "  3 - Step 3: Preprocessor (CFG, paths, source_functions.json)"
    echo "  4 - Step 4: AI test generation (apis.main)"
    echo "  5 - Step 5: Regenerate helpers.h + merge paths"
    echo "  6 - Step 6: Generate header file from helpers (fallback)"
    echo "  7 - Step 7: Final validation (integrated in step 4 for per-function mode)"
    echo "  8 - Step 8: Compile unit tests"
    echo "  9 - Step 9: Run unit tests"
    echo "  compile - Compile unit tests (alternative to 8)"
    echo "  run - Run unit tests (alternative to 9)"
    echo "  coverage - Generate code coverage report"
    echo "  info - Show pipeline summary (metrics, tokens, coverage, iterations)"
    echo "  all - Perform all operations (default)"
    echo ""
    echo "  Range examples:"
    echo "    5+     - Run from step 5 onwards (5,6,7,8,9,coverage,info)"
    echo "    3-7    - Run steps 3 through 7"
    echo "    4,8,9  - Run only steps 4, 8, and 9"
    echo ""
    echo "Create embed:"
    echo "  true     - Add --create_embed flag to main.py"
    echo "  false    - Don't add --create_embed flag (default)"
    echo ""
    echo "Architecture:"
    echo "  multiagent  - Dual-phase: Test Designer + Test Coder (default)"
    echo "  monolithic  - Single-phase: Direct C code generation"
    echo ""
    echo "Per-function generation:"
    echo "  true     - Generate, validate, and merge unit tests per function"
    echo "  false    - Monolithic generation (default)"
    echo ""
    echo "Model:"
    echo "  gpt        - Use OpenAI gpt-4.1 (default)"
    echo "  gemini     - Use Google Gemini gemini-2.5-flash"
    echo "  openrouter - Use OpenRouter (openai/gpt-4o-mini)"
    echo "  deepseek   - Use DeepSeek (deepseek-chat)"
    echo ""
    echo "Max workers:"
    echo "  Number of parallel workers for test generation (default: 10)"
    echo "  Use 1 for sequential processing (useful for debugging)"
    echo ""
    echo "Max iterations:"
    echo "  Maximum validation iterations to fix compilation errors (default: 3)"
    echo "  Use higher values if code needs more fix attempts"
    exit 1
fi

SUBJECT=$1
OUTPUT_DIR=${2:-"test/projects"}  # Default to test/projects if no second argument provided
OPERATIONS=${3:-"all"}           # Default to all operations if no third argument provided
CREATE_EMBED=${4:-"false"}       # Default to false if no fourth argument provided
ARCHITECTURE=${5:-"multiagent"}  # Default to multiagent if no fifth argument provided
PER_FUNCTION=${6:-"false"}       # Default to false if no sixth argument provided
MODEL=${7:-"gpt"}                # Default to gpt if no seventh argument provided
MAX_WORKERS=${8:-"10"}           # Default to 10 if no eighth argument provided
MAX_ITERATIONS=${9:-"3"}         # Default to 3 if no ninth argument provided

# Initialize coverage variables for final summary
COVERAGE_COLLECTED="false"
FUNC_COVERAGE="N/A"
LINE_COVERAGE="N/A"
BRANCH_COVERAGE="N/A"

echo "Starting $SUBJECT unit test generation and execution..."
echo "Output directory: $OUTPUT_DIR"
echo "Operations: $OPERATIONS"
echo "Create embed: $CREATE_EMBED"
echo "Architecture: $ARCHITECTURE"
echo "Per-function generation: $PER_FUNCTION"
echo "Model: $MODEL"
echo "Max workers: $MAX_WORKERS"
echo "Max iterations: $MAX_ITERATIONS"

# Determine source file and header file(s) based on subject
if [ "$SUBJECT" == "bst" ]; then
    SOURCE_FILE="subjects/bst/bst.c"
    HEADER_FILES=""
    OUTPUT_PATH=$OUTPUT_DIR/bst
elif [ "$SUBJECT" == "qsort" ]; then
    SOURCE_FILE="subjects/qsort/qsort.c"
    HEADER_FILES=""
    OUTPUT_PATH=$OUTPUT_DIR/qsort
elif [ "$SUBJECT" == "quadtree" ]; then
    SOURCE_FILE="subjects/quadtree-0.1.0/src/quadtree.c"
    HEADER_FILES=""
    OUTPUT_PATH=$OUTPUT_DIR/quadtree
elif [ "$SUBJECT" == "rgba" ]; then
    SOURCE_FILE="subjects/rgba/src/rgba.c"
    HEADER_FILES=""
    OUTPUT_PATH=$OUTPUT_DIR/rgba
elif [ "$SUBJECT" == "buffer" ]; then
    SOURCE_FILE="subjects/buffer-0.4.0/src/buffer.c"
    HEADER_FILES="subjects/buffer-0.4.0/src/buffer.h"
    OUTPUT_PATH=$OUTPUT_DIR/buffer
elif [ "$SUBJECT" == "small-buffer" ]; then
    SOURCE_FILE="subjects/buffer/src/buffer.c"
    HEADER_FILES="subjects/buffer/src/buffer.h"
    OUTPUT_PATH=$OUTPUT_DIR/buffer
elif [ "$SUBJECT" == "genann" ]; then
    SOURCE_FILE="subjects/genann/src/genann.c"
    HEADER_FILES="subjects/genann/src/genann.h subjects/genann/src/minctest.h"
    OUTPUT_PATH=$OUTPUT_DIR/genann
elif [ "$SUBJECT" == "grabc" ]; then
    SOURCE_FILE="subjects/grabc/grabc.c"
    HEADER_FILES="subjects/grabc/grabc.h"
    COMPILE_COMMAND="make -C subjects/grabc test"
    OUTPUT_PATH=$OUTPUT_DIR/grabc
elif [ "$SUBJECT" == "url_parser" ]; then
    SOURCE_FILE="subjects/url_parser/url.c"
    HEADER_FILES="subjects/url_parser/url.h"
    OUTPUT_PATH=$OUTPUT_DIR/url_parser
elif [ "$SUBJECT" == "xzoom" ]; then
    SOURCE_FILE="subjects/xzoom/test/xzoom_mock.c"
    HEADER_FILES="subjects/xzoom/test/x11_mock.h include/$SUBJECT/header.h"
    COMPILE_COMMAND="make -C subjects/xzoom unit_test"
    OUTPUT_PATH=$OUTPUT_DIR/xzoom/test
else
    echo "Error: Unsupported subject '$SUBJECT'. Supported subjects are: bst, qsort, quadtree, rgba, buffer, small-buffer, genann, grabc, url_parser, xzoom."
    exit 1
fi

if [ -z "$HEADER_FILES" ]; then
    HEADER_FILES="include/$SUBJECT/header.h"
fi

echo "📁 Header files: $HEADER_FILES"

# Function to check if an operation should be performed
# Supports: "all", "5+", "3-7", "1,2,3", "coverage", "info"
should_perform() {
    local operation=$1
    
    # "all" means perform everything
    if [ "$OPERATIONS" == "all" ]; then
        return 0
    fi
    
    # Check for range "from" syntax: "5+" means step 5 and after
    if [[ "$OPERATIONS" =~ ^([0-9]+)\+$ ]]; then
        local from_step="${BASH_REMATCH[1]}"
        # For numeric operations, check if >= from_step
        if [[ "$operation" =~ ^[0-9]+$ ]]; then
            [ "$operation" -ge "$from_step" ] && return 0
        fi
        # For named operations (coverage, info), always include them with N+
        if [[ "$operation" == "coverage" || "$operation" == "info" ]]; then
            return 0
        fi
        return 1
    fi
    
    # Check for range syntax: "3-7" means steps 3 through 7
    if [[ "$OPERATIONS" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        local from_step="${BASH_REMATCH[1]}"
        local to_step="${BASH_REMATCH[2]}"
        # For numeric operations, check if within range
        if [[ "$operation" =~ ^[0-9]+$ ]]; then
            [ "$operation" -ge "$from_step" ] && [ "$operation" -le "$to_step" ] && return 0
        fi
        return 1
    fi
    
    # Check if operation is in the comma-separated list
    echo "$OPERATIONS" | grep -qE "(^|,)$operation(,|$)"
    return $?
}

# Function to print the pipeline summary (metrics, tokens, coverage, iterations)
print_pipeline_summary() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                         📊 PIPELINE SUMMARY                              ║"
    echo "║                           Subject: $SUBJECT"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"

    # --- Section 1: Source Code Metrics ---
    echo ""
    echo "┌──────────────────────────────────────────────────────────────────────────┐"
    echo "│                        📐 Source Code Metrics                            │"
    echo "├──────────────────────────────────────────────────────────────────────────┤"

    # Get LOC
    local loc="N/A"
    if [ -f "$SOURCE_FILE" ]; then
        loc=$(wc -l < "$SOURCE_FILE" | tr -d ' ')
    fi

    # Get Function Count and Execution Paths from source_functions.json
    local func_count="N/A"
    local path_count="N/A"
    if [ -f "$OUTPUT_PATH/source_functions.json" ]; then
        local metrics=$(python3 -c "
import json
with open('$OUTPUT_PATH/source_functions.json', 'r') as f:
    d = json.load(f)
funcs = d.get('source_functions', [])
fc = len(funcs)
pc = sum(len(f.get('paths', [])) for f in funcs)
print(f'{fc},{pc}')
" 2>/dev/null)
        func_count=$(echo "$metrics" | cut -d',' -f1)
        path_count=$(echo "$metrics" | cut -d',' -f2)
    fi

    printf "│  %-30s %s\n" "Lines of Code (LOC):" "$loc"
    printf "│  %-30s %s\n" "Function Count:" "$func_count"
    printf "│  %-30s %s\n" "Unique Execution Paths:" "$path_count"
    echo "└──────────────────────────────────────────────────────────────────────────┘"

    # --- Section 2: Token Usage Summary ---
    echo ""
    echo "┌──────────────────────────────────────────────────────────────────────────┐"
    echo "│                        🔢 Token Usage Summary                            │"
    echo "├──────────────────────────────────────────────────────────────────────────┤"

    if [ -f "$OUTPUT_PATH/token_calculator.json" ]; then
        python3 -c "
import json
with open('$OUTPUT_PATH/token_calculator.json', 'r') as f:
    d = json.load(f)

totals = d.get('totals', {})
by_step = d.get('by_step', {})
metadata = d.get('metadata', {})

print(f\"│  {'Model:':<30} {metadata.get('model', 'N/A')}\")
print(f\"│  {'Total Input Tokens:':<30} {totals.get('total_input_tokens', 0):,}\")
print(f\"│  {'Total API Calls:':<30} {totals.get('total_api_calls', 0)}\")
print('│')
print('│  Breakdown by Step:')

for step, data in by_step.items():
    tokens = data.get('input_tokens', 0)
    calls = data.get('api_calls', 0)
    avg = data.get('avg_tokens_per_call', 0)
    print(f\"│    {step:<26} {tokens:>8,} tokens  ({calls} calls, avg {avg:.0f})\")
" 2>/dev/null || echo "│  Token data not available"
    else
        echo "│  Token calculator data not found at $OUTPUT_PATH/token_calculator.json"
    fi
    echo "└──────────────────────────────────────────────────────────────────────────┘"

    # --- Section 3: Coverage Summary ---
    echo ""
    echo "┌──────────────────────────────────────────────────────────────────────────┐"
    echo "│                        📈 Coverage Summary                               │"
    echo "├──────────────────────────────────────────────────────────────────────────┤"

    local cov_dir="$OUTPUT_PATH/coverage"
    local cov_file="$cov_dir/source-only.info"
    local lcov_branch="--rc lcov_branch_coverage=1"
    
    # Try to read coverage from saved files (from previous runs)
    if [ -f "$cov_file" ]; then
        local cov_output=$(lcov --summary "$cov_file" $lcov_branch 2>&1)
        
        local func_cov=$(echo "$cov_output" | grep -i "functions" | head -1 | sed 's/.*: //' | tr -d ' ')
        local line_cov=$(echo "$cov_output" | grep -i "lines" | head -1 | sed 's/.*: //' | tr -d ' ')
        local branch_cov=$(echo "$cov_output" | grep -i "branches" | head -1 | sed 's/.*: //' | tr -d ' ')
        
        [ -z "$func_cov" ] && func_cov="N/A"
        [ -z "$line_cov" ] && line_cov="N/A"
        [ -z "$branch_cov" ] && branch_cov="N/A"
        
        printf "│  %-30s %s\n" "Function Coverage:" "$func_cov"
        printf "│  %-30s %s\n" "Line Coverage:" "$line_cov"
        printf "│  %-30s %s\n" "Branch Coverage:" "$branch_cov"
        echo "│"
        echo "│  📁 HTML Report: $cov_dir/source/index.html"
    elif [ "$COVERAGE_COLLECTED" == "true" ]; then
        # Use variables from current run if available
        printf "│  %-30s %s\n" "Function Coverage:" "$FUNC_COVERAGE"
        printf "│  %-30s %s\n" "Line Coverage:" "$LINE_COVERAGE"
        printf "│  %-30s %s\n" "Branch Coverage:" "$BRANCH_COVERAGE"
        echo "│"
        echo "│  📁 HTML Report: $cov_dir/source/index.html"
    else
        echo "│  Coverage not collected. Run with 'coverage' operation to generate."
    fi
    echo "└──────────────────────────────────────────────────────────────────────────┘"

    # --- Section 4: Iteration Metrics ---
    echo ""
    echo "┌──────────────────────────────────────────────────────────────────────────┐"
    echo "│                        🔄 Iteration Metrics                              │"
    echo "├──────────────────────────────────────────────────────────────────────────┤"

    if [ -f "$OUTPUT_PATH/token_calculator.json" ]; then
        python3 -c "
import json
with open('$OUTPUT_PATH/token_calculator.json', 'r') as f:
    d = json.load(f)

by_step = d.get('by_step', {})
validation = by_step.get('validation', {})
validation_calls = validation.get('api_calls', 0)
test_gen = by_step.get('monolithic_test', by_step.get('test_generation', {}))
test_calls = test_gen.get('api_calls', 0)

print(f\"│  {'Validation API Calls:':<30} {validation_calls}\")
print(f\"│  {'Test Generation Calls:':<30} {test_calls}\")
if test_calls > 0:
    avg_iter = validation_calls / test_calls
    print(f\"│  {'Avg Iterations per Test:':<30} {avg_iter:.2f}\")
" 2>/dev/null || echo "│  Iteration data not available"
    else
        echo "│  Token calculator data not found"
    fi
    echo "└──────────────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Step 1: Extract helper functions from helper pool
if should_perform "1"; then
    echo "🔍 Step 1: Extracting helper functions from helper pool..."
    python3 utils/extract_funcs_enhanced.py --folder test/helper/functions/ apis/function_pools/
fi

# Step 2: Generate header file from source code if no header files exist
if should_perform "2" && [ -z "$HEADER_FILES" ]; then
    echo "🔧 Step 2: Generating header file from source code..."
    python3 utils/gen_headers_clang.py "$SOURCE_FILE" "$HEADER_FILES"
fi

# Step 3: Run preprocessor to generate CFG, paths, and source_functions.json
if should_perform "3"; then
    echo "📊 Step 3: Running preprocessor to generate CFG and extract execution paths..."
    SOURCE_DIR=$(dirname "$SOURCE_FILE")
    echo "Source directory: $SOURCE_DIR"

    # Run preprocessor to generate AST, atomic files, CFG, and paths
    # Use --clean to remove leftover files from previous runs
    # Pass the specific source file to avoid processing wrong files in multi-file directories
    python3 scripts/preprocessor.py "$SOURCE_FILE" --model "$MODEL" --clean

    if [ $? -eq 0 ]; then
        echo "✅ Preprocessor completed successfully"

        # Verify function descriptions in source_functions.json
        echo ""
        echo "📝 Verifying function descriptions in source_functions.json..."

        python3 -c "
import json
import os

source_functions_file = '$OUTPUT_PATH/source_functions.json'
if not os.path.exists(source_functions_file):
    print('⚠️  Warning: source_functions.json not found')
else:
    with open(source_functions_file, 'r') as f:
        data = json.load(f)
    funcs = data.get('source_functions', [])
    total = len(funcs)
    with_desc = sum(1 for func in funcs if 'description' in func and func['description'])

    if with_desc == total:
        print(f'✅ All {total} functions have descriptions (generated by preprocessor)')
    elif with_desc > 0:
        print(f'⚠️  Warning: Only {with_desc}/{total} functions have descriptions')
    else:
        print(f'⚠️  Warning: No function descriptions found in source_functions.json')
        print('    The preprocessor may have failed to generate documentation')
"
    else
        echo "⚠️  Warning: Preprocessor failed, continuing without path data"
    fi
fi

# Step 4: AI Test Generation
if should_perform "4"; then
    echo ""
    echo "📦 Step 4: AI Test Generation ($ARCHITECTURE architecture)..."

    # Build the command with header file argument(s)
    CMD_ARGS="$SOURCE_FILE"

    # Add header file arguments - support space-separated multiple files
    if [ -n "$HEADER_FILES" ]; then
        # Convert space-separated header files to multiple --header_filepath arguments
        for header_file in $HEADER_FILES; do
            CMD_ARGS="$CMD_ARGS --header_filepath $header_file"
        done
    fi

    CMD_ARGS="$CMD_ARGS --predefined_functions_path apis/function_pools/predefined_functions.json --output_path $OUTPUT_PATH"

    if [ "$CREATE_EMBED" == "true" ]; then
        CMD_ARGS="$CMD_ARGS --create_embed"
    fi

    # Add architecture flag
    CMD_ARGS="$CMD_ARGS --architecture $ARCHITECTURE"

    if [ "$PER_FUNCTION" == "true" ]; then
        CMD_ARGS="$CMD_ARGS --per_function_generation"
    fi

    # Add model flag
    CMD_ARGS="$CMD_ARGS --model $MODEL"

    # Add max_workers flag
    CMD_ARGS="$CMD_ARGS --max_workers $MAX_WORKERS"

    # Add max_iterations flag
    CMD_ARGS="$CMD_ARGS --max_iterations $MAX_ITERATIONS"

    echo "Running: python3 -m apis.main $CMD_ARGS"
    eval "python3 -m apis.main $CMD_ARGS"
fi

# Step 5: Regenerate helpers.h and merge paths
if should_perform "5"; then
    # Step 5a: Regenerate helpers.h from helpers.c to ensure correct signatures
    echo ""
    echo "🔧 Step 5a: Regenerating helpers.h from helpers.c..."
    if [ -f "$OUTPUT_PATH/helpers.c" ]; then
        python3 utils/gen_headers_clang.py "$OUTPUT_PATH/helpers.c" "$OUTPUT_PATH/helpers.h"
        if [ $? -eq 0 ]; then
            echo "✅ helpers.h regenerated successfully with correct signatures"
        else
            echo "⚠️  Warning: Failed to regenerate helpers.h"
        fi
    else
        echo "⚠️  Warning: helpers.c not found at $OUTPUT_PATH/helpers.c"
    fi

    # Step 5b: Merge paths into operation_map.json
    echo ""
    echo "🔗 Step 5b: Merging execution paths into operation_map.json..."

    if [ -f "$OUTPUT_PATH/operation_map.json" ]; then
        python3 scripts/merge_paths_to_opmap.py "$OUTPUT_PATH/operation_map.json" tmp/paths/

        if [ $? -eq 0 ]; then
            echo "✅ Paths successfully merged into operation map"
        else
            echo "⚠️  Warning: Failed to merge paths into operation map"
        fi
    else
        echo "⚠️  Warning: operation_map.json not found at $OUTPUT_PATH/operation_map.json"
    fi
fi

# Step 6: Generate header file from helpers (fallback if not done in Step 5)
if should_perform "6"; then
    echo "🔧 Step 6: Generating header file from helpers (if not already done)..."
    if [ ! -f "$OUTPUT_PATH/helpers.h" ] || [ "$PER_FUNCTION" != "true" ]; then
        echo "Command: python3 utils/gen_headers_clang.py $OUTPUT_PATH/helpers.c $OUTPUT_PATH/helpers.h"
        python3 utils/gen_headers_clang.py "$OUTPUT_PATH/helpers.c" "$OUTPUT_PATH/helpers.h"
    else
        echo "✓ helpers.h already generated in Step 5"
    fi
fi

# Define the COMPILE_COMMAND
if [ -n "$COMPILE_COMMAND" ]; then
    echo "Using custom compile command: $COMPILE_COMMAND"
else
    # Get the directory containing the main source file
    SOURCE_DIR=$(dirname "$SOURCE_FILE")
    echo "📁 Source directory: $SOURCE_DIR"
    echo "📄 Source files: $SOURCE_FILE"

    # Build include flags based on architecture
    # Always include Unity framework
    UNITY_DIR="lib/unity"
    UNITY_INCLUDE="-I$UNITY_DIR"
    UNITY_SOURCE="$UNITY_DIR/unity.c"

    # Malloc wrapper for testing allocation failures
    MALLOC_WRAP_DIR="lib/malloc_wrap"
    MALLOC_WRAP_INCLUDE="-I$MALLOC_WRAP_DIR"
    MALLOC_WRAP_SOURCE="$MALLOC_WRAP_DIR/malloc_wrap.c"
    MALLOC_WRAP_FLAGS="-Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc"

    if [ "$ARCHITECTURE" == "monolithic" ]; then
        # Monolithic needs extra include paths: source dir + output path (for helpers.h) + header file directories + Unity + malloc_wrap
        INCLUDE_FLAGS="-I$SOURCE_DIR -I$OUTPUT_PATH $UNITY_INCLUDE $MALLOC_WRAP_INCLUDE"
        for header_file in $HEADER_FILES; do
            header_dir=$(dirname "$header_file")
            if [ -n "$header_dir" ] && [ "$header_dir" != "." ]; then
                INCLUDE_FLAGS="$INCLUDE_FLAGS -I$header_dir"
            fi
        done
        echo "📁 Include flags (monolithic): $INCLUDE_FLAGS"
    else
        INCLUDE_FLAGS="-I$SOURCE_DIR $UNITY_INCLUDE $MALLOC_WRAP_INCLUDE"
    fi

    # ASan flags for better debugging: -fsanitize=address catches NULL derefs, buffer overflows, use-after-free
    # Include Unity source file and malloc_wrap for linking
    # Malloc wrap flags enable testing of allocation failure paths
    COMPILE_COMMAND="gcc -g -std=c99 -Wall -fsanitize=address -fno-omit-frame-pointer $MALLOC_WRAP_FLAGS $INCLUDE_FLAGS $OUTPUT_PATH/unit_test.c $OUTPUT_PATH/helpers.c $UNITY_SOURCE $MALLOC_WRAP_SOURCE $SOURCE_FILE -o $OUTPUT_PATH/unit_test -lm"
    echo "Using default compile command: $COMPILE_COMMAND"
fi

# Step 7: Validate the generated C code (only for legacy monolithic mode)
# Per-function mode already validates each function in Step 4 of apis.main
if should_perform "7" && [ "$PER_FUNCTION" != "true" ]; then
    echo "🔍 Step 7: Validating C code..."
    echo "Command: python3 -m apis.validation $SOURCE_FILE --name $SUBJECT --compile_command $COMPILE_COMMAND --output_path $OUTPUT_PATH"
    python3 -m apis.validation "$SOURCE_FILE" --name "$SUBJECT" --compile_command "$COMPILE_COMMAND" --output_path "$OUTPUT_PATH"
elif should_perform "7"; then
    echo "✓ Step 7: Skipped (per-function validation already completed in Step 4)"
fi

# Note: helpers.h is generated once in Step 5 after apis.main completes
# No need to regenerate here - this avoids redundant calls to gen_headers_clang.py

# Step 8: Compile the unit test
if should_perform "8"; then
    echo "🔨 Step 8: Compiling final unit test..."
    eval "$COMPILE_COMMAND"
fi

# Step 9: Run the unit test
if should_perform "9"; then
    echo "🧪 Step 9: Running unit test..."
    ./"$OUTPUT_PATH/unit_test"
fi

if should_perform "coverage"; then
    echo "📊 Running coverage analysis..."
    
    # Setup directories
    BUILD_DIR="build/$SUBJECT"
    COVERAGE_DIR="$OUTPUT_PATH/coverage"
    mkdir -p "$BUILD_DIR"
    mkdir -p "$COVERAGE_DIR"

    # Use validated C code if it exists, otherwise fall back to original
    if [ -f "$OUTPUT_PATH/unit_test.c" ]; then
        UNIT_TEST_FILE="$OUTPUT_PATH/unit_test.c"
        echo "✅ Using $UNIT_TEST_FILE for coverage"
    else
        echo "❌ Error: No unit test C file found for coverage analysis."
        exit 1
    fi

    # Get source directory and files
    SOURCE_DIR=$(dirname "$SOURCE_FILE")

    echo "=== Building coverage for $SUBJECT ==="
    echo "Source file: $SOURCE_FILE"
    echo "Source directory: $SOURCE_DIR"
    echo "Unit test file: $UNIT_TEST_FILE"
    echo "Helper file: $OUTPUT_PATH/helpers.c"

    # Build include flags for coverage compilation (same logic as Step 8)
    # Include Unity framework
    UNITY_DIR="lib/unity"
    UNITY_INCLUDE="-I$UNITY_DIR"
    UNITY_SOURCE="$UNITY_DIR/unity.c"

    # Malloc wrapper for testing allocation failures (same as Step 8)
    MALLOC_WRAP_DIR="lib/malloc_wrap"
    MALLOC_WRAP_INCLUDE="-I$MALLOC_WRAP_DIR"
    MALLOC_WRAP_SOURCE="$MALLOC_WRAP_DIR/malloc_wrap.c"
    MALLOC_WRAP_FLAGS="-Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc"

    if [ "$ARCHITECTURE" == "monolithic" ]; then
        COVERAGE_INCLUDE_FLAGS="-I$SOURCE_DIR -I$OUTPUT_PATH $UNITY_INCLUDE $MALLOC_WRAP_INCLUDE"
        for header_file in $HEADER_FILES; do
            header_dir=$(dirname "$header_file")
            if [ -n "$header_dir" ] && [ "$header_dir" != "." ]; then
                COVERAGE_INCLUDE_FLAGS="$COVERAGE_INCLUDE_FLAGS -I$header_dir"
            fi
        done
        echo "📁 Coverage include flags (monolithic): $COVERAGE_INCLUDE_FLAGS"
    else
        COVERAGE_INCLUDE_FLAGS="-I$SOURCE_DIR $UNITY_INCLUDE $MALLOC_WRAP_INCLUDE"
    fi

    # Compile with coverage instrumentation
    echo "🔨 Compiling with coverage instrumentation..."
    gcc -fprofile-arcs -ftest-coverage -g -O0 \
        $MALLOC_WRAP_FLAGS \
        $COVERAGE_INCLUDE_FLAGS \
        -o "$BUILD_DIR/${SUBJECT}_coverage_test" \
        "$UNIT_TEST_FILE" \
        "$OUTPUT_PATH/helpers.c" \
        "$UNITY_SOURCE" \
        "$MALLOC_WRAP_SOURCE" \
        "$SOURCE_FILE" \
        -lm

    # Run tests to generate coverage data
    echo "🧪 Running tests for coverage data..."
    cd "$(pwd)" && "$BUILD_DIR/${SUBJECT}_coverage_test"

    # Check if lcov is available
    if ! command -v lcov &> /dev/null; then
        echo "⚠️  lcov not found. Installing coverage tools..."
        echo "Please install lcov: brew install lcov (macOS) or apt-get install lcov (Ubuntu)"
        echo "Generating simple coverage summary with gcov..."
        
        # Use gcov as fallback
        cd "$BUILD_DIR"
        gcov *.gcda
        echo "📄 Coverage files generated in $BUILD_DIR"
        ls -la *.gcov 2>/dev/null || echo "No .gcov files generated"
    else
        # Generate coverage report with lcov
        echo "📈 Generating coverage report..."
        
        # Enable branch coverage for lcov
        LCOV_BRANCH_FLAG="--rc lcov_branch_coverage=1"
        
        # Capture coverage data (with branch coverage enabled)
        lcov --capture \
            --directory "$BUILD_DIR" \
            --output-file "$COVERAGE_DIR/coverage.info" \
            $LCOV_BRANCH_FLAG \
            --quiet

        # Filter to include only source files (exclude system headers and test files)
        lcov --extract "$COVERAGE_DIR/coverage.info" \
            "$(pwd)/$SOURCE_DIR/*" \
            --output-file "$COVERAGE_DIR/source-only.info" \
            $LCOV_BRANCH_FLAG \
            --quiet

        # Generate HTML reports
        if command -v genhtml &> /dev/null; then
            echo "📊 Generating HTML coverage reports..."
            
            # Full coverage report (with branch coverage)
            genhtml "$COVERAGE_DIR/coverage.info" \
                    --output-directory "$COVERAGE_DIR/full" \
                    --title "$SUBJECT Full Coverage Report" \
                    --branch-coverage \
                    --quiet

            # Source-only coverage report (with branch coverage)
            genhtml "$COVERAGE_DIR/source-only.info" \
                    --output-directory "$COVERAGE_DIR/source" \
                    --title "$SUBJECT Source Coverage Report" \
                    --branch-coverage \
                    --quiet

            echo "=== Coverage Analysis Complete ==="
            echo "📁 Coverage directory: $COVERAGE_DIR"
            echo "📊 Full report: $COVERAGE_DIR/full/index.html"
            echo "🎯 Source-only report: $COVERAGE_DIR/source/index.html"
            echo "🔍 Open reports: open $COVERAGE_DIR/source/index.html"
        else
            echo "⚠️  genhtml not available. Coverage data captured but no HTML report generated."
            echo "📄 Coverage data: $COVERAGE_DIR/coverage.info"
        fi

        # Parse lcov summary to extract coverage metrics (with branch coverage enabled)
        COVERAGE_OUTPUT=$(lcov --summary "$COVERAGE_DIR/source-only.info" $LCOV_BRANCH_FLAG 2>&1)
        
        # Extract Function Coverage
        FUNC_COVERAGE=$(echo "$COVERAGE_OUTPUT" | grep -i "functions" | head -1 | sed 's/.*: //' | tr -d ' ')
        if [ -z "$FUNC_COVERAGE" ]; then
            FUNC_COVERAGE="N/A"
        fi
        
        # Extract Line Coverage
        LINE_COVERAGE=$(echo "$COVERAGE_OUTPUT" | grep -i "lines" | head -1 | sed 's/.*: //' | tr -d ' ')
        if [ -z "$LINE_COVERAGE" ]; then
            LINE_COVERAGE="N/A"
        fi
        
        # Extract Branch Coverage
        BRANCH_COVERAGE=$(echo "$COVERAGE_OUTPUT" | grep -i "branches" | head -1 | sed 's/.*: //' | tr -d ' ')
        if [ -z "$BRANCH_COVERAGE" ]; then
            BRANCH_COVERAGE="N/A"
        fi
        
        # Store coverage for final summary
        COVERAGE_COLLECTED="true"
    fi

    echo "✅ Coverage analysis completed!"
fi

# Info: Show pipeline summary
if should_perform "info"; then
    print_pipeline_summary
fi

echo ""
echo "✅ Pipeline completed for $SUBJECT"