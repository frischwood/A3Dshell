#!/bin/bash
#
# Docker Quick Start Script for A3DShell A3Dshell
#
# This script provides convenient shortcuts for common Docker operations

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}A3DShell A3Dshell - Docker Quick Start${NC}"
echo "================================================"
echo ""

# Function to show usage
show_help() {
    echo "Usage: ./docker/docker-quickstart.sh [command]"
    echo "   or: cd docker && ./docker-quickstart.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build          - Build the Docker image"
    echo "  test           - Run quick test simulation"
    echo "  basic          - Run basic example simulation"
    echo "  shapefile      - Run shapefile example"
    echo "  highres        - Run high-resolution example"
    echo "  shell          - Open interactive shell in container"
    echo "  clean          - Clean up output and cache"
    echo "  help           - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docker/docker-quickstart.sh build"
    echo "  ./docker/docker-quickstart.sh test"
    echo "  cd docker && ./docker-quickstart.sh shell"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: docker-compose not found${NC}"
    echo "Please install Docker Desktop or docker-compose"
    exit 1
fi

# Change to docker directory if not already there
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Parse command
case "${1:-help}" in
    build)
        echo -e "${GREEN}Building Docker image...${NC}"
        docker-compose build
        echo ""
        echo -e "${GREEN}✓ Build complete!${NC}"
        echo "Run './docker/docker-quickstart.sh test' to test the setup"
        ;;

    test)
        echo -e "${GREEN}Running quick test simulation...${NC}"
        echo "Config: config/example_quick_test.ini"
        echo "Expected time: ~5 minutes"
        echo ""
        docker-compose run --rm a3dshell \
            python -m src.cli --config config/example_quick_test.ini
        echo ""
        echo -e "${GREEN}✓ Test complete!${NC}"
        echo "Check ../output/quick_test_20m/ for results"
        ;;

    basic)
        echo -e "${GREEN}Running basic simulation...${NC}"
        echo "Config: config/example_basic.ini"
        echo "Expected time: ~15-30 minutes"
        echo ""
        docker-compose run --rm a3dshell \
            python -m src.cli --config config/example_basic.ini
        echo ""
        echo -e "${GREEN}✓ Simulation complete!${NC}"
        echo "Check ../output/ for results"
        ;;

    shapefile)
        echo -e "${GREEN}Running shapefile example...${NC}"
        echo "Config: config/example_shapefile.ini"
        echo ""
        echo -e "${YELLOW}Note: Update ROI_SHAPEFILE path in config first!${NC}"
        echo ""
        docker-compose run --rm a3dshell \
            python -m src.cli --config config/example_shapefile.ini
        ;;

    highres)
        echo -e "${GREEN}Running high-resolution simulation...${NC}"
        echo "Config: config/example_high_resolution.ini"
        echo "Expected time: ~30-60 minutes"
        echo ""
        docker-compose run --rm a3dshell \
            python -m src.cli --config config/example_high_resolution.ini
        ;;

    shell)
        echo -e "${GREEN}Opening interactive shell...${NC}"
        echo "Type 'exit' to leave the container"
        echo ""
        docker-compose run --rm a3dshell /bin/bash
        ;;

    clean)
        echo -e "${YELLOW}Cleaning output and cache...${NC}"
        read -p "This will remove all simulation results and cached data. Continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf ../output/*/
            rm -rf ../cache/dem_tiles/*
            rm -rf ../cache/maps/*
            echo -e "${GREEN}✓ Cleaned!${NC}"
        else
            echo "Cancelled"
        fi
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
