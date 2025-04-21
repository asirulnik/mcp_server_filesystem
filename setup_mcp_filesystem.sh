#!/bin/bash
# Setup script for MCP File System Server in /Users/andrewsirulnik/claude_mcp_servers

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log function
log() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
  exit 1
}

# Define paths
BASE_DIR="/Users/andrewsirulnik/claude_mcp_servers"
REPO_DIR="$BASE_DIR/mcp_server_filesystem"
BUG_LOG="$REPO_DIR/bug_collection.log"
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Check if Python 3.11+ is installed
check_python() {
  log "Checking Python version..."
  if command -v python3 >/dev/null 2>&1; then
    python_cmd="python3"
  elif command -v python >/dev/null 2>&1; then
    python_cmd="python"
  else
    error "Python is not installed. Please install Python 3.11 or higher."
  fi

  python_version=$($python_cmd --version | cut -d " " -f 2)
  log "Found Python $python_version"
  
  # Compare versions
  major=$(echo $python_version | cut -d. -f1)
  minor=$(echo $python_version | cut -d. -f2)
  
  if [ $major -lt 3 ] || ([ $major -eq 3 ] && [ $minor -lt 11 ]); then
    error "Python 3.11 or higher is required. Found $python_version."
  fi
}

# Clone the repository
clone_repo() {
  log "Cloning MCP File System Server repository..."
  mkdir -p "$BASE_DIR"
  
  if [ -d "$REPO_DIR/.git" ]; then
    warn "Repository already exists at $REPO_DIR. Updating instead of cloning."
    cd "$REPO_DIR"
    git pull
    if [ $? -ne 0 ]; then
      error "Failed to update repository."
    fi
  else
    if [ -d "$REPO_DIR" ]; then
      warn "Directory exists but is not a git repository. Removing and cloning fresh."
      rm -rf "$REPO_DIR"
    fi
    
    cd "$BASE_DIR"
    git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
    if [ $? -ne 0 ]; then
      error "Failed to clone repository."
    fi
  fi
  
  cd "$REPO_DIR"
}

# Create a virtual environment and install dependencies
setup_venv() {
  log "Setting up virtual environment..."
  cd "$REPO_DIR"
  $python_cmd -m venv venv
  
  source venv/bin/activate
  
  log "Installing dependencies..."
  pip install -e .
  if [ $? -ne 0 ]; then
    error "Failed to install dependencies."
  fi
  
  log "Installing development dependencies..."
  pip install -e ".[dev]"
  if [ $? -ne 0 ]; then
    warn "Failed to install development dependencies, but continuing anyway."
  fi
}

# Create the bug collection log file
create_bug_log() {
  log "Creating bug_collection.log file..."
  cat > "$BUG_LOG" << EOL
# Bug Collection Log

## Format
- Timestamp: [YYYY-MM-DD HH:MM:SS]
- Command: The command that was attempted
- Error: The error message received
- Insight: Any additional information that might help debug the issue

## Bugs
EOL
  log "bug_collection.log created successfully at $BUG_LOG."
}

# Create Claude Desktop configuration
setup_claude_config() {
  log "Setting up Claude Desktop configuration..."
  
  # Create config directory if it doesn't exist
  mkdir -p "$CLAUDE_CONFIG_DIR"
  
  # Get path to Python executable in venv
  python_exec="$REPO_DIR/venv/bin/python"
  
  # Create configuration file
  log "Creating configuration at: $CLAUDE_CONFIG_FILE"
  cat > "$CLAUDE_CONFIG_FILE" << EOL
{
  "mcpServers": {
    "filesystem": {
      "command": "$python_exec",
      "args": [
        "$REPO_DIR/src/main.py",
        "--project-dir",
        "$BASE_DIR",
        "--log-level",
        "INFO"
      ],
      "env": {
        "PYTHONPATH": "$REPO_DIR"
      },
      "disabled": false,
      "autoApprove": [
        "list_directory",
        "read_file"
      ]
    }
  }
}
EOL

  log "Claude Desktop configuration created successfully."
}

# Main execution
main() {
  log "Starting MCP File System Server setup in $BASE_DIR..."
  check_python
  clone_repo
  setup_venv
  create_bug_log
  setup_claude_config
  log "Setup completed successfully!"
  log "You can now restart the Claude Desktop app to use the MCP File System Server."
  log "The server is configured to use $BASE_DIR as the project directory."
}

# Execute main function
main
