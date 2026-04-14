"""
Graph building and topological sorting for RTL dependencies.
"""

from typing import Dict, Set, List, Tuple, Optional
from collections import defaultdict


class DependencyGraph:
    """Build and analyze dependency graph from parsed RTL files."""

    def __init__(self, parsed_files, symbol_table):
        """
        Initialize with parsed files and symbol table.

        Args:
            parsed_files: List of ParsedFile objects
            symbol_table: Dict[str, Tuple[str, str]] mapping definition names to (file_path, symbol_type) tuples
        """
        self.parsed_files = parsed_files
        self.symbol_table = symbol_table
        self.graph: Dict[str, Set[str]] = {}  # file_path -> set of dependent file paths
        self.reverse_graph: Dict[str, Set[str]] = {}  # for cycle detection
        self.file_includes: Dict[str, str] = {}  # maps include filename -> resolved path
        self.self_loops: Dict[str, List[str]] = {}  # tracks self-loop dependencies

        # Known external libraries/packages to ignore (built-in to tools)
        self.external_packages = {
            'uvm_pkg', 'uvm',  # UVM framework
        }
        self.external_includes = {
            'uvm_macros.svh', 'uvm_macros',  # UVM macro file
        }

        # Build file index
        self.file_index = {pf.file_path: pf for pf in parsed_files}

    def build_graph(self) -> Dict[str, Set[str]]:
        """
        Build the dependency graph.

        Returns:
            Dict mapping file paths to their dependencies
        """
        for parsed_file in self.parsed_files:
            if parsed_file.file_path not in self.graph:
                self.graph[parsed_file.file_path] = set()
                self.reverse_graph[parsed_file.file_path] = set()
                self.self_loops[parsed_file.file_path] = []

            # Process symbol dependencies
            # print(parsed_file.depends_on)
            for dep_name in parsed_file.depends_on:
                if dep_name in self.symbol_table:
                    dep_file, _ = self.symbol_table[dep_name]  # Extract file_path from (file_path, type) tuple
                    if dep_file == parsed_file.file_path:
                        # Detect and report self-loops
                        self.self_loops[parsed_file.file_path].append(dep_name)
                        print(f"Warning: {parsed_file.file_path}: self-loop detected (depends on '{dep_name}')")
                    else:
                        self.graph[parsed_file.file_path].add(dep_file)
                        if dep_file not in self.reverse_graph:
                            self.reverse_graph[dep_file] = set()
                        self.reverse_graph[dep_file].add(parsed_file.file_path)
                else:
                    # Skip warning for known external packages
                    if not self._is_external_package(dep_name):
                        print(f"Warning: {parsed_file.file_path}: undefined dependency '{dep_name}'")

            # Process includes
            for include_path in parsed_file.includes:
                # Skip warning for known external includes
                if self._is_external_include(include_path):
                    continue

                resolved_path = self._resolve_include_path(parsed_file.file_path, include_path)
                if resolved_path and resolved_path in self.file_index:
                    if resolved_path == parsed_file.file_path:
                        # Detect and report self-include
                        self.self_loops[parsed_file.file_path].append(include_path)
                        print(f"Warning: {parsed_file.file_path}: self-loop detected (includes itself via '{include_path}')")
                    else:
                        self.graph[parsed_file.file_path].add(resolved_path)
                        if resolved_path not in self.reverse_graph:
                            self.reverse_graph[resolved_path] = set()
                        self.reverse_graph[resolved_path].add(parsed_file.file_path)
                else:
                    print(f"Warning: {parsed_file.file_path}: could not resolve include '{include_path}'")

        return self.graph

    def _is_external_package(self, package_name: str) -> bool:
        """
        Check if a package name is a known external/built-in package.

        Args:
            package_name: Name of the package

        Returns:
            True if the package is external and should be ignored
        """
        return package_name.lower() in self.external_packages

    def _is_external_include(self, include_path: str) -> bool:
        """
        Check if an include path is a known external/built-in include.

        Args:
            include_path: Path or filename of the include

        Returns:
            True if the include is external and should be ignored
        """
        import os
        # Check both the full path and just the filename
        path_lower = include_path.lower().replace('\\', '/')
        filename = os.path.basename(path_lower).lower()

        # Check against external includes
        for external in self.external_includes:
            external_lower = external.lower()
            if path_lower == external_lower or filename == external_lower:
                return True
        return False

    def _resolve_include_path(self, current_file: str, include_path: str) -> Optional[str]:
        """
        Resolve include path relative to current file.

        Args:
            current_file: Path to current file
            include_path: Include path (may be relative)

        Returns:
            Absolute path if found in file index, None otherwise
        """
        import os

        # Normalize paths to use forward slashes for cross-platform consistency
        current_file = current_file.replace('\\', '/')
        include_path = include_path.replace('\\', '/')

        # Try include_path as-is (absolute or relative to working directory)
        if include_path in self.file_index:
            return include_path

        # Try relative to current file's directory
        current_dir = os.path.dirname(current_file)
        relative_path = os.path.join(current_dir, include_path).replace('\\', '/')
        if relative_path in self.file_index:
            return relative_path

        # Try to find by filename only (in case full path isn't specified)
        include_basename = os.path.basename(include_path)
        for file_path in self.file_index:
            if os.path.basename(file_path) == include_basename:
                return file_path

        return None

    def detect_cycles(self) -> Tuple[bool, List[List[str]]]:
        """
        Detect cycles in the dependency graph.

        Returns:
            Tuple of (has_cycles, list of cycles found)
        """
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs_visit(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    dfs_visit(neighbor, path)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)
            path.pop()

        for node in self.graph:
            if node not in visited:
                dfs_visit(node, [])

        return len(cycles) > 0, cycles

    def topological_sort(self) -> Tuple[List[str], bool, List[List[str]]]:
        """
        Perform topological sort using DFS.

        Returns:
            Tuple of:
            - sorted_list: Topologically sorted file list
            - has_cycles: Whether cycles were detected
            - cycles: List of detected cycles (if any)
        """
        has_cycles, cycles = self.detect_cycles()

        if has_cycles:
            print("ERROR: Circular dependencies detected:")
            for cycle in cycles:
                print(f"  {' -> '.join(cycle)}")

        visited = set()
        sorted_list = []

        def dfs_visit(node: str) -> None:
            if node in visited:
                return
            visited.add(node)

            # Visit all dependencies first
            for dep in self.graph.get(node, set()):
                dfs_visit(dep)

            # Add node after its dependencies
            sorted_list.append(node)

        # Process all files
        for node in self.graph:
            dfs_visit(node)

        return sorted_list, has_cycles, cycles

    def has_self_loops(self) -> bool:
        """
        Check if any self-loops were detected.

        Returns:
            True if any self-loops exist
        """
        return any(len(loops) > 0 for loops in self.self_loops.values())

    def get_self_loops_summary(self) -> str:
        """
        Generate a summary of detected self-loops.

        Returns:
            String summary of self-loops (empty if none)
        """
        lines = []
        for file_path, loops in self.self_loops.items():
            if loops:
                lines.append(f"{file_path}:")
                for loop in loops:
                    lines.append(f"  - {loop}")
        return "\n".join(lines) if lines else ""
