# Setup Complete - A3DShell A3Dshell

## ✅ All Components Ready

Your A3DShell A3Dshell installation is now complete with all necessary components!

## 📁 Directory Structure

```
A3Dshell/
├── config/                          # Configuration files ✓
│   ├── example_basic.ini           # Standard simulation
│   ├── example_quick_test.ini      # Fast testing
│   ├── example_shapefile.ini       # Shapefile ROI
│   ├── example_high_resolution.ini # High-res (5m)
│   └── README.md                   # Config guide
│
├── input/                           # Input data ✓
│   ├── brdf-files/                 # BRDF data (80+ files)
│   ├── templates/                  # Templates (sno, pv, ini, poi.smet)
│   ├── imis/                       # IMIS metadata
│   ├── tlm/                        # SwissTLM (auto-downloaded)
│   └── bin/                        # For binaries (see README)
│       └── README.md               # Binary installation guide
│
├── output/                          # Simulation outputs (empty)
├── cache/                           # Download cache (empty)
│   ├── dem_tiles/
│   ├── maps/
│   └── metadata.json
│
└── src/                             # Source code (16 modules) ✓
    ├── cli.py
    ├── config.py
    └── [all modules implemented]
```

## 🎯 What's Included

### ✅ BRDF Files
- **Location:** `input/brdf-files/`
- **Status:** ✓ Copied and ready
- **Usage:** Set `USE_GROUNDEYE = true` in config
- **Count:** 80+ weighted files for different angles

### ✅ Configuration Examples
- **Location:** `config/`
- **Count:** 4 example configurations
- **Types:**
  - Basic (standard simulation)
  - Quick test (fast validation)
  - Shapefile (custom ROI)
  - High-resolution (detailed)

### ✅ Input Templates
- **Location:** `input/templates/`
- **Includes:**
  - `.sno` files (snow configuration templates)
  - `.pv` template (PV panels)
  - `.ini` templates (Snowpack, A3D configs)
  - `poi.smet` (point of interest template)
  - `dictSno.pkl` (snow parameters dictionary)

### ✅ IMIS Metadata
- **Location:** `input/imis/` (symlink to `input/imisMeta/`)
- **Includes:**
  - Station metadata files
  - Shapefiles
  - 10-year and daily data indices

### 📦 Binary Directory
- **Location:** `input/bin/`
- **Status:** Empty (ready for binaries)
- **See:** `input/bin/README.md` for installation instructions

**To add Snowpack binary:**
1. Install system-wide: `snowpack` (recommended)
2. Or copy to `input/bin/snowpack`
3. Or specify path in config: `SP_BIN_PATH = /path/to/snowpack`

## 🚀 Quick Start

### 1. Test the Setup

```bash
# Quick test (2 days, 500m ROI, coarse resolution)
python -m src.cli --config config/example_quick_test.ini
```

**Expected runtime:** ~5 minutes (with downloads)
**Output:** `output/quick_test_20m/` and `.zip`

### 2. Standard Simulation

```bash
# Full month, 1km ROI, standard resolution
python -m src.cli --config config/example_basic.ini
```

**Expected runtime:** ~15-30 minutes
**Output:** `output/example_10m/` and `.zip`

### 3. Your Own Simulation

```bash
# Copy and customize
cp config/example_basic.ini config/my_area.ini
# Edit coordinates, dates, parameters
python -m src.cli --config config/my_area.ini
```

## 📋 Pre-flight Checklist

Before running your first simulation:

- [x] Input files copied (`bash copy_input_files.sh`)
- [x] Dependencies installed (`pip install -r requirements.txt`)
- [x] BRDF files present (`input/brdf-files/`)
- [x] Templates copied (`input/templates/`)
- [x] IMIS metadata copied (`input/imis/`)
- [x] Configuration examples available (`config/`)
- [ ] Snowpack binary installed/configured (optional, see `input/bin/README.md`)

## 🔧 Optional: Snowpack Binary

Snowpack is **optional** but recommended for full functionality.

### Option A: System Installation (Recommended)
```bash
# macOS with Homebrew
brew install snowpack

# From source
git clone https://github.com/snowpack-model/snowpack.git
cd snowpack && mkdir build && cd build
cmake .. && make
```

### Option B: Skip Snowpack
```bash
python -m src.cli --config config/example_basic.ini --skip-snowpack
```

**Note:** Without Snowpack, SMET files won't be generated. You'll need to provide them separately for Alpine3D.

## 🗂️ Configuration Files Explained

### `config/example_basic.ini`
- **Purpose:** Standard general-purpose simulation
- **ROI:** 1000m bounding box
- **Resolution:** 10m GSD
- **Period:** 1 month
- **Use for:** Most simulations

### `config/example_quick_test.ini`
- **Purpose:** Fast testing and validation
- **ROI:** 500m bounding box
- **Resolution:** 20m GSD (coarse)
- **Period:** 2 days
- **Use for:** Testing setup, quick validation

### `config/example_shapefile.ini`
- **Purpose:** Custom ROI from shapefile
- **ROI:** From shapefile (must edit path!)
- **Resolution:** 10m GSD
- **Period:** 1 month
- **Use for:** Complex study areas

### `config/example_high_resolution.ini`
- **Purpose:** High-detail simulations
- **ROI:** 1000m bounding box
- **Resolution:** 5m GSD, 0.5m reference DEM
- **Period:** 1 week
- **Use for:** Small areas needing detail

## 🎓 Learning Path

1. **Start:** Run `config/example_quick_test.ini` (5 min)
2. **Understand:** Check output structure in `output/quick_test_20m/`
3. **Customize:** Copy and edit a config file
4. **Experiment:** Try different ROI sizes and resolutions
5. **Production:** Run full simulations with your data

## 📚 Documentation

- **README.md** - Complete user guide
- **QUICKSTART.md** - 5-minute start guide
- **config/README.md** - Configuration reference
- **input/bin/README.md** - Binary installation
- **COMPLETION_SUMMARY.md** - Technical details

## ⚡ Performance Tips

1. **Start small:** Use `example_quick_test.ini` first
2. **Use caching:** Second run ~10x faster
3. **Coarse first:** Test with GSD=20, then refine
4. **Monitor logs:** Use `--log-level DEBUG` to see progress
5. **Check coordinates:** Use [map.geo.admin.ch](https://map.geo.admin.ch)

## 🆘 Common Issues

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Snowpack not found"
```bash
# Skip for now
python -m src.cli --config config/example_basic.ini --skip-snowpack

# Or install (see input/bin/README.md)
```

### "Shapefile not found"
Edit `config/example_shapefile.ini` and set correct path:
```ini
ROI_SHAPEFILE = /full/path/to/your/roi.shp
```

## ✨ You're Ready!

Everything is set up and ready to go. Run your first simulation:

```bash
python -m src.cli --config config/example_quick_test.ini
```

Expected output:
```
================================================================
A3DShell Simulation: quick_test_20m
================================================================
Phase 1: Setup
Phase 2: ROI & Data
Phase 3: DEM Processing
Phase 4: LUS Processing
Phase 5: IMIS Station Selection
Phase 6: Snowpack Preprocessing
Phase 7: A3D Configuration
Phase 8: Output Packaging
================================================================
✓ Simulation setup complete!
Output: output/quick_test_20m
================================================================
```

Happy simulating! 🏔️❄️

---

**Next:** See README.md for complete documentation and advanced features.
