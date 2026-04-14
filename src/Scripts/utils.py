"""
Utility functions for file discovery and symbol table building.
"""

import os
from typing import List, Dict, Set, Tuple
from parser import RTLParser


def discover_files(root_dir: str) -> List[str]:
    """
    Recursively discover all RTL files in a directory.

    Args:
        root_dir: Root directory to search

    Returns:
        List of absolute paths to .v, .sv, .svh files (with forward slashes)
    """
    if not os.path.isdir(root_dir):
        raise ValueError(f"Root directory does not exist: {root_dir}")

    rtl_extensions = {'.v', '.sv', '.svh'}
    files = []

    for root, dirs, filenames in os.walk(root_dir):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in rtl_extensions:
                # Use forward slashes for cross-platform compatibility
                file_path = os.path.join(root, filename).replace('\\', '/')
                files.append(file_path)

    return sorted(files)


def build_symbol_table(parsed_files) -> Dict[str, Tuple[str, str]]:
    """
    Build a symbol table mapping definition names to (file_path, type) tuples.

    Args:
        parsed_files: List of ParsedFile objects

    Returns:
        Dict[str, Tuple[str, str]] mapping definition names to (file_path, symbol_type) tuples.
        Symbol types include: module, interface, package, sequence, property, etc.
    """
    symbol_table: Dict[str, Tuple[str, str]] = {}
    duplicates: Dict[str, List[Tuple[str, str]]] = {}

    for parsed_file in parsed_files:
        for def_name in parsed_file.defines:
            def_type = parsed_file.define_types.get(def_name, 'unknown')
            
            if def_name in symbol_table:
                # Track duplicate definitions
                if def_name not in duplicates:
                    duplicates[def_name] = [symbol_table[def_name]]
                duplicates[def_name].append((parsed_file.file_path, def_type))
            else:
                symbol_table[def_name] = (parsed_file.file_path, def_type)

    # Report duplicates only for "unique" types (module, interface, package)
    for def_name, definitions in duplicates.items():
        # Get the type from the first definition (all duplicates have same name)
        def_type = definitions[0][1]
        
        # Only warn if this type should be unique
        if RTLParser.get_definition_uniqueness(def_type):
            print(f"Warning: duplicate definition '{def_name}' (type: {def_type}) in files:")
            for file_path, _ in definitions:
                print(f"  - {file_path}")
        else:
            # For non-unique types (sequence, property), just use the last definition found
            # This is acceptable since multiple definitions of these types are allowed
            pass

    return symbol_table


def write_file_list(file_list: List[str], output_path: str) -> None:
    """
    Write ordered file list to a file.

    Args:
        file_list: List of file paths in dependency order
        output_path: Path to output file (typically src_files.list)
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for file_path in file_list:
                # Convert backslashes to forward slashes for cross-platform compatibility
                normalized_path = file_path.replace('\\', '/')
                f.write('"' + normalized_path + '"\n')
        print(f"Successfully wrote {len(file_list)} files to {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")


def print_dependency_summary(file_list: List[str], symbol_table: Dict[str, str]) -> None:
    """
    Print a summary of the dependency resolution.

    Args:
        file_list: Ordered list of files
        symbol_table: Symbol table
    """
    print(f"\nDependency Resolution Summary")
    print(f"{'=' * 50}")
    print(f"Total files: {len(file_list)}")
    print(f"Total symbols: {len(symbol_table)}")
    print(f"\nOrdered file list:")
    print(f"{'-' * 50}")
    for i, file_path in enumerate(file_list, 1):
        # Convert backslashes to forward slashes for display consistency
        normalized_path = file_path.replace('\\', '/')
        print(f"{i:3d}. {normalized_path}")
