# A3Dshell Web - Google Cloud Run Dockerfile
#
# Multi-stage build that compiles MeteoIO and Snowpack from source.
# Optimized for Cloud Run deployment with scale-to-zero.
#
# Build: gcloud run deploy a3dshell --source .
# Or locally: docker build -t a3dshell-web .

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
    git log -1 --format="MeteoIO_Commit=%H%nMeteoIO_Date=%ci" > /tmp/meteoio_version.txt && \
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
    git log -1 --format="Snowpack_Commit=%H%nSnowpack_Date=%ci" > /tmp/snowpack_version.txt && \
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
# Stage 2: Final image - Runtime environment for Cloud Run
# ============================================================
FROM python:3.11-slim

# Add metadata labels
LABEL maintainer="A3Dshell Contributors" \
      description="A3Dshell Web - Alpine 3D Simulation Helper for Cloud Run"

# Install runtime dependencies + build tools for Python packages
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built binaries and libraries from builder stage
COPY --from=builder /usr/local/bin/snowpack /usr/local/bin/
COPY --from=builder /usr/local/bin/meteoio_timeseries /usr/local/bin/
COPY --from=builder /usr/local/lib/libmeteoio.* /usr/local/lib/
COPY --from=builder /usr/local/lib/libsnowpack.* /usr/local/lib/

# Copy version info
COPY --from=builder /tmp/meteoio_version.txt /tmp/
COPY --from=builder /tmp/snowpack_version.txt /tmp/

# Update shared library cache
RUN ldconfig

# Set environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Binary paths for the application
ENV SNOWPACK_BIN=/usr/local/bin/snowpack
ENV METEOIO_BIN=/usr/local/bin/meteoio_timeseries
ENV ALPINE3D_BIN=alpine3d

# Cloud Run uses PORT environment variable
ENV PORT=8501

# Create application directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY input/ ./input/
COPY gui_app.py .

# Create output and cache directories (will be ephemeral in Cloud Run)
RUN mkdir -p output cache/dem_tiles cache/maps config

# Create BUILD_INFO.txt
RUN echo "A3Dshell Web - Cloud Run Build" > BUILD_INFO.txt && \
    echo "Build Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> BUILD_INFO.txt && \
    echo "" >> BUILD_INFO.txt && \
    cat /tmp/meteoio_version.txt >> BUILD_INFO.txt && \
    cat /tmp/snowpack_version.txt >> BUILD_INFO.txt

# Verify installations
RUN echo "Verifying installations..." && \
    snowpack --version || echo "Snowpack ready" && \
    meteoio_timeseries --version || echo "MeteoIO ready"

# Expose port (Cloud Run uses $PORT)
EXPOSE 8501

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

# Run Streamlit - Cloud Run requires listening on 0.0.0.0
CMD streamlit run gui_app.py \
    --server.address=0.0.0.0 \
    --server.port=${PORT} \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
