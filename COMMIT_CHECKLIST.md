# Commit Checklist Before Publishing v0.1.0

## Changes Made

### 1. GitHub Actions Workflow
- ✅ Created `.github/workflows/publish-docker.yml`
- Automatically builds and publishes Docker images on release
- Uses correct repository name dynamically: `${{ github.repository }}`

### 2. Dockerfile Updates
- ✅ Removed `copy_input_files.sh` (no longer needed)
- ✅ Removed `run_gui.sh` copy (not needed in image)
- ✅ Added `mkdir -p input/bin` to ensure directory exists
- ✅ Removed `chmod +x copy_input_files.sh` line
- ✅ Updated all repository URLs to `frischwood/A3Dshell`

### 3. .gitignore Updates
- ✅ Keep directory structure but ignore contents for:
  - `input/*` (except subdirectories)
  - `input/bin/*` (keep directory, ignore binaries)
  - `output/*`
  - `cache/*` and subdirectories
  - `config/shapefiles/*`
- ✅ Use `.gitkeep` files to preserve empty directories

### 4. .gitkeep Files Created
- ✅ `input/.gitkeep`
- ✅ `input/bin/.gitkeep`
- ✅ `output/.gitkeep`
- ✅ `cache/.gitkeep`
- ✅ `cache/dem_tiles/.gitkeep`
- ✅ `cache/maps/.gitkeep`
- ✅ `config/shapefiles/.gitkeep`

### 5. README.md Updates
- ✅ Removed `bash copy_input_files.sh` from installation instructions
- ✅ Updated repository URL to `frischwood/A3Dshell`
- ✅ Updated all Docker registry references to `ghcr.io/frischwood/A3Dshell`

### 6. Other Files Updated
- ✅ `docker/docker-compose.registry.yml` - Updated image name
- ✅ `PUBLISHING.md` - Updated all repository references
- ✅ `docker/Dockerfile` - Updated OCI labels with correct repo URL

## Files to Commit

```bash
# Check what will be committed
git status

# Should show:
# New files:
#   .github/workflows/publish-docker.yml
#   input/.gitkeep
#   input/bin/.gitkeep
#   output/.gitkeep
#   cache/.gitkeep
#   cache/dem_tiles/.gitkeep
#   cache/maps/.gitkeep
#   config/shapefiles/.gitkeep
#
# Modified files:
#   .gitignore
#   docker/Dockerfile
#   docker/docker-compose.registry.yml
#   README.md
#   PUBLISHING.md
```

## Commit Commands

```bash
cd /Users/frischho/Documents/dev/A3Dshell

# Add all changes
git add .github/workflows/publish-docker.yml
git add .gitignore
git add docker/Dockerfile
git add docker/docker-compose.registry.yml
git add README.md
git add PUBLISHING.md
git add input/.gitkeep
git add input/bin/.gitkeep
git add output/.gitkeep
git add cache/.gitkeep
git add cache/dem_tiles/.gitkeep
git add cache/maps/.gitkeep
git add config/shapefiles/.gitkeep

# Or simply:
git add -A

# Commit
git commit -m "Prepare for v0.1.0 release

- Add GitHub Actions workflow for automatic Docker image publishing
- Remove deprecated copy_input_files.sh references
- Update .gitignore to preserve directory structure with .gitkeep files
- Update all repository references from frischho to frischwood
- Clean up Dockerfile (remove unused scripts)
"

# Push to GitHub
git push origin main
```

## After Pushing - Create Release

```bash
# 1. Create tag
git tag -a v0.1.0 -m "Initial public release of A3DShell"

# 2. Push tag
git push origin v0.1.0

# 3. This will automatically trigger GitHub Actions to build and publish the Docker image!

# 4. Monitor the build at:
# https://github.com/frischwood/A3Dshell/actions
```

## Expected GitHub Actions Workflow

Once you push the tag, GitHub Actions will:

1. ✅ Checkout the repository
2. ✅ Set up Docker Buildx for multi-platform builds
3. ✅ Log in to GitHub Container Registry (GHCR)
4. ✅ Extract metadata (version tags from v0.1.0)
5. ✅ Build Docker image for linux/amd64 and linux/arm64
   - Clone and build MeteoIO from GitLab
   - Clone and build Snowpack from GitLab
   - Install Python dependencies
   - Create BUILD_INFO.txt with version tracking
6. ✅ Push to `ghcr.io/frischwood/A3Dshell` with tags:
   - `v0.1.0`
   - `0.1`
   - `0`
   - `latest`

Build time: ~8-12 minutes

## Verify After Build

```bash
# Pull the published image
docker pull ghcr.io/frischwood/A3Dshell:v0.1.0

# Test it
docker run --rm ghcr.io/frischwood/A3Dshell:v0.1.0 cat BUILD_INFO.txt

# Should show MeteoIO and Snowpack build information
```

## Notes

- The workflow uses `${{ github.repository }}` so it automatically picks up `frischwood/A3Dshell`
- No hardcoded repository names in the workflow file
- MeteoIO and Snowpack are built from source during Docker build (not copied from input/bin/)
- Directory structure is preserved in git with .gitkeep files
- All outputs go to mounted volumes, not inside the container

## Troubleshooting

If GitHub Actions doesn't trigger:
1. Check repository Settings → Actions → General
2. Ensure "Read and write permissions" is enabled
3. Verify tag format matches `v*.*.*` pattern
4. Check `.github/workflows/publish-docker.yml` is in the main branch
