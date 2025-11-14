# Quick Start Guide - A3DShell A3Dshell

Get up and running with A3DShell in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Internet connection (for downloading DEM data)

## Installation

```bash
# 1. Navigate to A3Dshell directory
cd A3Dshell

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Copy required input files
bash copy_input_files.sh
```

That's it! You're ready to run simulations.

## Your First Simulation

### Step 1: Create Configuration

Use one of the provided examples as a starting point:

```bash
# For a standard simulation
cp config/example_basic.ini config/my_first_simulation.ini

# Or for a quick test
cp config/example_quick_test.ini config/my_first_simulation.ini
```

Open `config/my_first_simulation.ini` and adjust these key parameters:

```ini
[GENERAL]
SIMULATION_NAME = my_first_sim    # Your simulation name (no spaces!)
START_DATE = 2023-10-01T00:00:00  # Start date
END_DATE = 2023-10-07T23:59:59    # End date (1 week for testing)

[INPUT]
EAST_epsg2056 = 783500    # Your POI easting (EPSG:2056)
NORTH_epsg2056 = 189500   # Your POI northing (EPSG:2056)
altLV95 = 1560            # Your POI altitude
ROI = 500                 # Small ROI for quick testing (meters)
```

### Step 2: Run!

```bash
python -m src.cli --config config/my_first_simulation.ini
```

The tool will:
1. Download DEM data from Swisstopo
2. Process terrain data
3. Generate land use grids
4. Select meteorological stations
5. Configure Alpine3D
6. Package everything

### Step 3: Check Output

Your simulation folder is ready:

```bash
ls output/my_first_sim/
```

You'll find:
- `input/` - All A3D input files
- `io.ini` - Alpine3D configuration
- `SIMULATION_SUMMARY.txt` - What was created

Plus a complete zip package:
```bash
ls output/my_first_sim.zip
```

## Common Scenarios

### Scenario 1: Quick Test with Bounding Box

Test the tool with a small area:

```bash
python -m src.cli \
  --name quick_test \
  --poi-x 645000 --poi-y 115000 --poi-z 1500 \
  --roi 500 \
  --gsd 10 \
  --start 2023-10-01T00:00:00 \
  --end 2023-10-03T23:59:59
```

**Runtime:** ~5 minutes
**Output size:** ~50 MB

### Scenario 2: Use Your Own Shapefile

Have a custom study area?

```bash
python -m src.cli --config my_simulation.ini \
  --use-shp-roi \
  --roi-shapefile /path/to/my_study_area.shp
```

Or in your `.ini` file:
```ini
[INPUT]
USE_SHP_ROI = true
ROI_SHAPEFILE = /path/to/my_study_area.shp
```

### Scenario 3: High-Resolution DEM

Need finer resolution?

```bash
python -m src.cli --config my_simulation.ini \
  --gsd 2 \
  --gsd-ref 0.5
```

**Note:** Higher resolution = longer processing time and larger files

### Scenario 4: Larger Area, Longer Period

Production simulation:

```ini
[GENERAL]
SIMULATION_NAME = production_davos_oct2023
START_DATE = 2023-10-01T00:00:00
END_DATE = 2023-10-31T23:59:59

[INPUT]
EAST_epsg2056 = 783500
NORTH_epsg2056 = 189500
altLV95 = 1560
ROI = 5000              # 5km area
BUFFERSIZE = 100000     # Look farther for stations

[OUTPUT]
GSD = 10.0
```

**Runtime:** ~30-60 minutes
**Output size:** ~500 MB - 2 GB

## Understanding the Configuration

### Minimal Required Config

```ini
[GENERAL]
SIMULATION_NAME = test
START_DATE = 2023-10-01T00:00:00
END_DATE = 2023-10-31T23:59:59

[INPUT]
EAST_epsg2056 = 645000
NORTH_epsg2056 = 115000
altLV95 = 1500
ROI = 1000
```

Everything else has sensible defaults!

### Key Parameters Explained

**ROI (Region of Interest):**
- Bounding box mode: `ROI = 1000` creates 1000m × 1000m square
- Shapefile mode: Use your custom polygon

**GSD (Grid Spacing):**
- `GSD = 10` → 10m resolution (standard)
- `GSD = 5` → 5m resolution (finer)
- `GSD = 20` → 20m resolution (faster)

**GSD_ref (Reference DEM):**
- `GSD_ref = 2.0` → Standard SwissALTI3D (recommended)
- `GSD_ref = 0.5` → High-resolution SwissALTI3D (slower)

**BUFFERSIZE:**
- Distance to search for meteorological stations
- Larger = more stations to choose from
- Typical: 50000 (50km)

## CLI Shortcuts

### Override Config on the Fly

```bash
# Try different resolutions quickly
python -m src.cli --config base.ini --gsd 5
python -m src.cli --config base.ini --gsd 10
python -m src.cli --config base.ini --gsd 20

# Try different ROI sizes
python -m src.cli --config base.ini --roi 500
python -m src.cli --config base.ini --roi 1000
python -m src.cli --config base.ini --roi 5000
```

### Create Template

```bash
python -m src.cli --create-template config/new_config.ini
```

### Explore Available Examples

```bash
ls config/
# example_basic.ini - Standard simulation
# example_quick_test.ini - Fast testing
# example_shapefile.ini - Custom ROI shapefile
# example_high_resolution.ini - High detail (5m)
```

### Debug Mode

```bash
python -m src.cli --config my_simulation.ini --log-level DEBUG
```

## What Gets Created?

After running, you'll have:

```
output/my_simulation/
├── input/
│   ├── surface-grids/
│   │   ├── 10m_dem_my_simulation.asc    # Terrain model
│   │   ├── 10m_lus_my_simulation.lus    # Land use
│   │   └── my_simulation.pv              # Template
│   ├── meteo/
│   │   └── *.smet                        # Weather data
│   ├── snowfiles/
│   │   └── *.sno                         # Snow configs
│   └── brdf-files/                       # (if enabled)
├── output/                               # For A3D results
├── mapping/
│   └── roi.shp                           # Your ROI
├── io.ini                                # A3D config
└── SIMULATION_SUMMARY.txt                # Summary

# Plus:
output/my_simulation.zip                  # Complete package
```

## Caching Magic

The tool automatically caches downloaded data:

```
cache/
├── dem_tiles/     # DEM files from Swisstopo
├── maps/          # National maps
└── metadata.json  # Cache index
```

**Benefits:**
- Second run is ~10x faster!
- Shared across simulations
- Survives computer restart

## Tips for Success

### 1. Start Small
```bash
# Test with small area first
--roi 500 --gsd 20
```

### 2. Check Your Coordinates
Use [map.geo.admin.ch](https://map.geo.admin.ch) to find EPSG:2056 coordinates

### 3. Watch the Logs
```bash
# See what's happening
--log-level INFO

# See everything
--log-level DEBUG
```

### 4. Use the Cache
If something fails, just run again - cached data will speed up retry!

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Shapefile not found"
Use absolute paths:
```ini
ROI_SHAPEFILE = /full/path/to/roi.shp
```

### "Snowpack execution failed"
Skip Snowpack for testing:
```bash
python -m src.cli --config my_simulation.ini --skip-snowpack
```

### Need Help?
Check the full README:
```bash
cat README.md
```

## Next Steps

1. ✅ Run your first simulation
2. 📊 Try different resolutions (GSD)
3. 🗺️ Test with your own shapefile
4. 🚀 Run a production simulation
5. 🔬 Explore the output files

## Ready for Production?

See `README.md` for:
- Complete configuration reference
- All CLI options
- Advanced features
- Performance optimization
- Troubleshooting guide

Happy simulating! 🏔️❄️
