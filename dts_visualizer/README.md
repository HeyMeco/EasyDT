# DTS Visualizer

A Python tool that parses and visualizes Device Tree Source (DTS) files as tree structures.

## Features

- Parses DTS files, handling:
  - Node hierarchy
  - Properties
  - Labels
  - Comments
- Visualizes the tree structure with a colorful, intuitive interface
- Shows properties and their values for each node
- Exports the device tree to JSON format for further processing

## Requirements

- Python 3.12+
- Rich library for visualization

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/dts-visualizer.git
   cd dts-visualizer
   ```

2. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

## Usage

Run the tool with a DTS file as an argument:

```
uv run dts_visualizer.py path/to/your/file.dts
```

### Exporting to JSON

To export the device tree to JSON format:

```
uv run dts_visualizer.py path/to/your/file.dts --output json
```

By default, the JSON file will be saved with the same name as the input file but with a `.json` extension. You can specify a custom output path:

```
uv run dts_visualizer.py path/to/your/file.dts --output json --output-file custom_path.json
```

The exported JSON contains the complete device tree structure including:
- Node names and hierarchies
- Properties and their values
- Labels associated with nodes

## Example

For a DTS file like:

```
/ {
    model = "Example Device";
    
    cpus {
        #address-cells = <1>;
        #size-cells = <0>;
        
        cpu0: cpu@0 {
            compatible = "vendor,cpu";
            reg = <0>;
        };
    };
    
    memory@40000000 {
        device_type = "memory";
        reg = <0x40000000 0x10000000>;
    };
};
```

The visualization would show the hierarchical structure with properties and labels highlighted in different colors.

## Limitations

- Complex macros and conditional directives may not be fully supported
- Some specialized DTS features might require additional parsing logic

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests. 