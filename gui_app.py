"""
A3DShell refactored_v2 - Simple GUI
====================================

A Streamlit-based GUI for configuring and running A3DShell simulations.

Run with: streamlit run gui_app.py
"""

import streamlit as st
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
import configparser
import os

# Page configuration
st.set_page_config(
    page_title="A3DShell Simulation Setup",
    page_icon="🏔️",
    layout="wide"
)

# Title
st.title("🏔️ A3DShell Simulation Setup")
st.markdown("Configure and run Alpine3D simulation setups")

# Sidebar for existing configs
st.sidebar.header("📁 Load Existing Config")
config_dir = Path("config")
existing_configs = list(config_dir.glob("*.ini"))
config_names = ["Create New"] + [c.name for c in existing_configs]

selected_config = st.sidebar.selectbox(
    "Select configuration:",
    config_names
)

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = {}

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

# Tabs for configuration sections
tab1, tab2, tab3, tab4 = st.tabs(["📋 General", "📍 Location & ROI", "🗺️ Output", "▶️ Run"])

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

# ============================================================
# Tab 2: Location & ROI
# ============================================================
with tab2:
    st.header("Point of Interest (POI)")

    col1, col2, col3 = st.columns(3)

    with col1:
        poi_x = st.number_input(
            "Easting (EPSG:2056 or CH1903)",
            value=float(st.session_state.config.get('poi_x', 645000)),
            format="%.1f",
            help="X coordinate (auto-converts CH1903 to EPSG:2056)"
        )

    with col2:
        poi_y = st.number_input(
            "Northing (EPSG:2056 or CH1903)",
            value=float(st.session_state.config.get('poi_y', 115000)),
            format="%.1f",
            help="Y coordinate (auto-converts CH1903 to EPSG:2056)"
        )

    with col3:
        poi_z = st.number_input(
            "Altitude (m)",
            value=float(st.session_state.config.get('poi_z', 1500)),
            format="%.1f"
        )

    st.divider()
    st.header("Region of Interest (ROI)")

    use_shapefile = st.checkbox(
        "Use custom shapefile for ROI",
        value=st.session_state.config.get('use_shp', False)
    )

    if use_shapefile:
        roi_shapefile = st.text_input(
            "Shapefile Path",
            value=st.session_state.config.get('roi_shapefile', ''),
            help="Absolute or relative path to .shp file or .zip archive"
        )
    else:
        roi_size = st.number_input(
            "ROI Size (meters)",
            value=int(st.session_state.config.get('roi_size', 1000)),
            min_value=100,
            max_value=50000,
            step=100,
            help="Size of bounding box around POI"
        )

    buffer_size = st.number_input(
        "Buffer Size for IMIS Stations (meters)",
        value=int(st.session_state.config.get('buffer_size', 50000)),
        min_value=1000,
        max_value=200000,
        step=1000,
        help="Distance to search for meteorological stations"
    )

# ============================================================
# Tab 3: Output Settings
# ============================================================
with tab3:
    st.header("Output Settings")

    col1, col2 = st.columns(2)

    with col1:
        gsd = st.number_input(
            "Grid Spacing (GSD) - meters",
            value=float(st.session_state.config.get('gsd', 10.0)),
            min_value=1.0,
            max_value=100.0,
            step=1.0,
            help="Output resolution (smaller = higher resolution, longer processing)"
        )

    with col2:
        gsd_ref = st.selectbox(
            "Reference DEM Resolution",
            [0.5, 2.0],
            index=[0.5, 2.0].index(float(st.session_state.config.get('gsd_ref', 2.0))),
            help="Source DEM resolution from Swisstopo"
        )

    st.divider()
    st.header("Land Use")

    st.info("ℹ️ SwissTLMRegio integration is a future feature. Currently, only constant land use values are supported.")

    use_lus_tlm = st.checkbox(
        "Use SwissTLMRegio for land use (Coming Soon)",
        value=False,
        disabled=True,
        help="Automatic download of Swiss topographic land use data - not yet implemented"
    )

    lus_constant = st.number_input(
        "Constant Land Use Value",
        value=int(st.session_state.config.get('lus_cst', 11500)),
        help="Single PREVAH land use code (format: 1LLCD where LL is PREVAH code)"
    )

# ============================================================
# Tab 4: Run Simulation
# ============================================================
with tab4:
    st.header("Configuration Summary")

    # Build start/end datetime strings
    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    # Summary display
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Simulation Name", simu_name)
        st.metric("Period", f"{(end_dt - start_dt).days} days")
        st.metric("POI", f"{poi_x:.0f}E, {poi_y:.0f}N, {poi_z:.0f}m")

    with col2:
        st.metric("Coordinate System", coord_sys)
        st.metric("Grid Spacing", f"{gsd}m")
        if use_shapefile:
            st.metric("ROI", "Custom Shapefile")
        else:
            st.metric("ROI", f"{roi_size}m bbox")

    st.divider()

    # Save config section
    col1, col2 = st.columns([3, 1])

    with col1:
        save_config_name = st.text_input(
            "Config filename (without .ini)",
            value=simu_name if simu_name else "my_simulation",
            help="Name for saving this configuration"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        save_button = st.button("💾 Save Config", use_container_width=True)

    if save_button:
        if not save_config_name:
            st.error("Please provide a config filename")
        else:
            # Create config file
            config_content = f"""# A3DShell Configuration
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

            config_content += f"""BUFFERSIZE = {buffer_size}

[OUTPUT]
OUT_COORDSYS = {coord_sys}
GSD = {gsd}
GSD_ref = {gsd_ref}
DEM_ADDFMTLIST =
MESH_FMT = vtu

[MAPS]
PLOT_HORIZON = false

[A3D]
USE_GROUNDEYE = false
USE_LUS_TLM = {'true' if use_lus_tlm else 'false'}
"""

            if not use_lus_tlm:
                config_content += f"LUS_PREVAH_CST = {lus_constant}\n"

            config_content += """DO_PVP_3D = false
PVP_3D_FMT = vtu
SP_BIN_PATH = input/bin/snowpack
"""

            # Save file
            config_path = config_dir / f"{save_config_name}.ini"
            with open(config_path, 'w') as f:
                f.write(config_content)

            st.success(f"✅ Configuration saved to: {config_path}")

    st.divider()

    # Run simulation section
    st.header("Run Simulation")

    col1, col2 = st.columns([2, 1])

    with col1:
        skip_snowpack = st.checkbox("Skip Snowpack preprocessing", value=False)
        log_level = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing

    if st.button("▶️ Start Simulation", type="primary", use_container_width=True):
        if not simu_name:
            st.error("Please provide a simulation name")
        else:
            # Create a temporary config for this run
            temp_config = config_dir / f"_temp_{simu_name}.ini"

            config_content = f"""# Temporary A3DShell Configuration
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

            config_content += f"""BUFFERSIZE = {buffer_size}

[OUTPUT]
OUT_COORDSYS = {coord_sys}
GSD = {gsd}
GSD_ref = {gsd_ref}
DEM_ADDFMTLIST =
MESH_FMT = vtu

[MAPS]
PLOT_HORIZON = false

[A3D]
USE_GROUNDEYE = false
USE_LUS_TLM = {'true' if use_lus_tlm else 'false'}
"""

            if not use_lus_tlm:
                config_content += f"LUS_PREVAH_CST = {lus_constant}\n"

            config_content += """DO_PVP_3D = false
PVP_3D_FMT = vtu
SP_BIN_PATH = input/bin/snowpack
"""

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
                    st.text_area("Simulation Log", value=result.stdout, height=400)

                    if result.returncode == 0:
                        st.success("✅ Simulation completed successfully!")
                        st.balloons()

                        # Show output location
                        output_dir = Path("output") / simu_name
                        if output_dir.exists():
                            st.info(f"📁 Output location: {output_dir}")
                    else:
                        st.error(f"❌ Simulation failed with exit code {result.returncode}")
                        if result.stderr:
                            st.error("Error output:")
                            st.code(result.stderr)

                except subprocess.TimeoutExpired:
                    st.error("⏱️ Simulation timed out (> 1 hour)")
                except Exception as e:
                    st.error(f"❌ Error running simulation: {str(e)}")

                finally:
                    # Clean up temp config
                    if temp_config.exists():
                        temp_config.unlink()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
A3DShell refactored_v2 | Alpine3D Simulation Setup Tool
</div>
""", unsafe_allow_html=True)
