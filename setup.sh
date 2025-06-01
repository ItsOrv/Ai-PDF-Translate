#!/bin/bash
# Setup script for Persian PDF Translator

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Persian PDF Translator Setup =====${NC}"
echo "This script will set up the environment for the Persian PDF Translator."

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}Found Python $python_version${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Download Persian fonts
echo -e "\n${YELLOW}Downloading Persian fonts...${NC}"
python download_fonts.py

# Create .env file for API key
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file for API key...${NC}"
    echo "GEMINI_API_KEY=" > .env
    echo -e "${RED}Please edit the .env file and add your Gemini API key.${NC}"
    echo -e "You can get a Gemini API key from: ${GREEN}https://aistudio.google.com/app/apikey${NC}"
else
    echo -e "\n${YELLOW}Found existing .env file.${NC}"
fi

# Test the API key if it exists
if grep -q "GEMINI_API_KEY=" .env && ! grep -q "GEMINI_API_KEY=$" .env; then
    echo -e "\n${YELLOW}Testing API key...${NC}"
    python test_api_key.py
else
    echo -e "\n${YELLOW}No API key found in .env file.${NC}"
    echo -e "Please add your Gemini API key to the .env file."
    echo -e "Format: ${GREEN}GEMINI_API_KEY=your_api_key_here${NC}"
fi

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "To use the translator, run: ${GREEN}python main.py --input your_file.pdf --output translated.pdf${NC}"
echo -e "For more options, run: ${GREEN}python main.py --help${NC}"
echo
echo -e "${YELLOW}Don't forget to activate the virtual environment before running:${NC}"
echo -e "${GREEN}source venv/bin/activate${NC}" 