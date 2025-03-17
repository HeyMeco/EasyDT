#!/usr/bin/env python3
"""
DTS Visualizer - A tool to visualize Device Tree Source files as tree structures

Usage:
    python dts_visualizer.py <dts_file> [--output format]
"""

import sys
import re
import argparse
from typing import Dict, List, Any, Tuple, Optional
import os
import json
from rich.tree import Tree
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

class DTSNode:
    """Represents a node in the device tree."""
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.properties = {}
        self.labels = []
        self.references = []  # References created with &name
        
    def add_child(self, child: 'DTSNode'):
        """Add a child node to this node."""
        self.children.append(child)
        
    def add_property(self, name: str, value):
        """Add a property to this node."""
        self.properties[name] = value
        
    def add_label(self, label: str):
        """Add a label to this node."""
        self.labels.append(label)
        
    def add_reference(self, reference: str):
        """Add a reference (using &name syntax) to this node."""
        self.references.append(reference)
        
    def __str__(self):
        return self.name
    
    def to_dict(self):
        """Convert node to dictionary for JSON export."""
        result = {
            "name": self.name,
            "labels": self.labels,
            "references": self.references,
            "properties": self.properties,
            "children": [child.to_dict() for child in self.children]
        }
        return result

class DTSParser:
    """Parser for DTS files."""
    def __init__(self, content: str, references=None, includes=None):
        self.content = content
        self.root = DTSNode("root")
        self.current_node = self.root
        # Initialize or use provided references dictionary
        self.references = references or {}  
        # Initialize or use provided includes dictionary
        self.includes = includes or {}
        
    def parse(self) -> DTSNode:
        """Parse the DTS content and return the root node."""
        # Remove comments
        content = re.sub(r'/\*.*?\*/', '', self.content, flags=re.DOTALL)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        
        # Extract includes for potential processing
        include_pattern = r'^\s*#include\s+"([^"]+)"\s*$'
        includes = re.finditer(include_pattern, content, re.MULTILINE)
        for include in includes:
            include_file = include.group(1)
            self.includes[include_file] = True
        
        # Remove include directives from content for now
        content = re.sub(include_pattern, '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*/dts-v1/;.*$', '', content, flags=re.MULTILINE)
        
        # Track node depth
        depth = 0
        current_node = self.root
        node_stack = [current_node]
        
        # Process line by line
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
                
            # Handle node opening with possible reference
            node_match = re.match(r'([a-zA-Z0-9_,+.:-]+:)?\s*(&)?([a-zA-Z0-9_,@.+/-]+)\s*{', line)
            if node_match:
                label = node_match.group(1)
                is_reference = node_match.group(2) is not None
                name = node_match.group(3)
                
                # Create new node
                new_node = DTSNode(name, current_node)
                if label:
                    new_node.add_label(label.rstrip(':'))
                
                # Handle reference (&name)
                if is_reference:
                    new_node.add_reference('&' + name)
                    self.references['&' + name] = new_node
                
                current_node.add_child(new_node)
                current_node = new_node
                node_stack.append(current_node)
                depth += 1
            
            # Handle node additions/inclusions with <&name> syntax
            elif re.match(r'\s*<&[a-zA-Z0-9_]+>\s*;', line):
                ref_match = re.search(r'<&([a-zA-Z0-9_]+)>', line)
                if ref_match:
                    ref_name = '&' + ref_match.group(1)
                    # Store reference to resolve after full parsing
                    current_node.add_property('__node_inclusion__', ref_name)
                
            # Handle properties
            elif ':' in line and '{' not in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    prop_name = parts[0].strip().rstrip(':')
                    prop_value = parts[1].strip().rstrip(';')
                    current_node.add_property(prop_name, prop_value)
                else:
                    # Handle boolean properties
                    prop_name = line.strip().rstrip(';').rstrip(':')
                    current_node.add_property(prop_name, True)
            
            # Handle properties with = but no :
            elif '=' in line and '{' not in line and ';' in line:
                parts = line.split('=', 1)
                prop_name = parts[0].strip()
                prop_value = parts[1].strip().rstrip(';')
                current_node.add_property(prop_name, prop_value)
            
            # Handle node closing
            elif '}' in line:
                count = line.count('}')
                for _ in range(count):
                    if len(node_stack) > 1:  # Don't pop the root
                        node_stack.pop()
                    depth -= 1
                current_node = node_stack[-1]
            
            # Handle multi-line properties
            elif '=' in line and ';' not in line:
                # Collect multi-line property
                prop_parts = line.split('=', 1)
                prop_name = prop_parts[0].strip()
                prop_value = prop_parts[1].strip()
                
                # Continue collecting until we find a semicolon
                j = i + 1
                while j < len(lines) and ';' not in lines[j]:
                    prop_value += ' ' + lines[j].strip()
                    j += 1
                
                if j < len(lines):
                    prop_value += ' ' + lines[j].strip().rstrip(';')
                    i = j  # Skip processed lines
                
                current_node.add_property(prop_name, prop_value)
            
            i += 1
        
        # We'll still resolve the references for this file
        # but the MultiFileDTSParser will do a global resolution later
        self._resolve_references(self.root)
            
        return self.root
    
    def _resolve_references(self, node: DTSNode):
        """Resolve node references recursively."""
        # Check if this node has inclusions
        if '__node_inclusion__' in node.properties:
            ref_name = node.properties['__node_inclusion__']
            if ref_name in self.references:
                # Copy properties and children from referenced node
                ref_node = self.references[ref_name]
                for prop_name, prop_value in ref_node.properties.items():
                    if prop_name not in node.properties:
                        node.add_property(prop_name, prop_value)
                
                # Add children from referenced node
                for child in ref_node.children:
                    # Create a copy of the child with current node as parent
                    copy_child = DTSNode(child.name, node)
                    for label in child.labels:
                        copy_child.add_label(label)
                    for ref in child.references:
                        copy_child.add_reference(ref)
                    for prop_name, prop_value in child.properties.items():
                        copy_child.add_property(prop_name, prop_value)
                    
                    # Recursively add children
                    self._copy_children(child, copy_child)
                    
                    # Add this copy to current node
                    node.add_child(copy_child)
            
            # Remove the temporary property
            del node.properties['__node_inclusion__']
        
        # Process children recursively
        for child in node.children:
            self._resolve_references(child)
    
    def _copy_children(self, source_node: DTSNode, target_node: DTSNode):
        """Helper method to recursively copy children from source to target node."""
        for child in source_node.children:
            # Create a copy of the child with target node as parent
            copy_child = DTSNode(child.name, target_node)
            for label in child.labels:
                copy_child.add_label(label)
            for ref in child.references:
                copy_child.add_reference(ref)
            for prop_name, prop_value in child.properties.items():
                copy_child.add_property(prop_name, prop_value)
            
            # Recursively add children
            self._copy_children(child, copy_child)
            
            # Add this copy to target node
            target_node.add_child(copy_child)

class MultiFileDTSParser:
    """Parser for handling multiple DTS files with cross-file references."""
    def __init__(self):
        self.references = {}  # Global references across all files
        self.includes = {}    # Track include relationships
        self.parsed_files = {}  # Cache of parsed files
        self.root = DTSNode("multi_root")  # Root for combined tree
        
    def parse_file(self, filepath: str, base_dir: str = None) -> DTSNode:
        """Parse a DTS file and its includes, returning the parsed tree."""
        # Normalize path
        if base_dir and not os.path.isabs(filepath):
            filepath = os.path.join(base_dir, filepath)
        filepath = os.path.normpath(filepath)
        
        # Check if already parsed
        if filepath in self.parsed_files:
            return self.parsed_files[filepath]
        
        # Read the file
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Warning: Could not find file {filepath}")
            return None
        
        # Parse the file
        base_dir = os.path.dirname(filepath)
        parser = DTSParser(content, self.references, self.includes)
        node = parser.parse()
        
        # Update references
        self.references.update(parser.references)
        
        # Process includes if any
        for include_file in parser.includes:
            # Resolve relative path
            include_path = os.path.join(base_dir, include_file)
            include_path = os.path.normpath(include_path)
            
            # Parse included file if not already parsed
            if include_path not in self.parsed_files:
                self.parse_file(include_path, base_dir)
        
        # Cache the parsed result
        self.parsed_files[filepath] = node
        
        # Add to the multi-root
        self.root.add_child(node)
        
        return node
    
    def resolve_all_references(self):
        """Resolve all references across all parsed files."""
        for filepath, node in self.parsed_files.items():
            parser = DTSParser("", self.references)
            parser._resolve_references(node)
        
        # Also resolve references in the multi-root
        parser = DTSParser("", self.references)
        parser._resolve_references(self.root)
        
        return self.root

class DTSVisualizer:
    """Visualizes a DTS tree structure."""
    def __init__(self, root: DTSNode):
        self.root = root
        self.console = Console()
        
    def visualize(self):
        """Visualize the DTS tree structure using Rich."""
        tree = Tree(f"[bold]{self.root.name}[/bold]")
        
        self._add_node_to_tree(self.root, tree)
        
        self.console.print("\n[bold cyan]Device Tree Visualization[/bold cyan]")
        self.console.print(Panel(tree, expand=False, border_style="green"))
        
    def export_json(self, output_file: str):
        """Export the DTS tree as JSON."""
        tree_dict = self.root.to_dict()
        
        with open(output_file, 'w') as f:
            json.dump(tree_dict, f, indent=2)
            
        self.console.print(f"[green]Exported JSON to {output_file}[/green]")
    
    def _add_node_to_tree(self, node: DTSNode, tree: Tree):
        """Recursively add nodes to the tree."""
        for child in node.children:
            # Prepare node representation
            node_text = f"[bold blue]{child.name}[/bold blue]"
            
            # Add labels if any
            if child.labels:
                labels_str = ", ".join(child.labels)
                node_text += f" [dim]({labels_str})[/dim]"
            
            # Add references if any
            if child.references:
                refs_str = ", ".join(child.references)
                node_text += f" [bold magenta]{refs_str}[/bold magenta]"
            
            # Create branch for this node
            branch = tree.add(node_text)
            
            # Add properties
            if child.properties:
                props_branch = branch.add("[italic]Properties[/italic]")
                for name, value in child.properties.items():
                    props_branch.add(f"[green]{name}[/green] = [yellow]{value}[/yellow]")
            
            # Process children recursively
            self._add_node_to_tree(child, branch)

def main():
    parser = argparse.ArgumentParser(description="Visualize DTS files as tree structures")
    parser.add_argument("dts_files", nargs='+', help="Path(s) to the DTS file(s) to visualize")
    parser.add_argument("--output", "-o", choices=["json"], help="Export format (json)")
    parser.add_argument("--output-file", "-f", help="Output file path for exports")
    parser.add_argument("--combined", "-c", action="store_true", help="Create a combined visualization of all files")
    args = parser.parse_args()
    
    try:
        # Create multi-file parser
        multi_parser = MultiFileDTSParser()
        
        # Parse all provided files
        for dts_file in args.dts_files:
            print(f"Parsing {dts_file}...")
            multi_parser.parse_file(dts_file)
        
        # Resolve all references
        print("Resolving references across all files...")
        multi_parser.resolve_all_references()
        
        # Visualize based on mode
        if args.combined:
            # Combined visualization
            print("Creating combined visualization...")
            visualizer = DTSVisualizer(multi_parser.root)
            visualizer.visualize()
            
            # Handle exports for combined view
            if args.output == "json":
                output_file = args.output_file or "combined_dts.json"
                visualizer.export_json(output_file)
        else:
            # Individual visualizations
            for dts_file in args.dts_files:
                filepath = os.path.normpath(dts_file)
                if filepath in multi_parser.parsed_files:
                    print(f"Visualizing {dts_file}...")
                    node = multi_parser.parsed_files[filepath]
                    visualizer = DTSVisualizer(node)
                    visualizer.visualize()
                    
                    # Handle exports for individual files
                    if args.output == "json":
                        output_file = args.output_file or f"{os.path.splitext(dts_file)[0]}.json"
                        visualizer.export_json(output_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 