"""
Main entry point for RTL dependency resolver.

Usage:
    python main.py <rtl_root_dir> [output_file]

Example:
    python main.py ./rtl_designs src_files.list
"""

import sys
import os
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from parser import RTLParser
from graph import DependencyGraph
from utils import discover_files, build_symbol_table, write_file_list, print_dependency_summary


def resolve_dependencies(
    root_dir: str,
    output_file: Optional[str] = None
) -> list:
    """
    Main function to resolve RTL file dependencies.

    Args:
        root_dir: Root directory containing RTL files
        output_file: Optional output file path (default: src_files.list)

    Returns:
        List of files in topological order
    """
    print(f"Discovering RTL files in {root_dir}...")
    files = discover_files(root_dir)

    if not files:
        print("ERROR: No RTL files found!")
        return []

    print(f"Found {len(files)} RTL files")

    # Parse all files
    print("\nParsing files...")
    parser = RTLParser()
    parsed_files = []
    for file_path in files:
        parsed = parser.parse_file(file_path)
        parsed_files.append(parsed)

    # Build symbol table
    print("Building symbol table...")
    symbol_table = build_symbol_table(parsed_files)

    # Build dependency graph
    print("Building dependency graph...")
    dep_graph = DependencyGraph(parsed_files, symbol_table)
    graph = dep_graph.build_graph()

    # Topological sort
    print("Performing topological sort...")
    sorted_files, has_cycles, cycles = dep_graph.topological_sort()

    if has_cycles:
        print("\nWARNING: Circular dependencies detected!")
        print("The generated order may not be fully correct.")
        print("Please review the cycles listed above.\n")

    # Check for self-loops
    if dep_graph.has_self_loops():
        print("WARNING: Self-loop dependencies detected!")
        print("(A file depends on itself, which is invalid)\n")
        self_loops_summary = dep_graph.get_self_loops_summary()
        if self_loops_summary:
            print(self_loops_summary)
        print()

    # Print summary
    print_dependency_summary(sorted_files, symbol_table)

    # Write output
    if output_file is None:
        output_file = "src_files.list"

    write_file_list(sorted_files, output_file)

    return sorted_files


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    root_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "src_files.list"

    # Resolve to absolute path
    root_dir = os.path.abspath(root_dir)

    try:
        resolve_dependencies(root_dir, output_file)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
