# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an eodash-catalog template project that creates STAC (SpatioTemporal Asset Catalog) catalogs for Earth observation data visualization. The project consists of:

- **Catalog configuration**: JSON files defining catalog metadata and collection references
- **Collection definitions**: YAML/JSON files for individual datasets with custom data processing
- **Custom handlers**: Python modules that process collections and integrate with external APIs
- **Layer configurations**: Base layers and overlays for map visualization
- **Automated deployment**: GitHub Actions workflows for building and deploying catalogs

## Development Commands

### Building the Catalog
The catalog is built using Docker with the eodash-catalog tool:
```bash
docker pull ghcr.io/eodash/eodash_catalog:latest
docker run -v "$PWD:/workspace" -w "/workspace" ghcr.io/eodash/eodash_catalog:latest eodash_catalog
```

The build process generates a static STAC catalog structure in the `build/` directory.

### Dependencies
Install Python dependencies with:
```bash
pip install -r requirements.txt
```

Key dependencies:
- `eodash_catalog<2`: Core catalog building library
- `pyyaml<7`: YAML configuration processing

## Architecture

### Data Flow
1. **Collection definitions** (`collections/*.yaml`) reference external data sources (WMS, TiTiler, STAC APIs)
2. **Custom handlers** (`custom_handlers/*.py`) process and augment collections programmatically
3. **Catalog configuration** (`catalogs/*.json`) defines which collections to include
4. **Build process** generates static STAC catalog structure
5. **GitHub Actions** automatically builds and deploys to GitHub Pages

### Core Components

**Catalog Definition** (`catalogs/*.json`):
- Contains catalog metadata, endpoints, and collection references
- Specifies default base layers and overlay layers
- Defines assets endpoint for additional resources

**Collections** (`collections/*.yaml`):
- Individual dataset definitions with EodashIdentifier, themes, and data sources
- Can reference custom Python handlers for data processing
- Support multiple resource types (TiTiler, GeoJSON, WMS, etc.)

**Custom Handlers** (`custom_handlers/*.py`):
- Must implement `process(collection, catalog_config, endpoint_config, collection_config)` function
- Return modified STAC collection object
- Handle integration with external APIs (TiTiler, STAC APIs, etc.)
- Common patterns: URL generation, STAC item creation, asset management

**Layer Configurations**:
- `layers/baselayers.yaml`: Background map layers (OSM, satellite imagery)
- `layers/overlays.yaml`: Overlay layers (labels, boundaries)

### GitHub Actions Workflows

**Main Build** (`.github/workflows/build_main.yaml`):
- Triggers on push to main branch
- Builds catalog using Docker
- Deploys to gh-pages branch

**Preview** (`.github/workflows/preview.yml`):
- Creates preview deployments for pull requests
- Uses `.github/update_catalog.py` to dynamically update collections based on changed files
- Includes cleanup for closed PRs

**Update Script** (`.github/update_catalog.py`):
- Analyzes changed files in PRs
- Automatically updates catalog collections based on modified collection/indicator files
- Distinguishes between regular collections and indicator-based collections

## Custom Handler Development

Custom handlers must follow this pattern:
```python
def process(collection, catalog_config, endpoint_config, collection_config):
    # Process collection data
    # Add STAC items, modify metadata, create external API links
    return collection
```

Common operations:
- Creating STAC items with proper temporal/spatial extents
- Adding assets (data, thumbnails, metadata)
- Generating tile URLs for map visualization
- Integrating with TiTiler for COG processing

## Configuration Structure

### Collection Resources
Collections can define multiple resources:
- **Custom endpoints**: Python function references for data processing
- **GeoJSON sources**: Vector data with styling
- **Time series**: Temporal data with multiple time entries
- **External APIs**: STAC, WMS, or custom endpoints

### Environment Variables
The build process supports environment variables for API credentials:
- `SH_INSTANCE_ID`: Sentinel Hub instance ID
- `SH_CLIENT_ID`: Sentinel Hub client ID
- `SH_CLIENT_SECRET`: Sentinel Hub client secret