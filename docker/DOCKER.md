# Docker Maintainer Documentation

This document contains technical details for maintaining and publishing Docker images for A3DShell. For user-facing Docker usage instructions, see the main [README.md](../README.md).

## Overview

The A3DShell Docker setup provides:
- Multi-stage build for optimized image size
- Pre-compiled MeteoIO and Snowpack binaries
- Complete Python environment with geospatial libraries
- Automatic publishing to GitHub Container Registry
- Support for both GUI and CLI workflows

## Image Details

### Base Image
- **Base**: `python:3.11-slim`
- **Final Size**: ~1.2 GB (includes all dependencies and data)
- **Architecture**: Multi-platform (linux/amd64, linux/arm64)

### What's Included
- Python 3.11 with scientific packages (numpy, pandas, scipy)
- Geospatial stack (GDAL, PROJ, GEOS, geopandas, rasterio)
- MeteoIO (compiled from WSL GitLab)
- Snowpack (compiled from WSL GitLab)
- Complete input data (BRDF files, templates, IMIS metadata)
- Streamlit GUI application
- Non-root user (`a3duser`, UID 1000)

## Building Locally

### Standard Build

```bash
cd docker/

# Build with docker-compose (recommended)
docker-compose build

# Or with plain docker
docker build -t a3dshell:latest -f Dockerfile ..
```

**Build time**: ~5-10 minutes (depends on network and CPU)

### Build Arguments

The Dockerfile supports custom build arguments:

```bash
# Use specific MeteoIO/Snowpack versions
docker build \
  --build-arg METEOIO_VERSION=master \
  --build-arg SNOWPACK_VERSION=master \
  -t a3dshell:custom \
  -f Dockerfile ..
```

### Multi-stage Build Process

**Stage 1: Builder**
```dockerfile
FROM python:3.11-slim as builder
# Compiles MeteoIO from source
# Compiles Snowpack from source
# Results cached in /usr/local/lib and /usr/local/bin
```

**Stage 2: Runtime**
```dockerfile
FROM python:3.11-slim
# Copies compiled binaries from Stage 1
# Installs Python dependencies
# Copies application code and data
# Sets up non-root user
```

This approach keeps the final image size manageable by discarding build tools and intermediate files.

## Publishing to GitHub Container Registry

### Automatic Publishing (Recommended)

Images are automatically built and published via GitHub Actions when you create a release.

**Workflow**: `.github/workflows/publish-docker.yml`

**Triggers**:
1. New release published on GitHub
2. Git tags matching `v*.*.*` pattern
3. Manual workflow dispatch

**Process**:
```
Create Git tag (v1.0.0)
    ↓
Push tag to GitHub
    ↓
GitHub Actions triggered
    ↓
Multi-platform build (amd64, arm64)
    ↓
Push to ghcr.io/frischho/a3dshell
    ↓
Tags created: v1.0.0, 1.0, 1, latest
```

### Publishing a New Release

**Step 1: Create and push Git tag**
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0 - Brief description"

# Push tag to GitHub
git push origin v1.0.0
```

**Step 2: Create GitHub Release**

Via GitHub Web UI:
1. Go to repository → Releases → "Create a new release"
2. Select your tag (`v1.0.0`)
3. Add release title: "v1.0.0 - Description"
4. Write release notes describing changes
5. Click "Publish release"

Via GitHub CLI:
```bash
gh release create v1.0.0 \
  --title "v1.0.0 - Release title" \
  --notes "## Changes
- Feature A added
- Bug B fixed
- Enhancement C implemented"
```

**Step 3: Monitor Build**

GitHub Actions automatically:
- Builds for multiple architectures
- Runs for ~5-10 minutes
- Pushes to `ghcr.io/frischho/a3dshell`
- Creates semantic version tags

Check progress:
- GitHub → Actions tab
- View workflow run logs
- Verify completion

**Step 4: Verify Published Image**

```bash
# Pull and test the new image
docker pull ghcr.io/frischho/a3dshell:v1.0.0
docker pull ghcr.io/frischho/a3dshell:latest

# Verify tags exist
docker image ls | grep a3dshell

# Test functionality
docker run --rm ghcr.io/frischho/a3dshell:v1.0.0 python -m src.cli --version
```

### Manual Publishing

If you need to publish manually:

**1. Build the image**
```bash
docker build -t ghcr.io/frischho/a3dshell:v1.0.0 -f docker/Dockerfile .
```

**2. Login to GHCR**
```bash
# Create personal access token with packages:write scope
# From GitHub: Settings → Developer settings → Personal access tokens

echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

**3. Tag the image**
```bash
docker tag ghcr.io/frischho/a3dshell:v1.0.0 ghcr.io/frischho/a3dshell:1.0
docker tag ghcr.io/frischho/a3dshell:v1.0.0 ghcr.io/frischho/a3dshell:1
docker tag ghcr.io/frischho/a3dshell:v1.0.0 ghcr.io/frischho/a3dshell:latest
```

**4. Push all tags**
```bash
docker push ghcr.io/frischho/a3dshell:v1.0.0
docker push ghcr.io/frischho/a3dshell:1.0
docker push ghcr.io/frischho/a3dshell:1
docker push ghcr.io/frischho/a3dshell:latest
```

## Versioning Strategy

### Semantic Versioning

Follow semantic versioning: `vMAJOR.MINOR.PATCH`

```
v1.0.0
│ │ │
│ │ └─ Patch: Bug fixes, minor changes (backward compatible)
│ └─── Minor: New features (backward compatible)
└───── Major: Breaking changes (not backward compatible)
```

### Docker Tag Strategy

For each release `v1.2.3`, create these tags:
- `v1.2.3` - Exact version (immutable, never changes)
- `1.2` - Minor version (gets patch updates)
- `1` - Major version (gets minor and patch updates)
- `latest` - Most recent stable release

**Example progression**:
```
v1.0.0 → tags: v1.0.0, 1.0, 1, latest
v1.0.1 → tags: v1.0.1, 1.0, 1, latest (1.0, 1, latest move)
v1.1.0 → tags: v1.1.0, 1.1, 1, latest (1.1, 1, latest move)
v2.0.0 → tags: v2.0.0, 2.0, 2, latest (2.0, 2, latest move)
```

### Pre-release Versions

For testing before official release:

```bash
# Create pre-release tag
git tag -a v1.0.0-beta.1 -m "Beta release for testing"
git push origin v1.0.0-beta.1

# Build and push with beta tag
docker build -t ghcr.io/frischho/a3dshell:v1.0.0-beta.1 .
docker push ghcr.io/frischho/a3dshell:v1.0.0-beta.1
```

Don't update `latest` tag for pre-releases.

## GitHub Actions Workflow

### Configuration

File: `.github/workflows/publish-docker.yml`

**Key features**:
- Multi-platform builds (amd64, arm64)
- Semantic version tag extraction
- Layer caching for faster builds
- Automatic GHCR authentication

**Permissions required**:
```yaml
permissions:
  contents: read    # Read repository
  packages: write   # Push to GHCR
```

### Workflow Customization

**Change trigger conditions**:
```yaml
on:
  release:
    types: [published]  # Only on published releases
  # or
  push:
    tags:
      - 'v*.*.*'        # Any semantic version tag
```

**Add build platforms**:
```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

**Modify tag strategy**:
```yaml
tags: |
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  type=semver,pattern={{major}}
  type=raw,value=latest,enable={{is_default_branch}}
  type=sha,prefix={{branch}}-  # Add git SHA tag
```

### Troubleshooting Workflow

**Build fails during MeteoIO/Snowpack compilation**:
- Check upstream repositories are accessible
- Verify build dependencies are correct
- Check for breaking changes in source repos

**Authentication errors**:
- Verify `GITHUB_TOKEN` has correct permissions
- Check repository settings → Actions → General → Workflow permissions

**Multi-platform build timeout**:
- Consider building platforms separately
- Use self-hosted runners for ARM builds
- Increase timeout in workflow file

## Docker Compose Files

### docker-compose.yml

For **local development** - builds image from source:

```yaml
services:
  a3dshell:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    image: a3dshell:latest
    # ... volumes, ports, etc.
```

Usage:
```bash
cd docker/
docker-compose build      # Build image
docker-compose up         # Start GUI
docker-compose run --rm a3dshell python -m src.cli --config ../config/example_quick_test.ini
```

### docker-compose.registry.yml

For **end users** - pulls pre-built image:

```yaml
services:
  a3dshell:
    image: ghcr.io/frischho/a3dshell:latest
    # or pin to version:
    # image: ghcr.io/frischho/a3dshell:v1.0.0
    # ... volumes, ports, etc.
```

Usage:
```bash
docker-compose -f docker-compose.registry.yml up
docker-compose -f docker-compose.registry.yml run --rm a3dshell python -m src.cli --config config/example_quick_test.ini
```

## Dockerfile Structure

### Key Sections

**System Dependencies**:
```dockerfile
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    # ... compilation tools for builder stage
```

**Python Dependencies**:
```dockerfile
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt
```

**Application Setup**:
```dockerfile
COPY --chown=a3duser:a3duser . /app/a3dshell/
WORKDIR /app/a3dshell
```

**Volume Definitions**:
```dockerfile
VOLUME ["/app/a3dshell/output", "/app/a3dshell/cache", "/app/a3dshell/config"]
```

**Default Command**:
```dockerfile
CMD ["streamlit", "run", "gui_app.py", "--server.address=0.0.0.0"]
```

### Optimization Techniques

**1. Multi-stage build**:
- Separate build and runtime stages
- Discard build tools and intermediate files
- Reduces final image size by ~40%

**2. Layer caching**:
- Order FROM most stable to least stable
- Copy `requirements.txt` before source code
- Separate system and Python dependencies

**3. .dockerignore**:
```
__pycache__/
*.pyc
*.pyo
.git/
.pytest_cache/
output/
cache/
.env
*.log
```

Prevents unnecessary files from being copied into image.

**4. Non-root user**:
- Security best practice
- Runs as UID 1000 (common user ID)
- Avoids permission issues on Linux hosts

## Image Size Analysis

### Current Size Breakdown

```
Base python:3.11-slim:     ~140 MB
System libraries (GDAL):   ~300 MB
Python packages:           ~200 MB
MeteoIO + Snowpack:        ~50 MB
Application code:          ~20 MB
Input data (BRDF, etc):    ~500 MB
─────────────────────────────────
Total:                     ~1.2 GB
```

### Size Optimization Options

**Option 1: Separate data image**
- Base image without BRDF/template data: ~700 MB
- Data mounted as volume or separate image
- Tradeoff: More complex setup for users

**Option 2: Alpine base**
- Use `python:3.11-alpine` instead of slim
- Potential savings: ~100 MB
- Tradeoff: Compilation complexity, potential compatibility issues

**Option 3: Pre-built binaries**
- Don't compile MeteoIO/Snowpack in Dockerfile
- Provide pre-compiled binaries
- Faster builds, but less flexible

## Testing

### Local Testing

After building, test the image:

```bash
# Build
docker-compose build

# Test CLI
docker-compose run --rm a3dshell python -m src.cli --version
docker-compose run --rm a3dshell python -m src.cli --help

# Test GUI
docker-compose up
# Open http://localhost:8501 in browser

# Test with example config
docker-compose run --rm a3dshell \
  python -m src.cli --config config/example_quick_test.ini

# Verify output
ls -lh ../output/
```

### Automated Testing

Consider adding to GitHub Actions:

```yaml
- name: Test Docker image
  run: |
    docker-compose build
    docker-compose run --rm a3dshell python -m src.cli --version
    docker-compose run --rm a3dshell python -m src.cli --create-template /tmp/test.ini
```

## Alternative: Offline Distribution

For situations where registry access is unavailable:

### Save Image to File

```bash
# Save image
docker save a3dshell:latest | gzip > a3dshell-latest.tar.gz

# File size: ~1.2 GB compressed
```

### Load Image from File

```bash
# Load on another machine
gunzip -c a3dshell-latest.tar.gz | docker load

# Verify
docker images | grep a3dshell
```

### Limitations

- Large file size (~1.2 GB)
- No layer deduplication
- Manual distribution required
- Full re-download for updates
- No version management

**Recommendation**: Only use for offline/airgapped environments. Always prefer registry distribution for normal use.

## Security Considerations

### Non-root User

The image runs as `a3duser` (UID 1000):
```dockerfile
RUN useradd -m -u 1000 -s /bin/bash a3duser
USER a3duser
```

**Benefits**:
- Limits potential damage from container escape
- Matches typical Linux user UID
- Follows Docker security best practices

### Secrets Management

**Never include in image**:
- API keys
- Passwords
- Credentials
- Private keys

**Instead, use**:
- Environment variables: `-e API_KEY=xxx`
- Mounted files: `-v /secure/creds:/app/creds:ro`
- Docker secrets (Swarm mode)

### Image Scanning

Periodically scan for vulnerabilities:

```bash
# Using Docker Scout
docker scout cves ghcr.io/frischho/a3dshell:latest

# Using Trivy
trivy image ghcr.io/frischho/a3dshell:latest
```

Address critical and high-severity vulnerabilities promptly.

## Maintenance Checklist

### Regular Maintenance

- [ ] Update base image to latest Python 3.11 patch version
- [ ] Update Python dependencies in requirements.txt
- [ ] Check for MeteoIO/Snowpack updates
- [ ] Scan for security vulnerabilities
- [ ] Test with latest Docker/docker-compose versions
- [ ] Review and update documentation

### Before Each Release

- [ ] Test build locally
- [ ] Run example simulations (CLI and GUI)
- [ ] Verify all volume mounts work
- [ ] Check image size hasn't grown significantly
- [ ] Update CHANGELOG if it exists
- [ ] Tag with appropriate version
- [ ] Monitor GitHub Actions build
- [ ] Test pulling and running published image

### Quarterly Review

- [ ] Evaluate Docker base image options
- [ ] Consider image size optimizations
- [ ] Review GitHub Actions workflow efficiency
- [ ] Check for breaking changes in dependencies
- [ ] Update this documentation

## Troubleshooting

### Build Issues

**Problem**: MeteoIO compilation fails
```
Solution: Check upstream GitLab repository is accessible
Check build dependencies are installed
Verify network connectivity in build environment
```

**Problem**: Out of disk space during build
```
Solution: Clean up old images: docker system prune -a
Use docker buildx for better caching
Build on machine with more storage
```

**Problem**: Python package installation fails
```
Solution: Check requirements.txt for pinned versions
Verify PyPI is accessible
Try building with --no-cache
```

### Runtime Issues

**Problem**: Permission denied errors
```
Solution: Ensure host directories have correct permissions
Use: chown -R 1000:1000 output/ cache/ config/
Or run container with: --user $(id -u):$(id -g)
```

**Problem**: Volumes not persisting
```
Solution: Verify volume mounts in docker-compose.yml
Check paths are absolute or relative to compose file
Ensure directories exist on host
```

**Problem**: GUI not accessible
```
Solution: Check port mapping: -p 8501:8501
Verify firewall allows connections
Try: curl http://localhost:8501
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Multi-stage Build Guide](https://docs.docker.com/build/building/multi-stage/)

## Support

For Docker-specific issues:
1. Check this documentation
2. Review GitHub Actions logs
3. Test with `docker-compose.yml` locally
4. Open issue on GitHub repository

For user-facing Docker usage questions, refer users to the main [README.md](../README.md).
