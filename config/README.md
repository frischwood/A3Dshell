# Configuration Files

This directory contains example configuration files for A3DShell A3Dshell.

## Available Examples

### `example_basic.ini`
Standard configuration using bounding box ROI.
- 10m resolution
- 1000m x 1000m area
- One month simulation
- Good starting point for most simulations

**Use case:** General purpose simulation

### `example_shapefile.ini`
Configuration using custom shapefile for ROI.
- Direct shapefile path specification
- Useful for complex study areas
- Shows how to use .shp or .zip files

**Use case:** Custom study areas with irregular boundaries

### `example_high_resolution.ini`
High-resolution configuration.
- 5m resolution output
- 0.5m reference DEM
- Detailed land use from SwissTLMRegio
- Longer processing time

**Use case:** Detailed terrain analysis, small areas

### `example_quick_test.ini`
Fast testing configuration.
- 20m coarse resolution
- 500m x 500m small area
- 2-day period
- Constant land use (no TLM download)

**Use case:** Testing the pipeline, quick validation

## Creating Your Own Configuration

### Method 1: Copy and Modify

```bash
cp config/example_basic.ini config/my_simulation.ini
# Edit my_simulation.ini
python -m src.cli --config config/my_simulation.ini
```

### Method 2: Generate Template

```bash
python -m src.cli --create-template config/my_simulation.ini
# Edit my_simulation.ini
python -m src.cli --config config/my_simulation.ini
```

## Configuration Parameters

### Required Parameters

**[GENERAL]**
- `SIMULATION_NAME`: Unique identifier (no spaces)
- `START_DATE`, `END_DATE`: ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

**[INPUT]**
- `EAST_epsg2056`, `NORTH_epsg2056`: CH1903+ coordinates
- `altLV95`: Altitude in meters
- Either `ROI` (for bbox) or `ROI_SHAPEFILE` (for shapefile)

### Important Parameters

**Resolution:**
- `GSD`: Output grid spacing (5-20m typical)
- `GSD_ref`: Reference DEM resolution (0.5 or 2.0)

**ROI Mode:**
- Bounding box: `USE_SHP_ROI = false`, set `ROI` in meters
- Shapefile: `USE_SHP_ROI = true`, set `ROI_SHAPEFILE` path

**Land Use:**
- `USE_LUS_TLM = true`: Use SwissTLMRegio (automatic download)
- `USE_LUS_TLM = false`: Use constant value `LUS_PREVAH_CST`

**Station Selection:**
- `BUFFERSIZE`: Search radius for IMIS stations (50000-100000m typical)

**Binaries:**
- `SP_BIN_PATH`: Path to Snowpack binary

## Coordinate Systems

The tool works with Swiss coordinate systems:

- **Input**: EPSG:2056 (CH1903+ / LV95) - required
- **Output**: CH1903+ or CH1903 (configurable)
- WGS84 and CHTRS95 are not recommended

Use [map.geo.admin.ch](https://map.geo.admin.ch) to find coordinates in EPSG:2056.

## Tips

### Performance
- Start with coarse resolution (`GSD = 20`) for testing
- Use smaller ROI (`ROI = 500`) initially
- Short time period (few days) for validation

### Resolution Guidelines
- **20m**: Fast, good for large areas (>10km²)
- **10m**: Standard, balanced performance
- **5m**: Detailed, slower, use for small areas
- **2m**: Very detailed, very slow, small areas only

### ROI Size Guidelines
- **500m**: Very fast, testing only
- **1000m**: Fast, small catchment
- **5000m**: Medium, typical catchment
- **10000m+**: Large, longer processing time

### Time Period
- **Few days**: Testing and validation
- **1 month**: Standard simulation
- **Full season**: Production runs

## Common Use Cases

### Test the Setup
```bash
python -m src.cli --config config/example_quick_test.ini
```

### Standard Simulation
```bash
python -m src.cli --config config/example_basic.ini
```

### Custom Area
```bash
cp config/example_shapefile.ini config/my_area.ini
# Edit ROI_SHAPEFILE path
python -m src.cli --config config/my_area.ini
```

### High Detail
```bash
python -m src.cli --config config/example_high_resolution.ini
```

## Storing Your Configs

It's recommended to keep your configuration files in this directory for easy access:

```
config/
├── example_basic.ini           # Provided examples
├── example_shapefile.ini
├── example_high_resolution.ini
├── example_quick_test.ini
├── my_project_a.ini           # Your configurations
├── my_project_b.ini
└── production_run.ini
```

## Next Steps

1. Choose an example that matches your needs
2. Copy it to a new file
3. Edit coordinates, dates, and parameters
4. Run: `python -m src.cli --config config/your_file.ini`
5. Find output in `output/{SIMULATION_NAME}/`

For more details, see the main README.md.
