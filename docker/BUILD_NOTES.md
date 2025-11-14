# Docker Build Notes

## Fixed Issues

### 1. MeteoIO DBO Plugin
**Issue**: IMIS data access requires the DBO (Database) plugin to be enabled in MeteoIO.

**Solution**: Added `-DPLUGIN_DBO=ON` to the MeteoIO cmake configuration:
```cmake
cmake .. \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DPLUGIN_DBO=ON
```

This enables MeteoIO to connect to the IMIS database for meteorological data retrieval.

### 2. Rasterio Build Failure
**Issue**: `rasterio` failed to build because it requires GDAL development headers and C++ compiler.

**Error**:
```
ERROR: Failed building wheel for rasterio
ERROR: Could not build wheels for rasterio, which is required to install pyproject.toml-based projects
```

**Solution**: Added build tools to the runtime image:
```dockerfile
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    build-essential \    # Added
    gcc \                # Added
    g++ \                # Added
    && rm -rf /var/lib/apt/lists/*
```

**Why**: `rasterio` is a Python wrapper around GDAL and needs to compile C extensions. It requires:
- GDAL headers (`libgdal-dev`)
- C/C++ compilers (`gcc`, `g++`, `build-essential`)

### 3. Pip Version Warning
**Solution**: Upgraded pip before installing packages:
```dockerfile
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
```

## Build Order

The Dockerfile uses a multi-stage build:

### Stage 1: Builder
1. Install build dependencies (cmake, git, compilers, GDAL dev)
2. Clone and build MeteoIO with DBO plugin
3. Clone and build Snowpack
4. Install binaries to `/usr/local/`

### Stage 2: Runtime
1. Install runtime dependencies + build tools (for Python packages)
2. Copy compiled binaries from builder stage
3. Upgrade pip
4. Install Python dependencies (including rasterio)
5. Copy application code
6. Set up GUI and volumes

## Build Command

```bash
cd docker
docker-compose build
```

Expected build time: **10-15 minutes** (first build)

## Verification

After build completes, verify installations:
```bash
docker-compose run --rm a3dshell snowpack --version
docker-compose run --rm a3dshell meteoio_timeseries --version
docker-compose run --rm a3dshell python -c "import rasterio; print('rasterio OK')"
```

## Image Size

- **Builder stage**: ~2.5 GB (discarded after build)
- **Final image**: ~1.5-1.8 GB (includes MeteoIO, Snowpack, Python deps, GUI)

## Troubleshooting

**Build fails at MeteoIO**:
- Check internet connection to `gitlabext.wsl.ch`
- Verify cmake version >= 3.10

**Build fails at Python packages**:
- Ensure GDAL version compatibility
- Check that build-essential is installed

**Snowpack binary not found**:
- Verify `/usr/local/bin/snowpack` was copied from builder
- Run `ldconfig` to update library cache

## Notes

- The DBO plugin requires network access to IMIS database servers
- Some IMIS servers are internal to SLF and may not be accessible externally
- For external use, pre-downloaded IMIS data or the `--skip-snowpack` flag may be needed
