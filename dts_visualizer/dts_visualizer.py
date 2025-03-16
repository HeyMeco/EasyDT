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
        
    def add_child(self, child: 'DTSNode'):
        """Add a child node to this node."""
        self.children.append(child)
        
    def add_property(self, name: str, value):
        """Add a property to this node."""
        self.properties[name] = value
        
    def add_label(self, label: str):
        """Add a label to this node."""
        self.labels.append(label)
        
    def __str__(self):
        return self.name
    
    def to_dict(self):
        """Convert node to dictionary for JSON export."""
        result = {
            "name": self.name,
            "labels": self.labels,
            "properties": self.properties,
            "children": [child.to_dict() for child in self.children]
        }
        return result

class DTSParser:
    """Parser for DTS files."""
    def __init__(self, content: str):
        self.content = content
        self.root = DTSNode("root")
        self.current_node = self.root
        
    def parse(self) -> DTSNode:
        """Parse the DTS content and return the root node."""
        # Remove comments
        content = re.sub(r'/\*.*?\*/', '', self.content, flags=re.DOTALL)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        
        # Process includes and version directives
        # This is a simplified approach - for a complete parser, you'd handle these properly
        content = re.sub(r'^\s*#include.*$', '', content, flags=re.MULTILINE)
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
                
            # Handle node opening
            node_match = re.match(r'([a-zA-Z0-9_,+.:-]+:)?\s*([a-zA-Z0-9_,@.+/-]+)\s*{', line)
            if node_match:
                label = node_match.group(1)
                name = node_match.group(2)
                
                # Create new node
                new_node = DTSNode(name, current_node)
                if label:
                    new_node.add_label(label.rstrip(':'))
                
                current_node.add_child(new_node)
                current_node = new_node
                node_stack.append(current_node)
                depth += 1
                
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
    parser.add_argument("dts_file", help="Path to the DTS file to visualize")
    parser.add_argument("--output", "-o", choices=["json"], help="Export format (json)")
    parser.add_argument("--output-file", "-f", help="Output file path for exports")
    args = parser.parse_args()
    
    try:
        with open(args.dts_file, 'r') as f:
            content = f.read()
        
        print(f"Parsing {args.dts_file}...")
        dts_parser = DTSParser(content)
        root = dts_parser.parse()
        
        visualizer = DTSVisualizer(root)
        
        # Handle exports if requested
        if args.output == "json":
            output_file = args.output_file or f"{os.path.splitext(args.dts_file)[0]}.json"
            visualizer.export_json(output_file)
        
        # Always show visualization
        print(f"Visualizing {args.dts_file}...")
        visualizer.visualize()
        
    except FileNotFoundError:
        print(f"Error: File '{args.dts_file}' not found.")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 