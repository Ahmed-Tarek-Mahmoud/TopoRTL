"""
RTL file parser for extracting dependencies from SystemVerilog/Verilog files.
"""

import re
from dataclasses import dataclass, field
from typing import Set


@dataclass
class ParsedFile:
    """Represents parsed information from a single RTL file."""
    file_path: str
    defines: Set[str] = field(default_factory=set)      # modules, interfaces, packages defined
    define_types: dict = field(default_factory=dict)    # maps definition name -> type (module, sequence, property, etc.)
    depends_on: Set[str] = field(default_factory=set)   # names of modules/packages/interfaces
    includes: Set[str] = field(default_factory=set)     # included file paths


class RTLParser:
    """Lightweight regex-based parser for Verilog/SystemVerilog files."""

    def __init__(self):
        # Pattern to match module, interface, package, sequence, and property definitions
        self.definition_pattern = re.compile(
            r'\b(module|interface|package|sequence|property)\s+(\w+)',
            re.MULTILINE
        )

        # Pattern to match module/interface instantiations
        # Matches: TypeName instance_name(...)
        self.instantiation_pattern = re.compile(
            r'\b([a-zA-Z_]\w*)\s+([a-zA-Z_]\w*)\s*\(',
            re.MULTILINE
        )

        # Pattern to match import statements
        # Matches: import pkg_name::*
        self.import_pattern = re.compile(
            r'import\s+(\w+)\s*::',
            re.MULTILINE
        )

        # Pattern to match include directives
        # Matches: `include "filename" or `include "path/filename"
        self.include_pattern = re.compile(
            r'`include\s+["\']([^"\']+)["\']',
            re.MULTILINE
        )

    def parse_file(self, file_path: str) -> ParsedFile:
        """
        Parse a single RTL file and extract definitions and dependencies.

        Args:
            file_path: Path to the RTL file

        Returns:
            ParsedFile object with extracted information
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")
            return ParsedFile(file_path)

        parsed = ParsedFile(file_path)

        # Remove comments to avoid false matches
        # Remove single-line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # Remove block comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Remove string literals to avoid false matches in function calls
        content = re.sub(r'"(?:[^"\\]|\\.)*"', '""', content)  # Replace string literals with empty strings
        content = re.sub(r"'(?:[^'\\]|\\.)*'", "''", content)  # Replace char literals with empty chars

        # Remove print statements to avoid false matches
        # Remove complete statement blocks that contain UVM print calls or SystemVerilog system tasks
        content = re.sub(
            r'\b(?:uvm_info|uvm_error|uvm_fatal|uvm_warning|uvm_report_info|uvm_report_error|uvm_report_warning|uvm_report_fatal)\b.*?;',
            '',
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # Also remove UVM calls that might not have semicolons (malformed code)
        # Match uvm_xxx( ... ) or uvm_xxx( ... at end of content
        content = re.sub(
            r'\b(?:uvm_info|uvm_error|uvm_fatal|uvm_warning|uvm_report_info|uvm_report_error|uvm_report_warning|uvm_report_fatal)\b\s*\([^)]*\)(?:\s*;)?',
            '',
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(
            r'\$(?:display|info|warning|error|fatal|monitor|write|sformatf)\b.*?;',
            '',
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # Extract definitions
        for match in self.definition_pattern.finditer(content):
            def_type, def_name = match.groups()
            parsed.defines.add(def_name)
            parsed.define_types[def_name] = def_type.lower()

        # Extract depends_on from instantiations
        # Heuristic: TypeName instance_name ( TypeName is a dependency )
        for match in self.instantiation_pattern.finditer(content):
            type_name, instance_name = match.groups()
            # Filter out SystemVerilog keywords that might match
            if not self._is_keyword(type_name) and not self._is_keyword(instance_name):
                parsed.depends_on.add(type_name)

        # Extract imports
        for match in self.import_pattern.finditer(content):
            pkg_name = match.group(1)
            parsed.depends_on.add(pkg_name)

        # Extract includes
        for match in self.include_pattern.finditer(content):
            include_path = match.group(1)
            parsed.includes.add(include_path)

        return parsed

    @staticmethod
    def _get_definition_uniqueness(def_type: str) -> bool:
        """
        Check if a definition type should be unique (no duplicates allowed).
        
        Args:
            def_type: Type of definition (module, interface, package, sequence, property, etc.)
        
        Returns:
            True if only one definition of this type should exist, False if multiple OK
        """
        # Types that must be unique across the project
        unique_types = {'module', 'interface', 'package'}
        return def_type.lower() in unique_types

    @staticmethod
    def _is_keyword(word: str) -> bool:
        """
        Check if a word is a SystemVerilog/Verilog keyword.
        Helps filter out false matches from instantiation pattern.
        """
        keywords = {
            # RTL definition keywords
            'module', 'endmodule', 'package', 'endpackage', 'interface', 'endinterface',
            'primitive', 'endprimitive', 'specify', 'endspecify', 'table', 'endtable',
            'config', 'endconfig', 'modport',
            # IO and type keywords
            'input', 'output', 'inout', 'wire', 'reg', 'logic', 'bit',
            'int', 'real', 'string', 'void', 'always', 'begin', 'end',
            'signed', 'unsigned',  # Type modifiers
            # Control flow keywords
            'if', 'else', 'for', 'while', 'case', 'function', 'task',
            'fork', 'join', 'initial', 'final', 'generate', 'genvar',
            'always_comb', 'always_ff', 'always_latch',
            # Declaration keywords
            'parameter', 'localparam', 'defparam', 'assign', 'automatic',
            'static', 'protected', 'local', 'public', 'super', 'this',
            'new', 'delete', 'randomize', 'clocking', 'constraint',
            'randcase', 'assert', 'assume', 'cover', 'property', 'sequence',
            # Type definition keywords
            'typedef', 'enum', 'struct', 'union', 'class', 'virtual',
            'extends', 'implements', 'extern', 'pure', 'void', 'bit',
            'byte', 'shortint', 'longint', 'logic', 'event', 'mailbox',
            # SV block and join keywords
            'join', 'join_any', 'join_none', 'endcase', 'type', 'unique',
            'priority', 'let', 'alias', 'const', 'with', 'inside',
            'throughout', 'within', 'covergroup', 'endgroup', 'endtask',
            'endfunction', 'endclass', 'endpackage', 'endmodule',
            # Preprocessor keywords
            'define', 'ifdef', 'endif', 'include', # `ifndef is ignored 
            # Import/Export
            'import', 'export',
            # Other common keywords
            'wait', 'repeat', 'disable', 'default',
            'strong', 'medium', 'weak', 'small', 'large',
            'std', 'posedge', 'negedge', 'edge', 'all'
        }
        return word.lower() in keywords

    @staticmethod
    def get_definition_uniqueness(def_type: str) -> bool:
        """Public wrapper for _get_definition_uniqueness for external access."""
        return RTLParser._get_definition_uniqueness(def_type)
