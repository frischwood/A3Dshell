#!/bin/bash
#
# Copy necessary input files from original data/ directory to A3Dshell/input/
#
# Usage: bash copy_input_files.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Copying input files for A3DShell A3Dshell${NC}"
echo "=================================================="

# Check we're in the right directory
if [ ! -d "src" ] || [ ! -d "input" ]; then
    echo "Error: Must be run from A3Dshell directory"
    exit 1
fi

# Base paths
ORIGINAL_DATA="../data"
INPUT_DIR="./input"

if [ ! -d "$ORIGINAL_DATA" ]; then
    echo "Error: Original data directory not found at $ORIGINAL_DATA"
    echo "Please adjust the ORIGINAL_DATA variable in this script"
    exit 1
fi

echo ""
echo -e "${GREEN}1. Copying IMIS metadata${NC}"
if [ -d "$ORIGINAL_DATA/imisMeta" ]; then
    cp -r "$ORIGINAL_DATA/imisMeta" "$INPUT_DIR/"
    echo "   ✓ IMIS metadata copied"
else
    echo "   ⚠ IMIS metadata directory not found"
fi

echo ""
echo -e "${GREEN}2. Copying template files${NC}"
mkdir -p "$INPUT_DIR/templates"

if [ -f "$ORIGINAL_DATA/pv/template.pv" ]; then
    cp "$ORIGINAL_DATA/pv/template.pv" "$INPUT_DIR/templates/"
    echo "   ✓ PV template copied"
fi

if [ -f "$ORIGINAL_DATA/poi/poi.smet" ]; then
    cp "$ORIGINAL_DATA/poi/poi.smet" "$INPUT_DIR/templates/"
    echo "   ✓ POI SMET template copied"
fi

if [ -d "$ORIGINAL_DATA/snoFiles" ]; then
    cp "$ORIGINAL_DATA/snoFiles/"*.sno "$INPUT_DIR/templates/" 2>/dev/null || true
    cp "$ORIGINAL_DATA/snoFiles/dictSno.pkl" "$INPUT_DIR/templates/" 2>/dev/null || true
    echo "   ✓ SNO templates copied"
fi

echo ""
echo -e "${GREEN}3. Copying INI templates${NC}"
if [ -d "$ORIGINAL_DATA/iniFiles" ]; then
    cp "$ORIGINAL_DATA/iniFiles/"*.ini "$INPUT_DIR/templates/" 2>/dev/null || true
    echo "   ✓ INI templates copied"
else
    echo "   ⚠ INI files directory not found"
fi

echo ""
echo -e "${GREEN}4. BRDF files${NC}"
if [ -d "$INPUT_DIR/brdf-files" ]; then
    echo "   ✓ BRDF files already present"
else
    echo "   ⚠ BRDF files not found - copying if available"
    if [ -d "$ORIGINAL_DATA/brdf-files" ]; then
        cp -r "$ORIGINAL_DATA/brdf-files" "$INPUT_DIR/"
        echo "   ✓ BRDF files copied"
    else
        echo "   Note: BRDF files only needed if USE_GROUNDEYE=true"
        echo "   To copy manually: cp -r $ORIGINAL_DATA/brdf-files $INPUT_DIR/"
    fi
fi

echo ""
echo -e "${GREEN}5. SwissTLM (will be downloaded on first run)${NC}"
echo "   TLM data will be downloaded and cached automatically"

echo ""
echo "=================================================="
echo -e "${BLUE}Input files copied successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Install dependencies: pip install -r requirements.txt"
echo "2. (Optional) Install/copy Snowpack binary to input/bin/ (see input/bin/README.md)"
echo "3. Run a test simulation: python -m src.cli --config config/example_quick_test.ini"
echo ""
