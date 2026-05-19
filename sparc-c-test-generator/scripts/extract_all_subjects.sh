#!/bin/bash

# Script to extract functions from multiple C files

declare -A subjects=(
  ["bst"]="subjects/bst/bst.c"
  ["qsort"]="subjects/qsort/qsort.c"
  ["quadtree"]="subjects/quadtree-0.1.0/src/quadtree.c"
  ["rgba"]="subjects/rgba/src/rgba.c"
)

for name in "${!subjects[@]}"; do
  input_file="${subjects[$name]}"
  output_file="functions/${name}.json"
  echo "Extracting functions from $input_file -> $output_file"
  python3 utils/extract_funcs_enhanced.py "$input_file" "$output_file"
done
