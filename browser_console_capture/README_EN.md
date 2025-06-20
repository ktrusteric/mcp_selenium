# MCP Browser Console Capture Service

## Overview

MCP Browser Console Capture Service is a browser automation service based on the FastMCP framework, specifically designed for intelligent public sentiment analysis systems. This service provides comprehensive browser control, JavaScript execution, console log capture, and page interaction capabilities.

## Technology Stack

- **FastMCP**: MCP (Model Context Protocol) service framework
- **Selenium**: Browser automation tool
- **Chrome**: Primary supported browser
- **ChromeDriver**: Chrome browser driver
- **Python 3.10.12+**: Runtime environment

## Core Features

### 🌐 Browser Control
- Launch and manage Chrome/Firefox browser instances
- Page navigation and URL access
- Window size adjustment and management
- Multi-session support

### 📝 JavaScript Execution
- Execute custom JavaScript code in pages
- Retrieve execution results and return values
- Support for asynchronous script execution

### 📊 Console Log Capture
- Real-time capture of browser console logs
- Support for multiple log levels (INFO, WARNING, ERROR, DEBUG)
- Structured log data return
- Configurable log quantity limit (up to 10,000 entries)

### 🎯 Page Interaction
- Element clicking and text input
- Element waiting and condition checking
- Page screenshot functionality
- Cookie and page information retrieval

### 🔐 Authentication Mechanism
- Support for `test-token-eric` special authentication
- Default administrator privileges
- Complete operation log recording

## Environment Configuration Steps

### 1. System Requirements

```bash
# Ubuntu/Debian systems
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Install necessary system dependencies
sudo apt install -y wget unzip curl
```

### 2. Chrome Browser and ChromeDriver Installation

**Important:** This service requires Chrome browser at specific paths

### 3. ChromeDriver Installation

**Important:** ChromeDriver version must match Chrome version

Google Chrome for Testing 137.0.7151.119 
ChromeDriver 137.0.7151.119 (e0ac9d12dff5f2d33c935958b06bf1ded7f1c08c-refs/branch-heads/7151@{#2356})

Please download and install manually: JSON source URL
https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json

```bash
# Verify installation
/opt/chromedriver-linux64/chromedriver --version
/opt/chrome-linux64/chrome --version

# Configure corresponding paths in server.py
```

### 4. Python Environment Configuration

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install FastMCP (if not in requirements.txt)
pip install fastmcp
```

### 5. Configuration File Setup

Ensure the paths in `config.json` are configured correctly:

```json
{
  "mcpServers": {
    "browser-console-capture": {
      "command": "/home/cooper/IntelligentPublicSentimentSystem/mcp_services/browser_console_capture/server.py",
      "args": [],
      "env": {
        "PYTHONPATH": "/home/cooper/IntelligentPublicSentimentSystem"
      }
    }
  }
}
```

### 6. Permission Settings

```bash
# Ensure Chrome and ChromeDriver have execution permissions
sudo chmod +x /opt/chrome-linux64/chrome
sudo chmod +x /opt/chromedriver-linux64/chromedriver

# Create necessary directories
mkdir -p ./screenshots
mkdir -p ./logs
```

### 7. Environment Verification

```bash
# Test Chrome startup
/opt/chrome-linux64/chrome --version --no-sandbox

# Test ChromeDriver
/opt/chromedriver-linux64/chromedriver --version

# Test Python dependencies
python3 -c "import selenium; print('Selenium version:', selenium.__version__)"
python3 -c "import fastmcp; print('FastMCP imported successfully')"
```

## Starting the Service

```bash
IntelligentPublicSentimentSystem/mcp_services/browser_console_capture$ fastmcp run server.py:mcp
2025-06-20 03:02:09,006 - server_module - INFO - Log system initialization completed, configuration loaded
2025-06-20 03:02:09,010 - auth_utils - INFO - === Browser MCP Authentication Configuration ===
2025-06-20 03:02:09,010 - auth_utils - INFO - Default user: eric
2025-06-20 03:02:09,010 - auth_utils - INFO - Default role: admin
2025-06-20 03:02:09,010 - auth_utils - INFO - Special Token: test-token-eric
2025-06-20 03:02:09,011 - auth_utils - INFO - Browser MCP will automatically use eric user identity for authentication
2025-06-20 03:02:09,011 - auth_utils - INFO - ==========================
2025-06-20 03:02:09,011 - server_module - INFO - Initializing FastMCP server...
2025-06-20 03:02:09,016 - server_module - INFO - FastMCP server initialization completed
2025-06-20 03:02:09,017 - server_module - INFO - State dictionary initialization completed
```

## Usage Examples

### Basic Browser Operations

```python
# Start browser
start_browser(browser_type="chrome", headless=False)

# Navigate to page
navigate_to_url("https://example.com")

# Execute JavaScript
execute_javascript("console.log('Hello World'); return document.title;")

# Get console logs
get_console_logs(level="ALL", limit=100)
```

### Page Interaction

```python
# Click element
click_element("#submit-button", by="css")

# Input text
input_text("#search-input", "Search content", by="css")

# Wait for element
wait_for_element(".loading-complete", condition="visible")

# Take screenshot
take_screenshot("page_screenshot.png", full_page=True)
```

## Configuration Description

### Browser Configuration

- `chrome_binary_path`: Chrome browser executable file path
- `chromedriver_path`: ChromeDriver executable file path
- `headless`: Whether to run in headless mode
- `window_size`: Browser window size

### Log Configuration

- `log_level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `log_file`: Log file path
- `max_log_size`: Maximum log file size

### Performance Configuration

- `page_load_timeout`: Page load timeout
- `script_timeout`: Script execution timeout
- `implicit_wait`: Implicit wait time

### MCP Tool Functions

| Function Name | Description | Parameters |
|---------------|-------------|------------|
| `start_browser` | Start browser instance | `browser_type`, `headless`, `window_width`, `window_height` |
| `navigate_to_url` | Navigate to specified URL | `url`, `wait_for_load` |
| `execute_javascript` | Execute JavaScript code | `script`, `capture_console` |
| `get_console_logs` | Get console logs | `level`, `limit`, `clear_after_get` |
| `click_element` | Click page element | `selector`, `by`, `timeout` |
| `input_text` | Input text | `selector`, `text`, `by`, `clear_first` |
| `take_screenshot` | Take page screenshot | `filename`, `full_page`, `element_selector` |
| `close_browser` | Close browser instance | None |

## Security Considerations

1. **Production Environment Configuration**
   - Use headless mode, default is True
   - Restrict network access
   - Configure firewall rules

2. **Authentication Security**
   - `test-token-eric` 
   - Token required for certain scenarios

## Contributing Guidelines

1. Fork the project
2. Create a feature branch
3. Submit changes
4. Create a Pull Request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Contact Information

For questions or suggestions, please contact us through:

- Project Issues: [GitHub Issues]()
- Email: [Project Email]()
- Documentation: [Online Documentation]()