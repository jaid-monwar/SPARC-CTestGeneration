#!/usr/bin/env python3
"""
Count unique execution paths for all subjects in the subjects/ directory.

Runs the preprocessor on each subject to generate CFGs and extract paths,
counts total unique execution paths across all functions, then cleans up
the tmp/ directory before moving to the next subject.

Output: path_count.csv with columns (subject, path_count)

Usage:
    python scripts/count_execution_paths.py
    python scripts/count_execution_paths.py --output results.csv
    python scripts/count_execution_paths.py --subjects-dir subjects/
"""

import argparse
import csv
import glob
import json
import os
import shutil
import subprocess
import sys


def count_paths_in_dir(paths_dir):
    """Sum total_paths from all JSON files in a paths directory."""
    total = 0
    json_files = glob.glob(os.path.join(paths_dir, "*.json"))
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            total += data.get("total_paths", 0)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  [WARNING] Could not read {os.path.basename(jf)}: {e}")
    return total, len(json_files)


def find_c_files(subject_dir):
    """Find .c source files in a subject directory."""
    c_files = glob.glob(os.path.join(subject_dir, "*.c"))
    if not c_files:
        # Check src/ subdirectory
        c_files = glob.glob(os.path.join(subject_dir, "src", "*.c"))
    # Filter out test files
    c_files = [f for f in c_files if not os.path.basename(f).startswith("test")]
    return c_files


def main():
    parser = argparse.ArgumentParser(
        description="Count unique execution paths for all subjects"
    )
    parser.add_argument(
        "--subjects-dir",
        default="subjects",
        help="Directory containing subject folders (default: subjects)",
    )
    parser.add_argument(
        "--output",
        default="path_count.csv",
        help="Output CSV file (default: path_count.csv)",
    )
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subjects_dir = os.path.join(project_root, args.subjects_dir)
    preprocessor_script = os.path.join(project_root, "scripts", "preprocessor.py")
    tmp_dir = os.path.join(project_root, "tmp")
    paths_dir = os.path.join(tmp_dir, "paths")
    output_csv = os.path.join(project_root, args.output)

    if not os.path.isdir(subjects_dir):
        print(f"[ERROR] Subjects directory not found: {subjects_dir}")
        sys.exit(1)

    if not os.path.isfile(preprocessor_script):
        print(f"[ERROR] Preprocessor script not found: {preprocessor_script}")
        sys.exit(1)

    # Collect subject folders (sorted for deterministic ordering)
    subject_folders = sorted(
        [
            d
            for d in os.listdir(subjects_dir)
            if os.path.isdir(os.path.join(subjects_dir, d))
        ]
    )

    if not subject_folders:
        print(f"[ERROR] No subject folders found in {subjects_dir}")
        sys.exit(1)

    print(f"Found {len(subject_folders)} subjects in {subjects_dir}")
    print(f"Output will be written to: {output_csv}")
    print("=" * 60)

    results = []

    for i, subject in enumerate(subject_folders, 1):
        subject_path = os.path.join(subjects_dir, subject)
        c_files = find_c_files(subject_path)

        if not c_files:
            print(f"\n[{i}/{len(subject_folders)}] {subject}: No .c files found, skipping")
            results.append((subject, 0))
            continue

        print(f"\n[{i}/{len(subject_folders)}] {subject}: Processing {len(c_files)} file(s)...")

        # Clean tmp/ before running
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        # Run preprocessor (skip docs generation by using --skip-cfg=False, but skip docs step)
        # We only need steps up to path extraction (3a.1 through 3a.4)
        cmd = [
            sys.executable,
            preprocessor_script,
            subject_path,
            "--clean",
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Preprocessor failed for {subject}")
            if e.stderr:
                # Show last few lines of stderr for debugging
                lines = e.stderr.strip().split("\n")
                for line in lines[-5:]:
                    print(f"    {line}")
            results.append((subject, 0))
            # Clean up tmp/
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            continue
        except subprocess.TimeoutExpired:
            print(f"  [ERROR] Preprocessor timed out for {subject}")
            results.append((subject, 0))
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            continue

        # Count paths from tmp/paths/*.json
        path_count, func_count = count_paths_in_dir(paths_dir)
        print(f"  -> {func_count} function(s), {path_count} total unique execution path(s)")
        results.append((subject, path_count))

        # Clean up tmp/
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    # Write CSV
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"{'Subject':<45} {'Path Count':>10}")
    print("-" * 56)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["subject", "path_count"])
        for subject, count in results:
            writer.writerow([subject, count])
            print(f"{subject:<45} {count:>10}")

    total = sum(c for _, c in results)
    print("-" * 56)
    print(f"{'TOTAL':<45} {total:>10}")
    print(f"\nResults written to: {output_csv}")


if __name__ == "__main__":
    sys.exit(main() or 0)
