# Implementation Status - A3DShell A3Dshell

## Overview

This document tracks the implementation status of the A3Dshell architecture.

## ✅ Completed Modules

### Core Infrastructure
- [x] Directory structure
- [x] `src/config.py` - Configuration management (.ini + CLI overrides)
- [x] `src/core/paths.py` - Path management
- [x] `src/data/cache.py` - Cache system for DEM tiles and maps
- [x] `src/geometry/roi.py` - ROI handling (bbox & shapefile)
- [x] `src/geometry/transforms.py` - Coordinate transformations
- [x] `src/data/api.py` - Swisstopo API client with caching
- [x] `src/utils/logging.py` - Logging utilities
- [x] `src/utils/helpers.py` - Common helpers
- [x] `src/cli.py` - CLI skeleton
- [x] `requirements.txt` - Dependencies
- [x] `README.md` - Documentation

## 🚧 Modules To Implement

The following modules need to be ported/created from the original codebase:

### 1. DEM Processing (`src/data/dem.py`)

**Priority: HIGH**

Port from `A3DShell_main.py` lines 616-721, 827-869

**Functions needed:**
```python
class DEMProcessor:
    def __init__(self, cache_manager, path_manager)
    def download_and_merge_tiles(self, roi, gsd_ref) -> Path
    def crop_to_roi(self, dem_file, roi) -> Path
    def reproject(self, dem_file, target_crs, gsd) -> Path
    def downsample(self, dem_file, target_gsd) -> Path
    def fill_nodata(self, dem_file) -> Path
```

**Source references:**
- `reprojectRaster()` - lines 616-650
- `downsampleRaster()` - lines 687-721
- `cropRaster()` - lines 723-751
- `mergeRaster()` - lines 828-869

### 2. LUS Processing (`src/data/lus.py`)

**Priority: HIGH**

Port from `A3DShell_main.py` lines 753-812

**Functions needed:**
```python
class LUSProcessor:
    def __init__(self, path_manager)
    def create_from_tlm(self, tlm_shp_path, dem_file, roi) -> Path
    def create_from_constant(self, dem_file, roi, lus_const) -> Path
    def get_unique_values(self, lus_file) -> List[int]
```

**Source references:**
- `LUSfromDEM()` - lines 753-812
- `getGridUnique()` - lines 814-826

**TLM to PREVAH mapping** (line 768-770):
```python
TLMregio_PrevahID = {
    "Wald": 3, "Fels": 15, "Geroell": 21, "Gletscher": 14,
    "See": 1, "Stausee": 1, "Siedl": 2, "Stadtzentr": 2,
    "Sumpf": 22, "Obstanlage": 18, "Reben": 29
}
```

### 3. IMIS Station Selection (`src/data/imis.py`)

**Priority: MEDIUM**

Port from `A3DShell_main.py` lines 976-1030

**Functions needed:**
```python
class IMISManager:
    def __init__(self, imis_metadata_path)
    def get_stations_in_buffer(self, roi, buffer_size) -> GeoDataFrame
    def get_closest_stations(self, poi_x, poi_y, n=10) -> GeoDataFrame
```

**Source references:**
- `getImisInBboxbuffer()` - lines 999-1030
- `getClosestImis()` - lines 976-997

**Required files to copy:**
- `data/imisMeta/imisMeta_10y.txt`
- `data/imisMeta/imisMeta_daily.txt`
- `data/imisMeta/imisMeta_merged.shp` (and associated files)

### 4. Mesh Generation (`src/geometry/mesh.py`)

**Priority: MEDIUM**

Port from `A3DShell_main.py` lines 871-973

**Functions needed:**
```python
class MeshGenerator:
    def __init__(self)
    def create_from_dem(self, dem_file, output_fmt="vtu", georef=True) -> Path
    def create_pvp_mesh(self, pvp_file, dem_path, output_path) -> Path
```

**Source references:**
- `formMeshfromRaster()` - lines 871-910
- `formPVPMesh()` - lines 912-947
- `getMatRot3D()` - lines 949-973

**Dependencies:**
- Requires `futils` Fortran module from original code
- Requires `DEM.py` from original code (for PVP)
- Uses `meshio` and `pyvista`

### 5. Snowpack Preprocessing (`src/preprocessing/snowpack.py`)

**Priority: MEDIUM**

Port from `A3DShell_main.py` lines 1186-1271

**Functions needed:**
```python
class SnowpackPreprocessor:
    def __init__(self, path_manager, config)
    def create_ini_files(self, imis_stations) -> None
    def create_sno_files(self, imis_stations) -> None
    def run_snowpack(self) -> bool
    def copy_smet_files(self, source_dir, dest_dir) -> None
```

**Source references:**
- `spIniConfig()` - lines 1186-1210
- `spSnoRender()` - lines 1236-1261
- `spBuildCmd()` - lines 1263-1271
- `copySMET_sp2a3d()` - lines 129-153

**Required files to copy:**
- `data/iniFiles/spConfig.ini`
- `data/snoFiles/template.sno`
- `data/snoFiles/dictSno.pkl`

### 6. A3D Configuration (`src/preprocessing/a3d_config.py`)

**Priority: MEDIUM**

Port from `A3DShell_main.py` lines 1033-1183

**Functions needed:**
```python
class A3DConfigurator:
    def __init__(self, path_manager, config)
    def create_ini_file(self, imis_stations) -> None
    def create_sno_files(self, lus_file, imis_stations) -> None
```

**Source references:**
- `a3dIniConfig()` - lines 1034-1076
- `a3dSnoRender()` - lines 1108-1148

**Required files to copy:**
- `data/iniFiles/a3dConfig.ini`
- `data/iniFiles/a3dConfigComplex.ini`
- `data/snoFiles/template.sno`
- `data/snoFiles/template_complex.sno`
- `data/snoFiles/dictSno.pkl`
- `data/pv/template.pv`

### 7. Mapping & Visualization (`src/output/mapping.py`)

**Priority: LOW**

Port from `A3DShell_main.py` lines 174-362

**Functions needed:**
```python
class MappingGenerator:
    def __init__(self, path_manager, config)
    def create_context_maps(self, roi, dem_file, lus_file, imis_stations) -> None
    def plot_horizon(self, poi_x, poi_y, poi_z) -> None
    def plot_sun_path(self, poi, horizon_data) -> None
```

**Source references:**
- `mapping()` - lines 174-295
- `plotSunPath()` - lines 297-362

**Dependencies:**
- Requires `computeHorayzon.py` from original code
- Uses `matplotlib`, `pvlib`

**Required files to copy:**
- `data/mapping/` (if any static data)

### 8. Output Packaging (`src/output/packaging.py`)

**Priority: HIGH**

Port from `A3DShell_main.py` lines 94-172

**Functions needed:**
```python
class OutputPackager:
    def __init__(self, path_manager)
    def copy_static_files(self, use_groundeye) -> None
    def copy_ini_file(self, source_ini) -> None
    def zip_simulation(self, exclude_dirs=["tmp"]) -> Path
```

**Source references:**
- `copyStaticDir()` - lines 116-127
- `copyIniFile()` - lines 94-101
- `zipDir()` - lines 159-172

**Required files to copy:**
- `data/brdf-files/` (entire directory, if USE_GROUNDEYE=true)
- `data/pv/template.pv`
- `data/poi/poi.smet`

### 9. Main Simulation Orchestrator (`src/core/simulation.py`)

**Priority: HIGH**

Port from `A3DShell_main.py` lines 1309-1508 (realmain function)

**Functions needed:**
```python
class SimulationOrchestrator:
    def __init__(self, config, path_manager)
    def run(self) -> bool
    def _setup_directories(self)
    def _process_dem(self)
    def _process_lus(self)
    def _select_imis_stations(self)
    def _generate_mesh(self)
    def _create_mappings(self)
    def _configure_a3d(self)
    def _run_snowpack(self)
    def _package_output(self)
```

**Integration flow:**
1. Setup directories
2. Load ROI (bbox or shapefile)
3. Download/cache DEM tiles
4. Process DEM (merge, crop, reproject, downsample)
5. Download/cache SwissTLM data
6. Generate LUS from TLM or constant
7. Select IMIS stations in buffered ROI
8. Generate mesh from DEM
9. Generate context maps (optional)
10. Configure Snowpack
11. Run Snowpack preprocessing
12. Copy SMET files to A3D input
13. Configure A3D
14. Package and zip output

## 📋 Required Input Files to Copy

Create a script to copy necessary files from `data/` to `input/`:

```bash
# IMIS metadata
cp -r data/imisMeta input/

# Templates
mkdir -p input/templates
cp data/pv/template.pv input/templates/
cp data/poi/poi.smet input/templates/
cp data/snoFiles/*.sno input/templates/
cp data/snoFiles/dictSno.pkl input/templates/

# INI templates
cp data/iniFiles/*.ini input/templates/

# BRDF files (large, copy only if needed)
# cp -r data/brdf-files input/
```

## 🔧 External Dependencies

These files from the original codebase must remain accessible:

1. **`futils.py`** (or compiled Fortran module)
   - Used for DEM triangulation
   - Location: Original code root

2. **`DEM.py`**
   - Used for DEM queries in PVP mesh generation
   - Location: Original code root

3. **`computeHorayzon.py`**
   - Used for horizon calculations
   - Location: Original code root

**Solution**: Add original code directory to Python path or copy these files.

## 🧪 Testing Strategy

### Unit Tests
- Config parsing with various .ini formats
- ROI creation from bbox and shapefile
- Coordinate transformations
- Cache operations

### Integration Tests
- End-to-end simulation with bbox ROI
- End-to-end simulation with shapefile ROI
- Cache reuse across simulations
- CLI argument parsing and override

### Test Simulations
1. **Small test** (Gondo, 100m ROI, 10m GSD)
2. **Medium test** (Davos, 1000m ROI, 10m GSD)
3. **Shapefile test** (Custom ROI from shapefile)

## 📊 Implementation Priority

### Phase 1: Core Functionality (1-2 days)
1. ✅ Infrastructure (done)
2. DEM processing
3. LUS processing
4. Main simulation orchestrator
5. Output packaging

### Phase 2: Integration (1 day)
6. IMIS station selection
7. Snowpack preprocessing
8. A3D configuration
9. Copy required input files

### Phase 3: Advanced Features (1 day)
10. Mesh generation
11. Mapping & visualization
12. CLI completion
13. Testing

## 🚀 Quick Start for Continued Development

```bash
# 1. Implement DEM processor
#    Copy logic from A3DShell_main.py lines 616-869
#    Create: src/data/dem.py

# 2. Implement LUS processor
#    Copy logic from A3DShell_main.py lines 753-826
#    Create: src/data/lus.py

# 3. Implement simulation orchestrator
#    Copy logic from A3DShell_main.py lines 1309-1508
#    Create: src/core/simulation.py

# 4. Wire up CLI
#    Update src/cli.py main() to call orchestrator

# 5. Copy input files
bash copy_input_files.sh

# 6. Test
python -m src.cli --config ../a3dShell_iniFiles/test.ini
```

## 📝 Notes

- Keep the modular architecture
- Add comprehensive docstrings
- Use type hints
- Integrate caching where possible
- Add logging at key steps
- Handle errors gracefully
- Validate inputs early

## 🔗 Related Documents

- `README.md` - User documentation
- `requirements.txt` - Dependencies
- Original `A3DShell_main.py` - Source reference
