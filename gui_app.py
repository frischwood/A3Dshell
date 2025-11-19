"""
A3Dshell- Simple GUI
====================================

A Streamlit-based GUI for configuring and running A3Dshell simulations.

Run with: streamlit run gui_app.py
"""

import streamlit as st
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
import configparser
import os
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import shape
from pyproj import Transformer

# Page configuration
st.set_page_config(
    page_title="A3Dshell Simulation Setup",
    layout="wide"
)

# Helper functions
def get_build_info():
    """
    Read and parse BUILD_INFO.txt if it exists (Docker environment).

    Returns:
        dict: Build information or None if not found
    """
    build_info_path = Path("BUILD_INFO.txt")
    if build_info_path.exists():
        try:
            with open(build_info_path, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            return None
    return None

def find_shapefiles(base_dir):
    """
    Recursively find all .shp files in a directory.

    Args:
        base_dir: Base directory to search (str or Path)

    Returns:
        list: List of Path objects for found shapefiles, empty list if none found or dir invalid
    """
    try:
        base_path = Path(base_dir)
        if not base_path.exists() or not base_path.is_dir():
            return []

        # Find all .shp files recursively
        shapefiles = sorted(base_path.rglob("*.shp"))
        return shapefiles
    except Exception:
        return []

@st.cache_data(ttl=3600)
def get_swiss_boundary_polygon():
    """
    Fetch or create Swiss boundary polygon for validation.

    First attempts to fetch from Swisstopo REST API.
    Falls back to simplified boundary polygon if API unavailable.

    Returns:
        shapely.Polygon: Swiss boundary in EPSG:2056, or None if all methods fail
    """
    try:
        import requests
        from shapely.geometry import Polygon

        # Try Swisstopo REST API for height service (includes boundary query)
        # Alternative: Use a pre-simplified boundary polygon
        url = "https://api3.geo.admin.ch/rest/services/api/MapServer/identify?geometry=2660000,1185000&geometryType=esriGeometryPoint&layers=all:ch.swisstopo.swissboundaries3d-land-flaeche.fill&returnGeometry=true&sr=2056"

        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                # Extract geometry if available
                for result in data['results']:
                    if 'geometry' in result and 'rings' in result['geometry']:
                        rings = result['geometry']['rings']
                        if rings and len(rings) > 0:
                            # Create polygon from rings
                            from shapely.geometry import Polygon
                            polygon = Polygon(rings[0])
                            return polygon

        # Fallback: Use simplified Swiss boundary (approximate)
        # This is a generalized version for validation purposes
        # Coordinates in EPSG:2056 (Swiss LV95)
        simplified_coords = [
            (2485000, 1075000),  # SW corner
            (2485000, 1110000),
            (2490000, 1145000),  # West (Geneva area)
            (2495000, 1185000),
            (2510000, 1230000),
            (2525000, 1265000),  # NW
            (2570000, 1295000),  # North
            (2630000, 1296000),
            (2720000, 1295000),  # NE (Rhine valley)
            (2795000, 1280000),
            (2834000, 1255000),  # East (Grisons)
            (2830000, 1220000),
            (2815000, 1185000),
            (2785000, 1150000),  # SE
            (2750000, 1110000),
            (2715000, 1085000),  # Ticino
            (2680000, 1080000),
            (2630000, 1085000),
            (2580000, 1095000),
            (2530000, 1085000),
            (2490000, 1078000),  # South
            (2485000, 1075000),  # Close polygon
        ]

        polygon = Polygon(simplified_coords)
        return polygon

    except Exception:
        return None

def check_swiss_boundaries(x, y, roi_size=None):
    """
    Check if coordinates (and optional ROI) are within Swiss boundaries (EPSG:2056).

    Uses official Swiss boundary polygon from Swisstopo.

    Args:
        x: Easting coordinate (EPSG:2056)
        y: Northing coordinate (EPSG:2056)
        roi_size: Optional ROI size in meters (for bounding box check)

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    try:
        from shapely.geometry import Point, box

        # Get Swiss boundary polygon
        swiss_boundary = get_swiss_boundary_polygon()

        if swiss_boundary is None:
            # Fallback to bounding box check if API fails
            SWISS_MIN_E = 2485000
            SWISS_MAX_E = 2834000
            SWISS_MIN_N = 1075000
            SWISS_MAX_N = 1296000

            if not (SWISS_MIN_E <= x <= SWISS_MAX_E and SWISS_MIN_N <= y <= SWISS_MAX_N):
                return False, f"⚠️ Point ({x:.0f}, {y:.0f}) appears outside Swiss boundaries"

            if roi_size:
                half_size = roi_size / 2
                min_x, max_x = x - half_size, x + half_size
                min_y, max_y = y - half_size, y + half_size

                if not (SWISS_MIN_E <= min_x and max_x <= SWISS_MAX_E and
                       SWISS_MIN_N <= min_y and max_y <= SWISS_MAX_N):
                    return False, f"⚠️ ROI extends outside Swiss boundaries. Reduce ROI size or move center point."

            return True, "✅ Within Swiss boundaries"

        # Use actual Swiss boundary polygon
        point = Point(x, y)

        # Check if point is within Switzerland
        if not swiss_boundary.contains(point):
            return False, f"⚠️ Point ({x:.0f}, {y:.0f}) is outside Switzerland"

        # If ROI size provided, check if entire bounding box fits within Switzerland
        if roi_size:
            half_size = roi_size / 2
            roi_box = box(x - half_size, y - half_size, x + half_size, y + half_size)

            # Check if ROI box is fully within Switzerland
            if not swiss_boundary.contains(roi_box):
                return False, f"⚠️ ROI extends outside Switzerland. Reduce ROI size or move center point."

        return True, "✅ Within Switzerland"

    except Exception:
        # If anything fails, allow it (better than blocking)
        return True, "⚠️ Could not validate boundaries"

def check_polygon_in_swiss_boundaries(geojson_geometry):
    """
    Check if a drawn polygon is within Swiss boundaries.

    Uses official Swiss boundary polygon from Swisstopo.

    Args:
        geojson_geometry: GeoJSON geometry object (in WGS84)

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    try:
        from shapely.geometry import shape as shapely_shape
        import geopandas as gpd

        # Convert GeoJSON to shapely geometry (WGS84)
        geom_wgs84 = shapely_shape(geojson_geometry)

        # Transform to Swiss LV95
        gdf = gpd.GeoDataFrame([{'geometry': geom_wgs84}], crs='EPSG:4326')
        gdf_lv95 = gdf.to_crs('EPSG:2056')
        geom_lv95 = gdf_lv95.geometry.iloc[0]

        # Get Swiss boundary polygon
        swiss_boundary = get_swiss_boundary_polygon()

        if swiss_boundary is None:
            # Fallback to bounding box check if polygon unavailable
            SWISS_MIN_E = 2485000
            SWISS_MAX_E = 2834000
            SWISS_MIN_N = 1075000
            SWISS_MAX_N = 1296000

            minx, miny, maxx, maxy = geom_lv95.bounds

            if minx < SWISS_MIN_E or maxx > SWISS_MAX_E:
                return False, f"⚠️ Drawn ROI extends outside Swiss boundaries (East-West). Please redraw within Switzerland."

            if miny < SWISS_MIN_N or maxy > SWISS_MAX_N:
                return False, f"⚠️ Drawn ROI extends outside Swiss boundaries (North-South). Please redraw within Switzerland."

            return True, "✅ ROI within Swiss boundaries (bounding box check)"

        # Use actual Swiss boundary polygon
        # Check if drawn geometry is fully within Switzerland
        # Using .contains() checks if the ENTIRE geometry (including edges) is within the boundary
        if not swiss_boundary.contains(geom_lv95):
            # Additional check: does the drawn polygon intersect but not fully contained?
            if swiss_boundary.intersects(geom_lv95):
                return False, f"⚠️ Drawn ROI crosses Swiss border. Part of the ROI is outside Switzerland. Please redraw within Swiss borders."
            else:
                return False, f"⚠️ Drawn ROI is completely outside Switzerland. Please redraw within Swiss borders."

        return True, "✅ ROI within Switzerland (boundary polygon check)"

    except Exception as e:
        # Log the error for debugging
        import streamlit as st
        st.warning(f"⚠️ Boundary validation error: {str(e)}")
        # Fail safe: reject if validation fails
        return False, f"❌ Could not validate boundaries (error: {str(e)}). Please check your ROI."

def create_roi_map(center_lat=46.8, center_lon=8.2, zoom=8):
    """
    Create an interactive map with Swisstopo layers for drawing ROI polygons.

    Args:
        center_lat: Latitude for map center (WGS84)
        center_lon: Longitude for map center (WGS84)
        zoom: Initial zoom level

    Returns:
        folium.Map object with drawing tools
    """
    # Create base map centered on Switzerland
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=None  # We'll add custom tiles
    )

    # Add Swisstopo base layer (Swiss National Map)
    folium.raster_layers.WmsTileLayer(
        url='https://wms.geo.admin.ch/',
        layers='ch.swisstopo.pixelkarte-farbe',
        fmt='image/png',
        transparent=False,
        name='Swisstopo Map',
        overlay=False,
        control=True,
        attr='© swisstopo'
    ).add_to(m)

    # Add drawing tools (rectangle and polygon)
    draw = Draw(
        export=False,
        draw_options={
            'polyline': False,
            'rectangle': True,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'polygon': True
        },
        edit_options={
            'edit': True,
            'remove': True
        }
    )
    draw.add_to(m)

    return m

def save_drawn_roi(geojson_data, output_path):
    """
    Save drawn polygon as shapefile in Swiss coordinate system (EPSG:2056).

    Args:
        geojson_data: GeoJSON dict from drawn polygon
        output_path: Path to save shapefile

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Extract geometry from GeoJSON
        geom = shape(geojson_data['geometry'])

        # Create GeoDataFrame in WGS84
        gdf = gpd.GeoDataFrame([{'id': 1}], geometry=[geom], crs='EPSG:4326')

        # Transform to Swiss coordinate system (LV95)
        gdf = gdf.to_crs('EPSG:2056')

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as shapefile
        gdf.to_file(output_path)

        return True, f"✅ ROI saved successfully to {output_path}"

    except Exception as e:
        return False, f"❌ Error saving ROI: {str(e)}"


# Title
st.title("A3Dshell")
st.markdown("Configure Alpine3D simulation setups")

# Sidebar for existing configs
st.sidebar.header("Load Existing Config")
config_dir = Path("config")
existing_configs = list(config_dir.glob("*.ini"))
config_names = ["Create New"] + [c.name for c in existing_configs]

selected_config = st.sidebar.selectbox(
    "Select configuration:",
    config_names
)

# Build Info section in sidebar
st.sidebar.divider()
st.sidebar.header("ℹ️ About")

build_info = get_build_info()
if build_info:
    with st.sidebar.expander("🐳 Docker Build Info", expanded=False):
        st.code(build_info, language=None)
        st.caption("This information shows the exact versions of MeteoIO and Snowpack compiled into this Docker image.")
else:
    st.sidebar.info("Running in development mode (not Docker)")

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = {}

# Initialize ROI validation state
if 'roi_validated' not in st.session_state:
    st.session_state['roi_validated'] = False

# Load selected config
if selected_config != "Create New":
    config_path = config_dir / selected_config
    parser = configparser.ConfigParser(inline_comment_prefixes=("#",))
    parser.read(config_path)

    # Parse config into session state
    if "GENERAL" in parser:
        st.session_state.config['simu_name'] = parser.get("GENERAL", "SIMULATION_NAME", fallback="")
        st.session_state.config['start_date'] = parser.get("GENERAL", "START_DATE", fallback="")
        st.session_state.config['end_date'] = parser.get("GENERAL", "END_DATE", fallback="")

    if "INPUT" in parser:
        st.session_state.config['poi_x'] = parser.get("INPUT", "EAST_epsg2056", fallback="")
        st.session_state.config['poi_y'] = parser.get("INPUT", "NORTH_epsg2056", fallback="")
        st.session_state.config['poi_z'] = parser.get("INPUT", "altLV95", fallback="")
        st.session_state.config['use_shp'] = parser.getboolean("INPUT", "USE_SHP_ROI", fallback=False)
        st.session_state.config['roi_size'] = parser.get("INPUT", "ROI", fallback="1000")
        st.session_state.config['buffer_size'] = parser.get("INPUT", "BUFFERSIZE", fallback="50000")
        st.session_state.config['roi_shapefile'] = parser.get("INPUT", "ROI_SHAPEFILE", fallback="")

    if "OUTPUT" in parser:
        st.session_state.config['coord_sys'] = parser.get("OUTPUT", "OUT_COORDSYS", fallback="CH1903+")
        st.session_state.config['gsd'] = parser.get("OUTPUT", "GSD", fallback="10.0")
        st.session_state.config['gsd_ref'] = parser.get("OUTPUT", "GSD_ref", fallback="2.0")

    if "A3D" in parser:
        st.session_state.config['use_lus_tlm'] = parser.getboolean("A3D", "USE_LUS_TLM", fallback=False)
        st.session_state.config['lus_cst'] = parser.get("A3D", "LUS_PREVAH_CST", fallback="11500")

# Parent tabs for Switzerland vs Other Locations
mode_tab_switzerland, mode_tab_other = st.tabs(["Switzerland", "Other Locations"])

# ============================================================
# SWITZERLAND MODE
# ============================================================
with mode_tab_switzerland:
    st.info("ℹ️ **Switzerland Mode**: Automatic DEM download from Swisstopo, IMIS station data via MeteoIO, and Snowpack preprocessing")

    # Tabs for configuration sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["1.General", "2.ROI/DEM", "3.Landcover", "4.Meteo", "5.Run ▶️"])

    # ============================================================
    # Tab 1: General Settings
    # ============================================================
    with tab1:
        st.header("General Settings")
    
        col1, col2 = st.columns(2)
    
        with col1:
            simu_name = st.text_input(
                "Simulation Name",
                value=st.session_state.config.get('simu_name', ''),
                help="Unique name for this simulation (no spaces)"
            )
    
        with col2:
            coord_sys = st.selectbox(
                "Coordinate System",
                ["CH1903+", "CH1903", "WGS84"],
                index=["CH1903+", "CH1903", "WGS84"].index(st.session_state.config.get('coord_sys', 'CH1903+'))
            )
    
        st.subheader("Simulation Period")
        col1, col2 = st.columns(2)
    
        # Parse dates from config or use defaults
        default_start = datetime(2023, 10, 1)
        default_end = datetime(2023, 10, 31, 23, 59, 59)
    
        if st.session_state.config.get('start_date'):
            try:
                default_start = datetime.fromisoformat(st.session_state.config['start_date'].replace('T', ' '))
            except:
                pass
    
        if st.session_state.config.get('end_date'):
            try:
                default_end = datetime.fromisoformat(st.session_state.config['end_date'].replace('T', ' '))
            except:
                pass
    
        with col1:
            start_date = st.date_input("Start Date", value=default_start)
            start_time = st.time_input("Start Time", value=default_start.time())
    
        with col2:
            end_date = st.date_input("End Date", value=default_end)
            end_time = st.time_input("End Time", value=default_end.time())
    
        st.divider()
        st.info("Continue to the next tab: **2. Location & ROI**")
    
    # ============================================================
    # Tab 2: Location & ROI
    # ============================================================
    with tab2:
        st.header("Region of Interest (ROI)")

        # Initialize DEM settings variables (will be set by widgets below)
        gsd = float(st.session_state.config.get('gsd', 10.0))
        gsd_ref = float(st.session_state.config.get('gsd_ref', 2.0))

        use_shapefile = st.checkbox(
            "Use custom shapefile for ROI",
            value=st.session_state.config.get('use_shp', True)
        )
    
        if use_shapefile:
            # Option to provide existing shapefile or draw new one
            shapefile_option = st.radio(
                "How to define ROI:",
                ["Draw on interactive map", "Use existing shapefile"],
                horizontal=True
            )
    
            if shapefile_option == "Use existing shapefile":
                st.markdown("### Select Existing Shapefile")

                # Create two columns: shapefile selection on left, DEM settings on right
                shapefile_col, settings_col = st.columns([2, 1])

                with shapefile_col:
                    # Shapefile browser
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        search_dir = st.text_input(
                            "Search directory:",
                            value="config/",
                            help="Directory to search for shapefiles (must be in a mounted volume)"
                        )

                    with col2:
                        # Find shapefiles in directory
                        found_shapefiles = find_shapefiles(search_dir)

                        if found_shapefiles:
                            # Create dropdown options
                            shapefile_options = ["[Type path manually]"] + [str(shp) for shp in found_shapefiles]

                            selected_shapefile = st.selectbox(
                                "Available shapefiles:",
                                options=shapefile_options,
                                help="Select from found shapefiles or choose to type manually"
                            )

                            # Auto-populate if user selected a file
                            if selected_shapefile != "[Type path manually]":
                                roi_shapefile = selected_shapefile
                                st.session_state['roi_validated'] = True
                                st.success(f"✓ Selected: `{roi_shapefile}`")
                            else:
                                # Manual path input only if user chooses to type manually
                                roi_shapefile = st.text_input(
                                    "Shapefile path:",
                                    value=st.session_state.config.get('roi_shapefile', ''),
                                    help="Path to .shp file (must be in a mounted volume: config/, shapefiles/, etc.)"
                                )
                                st.session_state['roi_validated'] = bool(roi_shapefile)
                        else:
                            st.info(f"ℹ️ No shapefiles found in `{search_dir}`. Enter path manually below.")
                            roi_shapefile = st.text_input(
                                "Shapefile path:",
                                value=st.session_state.config.get('roi_shapefile', ''),
                                help="Path to .shp file (must be in a mounted volume: config/, shapefiles/, etc.)"
                            )
                            st.session_state['roi_validated'] = bool(roi_shapefile)

                    # Info message about Docker volumes
                    st.caption("**Docker users**: Shapefiles must be in mounted volumes (e.g., `config/`, `shapefiles/`). See README for details.")

                with settings_col:
                    # DEM Settings
                    # st.markdown("#### DEM Settings")

                    gsd_ref = st.selectbox(
                        "Reference DEM Resolution",
                        [0.5, 2.0],
                        index=[0.5, 2.0].index(float(st.session_state.config.get('gsd_ref', 2.0))),
                        help="Source DEM resolution from Swisstopo"
                    )

                    gsd = st.number_input(
                        "Output Grid Spacing - meters",
                        value=max(float(st.session_state.config.get('gsd', 10.0)), gsd_ref),
                        min_value=gsd_ref,
                        max_value=100.0,
                        step=1.0,
                        help="Output resolution (smaller = higher resolution, longer processing). Must be >= reference DEM resolution."
                    )

                    mask_dem = st.checkbox(
                        "Mask DEM to polygon shape",
                        value=True,
                        help="If checked, DEM is cropped to polygon (values outside = nodata). "
                             "If unchecked, DEM covers entire bounding box with all valid values.",
                        key="mask_dem_checkbox_existing_shp"
                    )
                    st.session_state.config['mask_dem_to_polygon'] = mask_dem
            else:
                # Interactive map for drawing ROI
                st.markdown("### Draw ROI on Swiss Map")
                st.info("**Instructions**: Use the rectangle (□) or polygon (⬠) tool on the left side of the map to draw your ROI.")

                # Initialize roi_shapefile from session state
                roi_shapefile = st.session_state.config.get('roi_shapefile', '')

                # Create two columns: map on left, controls on right
                map_col, controls_col = st.columns([2, 1])

                with map_col:
                    # Show map
                    roi_map = create_roi_map()
                    map_output = st_folium(roi_map, width=600, height=500, key="roi_map")

                with controls_col:
                    st.markdown("#### Save ROI")

                    # Handle drawn polygon
                    if map_output and map_output.get('last_active_drawing'):
                        drawn_geom = map_output['last_active_drawing']

                        # Debug: Show what was captured
                        with st.expander("🔍 Debug", expanded=False):
                            st.json(drawn_geom)

                        # Validate polygon is within Swiss boundaries
                        is_valid, boundary_msg = check_polygon_in_swiss_boundaries(drawn_geom['geometry'])

                        if is_valid:
                            st.success("✅ Polygon drawn!")
                            st.caption(boundary_msg)

                            # Input for shapefile name
                            shapefile_name = st.text_input(
                                "Shapefile name",
                                value="roi_drawn",
                                help="Name for the shapefile (without .shp extension)"
                            )

                            save_button = st.button("Save ROI", type="primary", use_container_width=True)

                            if save_button and shapefile_name:
                                # Save shapefile
                                shapefile_dir = Path("config/shapefiles")
                                shapefile_path = shapefile_dir / f"{shapefile_name}.shp"

                                success, message = save_drawn_roi(drawn_geom, str(shapefile_path))
                                if success:
                                    st.success(message)
                                    roi_shapefile = str(shapefile_path)
                                    st.session_state.config['roi_shapefile'] = str(shapefile_path)
                                    # Mark ROI as validated (polygon was already validated above)
                                    st.session_state['roi_validated'] = True
                                else:
                                    st.error(message)
                                    st.session_state['roi_validated'] = False
                        else:
                            # Polygon outside boundaries - show error and prevent saving
                            st.error("🚫 Outside boundaries")
                            st.caption(boundary_msg)
                            st.session_state['roi_validated'] = False
                    else:
                        # Show warning if no polygon drawn yet
                        if not roi_shapefile:
                            st.warning("⚠️ No polygon drawn yet")

                    # DEM Settings (always visible)
                    st.divider()
                    st.markdown("#### DEM Settings")

                    gsd_ref = st.selectbox(
                        "Reference DEM Resolution",
                        [0.5, 2.0],
                        index=[0.5, 2.0].index(float(st.session_state.config.get('gsd_ref', 2.0))),
                        help="Source DEM resolution from Swisstopo"
                    )

                    gsd = st.number_input(
                        "Output Grid Spacing - meters",
                        value=max(float(st.session_state.config.get('gsd', 10.0)), gsd_ref),
                        min_value=gsd_ref,
                        max_value=100.0,
                        step=1.0,
                        help="Output resolution (smaller = higher resolution, longer processing). Must be >= reference DEM resolution."
                    )

                    mask_dem = st.checkbox(
                        "Mask DEM to polygon shape",
                        value=True,
                        help="If checked, DEM is cropped to polygon (values outside = nodata). "
                             "If unchecked, DEM covers entire bounding box with all valid values.",
                        key="mask_dem_checkbox"
                    )
                    st.session_state.config['mask_dem_to_polygon'] = mask_dem
        else:
            # Bounding box mode - need center point coordinates
            # Always mask DEM for bbox mode
            st.session_state.config['mask_dem_to_polygon'] = True
            st.markdown("### ROI Center Point")
    
            # Option to pick point on map or enter manually
            center_point_option = st.radio(
                "How to define center point:",
                ["⌨️ Enter coordinates manually", "Pick on map"],
                horizontal=True
            )
    
            if center_point_option == "Pick on map":
                st.info("**Instructions**: Click anywhere on the map to select the ROI center point.")
    
                # Create map for point selection
                center_map = folium.Map(
                    location=[46.8, 8.2],
                    zoom_start=8,
                    tiles=None
                )
    
                # Add Swisstopo base layer
                folium.raster_layers.WmsTileLayer(
                    url='https://wms.geo.admin.ch/',
                    layers='ch.swisstopo.pixelkarte-farbe',
                    fmt='image/png',
                    transparent=False,
                    name='Swisstopo Map',
                    overlay=False,
                    control=True,
                    attr='© swisstopo'
                ).add_to(center_map)
    
                # Add click listener for coordinates
                center_map.add_child(folium.LatLngPopup())
    
                # Display map and capture clicks
                center_map_output = st_folium(center_map, width=800, height=400, key="center_point_map")
    
                # Extract coordinates from map click
                if center_map_output and center_map_output.get('last_clicked'):
                    lat = center_map_output['last_clicked']['lat']
                    lon = center_map_output['last_clicked']['lng']
    
                    # Transform WGS84 to Swiss LV95
                    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
                    poi_x, poi_y = transformer.transform(lon, lat)
    
                    # Fetch elevation from Swisstopo Height API
                    try:
                        import requests
                        height_url = f"https://api3.geo.admin.ch/rest/services/height?easting={poi_x:.1f}&northing={poi_y:.1f}&sr=2056"
                        response = requests.get(height_url, timeout=5)
    
                        if response.status_code == 200:
                            height_data = response.json()
                            poi_z = float(height_data.get('height', 1500))
                            st.success(f"✅ Point selected: {poi_x:.1f}, {poi_y:.1f} | Elevation: {poi_z:.1f}m")
                        else:
                            # Fallback if API fails
                            poi_z = float(st.session_state.config.get('poi_z', 1500))
                            st.warning(f"⚠️ Point selected: {poi_x:.1f}, {poi_y:.1f} | Using default elevation (API unavailable)")
                    except Exception:
                        # Fallback if request fails
                        poi_z = float(st.session_state.config.get('poi_z', 1500))
                        st.success(f"✅ Point selected: {poi_x:.1f}, {poi_y:.1f} | Using default elevation")
                else:
                    # Use defaults
                    poi_x = float(st.session_state.config.get('poi_x', 645000))
                    poi_y = float(st.session_state.config.get('poi_y', 115000))
                    poi_z = float(st.session_state.config.get('poi_z', 1500))
    
                # Show coordinates (read-only display)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Easting (EPSG:2056)", f"{poi_x:.1f}")
                with col2:
                    st.metric("Northing (EPSG:2056)", f"{poi_y:.1f}")
    
                # Allow altitude adjustment
                poi_z = st.number_input(
                    "Altitude (m)",
                    value=float(poi_z),
                    format="%.1f",
                    help="Adjust altitude of center point if needed"
                )
    
            else:
                # Manual coordinate entry
                col1, col2, col3 = st.columns(3)
    
                with col1:
                    poi_x = st.number_input(
                        "Easting (EPSG:2056 or CH1903)",
                        value=float(st.session_state.config.get('poi_x', 645000)),
                        format="%.1f",
                        help="X coordinate of ROI center (auto-converts CH1903 to EPSG:2056)"
                    )
    
                with col2:
                    poi_y = st.number_input(
                        "Northing (EPSG:2056 or CH1903)",
                        value=float(st.session_state.config.get('poi_y', 115000)),
                        format="%.1f",
                        help="Y coordinate of ROI center (auto-converts CH1903 to EPSG:2056)"
                    )
    
                with col3:
                    poi_z = st.number_input(
                        "Altitude (m)",
                        value=float(st.session_state.config.get('poi_z', 1500)),
                        format="%.1f",
                        help="Altitude of ROI center point"
                    )
    
            # ROI size (applies to both map and manual entry)
            roi_size = st.number_input(
                "ROI Size (meters)",
                value=int(st.session_state.config.get('roi_size', 1000)),
                min_value=100,
                max_value=50000,
                step=100,
                help="Size of bounding box around center point"
            )
    
            # Validate ROI is within Swiss boundaries
            is_valid, boundary_msg = check_swiss_boundaries(poi_x, poi_y, roi_size)
    
            if is_valid:
                st.success(boundary_msg)
                st.session_state['roi_validated'] = True
            else:
                st.error(boundary_msg)
                st.warning("⚠️ Please adjust the center point or reduce the ROI size to fit within Switzerland.")
                st.session_state['roi_validated'] = False

        # When using shapefile, POI is derived from ROI center (no manual input needed)
        if use_shapefile:
            # Set default POI values (will be overridden by backend from shapefile)
            poi_x = float(st.session_state.config.get('poi_x', 645000))
            poi_y = float(st.session_state.config.get('poi_y', 115000))
            poi_z = float(st.session_state.config.get('poi_z', 1500))
        else:
            # DEM settings for bbox mode (shapefile mode has them in right column)
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                gsd_ref = st.selectbox(
                    "Reference DEM Resolution",
                    [0.5, 2.0],
                    index=[0.5, 2.0].index(float(st.session_state.config.get('gsd_ref', 2.0))),
                    help="Source DEM resolution from Swisstopo"
                )

            with col2:
                gsd = st.number_input(
                    "Output Grid Spacing - meters",
                    value=max(float(st.session_state.config.get('gsd', 10.0)), gsd_ref),
                    min_value=gsd_ref,
                    max_value=100.0,
                    step=1.0,
                    help="Output resolution (smaller = higher resolution, longer processing). Must be >= reference DEM resolution."
                )

        st.divider()
        st.info("Continue to the next tab: **3. Landcover**")
    
    # ============================================================
    # Tab 3: Landcover
    # ============================================================
    with tab3:
        st.header("Land Use")

        use_lus_tlm = st.checkbox(
            "Use SwissTLMRegio for land use",
            value=True,
            help="Automatically download and process Swiss topographic land use data from Swisstopo. "
                 "Supports 11 TLM categories (Forest, Rock, Scree, Glacier, Lake, Settlement, Wetland, Orchard, Vineyard, etc.)"
        )

        lus_constant = st.number_input(
            "Constant Land Use Value",
            value=int(st.session_state.config.get('lus_cst', 11500)),
            help="Single PREVAH land use code (format: 1LLCD where LL is PREVAH code). Used when TLMregio is disabled.",
            disabled=use_lus_tlm
        )

        st.divider()
        st.info("Continue to the next tab: **4. Meteo**")

    # ============================================================
    # Tab 4: Meteo Settings
    # ============================================================
    with tab4:
        st.header("Meteorological Settings")

        buffer_size = st.number_input(
            "Buffer Size for IMIS Stations (meters)",
            value=int(st.session_state.config.get('buffer_size', 10000)),
            min_value=1000,
            max_value=200000,
            step=1000,
            help="Distance to search for meteorological stations around the ROI"
        )

        skip_snowpack = st.checkbox("Skip Snowpack preprocessing", value=False)

        # VPN warning if Snowpack preprocessing is enabled
        if not skip_snowpack:
            st.warning("⚠️ **SLF/WSL VPN Required**: Snowpack preprocessing requires VPN access to the IMIS database via MeteoIO.")

        st.divider()
        st.info("Continue to the next tab: **5. Run ▶️**")

    # ============================================================
    # Tab 5: Run tool
    # ============================================================
    with tab5:
        st.header("Configuration Summary")
    
        # Build start/end datetime strings
        start_dt = datetime.combine(start_date, start_time)
        end_dt = datetime.combine(end_date, end_time)
    
        # Summary display
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Simulation Name", simu_name)
            st.metric("Period", f"{(end_dt - start_dt).days} days")
            st.metric("Coordinate System", coord_sys)
            st.metric("Grid Spacing", f"{gsd}m")

        with col2:
            if use_shapefile:
                st.metric("ROI", "Custom Shapefile/Polygon")
            else:
                st.metric("ROI", f"{roi_size}m bbox")

            # Land use option
            if use_lus_tlm:
                st.metric("Land Use", "SwissTLMRegio")
            else:
                st.metric("Land Use", f"Constant ({lus_constant})")

            # DEM masking option (only show if using shapefile)
            if use_shapefile:
                mask_status = st.session_state.config.get('mask_dem_to_polygon', True)
                st.metric("DEM Masking", "Polygon" if mask_status else "Full BBox")
    
        st.divider()
    
        # Save config section
        col1, col2 = st.columns([3, 1])
    
        with col1:
            save_config_name = st.text_input(
                "Config filename (without .ini)",
                value=simu_name if simu_name else "my_simulation",
                help="Name for saving this A3Dshell configuration"
            )
    
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            save_button = st.button("Save Config", use_container_width=True)
    
        if save_button:
            if not save_config_name:
                st.error("Please provide a config filename")
            else:
                # Create config file
                config_content = f"""# A3Dshell Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[GENERAL]
SIMULATION_NAME = {simu_name}
START_DATE = {start_dt.strftime('%Y-%m-%dT%H:%M:%S')}
END_DATE = {end_dt.strftime('%Y-%m-%dT%H:%M:%S')}

[INPUT]
EAST_epsg2056 = {poi_x}
NORTH_epsg2056 = {poi_y}
altLV95 = {poi_z}
USE_SHP_ROI = {'true' if use_shapefile else 'false'}
"""
    
                if use_shapefile:
                    config_content += f"ROI_SHAPEFILE = {roi_shapefile}\n"
                else:
                    config_content += f"ROI = {roi_size}\n"

                config_content += f"BUFFERSIZE = {buffer_size}\n"
                config_content += f"\n[OUTPUT]\n"
                config_content += f"OUT_COORDSYS = {coord_sys}\n"
                config_content += f"GSD = {gsd}\n"
                config_content += f"GSD_ref = {gsd_ref}\n"
                config_content += f"DEM_ADDFMTLIST =\n"
                config_content += f"MESH_FMT = vtu\n"
                config_content += f"MASK_DEM_TO_POLYGON = {'true' if st.session_state.config.get('mask_dem_to_polygon', True) else 'false'}\n"
                config_content += f"\n[MAPS]\n"
                config_content += f"PLOT_HORIZON = false\n"
                config_content += f"\n[A3D]\n"
                config_content += f"USE_GROUNDEYE = false\n"
                config_content += f"USE_LUS_TLM = {'true' if use_lus_tlm else 'false'}\n"
    
                if not use_lus_tlm:
                    config_content += f"LUS_PREVAH_CST = {lus_constant}\n"

                config_content += "DO_PVP_3D = false\n"
                config_content += "PVP_3D_FMT = vtu\n"
                config_content += "SP_BIN_PATH = snowpack\n"
    
                # Save file
                config_path = config_dir / f"{save_config_name}.ini"
                with open(config_path, 'w') as f:
                    f.write(config_content)
    
                st.success(f"✅ Configuration saved to: {config_path}")
    
        st.divider()

        # Run simulation section
        st.header("Run Setup")

        col1, col2 = st.columns([2, 1])

        with col1:
            log_level = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
    
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
    
        # Check if ROI is validated
        roi_validated = st.session_state.get('roi_validated', False)
    
        # Show validation status
        if not roi_validated:
            st.error("🚫 Cannot run simulation: ROI/POI must be confirmed within Swiss boundaries")
            st.info("💡 Go to the **Location & ROI** tab to configure and validate your region of interest.")
    
        # Disable button if validation failed
        if st.button("▶️ Start Run", type="primary", use_container_width=True, disabled=not roi_validated):
            if not simu_name:
                st.error("Please provide a simulation name")
            else:
                # Create a temporary config for this run
                temp_config = config_dir / f"_temp_{simu_name}.ini"
    
                config_content = f"""# Temporary A3Dshell Configuration
    [GENERAL]
    SIMULATION_NAME = {simu_name}
    START_DATE = {start_dt.strftime('%Y-%m-%dT%H:%M:%S')}
    END_DATE = {end_dt.strftime('%Y-%m-%dT%H:%M:%S')}
    
    [INPUT]
    EAST_epsg2056 = {poi_x}
    NORTH_epsg2056 = {poi_y}
    altLV95 = {poi_z}
    USE_SHP_ROI = {'true' if use_shapefile else 'false'}
    """
    
                if use_shapefile:
                    config_content += f"ROI_SHAPEFILE = {roi_shapefile}\n"
                else:
                    config_content += f"ROI = {roi_size}\n"

                config_content += f"BUFFERSIZE = {buffer_size}\n"
                config_content += f"\n[OUTPUT]\n"
                config_content += f"OUT_COORDSYS = {coord_sys}\n"
                config_content += f"GSD = {gsd}\n"
                config_content += f"GSD_ref = {gsd_ref}\n"
                config_content += f"DEM_ADDFMTLIST =\n"
                config_content += f"MESH_FMT = vtu\n"
                config_content += f"MASK_DEM_TO_POLYGON = {'true' if st.session_state.config.get('mask_dem_to_polygon', True) else 'false'}\n"
                config_content += f"\n[MAPS]\n"
                config_content += f"PLOT_HORIZON = false\n"
                config_content += f"\n[A3D]\n"
                config_content += f"USE_GROUNDEYE = false\n"
                config_content += f"USE_LUS_TLM = {'true' if use_lus_tlm else 'false'}\n"
    
                if not use_lus_tlm:
                    config_content += f"LUS_PREVAH_CST = {lus_constant}\n"

                config_content += "DO_PVP_3D = false\n"
                config_content += "PVP_3D_FMT = vtu\n"
                config_content += "SP_BIN_PATH = snowpack\n"
    
                # Save temp config
                with open(temp_config, 'w') as f:
                    f.write(config_content)
    
                # Build command
                cmd = [
                    "python", "-m", "src.cli",
                    "--config", str(temp_config),
                    "--log-level", log_level
                ]
    
                if skip_snowpack:
                    cmd.append("--skip-snowpack")
    
                st.info(f"🚀 Starting simulation: {simu_name}")
                st.code(" ".join(cmd), language="bash")
    
                # Run simulation
                with st.spinner("Running simulation... (this may take several minutes)"):
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=3600  # 1 hour timeout
                        )
    
                        # Display output
                        st.subheader("Output")
                        st.text_area("Run Log", value=result.stdout, height=400)
    
                        if result.returncode == 0:
                            st.success("✅ Run completed successfully!")
                            st.snow()
    
                            # Show output location
                            output_dir = Path("output") / simu_name
                            if output_dir.exists():
                                st.info(f"📁 Output location: {output_dir}")
                        else:
                            st.error(f"❌ Run failed with exit code {result.returncode}")
                            if result.stderr:
                                st.error("Error output:")
                                st.code(result.stderr)
    
                    except subprocess.TimeoutExpired:
                        st.error("⏱️ Run timed out (> 1 hour)")
                    except Exception as e:
                        st.error(f"❌ Error running simulation: {str(e)}")
    
                    finally:
                        # Clean up temp config
                        if temp_config.exists():
                            temp_config.unlink()

# ============================================================
# OTHER LOCATIONS MODE
# ============================================================
with mode_tab_other:
    st.info("ℹ️ **Other Locations Mode**: Provide your own DEM (GeoTIFF), define POIs, and manage land use. Meteorological data must be provided manually.")

    # Tabs for Other Locations mode
    tab1_other, tab2_other, tab3_other, tab4_other = st.tabs(["1.General", "2.Location & DEM", "3.POIs & Output", "4.Run ▶️"])

    # ============================================================
    # Tab 1: General Settings (Other Locations)
    # ============================================================
    with tab1_other:
        st.header("General Settings")

        simu_name_other = st.text_input(
            "Simulation Name",
            value=st.session_state.config.get('simu_name', ''),
            help="Unique name for this simulation (no spaces)",
            key="simu_name_other"
        )

        st.divider()
        st.info("Continue to the next tab: **2. Location & DEM**")

    # ============================================================
    # Tab 2: Location & DEM (Other Locations)
    # ============================================================
    with tab2_other:
        st.header("Location & DEM Setup")

        st.subheader("Target Coordinate System")
        target_epsg = st.number_input(
            "EPSG Code",
            value=int(st.session_state.config.get('target_epsg', 32632)),
            min_value=1000,
            max_value=99999,
            help="EPSG code for your target coordinate system (e.g., 32632 for UTM Zone 32N)"
        )

        st.subheader("DEM Selection")
        st.markdown("Select your Digital Elevation Model (GeoTIFF) from the `config/dem/` directory")
        st.caption("💡 **Docker users**: Place your DEM files in `config/dem/` (mounted volume)")

        # Browse for DEM files in config/dem/
        dem_dir = Path("config/dem")
        dem_files = list(dem_dir.glob("*.tif")) + list(dem_dir.glob("*.tiff"))

        if dem_files:
            dem_options = ["[Select a DEM file]"] + [dem.name for dem in dem_files]
            selected_dem = st.selectbox(
                "Available DEM files:",
                options=dem_options,
                help="GeoTIFF files found in config/dem/"
            )

            if selected_dem != "[Select a DEM file]":
                dem_path = dem_dir / selected_dem
                st.success(f"✅ DEM selected: {selected_dem}")
                st.session_state.config['user_dem_path'] = str(dem_path.absolute())

                # Show file info
                file_size_mb = dem_path.stat().st_size / (1024 * 1024)
                st.info(f"📊 File size: {file_size_mb:.2f} MB")
            else:
                st.session_state.config['user_dem_path'] = None
        else:
            st.warning("⚠️ No DEM files found in `config/dem/`")
            st.info("Place your GeoTIFF (.tif) DEM files in the `config/dem/` directory")
            st.session_state.config['user_dem_path'] = None

        st.divider()
        st.info("👉 Continue to the next tab: **3. POIs & Output**")

    # ============================================================
    # Tab 3: POIs & Output (Other Locations)
    # ============================================================
    with tab3_other:
        st.header("Points of Interest (POIs) - Optional")

        st.markdown("**Optional**: Define your Points of Interest for simulation. These will be written to the POI SMET file.")
        st.info("💡 You can skip adding POIs if you just want to generate the setup folder and DEM processing.")

        # Initialize POI list in session state
        if 'poi_list' not in st.session_state:
            st.session_state.poi_list = []

        # POI input form
        with st.form("add_poi_form"):
            st.subheader("Add New POI")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                poi_name = st.text_input("POI Name", value="", placeholder="e.g., Station1")
            with col2:
                poi_x_new = st.number_input(f"Easting (EPSG:{target_epsg})", value=0.0, format="%.2f")
            with col3:
                poi_y_new = st.number_input(f"Northing (EPSG:{target_epsg})", value=0.0, format="%.2f")
            with col4:
                poi_z_new = st.number_input("Elevation (m)", value=0.0, format="%.2f")

            add_button = st.form_submit_button("➕ Add POI")

            if add_button and poi_name:
                st.session_state.poi_list.append({
                    'name': poi_name,
                    'x': poi_x_new,
                    'y': poi_y_new,
                    'z': poi_z_new
                })
                st.success(f"✅ Added POI: {poi_name}")

        # Display current POIs
        if st.session_state.poi_list:
            st.subheader("Current POIs")
            for idx, poi in enumerate(st.session_state.poi_list):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"{poi['name']}: ({poi['x']:.2f}, {poi['y']:.2f}, {poi['z']:.2f})")
                with col2:
                    if st.button("🗑️ Remove", key=f"remove_poi_{idx}"):
                        st.session_state.poi_list.pop(idx)
                        st.rerun()
        else:
            st.info("ℹ️ No POIs added yet. This is optional - you can proceed without POIs.")

        st.divider()

        st.subheader("Land Use")
        use_lus_tlm_other = st.checkbox(
            "Use TLM land use data",
            value=st.session_state.config.get('use_lus_tlm', False),
            disabled=True,
            help="Automatic download of Swiss topographic land use data - not available for other locations",
            key="use_lus_tlm_other"
        )

        lus_constant_other = st.number_input(
            "Constant Land Use Value",
            value=int(st.session_state.config.get('lus_cst', 11500)),
            help="Single PREVAH land use code (format: 1LLCD where LL is PREVAH code)",
            key="lus_constant_other"
        )

        st.divider()
        st.info("Continue to the next tab: **4. Run ▶️**")

    # ============================================================
    # Tab 4: Run (Other Locations)
    # ============================================================
    with tab4_other:
        st.header("Setup & Run")

        st.warning("⚠️ **Meteorological Data Required**: After setup completes, you must manually add your SMET meteorological files to `output/{simulation_name}/input/meteo/`")

        # Save config button
        st.subheader("Save Configuration")
        col1, col2 = st.columns([3, 1])

        with col1:
            save_config_name_other = st.text_input(
                "Config Filename (without .ini)",
                value=simu_name_other if simu_name_other else "",
                key="save_config_name_other"
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            save_button_other = st.button("💾 Save Config", type="secondary", use_container_width=True, key="save_button_other")

        if save_button_other:
            if not save_config_name_other:
                st.error("Please provide a config filename")
            else:
                # Create config file for Other Locations mode
                config_content = f"""# A3Dshell Configuration - Other Locations Mode
# Generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}

[GENERAL]
SIMULATION_NAME = {simu_name_other}

[INPUT]
DEM_MODE = user_provided
USER_DEM_PATH = {st.session_state.config.get('user_dem_path', '')}
TARGET_EPSG = {target_epsg}
"""
                config_content += "\n[OUTPUT]\n"
                config_content += f"OUT_COORDSYS = EPSG:{target_epsg}\n"
                config_content += "DEM_ADDFMTLIST =\n"
                config_content += "MESH_FMT = vtu\n"
                config_content += "\n[MAPS]\n"
                config_content += "PLOT_HORIZON = false\n"
                config_content += "\n[A3D]\n"
                config_content += "USE_GROUNDEYE = false\n"
                config_content += "USE_LUS_TLM = false\n"
                config_content += f"LUS_PREVAH_CST = {lus_constant_other}\n"
                config_content += "DO_PVP_3D = false\n"
                config_content += "PVP_3D_FMT = vtu\n"
                config_content += "SP_BIN_PATH = input/bin/snowpack\n"

                # Save POIs to config
                if st.session_state.poi_list:
                    config_content += "\n[POIS]\n"
                    for poi in st.session_state.poi_list:
                        config_content += f"{poi['name']} = {poi['x']},{poi['y']},{poi['z']}\n"

                # Save file
                config_dir = Path("config")
                config_path = config_dir / f"{save_config_name_other}.ini"
                with open(config_path, 'w') as f:
                    f.write(config_content)

                st.success(f"✅ Configuration saved to: {config_path}")

        st.divider()

        # Run simulation section
        st.subheader("Run Setup")

        log_level_other = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"], key="log_level_other")

        if st.button("▶️ Start Run", type="primary", use_container_width=True, key="run_button_other"):
            if not simu_name_other:
                st.error("Please provide a simulation name")
            elif not st.session_state.config.get('user_dem_path'):
                st.error("Please select a DEM file")
            else:
                # Create temporary config for this run
                temp_config = Path("config") / f"_temp_{simu_name_other}.ini"

                config_content = f"""# Temporary A3Dshell Configuration - Other Locations
[GENERAL]
SIMULATION_NAME = {simu_name_other}

[INPUT]
DEM_MODE = user_provided
USER_DEM_PATH = {st.session_state.config.get('user_dem_path', '')}
TARGET_EPSG = {target_epsg}
"""

                config_content += "\n[OUTPUT]\n"
                config_content += f"OUT_COORDSYS = EPSG:{target_epsg}\n"
                config_content += "DEM_ADDFMTLIST =\n"
                config_content += "MESH_FMT = vtu\n"
                config_content += "\n[MAPS]\n"
                config_content += "PLOT_HORIZON = false\n"
                config_content += "\n[A3D]\n"
                config_content += "USE_GROUNDEYE = false\n"
                config_content += "USE_LUS_TLM = false\n"
                config_content += f"LUS_PREVAH_CST = {lus_constant_other}\n"
                config_content += "DO_PVP_3D = false\n"
                config_content += "PVP_3D_FMT = vtu\n"
                config_content += "SP_BIN_PATH = input/bin/snowpack\n"

                # Add POIs
                if st.session_state.poi_list:
                    config_content += "\n[POIS]\n"
                    for poi in st.session_state.poi_list:
                        config_content += f"{poi['name']} = {poi['x']},{poi['y']},{poi['z']}\n"

                with open(temp_config, 'w') as f:
                    f.write(config_content)

                # Run command (no Snowpack preprocessing for Other Locations)
                cmd = [
                    "python", "-m", "src.cli",
                    "--config", str(temp_config),
                    "--log-level", log_level_other,
                    "--skip-snowpack"  # Always skip Snowpack for Other Locations
                ]

                with st.spinner("⏳ Running setup... This may take a few minutes"):
                    try:
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1
                        )

                        log_placeholder = st.empty()
                        full_log = []

                        for line in process.stdout:
                            full_log.append(line)
                            log_placeholder.code('\n'.join(full_log[-50:]))  # Show last 50 lines

                        process.wait()

                        if process.returncode == 0:
                            st.success("✅ Setup completed successfully!")
                            st.info(f"📁 **Next Steps**: Add your SMET meteorological files to `output/{simu_name_other}/input/meteo/`")
                        else:
                            st.error(f"❌ Setup failed with exit code {process.returncode}")

                    except Exception as e:
                        st.error(f"❌ Error running setup: {str(e)}")

                    finally:
                        # Clean up temp config
                        if temp_config.exists():
                            temp_config.unlink()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p style='margin-bottom: 5px;'><strong>A3Dshell</strong> </p>
    <p style='margin: 5px 0;'>
        <a href='https://github.com/frischwood/A3Dshell' target='_blank' style='color: #0366d6; text-decoration: none;'>
            GitHub Repository
        </a>
        &nbsp;|&nbsp;
        <a href='https://github.com/frischwood/A3Dshell/blob/main/LICENSE' target='_blank' style='color: #0366d6; text-decoration: none;'>
            MIT License
        </a>
    </p>
    <p style='margin-top: 5px; font-size: 0.85em;'>
        © 2025 A3Dshell Contributors | Open Source Software
    </p>
</div>
""", unsafe_allow_html=True)
