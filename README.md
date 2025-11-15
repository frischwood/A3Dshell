# A3DShell

A clean, user-friendly tool for setting up Alpine3D simulation environments.

## Overview

A3DShell automates the preparation of Alpine3D simulation inputs:
- Downloads and processes DEM data from Swisstopo
- Selects appropriate IMIS meteorological stations
- Prepares input meteo SMET files
- Packages everything into a ready-to-use Alpine3D simulation folder

**Key Features:**
- **Dual Interface**: Web GUI for easy use, CLI for power users
- **Docker Ready**: Pre-built images - no installation needed
- **Flexible ROI**: Bounding box or custom shapefile support
- **Smart Caching**: Avoid redundant downloads
- **INI Configuration**: Easy configuration file management
- **Auto Packaging**: Everything zipped and ready to go

## Installation

### Option 1: Docker - Pre-built Image (Recommended!)

#### First Time: Install Docker

If you don't have Docker installed:

**Windows & Mac:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify installation: `docker --version`

**Linux:**
```bash
# Quick install script (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
```

For other Linux distributions, see: https://docs.docker.com/engine/install/

#### Run A3DShell with Docker

**Recommended**: Clone the repository first to get the complete directory structure and example configurations:

```bash
# Clone the repository
git clone https://github.com/frischwood/A3Dshell.git
cd a3dshell

# Pull the latest Docker image
docker pull ghcr.io/frischwood/A3Dshell:latest

# Start the GUI
docker run --rm -p 8501:8501 \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest

# Then open browser to: http://localhost:8501
# (Note: Use localhost, NOT 0.0.0.0)
```

**Alternative**: If you don't want to clone the full repo, create the required directories manually:

```bash
# Create directory structure
mkdir -p a3dshell/{output,cache,config}
cd a3dshell

# Download example config (optional)
wget -P config/ https://raw.githubusercontent.com/frischwood/A3Dshell/main/config/example_quick_test.ini

# Download docker-compose file
wget https://raw.githubusercontent.com/frischwood/A3Dshell/main/docker/docker-compose.registry.yml

# Pull and run
docker pull ghcr.io/frischwood/A3Dshell:latest
docker-compose -f docker-compose.registry.yml up
```

**Important**: The Docker container needs these mounted directories:
- `output/` - Simulation results are written here
- `cache/` - Downloaded DEM/map tiles stored here (persistent)
- `config/` - Configuration files and shapefiles read from here

Without these mounts, outputs will be lost when the container stops!

**Run a simulation (CLI mode)**:
```bash
docker run --rm \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest \
  python -m src.cli --config config/example_quick_test.ini
```

### Option 2: Native Installation

For local development or if you prefer not to use Docker:

```bash
# Clone the repository
git clone https://github.com/frischwood/A3Dshell.git
cd A3Dshell

# Install Python dependencies
pip install -r requirements.txt
```

**Python Requirements:**
- Python 3.8+
- geopandas, rasterio, pyproj (geospatial processing)
- numpy, pandas, scipy (scientific computing)
- requests (API access)
- streamlit (for GUI)
- matplotlib (visualization)

#### MeteoIO and Snowpack Installation

A3DShell requires **MeteoIO** and **Snowpack** for meteorological data processing. These must be installed separately:

**What they're used for:**
- **MeteoIO**: Accesses IMIS meteorological stations through the DBO database
  - ⚠️ **Requires WSL/SLF VPN access** to connect to the database
  - Used to retrieve real-world meteorological data for your simulation area

- **Snowpack**: Converts IMIS reflected shortwave radiation measurements to incoming shortwave radiation
  - Runs preprocessing to generate A3D-ready input SMET files from IMIS data
  - Can be skipped if you have your own meteorological files (see Configuration below)

**Installation:**

See the detailed guide in `input/bin/README.md` for installation instructions, or install from source:

1. **Install MeteoIO:**
   ```bash
   # From source
   git clone https://gitlabext.wsl.ch/snow-models/meteoio.git
   cd meteoio
   mkdir build && cd build
   cmake ..
   make
   sudo make install
   ```

2. **Install Snowpack:**
   ```bash
   # From source
   git clone https://github.com/snowpack-model/snowpack.git
   cd snowpack
   mkdir build && cd build
   cmake ..
   make
   sudo make install
   ```

3. **Configure paths in A3DShell:**
   ```ini
   [A3D]
   SP_BIN_PATH = /usr/local/bin/snowpack  # Or wherever snowpack is installed
   ```

**Alternative: Skip Snowpack preprocessing**

If you have your own meteorological data files, you can skip the Snowpack preprocessing step:

```bash
# Via CLI
python -m src.cli --config config/my_simulation.ini --skip-snowpack

# In config file
[A3D]
SKIP_SNOWPACK = true
```

**Note:** Without MeteoIO/Snowpack, you'll need to provide your own SMET meteorological files in the appropriate format.

## Quick Start

### Using the Web GUI (Easiest)

**With Docker:**
```bash
docker pull ghcr.io/frischwood/A3Dshell:latest
docker run --rm -p 8501:8501 \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest
```

**Without Docker:**
```bash
streamlit run gui_app.py
# or
./run_gui.sh
```

Then open your browser to **http://localhost:8501**

#### GUI content:

1. **General Settings Tab**: Set simulation name, dates, coordinate system
2. **Location & ROI Tab**:
   - Define region using bounding box, existing shapefile, or **draw on interactive map**
   - Optionally specify point of interest
3. **Output Settings Tab**: Configure grid spacing, DEM resolution, land use
4. **Run Tab**: Review settings, save config, and run simulation

**Drawing ROI on Map:**
1. Select "Use custom shapefile for ROI"
2. Choose "🗺️ Draw on interactive map"
3. Use the rectangle tool (□) to draw your bounding box on the map
4. Click "💾 Save ROI" to export as shapefile
5. Shapefile automatically saved to `config/shapefiles/`

**Tips:**
- Load existing configs from sidebar dropdown
- Start with `example_quick_test.ini` for testing
- Save configurations before running
- Monitor logs in the output area
- Find results in `output/{simulation_name}/`

### Using the CLI

#### 1. Create a Configuration File

```bash
# Generate a template
python -m src.cli --create-template config/my_simulation.ini

# Or copy an example
cp config/example_basic.ini config/my_simulation.ini
```

Edit the configuration:

```ini
[GENERAL]
SIMULATION_NAME = davos_10m
START_DATE = 2023-10-01T00:00:00
END_DATE = 2023-10-31T23:59:59

[INPUT]
EAST_epsg2056 = 783500
NORTH_epsg2056 = 189500
altLV95 = 1560
USE_SHP_ROI = false
ROI = 1000
BUFFERSIZE = 10000

[OUTPUT]
OUT_COORDSYS = CH1903+
GSD = 10.0
GSD_ref = 2.0

[A3D]
USE_LUS_TLM = false
LUS_PREVAH_CST = 11500
```

#### 2. Run the Simulation Setup

```bash
# With Docker
docker run --rm \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest \
  python -m src.cli --config config/my_simulation.ini

# Without Docker
python -m src.cli --config config/my_simulation.ini
```

The tool will:
1. Download DEM tiles and national maps
2. Process and merge DEM data
3. Generate land use grids
4. Select IMIS stations
5. Run Snowpack preprocessing
6. Configure Alpine3D
7. Package everything into a zip file

#### 3. Find Your Output

```
output/
└── davos_10m/
    ├── input/              # All A3D input files
    │   ├── surface-grids/  # DEM, land use
    │   ├── meteo/          # SMET files
    │   ├── snowfiles/      # Snow configs
    │   └── brdf-files/     # BRDF data
    ├── output/             # Ready for A3D execution
    ├── mapping/            # Maps and ROI
    ├── io.ini              # A3D configuration
    └── ...

output/davos_10m.zip        # Complete package
```

## Usage Examples

### Web GUI Examples

**Quick Test:**
1. Open GUI: `http://localhost:8501`
2. Load config: Select `example_quick_test.ini` from sidebar
3. Click "Run Simulation" in the Run tab
4. Monitor progress in real-time

**Custom Simulation:**
1. Fill in General Settings (name, dates)
2. Set Location & ROI (coordinates, region size)
3. Configure Output Settings (resolution, land use)
4. Save configuration
5. Run simulation

### CLI Examples

**Basic Usage:**
```bash
python -m src.cli --config simulation.ini
```

**With Debug Logging:**
```bash
python -m src.cli --config simulation.ini --log-level DEBUG
```

**Override Config Parameters:**
```bash
python -m src.cli --config simulation.ini \
  --roi 2000 \
  --gsd 5 \
  --buffer-size 100000
```

**Pure CLI Mode (No Config File):**
```bash
python -m src.cli \
  --name test_10m \
  --poi-x 783500 --poi-y 189500 --poi-z 1560 \
  --roi 1000 \
  --gsd 10 \
  --start 2023-10-01T00:00:00 \
  --end 2023-10-31T23:59:59
```

**Using Shapefiles for ROI:**

In config file:
```ini
[INPUT]
USE_SHP_ROI = true
ROI_SHAPEFILE = /path/to/your/roi.shp
```

Via CLI:
```bash
python -m src.cli --config simulation.ini \
  --use-shp-roi \
  --roi-shapefile /path/to/roi.shp
```

**With Docker:**
```bash
# Run quick test
docker run --rm \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest \
  python -m src.cli --config config/example_quick_test.ini

# With shapefile (mount additional volume)
docker run --rm \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  -v /path/to/shapefiles:/app/shapefiles:ro \
  ghcr.io/frischwood/A3Dshell:latest \
  python -m src.cli --config config/my_simulation.ini \
    --roi-shapefile /app/shapefiles/roi.shp
```

## Configuration

### Required Parameters

**[GENERAL]**
- `SIMULATION_NAME`: Unique identifier (no spaces)
- `START_DATE`, `END_DATE`: Simulation period (ISO 8601 format)

**[INPUT]**
- `EAST_epsg2056`, `NORTH_epsg2056`, `altLV95`: Point of interest coordinates

### ROI Options

**Bounding Box Mode** (default):
```ini
USE_SHP_ROI = false
ROI = 1000  # Size in meters
```
Creates a square region around the POI.

**Shapefile Mode**:
```ini
USE_SHP_ROI = true
ROI_SHAPEFILE = /path/to/roi.shp
```
Uses custom shapefile geometry. Supports .shp files or .zip archives.

### Output Options

- `GSD`: Output grid spacing in meters (lower = higher resolution)
- `GSD_ref`: Reference DEM resolution (2.0 or 0.5 meters)
- `OUT_COORDSYS`: CH1903+ or CH1903 (recommended)
- `DEM_ADDFMTLIST`: Additional formats like "tif"
- `MESH_FMT`: Mesh format (vtu, vtk, stl)

### Land Use Options

**Use Constant Value**:
```ini
USE_LUS_TLM = false
LUS_PREVAH_CST = 11500
```
Assigns single land use type (format: 1LLCD where LL is PREVAH code).

**SwissTLMRegio Integration** (Future Feature):
```ini
USE_LUS_TLM = true  # Not yet implemented
```
Automatic download of Swiss topographic land use data - coming in future release.

<!-- ### Advanced Options

- `BUFFERSIZE`: Distance for IMIS station selection (meters)
- `PLOT_HORIZON`: Generate horizon plots
- `USE_GROUNDEYE`: Use BRDF model
- `DO_PVP_3D`: Generate PV panel meshes
- `SP_BIN_PATH`: Path to Snowpack binary -->

## Command-Line Reference

### Core Options
```
--config, -c PATH       Configuration file (.ini)
--name NAME             Simulation name
--start DATE            Start date (YYYY-MM-DDTHH:MM:SS)
--end DATE              End date (YYYY-MM-DDTHH:MM:SS)
```

### POI & ROI Options
```
--poi-x FLOAT           POI Easting (EPSG:2056)
--poi-y FLOAT           POI Northing (EPSG:2056)
--poi-z FLOAT           POI Altitude (LV95)
--use-shp-roi           Use shapefile for ROI
--roi-shapefile PATH    Path to ROI shapefile
--roi INT               ROI size in meters (bbox mode)
--buffer-size INT       Buffer for IMIS selection (m)
```

### Output Options
```
--gsd FLOAT             Grid spacing (m)
--gsd-ref FLOAT         Reference DEM resolution (m)
--coord-sys NAME        Output coordinate system
--mesh-fmt FMT          Mesh format (vtu, vtk, stl)
```

### Processing Options
```
--skip-snowpack         Skip Snowpack preprocessing
--no-horizon            Skip horizon plotting
```

### Utility Options
```
--log-level LEVEL       Logging level (DEBUG, INFO, WARNING, ERROR)
--log-file PATH         Log to file
--create-template PATH  Create template .ini and exit
--version               Show version and exit
```

## Caching

The tool automatically caches downloaded data:
- DEM tiles
- National maps
- Intermediate results

**Location:** `cache/` directory

**Benefits:**
- Much faster subsequent runs
- Reduced API calls to Swisstopo
- Shared data across simulations
- Automatic cache management

## Troubleshooting

### GUI Issues

**⚠️ Important: Always use `http://localhost:8501` not `http://0.0.0.0:8501`**

The address `0.0.0.0` is for server binding and cannot be accessed from a browser. Always use:
- `http://localhost:8501`
- or `http://127.0.0.1:8501`

**GUI won't start:**
```bash
pip install --upgrade streamlit
```

**Port already in use:**
```bash
streamlit run gui_app.py --server.port 8502
# or with Docker:
docker run -p 8502:8501 ... ghcr.io/frischwood/A3Dshell:latest
```

**Blank screen or GUI not loading:**
```bash
# Try rebuilding the Docker image
docker-compose build --no-cache
docker-compose up

# Or if using registry image, pull latest
docker-compose -f docker-compose.registry.yml pull
docker-compose -f docker-compose.registry.yml up

# Check browser console for errors (F12 in most browsers)
# Try accessing: http://localhost:8501/_stcore/health
```

<!-- **Can't find config files:**
- Ensure you're in the correct directory
- Configs should be in `config/` folder
- With Docker, make sure volumes are mounted correctly -->

### CLI Issues

**Import Errors:**
Run as a module from the project directory:
```bash
cd a3dshell
python -m src.cli --config simulation.ini
```

**Missing Dependencies:**
```bash
pip install -r requirements.txt

```
<!-- # or for conda:
 conda install -c conda-forge geopandas rasterio pyproj -->

<!-- ### Common Problems

**Shapefile Not Found:**
- Use absolute paths: `/full/path/to/roi.shp`
- Ensure all files present (.shp, .shx, .dbf, .prj)
- .zip archives are supported

**Snowpack Execution Failed:**
- Verify installation: `which snowpack`
- Specify full path: `SP_BIN_PATH = /usr/local/bin/snowpack`
- Or skip: `--skip-snowpack`

**DEM Download Issues:**
- Check internet connection
- Swisstopo may have rate limits
- Cache will prevent re-downloading

**Out of Memory:**
- Reduce ROI size
- Increase GSD (coarser resolution)
- Close other applications -->

### Docker-Specific Issues

**Docker image pull fails:**
```bash
# Make sure you're logged in for private images
docker login ghcr.io

# Or use specific version
docker pull ghcr.io/frischwood/A3Dshell:v1.0.0
```

**Volume mount issues on Windows:**
```bash
# Use absolute paths
docker run -v C:/Users/name/a3dshell/output:/app/a3dshell/output ...
```

**Permission issues:**
The container runs as user `a3duser` (UID 1000). If you have permission issues:
```bash
# On Linux/Mac, fix ownership
sudo chown -R 1000:1000 output/ cache/ config/
```

## Docker Details

### Available Images

Pull from GitHub Container Registry:
```bash
docker pull ghcr.io/frischwood/A3Dshell:latest    # Latest stable
docker pull ghcr.io/frischwood/A3Dshell:v1.0.0    # Specific version
docker pull ghcr.io/frischwood/A3Dshell:1.0       # Minor version
```

### What's Included

The Docker image contains:
- ✅ Python 3.11 with all dependencies
- ✅ GDAL and geospatial libraries
- ✅ MeteoIO and Snowpack (compiled from source)
- ✅ All input data (BRDF files, templates, IMIS metadata)
- ✅ GUI and CLI ready to use
- ✅ Complete environment (~1.2 GB)
- ✅ **Version tracking**: Each image includes BUILD_INFO.txt with exact MeteoIO/Snowpack commit hashes for reproducibility

### Version Information

To check which versions of MeteoIO and Snowpack are included in your Docker image:

```bash
# View build information
docker run --rm ghcr.io/frischwood/A3Dshell:v1.0.0 cat BUILD_INFO.txt

# Or via the GUI: Open http://localhost:8501 → Check sidebar "About" section
```

This ensures scientific reproducibility by tracking the exact source code versions used to build MeteoIO and Snowpack.

### Volume Mounts

Three directories should be mounted for persistence:
- `./output` → `/app/a3dshell/output` - Simulation results
- `./cache` → `/app/a3dshell/cache` - Downloaded data cache
- `./config` → `/app/a3dshell/config` - Configuration files

<!-- **Shapefile Storage:**

When using custom shapefiles for ROI definition, they **must be stored in a mounted volume**. The recommended approach:

1. **Store in `config/` directory** (already mounted):
   ```bash
   # Place your shapefiles here
   a3dshell/
   ├── config/
   │   ├── my_roi.shp
   │   ├── my_roi.shx
   │   ├── my_roi.dbf
   │   ├── my_roi.prj
   │   └── example_quick_test.ini
   ```

2. **Or create a dedicated `shapefiles/` directory**:
   ```bash
   # Create shapefiles directory
   mkdir -p shapefiles

   # Add volume mount to docker run command
   docker run --rm -p 8501:8501 \
     -v $(pwd)/output:/app/a3dshell/output \
     -v $(pwd)/cache:/app/a3dshell/cache \
     -v $(pwd)/config:/app/a3dshell/config \
     -v $(pwd)/shapefiles:/app/a3dshell/shapefiles:ro \
     ghcr.io/frischwood/A3Dshell:latest
   ```

3. **In the GUI**:
   - The shapefile browser will search the directory you specify (default: `config/`)
   - Only files in mounted volumes are accessible
   - Files outside mounted volumes cannot be read by the container

**Important**: Shapefiles consist of multiple files (`.shp`, `.shx`, `.dbf`, `.prj`). Make sure all components are in the same directory! -->

<!-- ### Docker Compose

Easier than plain docker commands:

**docker-compose.registry.yml** (uses pre-built image):
```bash
# Start GUI
docker-compose -f docker-compose.registry.yml up

# Run CLI
docker-compose -f docker-compose.registry.yml run --rm a3dshell \
  python -m src.cli --config config/example_quick_test.ini

# Stop
docker-compose -f docker-compose.registry.yml down
```

**docker-compose.yml** (builds locally):
```bash
cd docker/
docker-compose build
docker-compose up  # GUI
docker-compose run --rm a3dshell python -m src.cli --config ../config/example_quick_test.ini
``` -->

## Directory Structure

```
a3dshell/
├── input/                  # Shared input data
│   ├── brdf-files/        # BRDF data
│   ├── templates/         # Config templates
│   ├── imis/              # IMIS metadata
│   ├── tlm/               # SwissTLMRegio
│   └── bin/               # Binaries (snowpack, meteoio)
├── output/                 # Simulation outputs
│   └── {name}/            # Per-simulation folders
├── cache/                  # Download cache
│   ├── dem_tiles/         # Cached DEM tiles
│   └── maps/              # Cached maps
├── config/                 # Configuration files
│   ├── example_basic.ini
│   ├── example_shapefile.ini
│   ├── example_high_resolution.ini
│   └── example_quick_test.ini
├── src/                    # Source code
│   ├── cli.py             # CLI entry point
│   ├── config.py          # Configuration
│   ├── core/              # Core modules
│   ├── data/              # Data processing
│   ├── geometry/          # Geometry operations
│   ├── preprocessing/     # Snowpack & A3D config
│   └── utils/             # Utilities
├── docker/                 # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.registry.yml
│   └── DOCKER.md          # Maintainer docs
├── gui_app.py             # Streamlit GUI
├── run_gui.sh             # GUI launcher
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

<!-- ## Example Workflows

### Workflow 1: Quick Test with GUI

```bash
# Pull and start
docker pull ghcr.io/frischwood/A3Dshell:latest
docker run -p 8501:8501 -v $(pwd)/output:/app/a3dshell/output ghcr.io/frischwood/A3Dshell:latest

# In browser (localhost:8501):
# 1. Load example_quick_test.ini
# 2. Click "Run Simulation"
# 3. Wait ~2-5 minutes
# 4. Check output/ folder
```

### Workflow 2: Production Run with CLI

```bash
# Create config
python -m src.cli --create-template config/production.ini

# Edit config file with your parameters

# Run simulation
docker run --rm \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest \
  python -m src.cli --config config/production.ini --log-level DEBUG

# Results in output/production/
```

### Workflow 3: Custom Shapefile ROI

```bash
# Prepare shapefile in local directory: ./shapefiles/my_roi.shp

# Run with shapefile
docker run --rm \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  -v $(pwd)/shapefiles:/app/shapefiles:ro \
  ghcr.io/frischwood/A3Dshell:latest \
  python -m src.cli \
    --name custom_region \
    --poi-x 783500 --poi-y 189500 --poi-z 1560 \
    --use-shp-roi \
    --roi-shapefile /app/shapefiles/my_roi.shp \
    --gsd 5 \
    --start 2023-10-01T00:00:00 \
    --end 2023-10-31T23:59:59
``` -->

<!-- ## Additional Resources

- **Example Configs**: See `config/` directory
- **Binary Installation**: See `input/bin/README.md`
- **Docker Maintainer Docs**: See `docker/DOCKER.md`
- **Quick Start Guide**: See `QUICKSTART.md`
- **Implementation Details**: See `COMPLETION_SUMMARY.md` -->

## Future Development

The following features are planned for future releases:

### SwissTLMRegio Land Use Integration
Automatic download and processing of Swiss topographic land use data:
- Seamless integration with Swisstopo API
- Automatic conversion to PREVAH land use codes
- Support for custom mapping tables
- **Status**: Planned
- **Current workaround**: Use constant land use value (`USE_LUS_TLM = false`)

### Additional Planned Features
- Support for additional DEM sources beyond Swisstopo
- Integration with additional meteorological data sources

Contributions and feature requests are welcome!

## Support & Contributing

For issues, questions, or contributions, please visit the project repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
