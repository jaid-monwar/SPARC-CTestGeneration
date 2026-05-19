#!/usr/bin/env python3
"""
Extract all unique paths from START to RETURN nodes in a CFG DOT file.

This script parses a Graphviz DOT file representing a Control Flow Graph (CFG),
identifies all START nodes (entry points) and RETURN nodes (exit points),
and extracts all unique paths between them using depth-first search.

Output: JSON file with the same name as input DOT file containing all paths.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class CFGPathExtractor:
    def __init__(self, dot_file: str):
        self.dot_file = dot_file
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.node_labels: Dict[str, str] = {}
        self.node_types: Dict[str, str] = {}
        self.start_nodes: Set[str] = set()
        self.return_nodes: Set[str] = set()

    def parse_dot_file(self) -> None:
        """Parse the DOT file and extract graph structure and node information."""
        with open(self.dot_file, 'r') as f:
            content = f.read()

        # Extract node definitions
        # Pattern: node1 [shape="invhouse"; class="entry"; ... label="START\n    START"];
        node_pattern = r'(\w+)\s*\[([^\]]+)\];'
        for match in re.finditer(node_pattern, content):
            node_id = match.group(1)
            attributes = match.group(2)

            # Extract label
            label_match = re.search(r'label="([^"]*)"', attributes)
            if label_match:
                label_text = label_match.group(1)
                # Clean up the label (remove extra whitespace)
                label_lines = [line.strip() for line in label_text.split('\\n') if line.strip()]
                self.node_labels[node_id] = ' | '.join(label_lines)

                # Determine node type from label
                if 'START' in label_text:
                    self.node_types[node_id] = 'START'
                    self.start_nodes.add(node_id)
                elif 'RETURN' in label_text:
                    self.node_types[node_id] = 'RETURN'
                    self.return_nodes.add(node_id)
                elif 'CONDITION' in label_text:
                    self.node_types[node_id] = 'CONDITION'
                elif 'STATEMENT' in label_text:
                    self.node_types[node_id] = 'STATEMENT'
                elif 'MERGE' in label_text:
                    self.node_types[node_id] = 'MERGE'
                else:
                    self.node_types[node_id] = 'UNKNOWN'

        # Extract edges
        # Pattern: node1 -> node2 [class="regular"; color="#2592a1"];
        edge_pattern = r'(\w+)\s*->\s*(\w+)\s*\[([^\]]+)\];'
        for match in re.finditer(edge_pattern, content):
            from_node = match.group(1)
            to_node = match.group(2)
            attributes = match.group(3)

            # Extract edge class (consequence, alternative, regular, exception)
            class_match = re.search(r'class="([^"]*)"', attributes)
            edge_type = class_match.group(1) if class_match else 'regular'

            self.graph[from_node].append(to_node)

    def find_all_paths(self, start: str, end: str, path: List[str] = None,
                       visited: Set[str] = None) -> List[List[str]]:
        """
        Find all paths from start node to end node using DFS.

        Args:
            start: Starting node ID
            end: Target node ID
            path: Current path being explored
            visited: Set of visited nodes to detect cycles

        Returns:
            List of all paths (each path is a list of node IDs)
        """
        if path is None:
            path = []
        if visited is None:
            visited = set()

        path = path + [start]
        visited = visited | {start}

        # Base case: reached the end node
        if start == end:
            return [path]

        # No outgoing edges
        if start not in self.graph:
            return []

        # Recursive case: explore all neighbors
        all_paths = []
        for neighbor in self.graph[start]:
            # Avoid cycles
            if neighbor not in visited:
                new_paths = self.find_all_paths(neighbor, end, path, visited)
                all_paths.extend(new_paths)

        return all_paths

    def extract_all_paths(self) -> List[Dict]:
        """
        Extract all unique paths from all START nodes to all RETURN nodes.

        Returns:
            List of path dictionaries with node IDs, labels, and types
        """
        all_paths_data = []
        path_counter = 1

        # Find paths from each START node to each RETURN node
        for start_node in sorted(self.start_nodes):
            for return_node in sorted(self.return_nodes):
                paths = self.find_all_paths(start_node, return_node)

                for path in paths:
                    path_data = {
                        "path_id": path_counter,
                        "start_node": start_node,
                        "end_node": return_node,
                        "length": len(path),
                        "nodes": []
                    }

                    # Add detailed information for each node in the path
                    for node_id in path:
                        node_info = {
                            "node_id": node_id,
                            "type": self.node_types.get(node_id, "UNKNOWN"),
                            "label": self.node_labels.get(node_id, "")
                        }
                        path_data["nodes"].append(node_info)

                    all_paths_data.append(path_data)
                    path_counter += 1

        return all_paths_data

    def save_to_json(self, paths: List[Dict]) -> Tuple[str, str]:
        """
        Save paths to two JSON files:
        1. {filename}_detailed.json - Full detailed path information
        2. {filename}.json - Simplified with concatenated path strings

        Args:
            paths: List of path dictionaries

        Returns:
            Tuple of (detailed_json_path, simplified_json_path)
        """
        dot_path = Path(self.dot_file)
        base_name = dot_path.stem  # filename without extension

        # Generate detailed JSON filename
        detailed_json_file = dot_path.parent / f"{base_name}_detailed.json"

        # Generate simplified JSON filename
        simplified_json_file = dot_path.with_suffix('.json')

        # Detailed output (original format)
        detailed_data = {
            "source_file": str(dot_path.name),
            "total_paths": len(paths),
            "start_nodes": sorted(list(self.start_nodes)),
            "return_nodes": sorted(list(self.return_nodes)),
            "paths": paths
        }

        with open(detailed_json_file, 'w') as f:
            json.dump(detailed_data, f, indent=2)

        # Simplified output (concatenated path strings)
        simplified_paths = []
        for path in paths:
            # Concatenate all node labels with " --> "
            path_string = " --> ".join([node["label"] for node in path["nodes"]])
            simplified_paths.append({
                "path_id": path["path_id"],
                "path": path_string
            })

        simplified_data = {
            "source_file": str(dot_path.name),
            "total_paths": len(paths),
            "paths": simplified_paths
        }

        with open(simplified_json_file, 'w') as f:
            json.dump(simplified_data, f, indent=2)

        return (str(detailed_json_file), str(simplified_json_file))


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_cfg_paths.py <dot_file>")
        print("Example: python extract_cfg_paths.py insert_fixed.dot")
        sys.exit(1)

    dot_file = sys.argv[1]

    if not Path(dot_file).exists():
        print(f"Error: File '{dot_file}' not found")
        sys.exit(1)

    print(f"Parsing DOT file: {dot_file}")
    extractor = CFGPathExtractor(dot_file)
    extractor.parse_dot_file()

    print(f"Found {len(extractor.start_nodes)} START node(s): {extractor.start_nodes}")
    print(f"Found {len(extractor.return_nodes)} RETURN node(s): {extractor.return_nodes}")
    print(f"Total nodes: {len(extractor.node_labels)}")
    print(f"Total edges: {sum(len(v) for v in extractor.graph.values())}")

    print("\nExtracting all paths...")
    paths = extractor.extract_all_paths()

    print(f"Found {len(paths)} unique path(s)")

    detailed_file, simplified_file = extractor.save_to_json(paths)
    print(f"\nDetailed paths saved to: {detailed_file}")
    print(f"Simplified paths saved to: {simplified_file}")

    # Print summary of paths
    print("\n=== Path Summary ===")
    for i, path in enumerate(paths, 1):
        print(f"Path {i}: {path['length']} nodes - "
              f"{path['start_node']} -> {path['end_node']}")


if __name__ == "__main__":
    main()
