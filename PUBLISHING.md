# Publishing A3DShell - Step-by-Step Guide

This guide walks you through publishing your first release of A3DShell to GitHub and the GitHub Container Registry (GHCR).

## Prerequisites

- [ ] GitHub account with repository access
- [ ] Git installed and configured locally
- [ ] All changes committed to your local repository
- [ ] Docker installed (for testing the published image)

## Step 1: Verify Your Repository State

Before publishing, ensure everything is ready:

```bash
# Check current branch
git branch

# Check status - should be clean
git status

# View recent commits
git log --oneline -5

# Verify remote is set correctly
git remote -v
# Should show: origin  https://github.com/frischwood/A3Dshell.git
```

**If remote is not set:**
```bash
git remote add origin https://github.com/frischwood/A3Dshell.git
```

## Step 2: Push to GitHub (First Time)

If this is your first push to the public repository:

```bash
# Push main branch to GitHub
git push -u origin main

# Or if your default branch is 'master':
git push -u origin master
```

**Expected output:**
```
Enumerating objects: 245, done.
Counting objects: 100% (245/245), done.
Delta compression using up to 8 threads
Compressing objects: 100% (156/156), done.
Writing objects: 100% (245/245), 1.23 MiB | 2.45 MiB/s, done.
Total 245 (delta 78), reused 0 (delta 0)
To https://github.com/frischwood/A3Dshell.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Step 3: Verify GitHub Repository Settings

1. Go to: https://github.com/frischwood/A3Dshell
2. Click **Settings** → **Actions** → **General**
3. Scroll to **Workflow permissions**
4. Ensure **Read and write permissions** is selected
5. Click **Save**

This allows GitHub Actions to publish Docker images to GHCR.

## Step 4: Create Your First Release Tag

Choose a version number following semantic versioning (MAJOR.MINOR.PATCH):

- **v0.1.0** - Initial development release
- **v1.0.0** - First stable release
- **v1.1.0** - New features, backward compatible
- **v1.0.1** - Bug fixes only

**Create and push the tag:**

```bash
# Create an annotated tag for version 0.1.0 (initial release)
git tag -a v0.1.0 -m "Initial release of A3DShell

Features:
- Docker-based deployment with MeteoIO and Snowpack
- Streamlit GUI with interactive ROI drawing
- CLI mode for automation
- Swiss DEM and meteorological data integration
- Shapefile browser for existing ROI files
"

# View the tag
git tag -l

# Push the tag to GitHub
git push origin v0.1.0
```

**Expected output:**
```
Enumerating objects: 1, done.
Counting objects: 100% (1/1), done.
Writing objects: 100% (1/1), 234 bytes | 234.00 KiB/s, done.
Total 1 (delta 0), reused 0 (delta 0)
To https://github.com/frischwood/A3Dshell.git
 * [new tag]         v0.1.0 -> v0.1.0
```

## Step 5: Create GitHub Release

### Option A: Using GitHub CLI (Recommended)

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Linux: See https://github.com/cli/cli#installation

# Login to GitHub
gh auth login

# Create release
gh release create v0.1.0 \
  --title "A3DShell v0.1.0 - Initial Release" \
  --notes "## A3DShell v0.1.0 - Initial Public Release

### Features
- 🐳 **Docker-first deployment** - No complex installation required
- 🗺️ **Interactive GUI** - Streamlit-based interface with Swiss map integration
- 📍 **ROI Drawing** - Draw regions of interest directly on Swisstopo maps
- 📁 **Shapefile Browser** - Browse and select existing shapefiles
- 🔧 **CLI Mode** - Automation-friendly command-line interface
- ⚙️ **MeteoIO & Snowpack** - Pre-compiled and ready to use
- 📊 **Version Tracking** - Full reproducibility with build information

### Docker Image
Pull the image:
\`\`\`bash
docker pull ghcr.io/frischwood/A3Dshell:v0.1.0
docker pull ghcr.io/frischwood/A3Dshell:latest
\`\`\`

### Quick Start
\`\`\`bash
git clone https://github.com/frischwood/A3Dshell.git
cd a3dshell
docker pull ghcr.io/frischwood/A3Dshell:latest
docker run --rm -p 8501:8501 \\
  -v \$(pwd)/output:/app/a3dshell/output \\
  -v \$(pwd)/cache:/app/a3dshell/cache \\
  -v \$(pwd)/config:/app/a3dshell/config \\
  ghcr.io/frischwood/A3Dshell:latest
# Open http://localhost:8501
\`\`\`

### Requirements
- Docker installed
- VPN access to SLF/WSL network (for IMIS data via MeteoIO)

### Documentation
- See README.md for full installation and usage guide
- See docker/DOCKER.md for maintainer documentation

### Known Limitations
- USE_LUS_TLM (SwissTLMRegio integration) not yet implemented
- Interactive map currently supports rectangle drawing only

---
**Full Changelog**: https://github.com/frischwood/A3Dshell/commits/v0.1.0"
```

### Option B: Using GitHub Web Interface

1. Go to: https://github.com/frischwood/A3Dshell/releases
2. Click **"Draft a new release"**
3. **Choose a tag**: Select `v0.1.0` from dropdown (or type it)
4. **Release title**: `A3DShell v0.1.0 - Initial Release`
5. **Description**: Paste the release notes from Option A above
6. Click **"Publish release"**

## Step 6: Monitor GitHub Actions Build

The Docker image will be built automatically:

1. Go to: https://github.com/frischwood/A3Dshell/actions
2. You should see **"Publish Docker Image"** workflow running
3. Click on the workflow run to see progress
4. Build takes approximately **8-12 minutes** (multi-platform build)

**Workflow steps:**
```
✓ Checkout repository
✓ Set up Docker Buildx
✓ Log in to GitHub Container Registry
✓ Extract metadata (tags, labels)
✓ Build and push Docker image
  - Building for linux/amd64
  - Building for linux/arm64
  - Pushing to ghcr.io/frischwood/A3Dshell
✓ Image digest
```

**If the workflow fails:**
- Check the logs in the Actions tab
- Common issues:
  - Workflow permissions not set (see Step 3)
  - GITHUB_TOKEN missing (should be automatic)
  - Build errors in Dockerfile

## Step 7: Verify Published Image

Once the GitHub Action completes successfully:

### Check on GitHub Container Registry

1. Go to: https://github.com/frischho?tab=packages
2. You should see **a3dshell** package
3. Click on it to see package details
4. Verify tags: `v0.1.0`, `0.1`, `0`, `latest`

### Pull and Test Locally

```bash
# Pull the published image
docker pull ghcr.io/frischwood/A3Dshell:v0.1.0
docker pull ghcr.io/frischwood/A3Dshell:latest

# Verify image exists
docker images | grep a3dshell

# Expected output:
# ghcr.io/frischwood/A3Dshell   v0.1.0    abc123def456   5 minutes ago   1.2GB
# ghcr.io/frischwood/A3Dshell   latest    abc123def456   5 minutes ago   1.2GB

# Test the image - Check build info
docker run --rm ghcr.io/frischwood/A3Dshell:v0.1.0 cat BUILD_INFO.txt

# Expected output:
# ==================================================
# A3DShell Docker Image Build Information
# ==================================================
#
# Build Date: 2025-01-14 ...
#
# --- MeteoIO ---
# MeteoIO_Commit=...
# ...

# Test GUI
docker run --rm -p 8501:8501 ghcr.io/frischwood/A3Dshell:v0.1.0

# Open browser to http://localhost:8501
# Verify GUI loads and shows build info in sidebar
```

### Verify Image Labels

```bash
# Check OCI labels
docker inspect ghcr.io/frischwood/A3Dshell:v0.1.0 | jq '.[0].Config.Labels'

# Should show:
# {
#   "org.opencontainers.image.created": "2025-01-14T...",
#   "org.opencontainers.image.version": "v0.1.0",
#   "org.opencontainers.image.revision": "abc123...",
#   "org.opencontainers.image.source": "https://github.com/frischwood/A3Dshell",
#   ...
# }
```

## Step 8: Make Repository Public (If Private)

If your repository is currently private:

1. Go to: https://github.com/frischwood/A3Dshell/settings
2. Scroll to bottom → **Danger Zone**
3. Click **"Change visibility"**
4. Select **"Make public"**
5. Type repository name to confirm
6. Click **"I understand, make this repository public"**

**Note**: The Docker image on GHCR can be public even if the repo is private. Check package visibility:
1. Go to: https://github.com/users/frischho/packages/container/a3dshell/settings
2. Scroll to **Danger Zone**
3. Click **"Change visibility"** → **"Public"**

## Step 9: Update README Badge (Optional)

Add a badge to show the latest release:

Add to top of `README.md`:
```markdown
# A3DShell

[![Release](https://img.shields.io/github/v/release/frischwood/A3Dshell)](https://github.com/frischwood/A3Dshell/releases)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/frischwood/A3Dshell/pkgs/container/a3dshell)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Alpine 3D Simulation Helper - Preprocessing tool for Alpine3D simulations
```

Commit and push:
```bash
git add README.md
git commit -m "Add release badges to README"
git push
```

## Step 10: Test End-to-End User Experience

Simulate a new user trying your project:

```bash
# In a fresh directory
cd /tmp
mkdir test-a3dshell && cd test-a3dshell

# Clone repo
git clone https://github.com/frischwood/A3Dshell.git
cd a3dshell

# Pull image
docker pull ghcr.io/frischwood/A3Dshell:latest

# Run GUI
docker run --rm -p 8501:8501 \
  -v $(pwd)/output:/app/a3dshell/output \
  -v $(pwd)/cache:/app/a3dshell/cache \
  -v $(pwd)/config:/app/a3dshell/config \
  ghcr.io/frischwood/A3Dshell:latest

# Open http://localhost:8501
# Test basic functionality:
# ✓ GUI loads
# ✓ Sidebar shows build info
# ✓ Can browse config files
# ✓ Interactive map works
# ✓ Shapefile browser works
```

## Troubleshooting

### Image Not Found After Push

**Problem:** `docker pull ghcr.io/frischwood/A3Dshell:v0.1.0` fails with "not found"

**Solution:**
1. Check GitHub Actions completed successfully
2. Verify package visibility is "Public" at: https://github.com/users/frischho/packages/container/a3dshell/settings
3. Wait a few minutes - images take time to propagate

### GitHub Actions Workflow Not Triggering

**Problem:** Pushing tag doesn't trigger workflow

**Solution:**
1. Verify `.github/workflows/publish-docker.yml` exists in repo
2. Check workflow file syntax: https://github.com/frischwood/A3Dshell/actions
3. Ensure tag matches pattern: `v*.*.*` (e.g., `v0.1.0`, not `0.1.0`)

### Permission Denied When Pushing to GHCR

**Problem:** Workflow fails with "permission denied" or "unauthorized"

**Solution:**
1. Go to repository Settings → Actions → General
2. Set Workflow permissions to "Read and write permissions"
3. Click Save
4. Re-run the failed workflow

### Build Fails in GitHub Actions

**Problem:** Workflow runs but build step fails

**Solution:**
1. Check workflow logs for specific error
2. Test build locally first:
   ```bash
   cd docker/
   docker build -t test-build -f Dockerfile ..
   ```
3. If local build works but Actions fails, check:
   - Build timeout (increase if needed)
   - Disk space issues
   - Network issues (git clone failures)

## Future Releases

For subsequent releases:

```bash
# 1. Make your changes
git add .
git commit -m "Add new feature X"
git push

# 2. Create new tag
git tag -a v0.2.0 -m "Release v0.2.0 - Added feature X"
git push origin v0.2.0

# 3. Create release (GitHub CLI)
gh release create v0.2.0 \
  --title "A3DShell v0.2.0" \
  --notes "## What's New
- Feature X added
- Bug Y fixed

**Full Changelog**: https://github.com/frischwood/A3Dshell/compare/v0.1.0...v0.2.0"

# 4. Monitor Actions and verify
```

## Quick Reference: Common Commands

```bash
# Check current version
git describe --tags --abbrev=0

# List all tags
git tag -l

# Delete a tag locally and remotely (if you made a mistake)
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# Pull and test latest image
docker pull ghcr.io/frischwood/A3Dshell:latest
docker run --rm ghcr.io/frischwood/A3Dshell:latest cat BUILD_INFO.txt

# View GitHub package
open https://github.com/frischwood/A3Dshell/pkgs/container/a3dshell

# View releases
open https://github.com/frischwood/A3Dshell/releases
```

## Checklist for First Release

Use this checklist for your v0.1.0 release:

- [ ] All code committed and pushed to `main` branch
- [ ] Repository settings: Actions have read/write permissions
- [ ] Created annotated tag: `v0.1.0`
- [ ] Pushed tag to GitHub
- [ ] Created GitHub release (CLI or web interface)
- [ ] Monitored GitHub Actions workflow (completed successfully)
- [ ] Verified image on GHCR: https://github.com/frischho?tab=packages
- [ ] Package visibility set to "Public"
- [ ] Tested pulling image: `docker pull ghcr.io/frischwood/A3Dshell:v0.1.0`
- [ ] Verified BUILD_INFO.txt contains correct version info
- [ ] Tested GUI loads and works
- [ ] Repository is public (if desired)
- [ ] README badges added (optional)
- [ ] End-to-end user test completed

---

**Congratulations!** 🎉 Your first release is now published and ready for users to pull and run!
