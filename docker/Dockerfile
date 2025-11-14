# A3DShell A3Dshell Docker Image
#
# This container builds MeteoIO and Snowpack from source and includes
# all dependencies and input data needed to run A3DShell

# ============================================================
# Stage 1: Builder - Build MeteoIO and Snowpack from source
# ============================================================
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Build MeteoIO from source
WORKDIR /tmp/build
RUN echo "Building MeteoIO from source..." && \
    git clone https://gitlabext.wsl.ch/snow-models/meteoio.git && \
    cd meteoio && \
    # Capture version info
    git log -1 --format="MeteoIO_Commit=%H%nMeteoIO_Date=%ci%nMeteoIO_Branch=%D" > /tmp/meteoio_version.txt && \
    git describe --tags --always >> /tmp/meteoio_version.txt 2>/dev/null || echo "MeteoIO_Tag=no-tag" >> /tmp/meteoio_version.txt && \
    mkdir build && \
    cd build && \
    cmake .. \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=ON \
        -DPLUGIN_DBO=ON && \
    make -j$(nproc) && \
    make install && \
    echo "MeteoIO build complete"

# Build Snowpack from source
WORKDIR /tmp/build
RUN echo "Building Snowpack from source..." && \
    git clone https://gitlabext.wsl.ch/snow-models/snowpack.git && \
    cd snowpack && \
    # Capture version info
    git log -1 --format="Snowpack_Commit=%H%nSnowpack_Date=%ci%nSnowpack_Branch=%D" > /tmp/snowpack_version.txt && \
    git describe --tags --always >> /tmp/snowpack_version.txt 2>/dev/null || echo "Snowpack_Tag=no-tag" >> /tmp/snowpack_version.txt && \
    mkdir build && \
    cd build && \
    cmake .. \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=ON && \
    make -j$(nproc) && \
    make install && \
    echo "Snowpack build complete"

# ============================================================
# Stage 2: Final image - Runtime environment
# ============================================================
FROM python:3.11-slim

# Build arguments for metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="A3DShell Contributors" \
      org.opencontainers.image.url="https://github.com/frischho/a3dshell" \
      org.opencontainers.image.source="https://github.com/frischho/a3dshell" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="A3DShell" \
      org.opencontainers.image.title="A3DShell" \
      org.opencontainers.image.description="Alpine 3D Simulation Helper - MeteoIO and Snowpack preprocessing for Alpine3D" \
      org.opencontainers.image.licenses="MIT"

# Install runtime dependencies + build tools for Python packages
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy built binaries and libraries from builder stage
COPY --from=builder /usr/local/bin/snowpack /usr/local/bin/
COPY --from=builder /usr/local/bin/meteoio_timeseries /usr/local/bin/
COPY --from=builder /usr/local/lib/libmeteoio.* /usr/local/lib/
COPY --from=builder /usr/local/lib/libsnowpack.* /usr/local/lib/
COPY --from=builder /usr/local/lib/libsnio.* /usr/local/lib/

# Copy version info from builder stage
COPY --from=builder /tmp/meteoio_version.txt /tmp/
COPY --from=builder /tmp/snowpack_version.txt /tmp/

# Update shared library cache
RUN ldconfig

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Create application directory
WORKDIR /app/a3dshell

# Copy requirements first (for better caching)
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY input/ ./input/
COPY config/ ./config/
COPY copy_input_files.sh .
COPY gui_app.py .
COPY run_gui.sh .
COPY README.md ./

# Create output and cache directories
RUN mkdir -p output cache/dem_tiles cache/maps logs

# Create BUILD_INFO.txt with version information
RUN echo "==================================================" > BUILD_INFO.txt && \
    echo "A3DShell Docker Image Build Information" >> BUILD_INFO.txt && \
    echo "==================================================" >> BUILD_INFO.txt && \
    echo "" >> BUILD_INFO.txt && \
    echo "Build Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> BUILD_INFO.txt && \
    echo "" >> BUILD_INFO.txt && \
    echo "--- MeteoIO ---" >> BUILD_INFO.txt && \
    cat /tmp/meteoio_version.txt >> BUILD_INFO.txt && \
    echo "" >> BUILD_INFO.txt && \
    echo "--- Snowpack ---" >> BUILD_INFO.txt && \
    cat /tmp/snowpack_version.txt >> BUILD_INFO.txt && \
    echo "" >> BUILD_INFO.txt && \
    echo "--- System ---" >> BUILD_INFO.txt && \
    echo "Base Image: python:3.11-slim" >> BUILD_INFO.txt && \
    echo "Platform: $(uname -m)" >> BUILD_INFO.txt && \
    echo "CMake Build Type: Release" >> BUILD_INFO.txt && \
    echo "==================================================" >> BUILD_INFO.txt && \
    rm -f /tmp/meteoio_version.txt /tmp/snowpack_version.txt

# Set permissions
RUN chmod +x copy_input_files.sh

# Create a non-root user
RUN useradd -m -u 1000 a3duser && \
    chown -R a3duser:a3duser /app

# Switch to non-root user
USER a3duser

# Set up volume mount points
VOLUME ["/app/a3dshell/output", "/app/a3dshell/cache", "/app/a3dshell/config"]

# Verify installations on startup
RUN echo "Verifying installations..." && \
    snowpack --version || echo "Snowpack ready" && \
    meteoio_timeseries --version || echo "MeteoIO ready"

# Expose port for Streamlit GUI
EXPOSE 8501

# Default command (run GUI)
CMD ["streamlit", "run", "gui_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
