#!/bin/bash
# Ai-PDF-Translate Setup Script
# This script sets up the environment for the PDF translator

# Print colored text
print_color() {
  case $1 in
    "green") COLOR="\033[0;32m" ;;
    "red") COLOR="\033[0;31m" ;;
    "blue") COLOR="\033[0;34m" ;;
    "yellow") COLOR="\033[0;33m" ;;
    *) COLOR="\033[0m" ;;
  esac
  echo -e "${COLOR}$2\033[0m"
}

# Check if Python is installed
check_python() {
  if command -v python3 &>/dev/null; then
    print_color "green" "✓ Python 3 is installed"
    PYTHON_CMD="python3"
  elif command -v python &>/dev/null; then
    # Check Python version
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}' | cut -d '.' -f 1)
    if [ "$PYTHON_VERSION" -ge 3 ]; then
      print_color "green" "✓ Python 3 is installed"
      PYTHON_CMD="python"
    else
      print_color "red" "✗ Python 3 is required but Python $PYTHON_VERSION is installed"
      print_color "yellow" "Please install Python 3 and try again"
      exit 1
    fi
  else
    print_color "red" "✗ Python 3 is not installed"
    print_color "yellow" "Please install Python 3 and try again"
    exit 1
  fi
}

# Create virtual environment
create_venv() {
  print_color "blue" "Creating virtual environment..."
  $PYTHON_CMD -m venv venv
  if [ $? -ne 0 ]; then
    print_color "red" "✗ Failed to create virtual environment"
    print_color "yellow" "Try installing venv: $PYTHON_CMD -m pip install virtualenv"
    exit 1
  fi
  print_color "green" "✓ Virtual environment created"
}

# Activate virtual environment
activate_venv() {
  print_color "blue" "Activating virtual environment..."
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_color "green" "✓ Virtual environment activated"
  elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    print_color "green" "✓ Virtual environment activated"
  else
    print_color "red" "✗ Failed to activate virtual environment"
    exit 1
  fi
}

# Install dependencies
install_dependencies() {
  print_color "blue" "Installing dependencies..."
  pip install -r requirements.txt
  if [ $? -ne 0 ]; then
    print_color "red" "✗ Failed to install dependencies"
    exit 1
  fi
  print_color "green" "✓ Dependencies installed"
}

# Download Persian fonts
download_fonts() {
  print_color "blue" "Downloading Persian fonts..."
  python tools/download_fonts.py
  if [ $? -ne 0 ]; then
    print_color "red" "✗ Failed to download fonts"
    print_color "yellow" "You may need to download fonts manually"
  else
    print_color "green" "✓ Fonts downloaded"
  fi
}

# Create .env file if it doesn't exist
create_env_file() {
  if [ ! -f ".env" ]; then
    print_color "blue" "Creating .env file..."
    cp .env.example .env
    print_color "yellow" "⚠ Please edit .env file and add your Gemini API key"
  else
    print_color "green" "✓ .env file already exists"
  fi
}

# Create samples directory if it doesn't exist
create_samples_dir() {
  if [ ! -d "samples" ]; then
    print_color "blue" "Creating samples directory..."
    mkdir -p samples
    print_color "green" "✓ Samples directory created"
    print_color "yellow" "⚠ Please add some PDF files to the samples directory for testing"
  else
    print_color "green" "✓ Samples directory already exists"
  fi
}

# Main setup process
main() {
  print_color "blue" "=== Ai-PDF-Translate Setup ==="
  check_python
  create_venv
  activate_venv
  install_dependencies
  download_fonts
  create_env_file
  create_samples_dir
  
  print_color "blue" "=== Setup Complete ==="
  print_color "green" "You can now use the PDF translator!"
  print_color "yellow" "Don't forget to add your Gemini API key to the .env file"
  print_color "yellow" "Run 'python tools/test_api_key.py' to test your API key"
  print_color "yellow" "Run 'python example.py' to translate a sample PDF"
}

# Run the setup
main 