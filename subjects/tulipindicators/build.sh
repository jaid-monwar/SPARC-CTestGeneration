#!/bin/bash
# Build tulipindicators KLEE driver into LLVM bitcode.
#
# Usage: ./build.sh
#
# This produces tulipindicators.bc which can be run with:
#   klee --libc=uclibc --posix-runtime tulipindicators.bc

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KLEE_INCLUDE="${SCRIPT_DIR}/../../include"

cd "$SCRIPT_DIR"

echo "Compiling klee_driver.c to LLVM bitcode..."
clang -emit-llvm -c -g -O0 \
    -I"${KLEE_INCLUDE}" \
    -Wno-implicit-function-declaration \
    klee_driver.c \
    -o tulipindicators.bc

echo "Generated: ${SCRIPT_DIR}/tulipindicators.bc"
echo ""
echo "Run with KLEE:"
echo "  klee --libc=uclibc --posix-runtime ${SCRIPT_DIR}/tulipindicators.bc"
