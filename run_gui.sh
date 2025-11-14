#!/bin/bash
#
# Launch A3DShell GUI (Streamlit)
#

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting A3DShell GUI...${NC}"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found. Installing..."
    pip install streamlit
fi

# Launch GUI
echo -e "${GREEN}Opening browser at http://localhost:8501${NC}"
echo ""
streamlit run gui_app.py
