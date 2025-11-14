# Interactive Map Feature for ROI Drawing

## Overview

This document outlines the plan for implementing an interactive map feature in the A3DShell GUI that allows users to draw ROI polygons directly on a Swiss map.

## Requirements

### User Story
As a user, I want to:
1. Click a button to open an interactive map
2. See a Swiss map with DEM/terrain overlays from Swisstopo
3. Draw a polygon representing my ROI
4. Have the polygon automatically saved as a shapefile
5. Use this shapefile in my simulation

## Technical Approach

### Option 1: Streamlit-Folium (Recommended)

**Library:** `streamlit-folium`
**Pros:**
- Native Streamlit integration
- Built on Leaflet.js (proven mapping library)
- Drawing tools available via `folium.plugins.Draw`
- Can display WMS layers from Swisstopo
- Export to GeoJSON/Shapefile

**Implementation:**

```python
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import shape

# Create map centered on Switzerland
m = folium.Map(
    location=[46.8, 8.2],  # Center of Switzerland
    zoom_start=8,
    tiles=None  # We'll add custom tiles
)

# Add Swisstopo WMS layer
folium.WMS(
    'https://wms.geo.admin.ch/',
    layers='ch.swisstopo.pixelkarte-farbe',
    format='image/png',
    transparent=True,
    name='Swisstopo Map',
    overlay=False,
    control=True
).add_to(m)

# Add drawing tools
draw = Draw(
    export=True,
    draw_options={
        'polyline': False,
        'rectangle': True,
        'circle': False,
        'marker': False,
        'circlemarker': False,
        'polygon': True
    }
)
draw.add_to(m)

# Display map and capture drawn features
output = st_folium(m, width=800, height=600)

# Convert drawn polygon to shapefile
if output['last_active_drawing']:
    geom = shape(output['last_active_drawing']['geometry'])
    gdf = gpd.GeoDataFrame([1], geometry=[geom], crs='EPSG:4326')
    gdf = gdf.to_crs('EPSG:2056')  # Convert to Swiss coordinates
    gdf.to_file('output/roi.shp')
```

**Dependencies to add:**
```
streamlit-folium>=0.15.0
folium>=0.14.0
```

### Option 2: Plotly with Mapbox

**Library:** `plotly`
**Pros:**
- Already used in many data science workflows
- Good Streamlit integration
- Can display custom tile layers

**Cons:**
- Polygon drawing more complex
- Requires Mapbox token (free tier available)
- Less specialized for GIS workflows

### Option 3: Leafmap

**Library:** `streamlit-leafmap`
**Pros:**
- Built specifically for geospatial apps in Streamlit
- Easy polygon drawing
- Direct shapefile export
- Support for Swisstopo layers

**Cons:**
- Less mature than Folium
- Smaller community

## Swisstopo API Integration

### Available WMS Layers

Swisstopo provides WMS (Web Map Service) layers that can be integrated:

**Base URL:** `https://wms.geo.admin.ch/`

**Useful layers:**
- `ch.swisstopo.pixelkarte-farbe` - Colored map
- `ch.swisstopo.swissalti3d-reliefschattierung` - Hillshade/relief
- `ch.swisstopo.hangneigung-ueber_30` - Slope
- `ch.swisstopo.swissimage` - Aerial imagery

**Example WMS request:**
```
https://wms.geo.admin.ch/?
  SERVICE=WMS&
  REQUEST=GetMap&
  VERSION=1.3.0&
  LAYERS=ch.swisstopo.pixelkarte-farbe&
  STYLES=default&
  CRS=EPSG:2056&
  BBOX=2645000,1240000,2655000,1250000&
  WIDTH=800&
  HEIGHT=600&
  FORMAT=image/png
```

### Coordinate Systems

- Swisstopo uses **EPSG:2056** (Swiss LV95)
- Leaflet/Folium default to **EPSG:4326** (WGS84)
- Need transformation: WGS84 ↔ LV95

Using `pyproj`:
```python
from pyproj import Transformer

# WGS84 to Swiss LV95
transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
swiss_x, swiss_y = transformer.transform(lon, lat)

# Swiss LV95 to WGS84
transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
lon, lat = transformer.transform(swiss_x, swiss_y)
```

## Implementation Plan

### Phase 1: Basic Map Display (Quick Win)
- [ ] Add streamlit-folium dependency
- [ ] Create map view with Swisstopo base layer
- [ ] Display in GUI as expander/modal
- [ ] Center on Switzerland

**Estimated time:** 2-4 hours

### Phase 2: Drawing Tools
- [ ] Add Folium Draw plugin
- [ ] Enable polygon drawing
- [ ] Capture drawn geometry
- [ ] Display coordinates in Swiss system

**Estimated time:** 4-6 hours

### Phase 3: Shapefile Export
- [ ] Convert drawn polygon to GeoDataFrame
- [ ] Transform coordinates to EPSG:2056
- [ ] Save as shapefile
- [ ] Auto-populate shapefile path in GUI

**Estimated time:** 2-3 hours

### Phase 4: Enhanced Features (Optional)
- [ ] Load existing shapefile and display
- [ ] Edit existing ROI
- [ ] Multiple polygon support
- [ ] DEM overlay toggle
- [ ] Coordinates display on hover

**Estimated time:** 6-8 hours

## GUI Integration

### Proposed UI Flow

1. **Location & ROI Tab**
   - Radio button: "Bounding Box" / "Shapefile" / **"Draw on Map"**
   - If "Draw on Map" selected:
     - Button: "🗺️ Open Interactive Map"
     - Modal/expander opens with map
     - Draw polygon
     - Click "Save ROI"
     - Path auto-populated in shapefile field

2. **Alternative Flow**
   - Keep existing shapefile checkbox
   - Add button: "Draw Shapefile on Map"
   - Opens map in new section
   - Save and return to form

### Code Structure

```
gui_app.py
├── import streamlit_folium
├── def create_roi_map()
│   ├── Initialize Folium map
│   ├── Add Swisstopo WMS
│   ├── Add drawing tools
│   └── Return map object
├── def save_drawn_polygon(geojson, output_path)
│   ├── Convert to GeoDataFrame
│   ├── Transform CRS to EPSG:2056
│   ├── Validate geometry
│   └── Save shapefile
└── Tab 2: Location & ROI
    ├── Draw ROI button
    ├── Display map (conditional)
    └── Handle polygon save
```

## Technical Considerations

### Coordinate Precision
- Swiss coordinates are large (2.6M, 1.2M range)
- Need sufficient decimal precision
- Validate coordinates are within Swiss bounds

### File Management
- Save shapefiles to temporary directory
- Move to config/shapefiles/ on save
- Clean up old temporary files

### Performance
- Map loading can be slow
- Cache tile requests
- Lazy-load map (only when button clicked)

### Browser Compatibility
- Test on Chrome, Firefox, Safari
- Mobile touch support for drawing
- Fallback for older browsers

## Alternative: External Tool Integration

If implementing full map in Streamlit is too complex:

### Option: QGIS Integration
- Provide button "Open in QGIS"
- Launch QGIS with Swisstopo layers pre-configured
- User draws in QGIS
- Save shapefile
- Import back to A3DShell

### Option: Geoadmin.ch Link
- Provide link to map.geo.admin.ch
- Instructions for drawing
- Manual export/import workflow

## Testing Plan

- [ ] Test coordinate transformations (EPSG:4326 ↔ EPSG:2056)
- [ ] Verify shapefile format compatibility with backend
- [ ] Test with various polygon complexities
- [ ] Validate against existing shapefile ROI workflow
- [ ] Test on different browsers
- [ ] Performance test with large/complex polygons

## Documentation Updates

When implemented, update:
- [ ] GUI_README.md with map feature
- [ ] README.md with new workflow
- [ ] Add screenshots of map interface
- [ ] Update config examples

## Resources

- Streamlit-Folium: https://github.com/randyzwitch/streamlit-folium
- Folium documentation: https://python-visualization.github.io/folium/
- Swisstopo WMS: https://api3.geo.admin.ch/services/sdiservices.html
- Leaflet Draw: https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html
- Swiss coordinate systems: https://www.swisstopo.admin.ch/en/knowledge-facts/surveying-geodesy/reference-systems.html

## Dependencies to Add

Add to `requirements.txt`:
```
folium>=0.14.0
streamlit-folium>=0.15.0
```

These are lightweight and have minimal additional dependencies (mainly Jinja2 and requests, which we already have).

## Decision: Feasibility

**✅ YES, this is feasible and recommended!**

**Reasoning:**
1. **Technical:** `streamlit-folium` provides everything needed
2. **Effort:** Phased approach allows incremental delivery
3. **User Value:** Significant UX improvement over manual coordinates
4. **Maintenance:** Well-established libraries, good community support
5. **Dependencies:** Lightweight additions to requirements

**Recommendation:**
- Implement Phase 1-3 (basic drawing + export)
- Phase 4 features can be added based on user feedback
- Alternative: Keep it simple with just polygon drawing for v1

## Next Steps

1. Add dependencies to requirements.txt
2. Create prototype in separate branch
3. Test Swisstopo WMS integration
4. Implement basic UI in gui_app.py
5. User testing with sample data
6. Refine and merge to main

---

**Status:** Planning Complete - Ready for Implementation
**Priority:** Medium (nice-to-have feature, significant UX improvement)
**Estimated Total Time:** 8-13 hours for Phases 1-3
