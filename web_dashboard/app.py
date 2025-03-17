#!/usr/bin/env python3
"""
EasyDT Web Dashboard - A web interface for EasyDT tools
"""

import os
import sys
import json
import io
import tempfile
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file

# Add parent directory to sys.path to import dts_visualizer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dts_visualizer.dts_visualizer import MultiFileDTSParser, DTSVisualizer, DTSNode, DTSParser

# Create a subclass of MultiFileDTSParser that can parse strings
class InMemoryMultiFileDTSParser(MultiFileDTSParser):
    """A subclass of MultiFileDTSParser that can parse strings directly."""
    
    def parse_string(self, content: str, virtual_path: str) -> DTSNode:
        """Parse a DTS string content, using a virtual filepath for reference."""
        virtual_path = os.path.normpath(virtual_path)
        
        # Check if already parsed
        if virtual_path in self.parsed_files:
            return self.parsed_files[virtual_path]
        
        # Parse the content
        parser = DTSParser(content, self.references, self.includes)
        node = parser.parse()
        
        # Update references
        self.references.update(parser.references)
        
        # Cache the parsed result
        self.parsed_files[virtual_path] = node
        
        # Add to the multi-root
        self.root.add_child(node)
        
        return node

# Create a subclass of DTSVisualizer that doesn't write to disk
class InMemoryDTSVisualizer(DTSVisualizer):
    """A subclass of DTSVisualizer that keeps data in memory."""
    
    def export_json_to_dict(self):
        """Export the DTS tree as a Python dictionary instead of writing to a file."""
        return self.root.to_dict()
        
    def export_json(self, output_file=None):
        """Override to prevent console output when used from the web dashboard."""
        if output_file:
            tree_dict = self.root.to_dict()
            with open(output_file, 'w') as f:
                json.dump(tree_dict, f, indent=2)
        return self.root.to_dict()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

@app.route('/')
def index():
    """Render the dashboard home page"""
    return render_template('index.html')

@app.route('/visualizer')
def visualizer():
    """Render the DTS visualizer page"""
    return render_template('visualizer.html')

@app.route('/api/visualize', methods=['POST'])
def api_visualize():
    """API endpoint to handle DTS file upload and visualization"""
    if 'dts_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['dts_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read file directly from request into memory
        file_content = file.read().decode('utf-8')
        
        # Parse the DTS file in memory
        multi_parser = InMemoryMultiFileDTSParser()
        # Create a virtual file path for reference
        virtual_path = os.path.normpath(file.filename)
        multi_parser.parse_string(file_content, virtual_path)
        multi_parser.resolve_all_references()
        
        # Get the tree
        node = multi_parser.parsed_files[virtual_path]
        
        # Export to dict in memory (no disk writes)
        visualizer = InMemoryDTSVisualizer(node)
        dts_data = visualizer.export_json_to_dict()
        
        return jsonify({
            'success': True,
            'data': dts_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-json', methods=['POST'])
def api_download_json():
    """API endpoint to download DTS data as JSON"""
    try:
        data = request.json
        if not data or 'data' not in data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create JSON in memory
        json_data = json.dumps(data['data'], indent=2)
        
        # Create in-memory file-like object
        mem_file = io.BytesIO(json_data.encode('utf-8'))
        mem_file.seek(0)
        
        # Send the file from memory
        return send_file(
            mem_file,
            as_attachment=True,
            download_name='dts_data.json',
            mimetype='application/json'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    if debug:
        # Development mode
        app.run(host=host, port=port, debug=True)
    else:
        # Production mode with waitress
        from waitress import serve
        serve(app, host=host, port=port)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="EasyDT Web Dashboard")
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, debug=args.debug) 