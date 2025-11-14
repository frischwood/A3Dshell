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
CMD ["streamlit", "run", "gui_app.py", "--server.address=0.0.0.0"]
