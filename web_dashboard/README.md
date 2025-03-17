# EasyDT Web Dashboard

A web-based dashboard that provides a user-friendly interface to the EasyDT tools. Access and use the tools through a modern web interface without needing to use the command line.

## Features

- **Modern, Responsive Web Interface**: Designed with Bootstrap 5 for a clean, modern look that works on desktop and mobile devices.
- **DTS Visualizer**: Upload and visualize Device Tree Source files directly in your browser.
- **Interactive Tree View**: Explore device tree structures with an intuitive, collapsible tree view.
- **Export Functionality**: Export visualized data as JSON for further analysis or integration with other tools.
- **Easy-to-Use Interface**: Drag-and-drop file uploads and intuitive controls make it accessible to all users.

## Requirements

- Python 3.12+
- Flask 2.2.3+
- Waitress 2.1.2+ (for production deployment)
- Rich 10.0.0+ (for console output formatting)

## Installation

1. Clone the repository and navigate to the web dashboard directory:
   ```
   git clone https://github.com/HeyMeco/easydt.git
   cd easydt/web_dashboard
   ```

2. Create a virtual environment and install dependencies (or use the provided run script):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Usage

### Using the Run Script

The simplest way to start the dashboard is to use the provided run script:

```
./run.sh
```

This script will:
1. Create a virtual environment if it doesn't exist
2. Install the required dependencies
3. Start the web server
4. Provide a URL to access the dashboard (default: http://localhost:5000)

### Manual Start

If you prefer to start the server manually:

```
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

### Command Line Options

The application supports the following command line options:

- `--host`: Host to run the server on (default: 0.0.0.0)
- `--port`: Port to run the server on (default: 5000)
- `--debug`: Run in debug mode

Example:
```
python app.py --host 127.0.0.1 --port 8080 --debug
```

## Dashboard Pages

### Home Page

The home page provides an overview of the available tools and features in the EasyDT collection.

### DTS Visualizer

The DTS Visualizer page allows you to:

1. Upload a DTS file using drag-and-drop or file selection
2. Visualize the device tree structure
3. Explore nodes, properties, and labels in an interactive tree view
4. Export the parsed data as JSON
5. Expand or collapse all nodes in the tree

## Development

### Project Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates
  - `base.html`: Base template with common layout elements
  - `index.html`: Home page template
  - `visualizer.html`: DTS Visualizer template
- `static/`: Static assets
  - `css/`: CSS files
  - `js/`: JavaScript files

### Adding New Features

To add new tools or features to the dashboard:

1. Create new route handlers in `app.py`
2. Add template files in the `templates` directory
3. Update the navigation in `base.html`
4. Add necessary static assets in the `static` directory

## Production Deployment

For production deployment, the application uses Waitress as a WSGI server. The default configuration in the run script is suitable for basic deployments, but you may want to consider:

- Setting up a reverse proxy (Nginx, Apache) for SSL termination
- Adjusting Waitress settings for performance
- Using environment variables for configuration settings

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file in the root directory for details. 