"""
Embedded template constants for A3Dshell web-hosted frontend.

All templates are embedded as Python string constants to eliminate external file
dependencies. Templates can be overridden by placing files in input/templates/.
"""

from pathlib import Path
from typing import Optional

# =============================================================================
# Snowpack Configuration Template
# =============================================================================

SNOWPACK_INI_TEMPLATE = """[Input]
COORDSYS = CH1903+
TIME_ZONE = 1


METEO = DBO
DBO_URL = https://pgdata.int.slf.ch
DBO_DEBUG = True
; METEO = IMIS
; DBNAME          = sdbo.wd.op
; DBUSER          = snowpack_app
; DBPASS          = Plouf_Plouf
; USE_CONNECTION_STRING = TRUE
; DBPORT = 1521
; DBSID = sdbo
METEOPATH = ./input/meteo

SNOWPATH	=	.tmp/input/snowfiles
SNOW	=	SMET

USE_IMIS_PSUM=TRUE
USE_SNOWPACK_PSUM=TRUE

; RESAMPLING_STRATEGY =
; VSTATION1 =
; Virtual_parameters =
; VSTATIONS_REFRESH_RATE =
; VSTATIONS_REFRESH_OFFSET =
[INPUTEDITING]
*::KEEP = HS TA RH PSUM ISWR RSWR ILWR VW DW


[Output]
EXPERIMENT = test
COORDSYS = CH1903+
TIME_ZONE = 1

METEO = SMET
METEOPATH = ./output/meteo

SNOW_WRITE = TRUE
SNOW	=	SMET
SNOWPATH	= ./output/snowfiles
SNOW_DAYS_BETWEEN = 365
BACKUP_DAYS_BETWEEN	=	365
FIRST_BACKUP	=	365

PROF_WRITE	=	TRUE
PROFILE_FORMAT	=	PRO
PROF_START	=	0.0
PROF_DAYS_BETWEEN	=	1
HARDNESS_IN_NEWTON	=	FALSE
CLASSIFY_PROFILE	=	FALSE

TS_WRITE	=	TRUE
TS_START	=	0.0
TS_DAYS_BETWEEN		= 0.04166
TS_FORMAT = SMET

AVGSUM_TIME_SERIES	=	TRUE
CUMSUM_MASS	=	FALSE
PRECIP_RATES	=	FALSE
OUT_CANOPY	=	FALSE
OUT_HAZ	=	FALSE
OUT_HEAT	=	TRUE
OUT_T	=	TRUE
OUT_LW	=	TRUE
OUT_SW	=	TRUE
OUT_MASS	=	TRUE
OUT_METEO	=	TRUE
OUT_STAB	=	FALSE

#GRID2D =
#GRID2DPATH =

[SNOWPACK]
CALCULATION_STEP_LENGTH	=	15
ROUGHNESS_LENGTH	=	0.002
HEIGHT_OF_METEO_VALUES	=	4.5
HEIGHT_OF_WIND_VALUE	=	4.5
ENFORCE_MEASURED_SNOW_HEIGHTS	=	True
SW_MODE	=	REFLECTED
ATMOSPHERIC_STABILITY	=	MO_MICHLMAYR
CANOPY	=	False
MEAS_TSS	=	FALSE
CHANGE_BC	=	False
THRESH_CHANGE_BC = -1.2
SNP_SOIL	=	TRUE
SOIL_FLUX	=	TRUE
GEO_HEAT	=	0.06
GLACIER_KATABATIC_FLOW	=	FALSE


[SNOWPACKADVANCED]
ASSUME_RESPONSIBILITY	=	AGREE
VARIANT	=	DEFAULT
SNOW_EROSION	=	TRUE
WIND_SCALING_FACTOR	=	1.0
NUMBER_SLOPES	=	1
PERP_TO_SLOPE	=	FALSE
FORCE_RH_WATER	=	TRUE
THRESH_RAIN	=	1.2
THRESH_RH	=	0.5
THRESH_DTEMP_AIR_SNOW	=	3.0
HOAR_THRESH_RH	=	0.97
HOAR_THRESH_VW	=	3.5
HOAR_DENSITY_BURIED	=125.0
HOAR_MIN_SIZE_BURIED	=	2.0
HOAR_DENSITY_SURF	=	100.0
MIN_DEPTH_SUBSURF	=	0.07
T_CRAZY_MIN	=	210.0
T_CRAZY_MAX	=	340.0
METAMORPHISM_MODEL	=	DEFAULT
NEW_SNOW_GRAIN_SIZE	=	0.3
HN_DENSITY	=	PARAMETERIZED
HN_DENSITY_PARAMETERIZATION	=	LEHNING_NEW
STRENGTH_MODEL	=	DEFAULT
VISCOSITY_MODEL	=	DEFAULT
SALTATION_MODEL	=	SORENSEN
WATERTRANSPORTMODEL_SNOW	=	BUCKET
WATERTRANSPORTMODEL_SOIL	=	BUCKET
SW_ABSORPTION_SCHEME	=	MULTI_BAND
HARDNESS_PARAMETERIZATION	=	MONTI
DETECT_GRASS	=	FALSE
PLASTIC	=	FALSE
JAM	=	FALSE
WATER_LAYER	=	FALSE
HEIGHT_NEW_ELEM	=	0.02
MINIMUM_L_ELEMENT	=	0.0025
COMBINE_ELEMENTS	=	TRUE
ADVECTIVE_HEAT	=	FALSE

[Filters]
PSUM::filter1 = min
PSUM::arg1::soft = true
PSUM::arg1::min = 0.0

TA::filter1 = min_max
TA::arg1::min = 240
TA::arg1::max = 320

RH::filter1 = min_max
RH::arg1::min = 0.01
RH::arg1::max = 1.2
RH::filter2 = min_max
RH::arg2::soft = true
RH::arg2::min = 0.05
RH::arg2::max = 1.0

ISWR::filter1 = min_max
ISWR::arg1::min = -10
ISWR::arg1::max = 1500
ISWR::filter2 = min_max
ISWR::arg2::soft = true
ISWR::arg2::min = 0
ISWR::arg2::max = 1500

RSWR::filter1 = min_max
RSWR::arg1::min = -10
RSWR::arg1::max = 1500
RSWR::filter2 = min_max
RSWR::arg2::soft = true
RSWR::arg2::min = 0
RSWR::arg2::max = 1500

ILWR::filter1 = min_max
ILWR::arg1::min = 188
ILWR::arg1::max = 600
ILWR::filter2 = min_max
ILWR::arg2::soft = true
ILWR::arg2::min = 200
ILWR::arg2::max = 400

TSS::filter1	= min_max
TSS::arg1::min = 200
TSS::arg1::max = 320

TSG::filter1 = min_max
TSG::arg1::min = 200
TSG::arg1::max = 320

HS::filter1 = min
HS::arg1::soft = true
HS::arg1::min = 0.0
HS::filter2 = rate
HS::arg2::max = 5.55e-5 ;0.20 m/h

VW::filter1 = min_max
VW::arg1::min = -2
VW::arg1::max = 70
VW::filter2 = min_max
VW::arg2::soft = true
VW::arg2::min = 0.0
VW::arg2::max = 50.0

[Interpolations1D]
MAX_GAP_SIZE = 700200;1 day = 86400, 2 days = 172800
TA::resample1	= linear
RH::resample1	= linear
PSUM::resample1 = accumulate ;cf interractions with CALCULATION_STEP_LENGTH
PSUM::ARG1::period = 60
HS::resample1 = linear
VW::resample1 = linear
DW::resample1 = linear

[Generators]
VW::generators = CST
VW::Cst::value = 1.0
RH::generators = HUMIDITY
RH::arg1::type = RH
# TA generator with fixed values (shoudl be good enough and not totally crazy
# for small gaps filling)
TA::generator1  = Sin
TA::arg1::type  = yearly
TA::arg1::min   = 268.26
TA::arg1::max   = 285.56
TA::arg1::phase = 0.0833
ISWR::generator1 = clearSky_SW

; PSUM::generators = ESOLIP CST
; PSUM::Cst::value = 0
"""

# =============================================================================
# Alpine3D Configuration Template (Simple)
# =============================================================================

A3D_INI_TEMPLATE = """[General]
buff_chunk_size = 370
buff_before = 1.5
buffer_size = 30
buff_grids = 30

[Input]
coordsys = CH1903+
time_zone = 1
meteo = SMET
; dbname = sdbo.wd.op
; dbuser = snowpack_app
; dbpass = Plouf_Plouf
; use_connection_string = TRUE
; dbport = 1521
; dbsid = sdbo
meteopath = ./input/meteo
station1 = MUT2
landuse = ARC
landusefile = input/surface-grids/2m_lus_test.lus
dem = ARC
demfile = input/surface-grids/2m_dem_test.asc
snowpath = ./input/snowfiles
snow = SMET
slope_algorithm = HORN
pvp = SMET
pvpfile = ./input/surface-grids/totalp.pv
brdfpath = ./input/brdf-files
station2 = ORT2
station3 = TUM2
POI = SMET
POIFILE = input/meteo/poi.smet

USE_IMIS_PSUM = TRUE
USE_SNOWPACK_PSUM = TRUE

; ISWR::create = ISWR_ALBEDO

[Output]
experiment = test
coordsys = CH1903+
time_zone = 1
meteo = SMET
meteopath = ./output/meteo
snow_write = TRUE
snow = SMET
snowpath = ./output/snowfiles
snow_days_between = 365
backup_days_between = 365
first_backup = 365
prof_write = FALSE
profile_format = PRO
prof_start = 0.0
prof_days_between = 1
hardness_in_newton = FALSE
classify_profile = FALSE
ts_write = TRUE
ts_start = 0.0
ts_days_between = 0.04166
ts_format = SMET
avgsum_time_series = TRUE
cumsum_mass = FALSE
precip_rates = FALSE
out_canopy = FALSE
out_haz = FALSE
out_heat = TRUE
out_t = TRUE
out_lw = TRUE
out_sw = TRUE
out_mass = TRUE
out_meteo = TRUE
out_stab = FALSE
grids_write = TRUE
grid2d = NETCDF
grid2dfile = out.nc
grids_start = 0.0
grids_days_between = 1
grids_parameters = TOP_ALB SURF_ALB ILWR ISWR ISWR_DIFF ISWR_DIR ISWR_TERRAIN ILWR_TERRAIN
grid2dpath = ./output/grids
a3d_view = true

[SNOWPACK]
calculation_step_length = 60
roughness_length = 0.002
height_of_meteo_values = 4.5
height_of_wind_value = 4.5
enforce_measured_snow_heights = TRUE
sw_mode = INCOMING
atmospheric_stability = NEUTRAL
canopy = False
meas_tss = FALSE
change_bc = False
thresh_change_bc = -1.2
snp_soil = TRUE
soil_flux = TRUE
geo_heat = 0.046
glacier_katabatic_flow = FALSE

[SNOWPACKADVANCED]
assume_responsibility = AGREE
variant = DEFAULT
snow_erosion = FALSE
wind_scaling_factor = 1.0
number_slopes = 1
perp_to_slope = FALSE
force_rh_water = TRUE
thresh_rain = 1.2
thresh_rh = 0.5
thresh_dtemp_air_snow = 3.0
hoar_thresh_rh = 0.97
hoar_thresh_vw = 3.5
hoar_density_buried = 125.0
hoar_min_size_buried = 2.0
hoar_density_surf = 100.0
min_depth_subsurf = 0.07
t_crazy_min = 210.0
t_crazy_max = 340.0
metamorphism_model = DEFAULT
new_snow_grain_size = 0.3
hn_density = PARAMETERIZED
hn_density_parameterization = LEHNING_NEW
strength_model = DEFAULT
viscosity_model = DEFAULT
saltation_model = SORENSEN
watertransportmodel_snow = BUCKET
watertransportmodel_soil = BUCKET
sw_absorption_scheme = MULTI_BAND
hardness_parameterization = MONTI
detect_grass = FALSE
plastic = FALSE
jam = FALSE
water_layer = FALSE
height_new_elem = 0.02
minimum_l_element = 0.0025
combine_elements = TRUE
advective_heat = FALSE

[EBalance]
terrain_radiation = TRUE
terrain_radiation_method = SIMPLE
pv_shadowing = TRUE
pvpfile = ./input/surface-grids/totalp.pv
complex_anisotropy = TRUE
complex_multiple = TRUE
brdfpath = ./input/brdf-files
complex_write_viewlist = FALSE
complex_read_viewlist = FALSE

[Filters]
psum::filter1 = min
psum::arg1::soft = true
psum::arg1::min = 0.0
ta::filter1 = min_max
ta::arg1::min = 240
ta::arg1::max = 320
rh::filter1 = min_max
rh::arg1::min = 0.01
rh::arg1::max = 1.2
rh::filter2 = min_max
rh::arg2::soft = true
rh::arg2::min = 0.05
rh::arg2::max = 1.0
iswr::filter1 = min_max
iswr::arg1::min = -10
iswr::arg1::max = 1500
iswr::filter2 = min_max
iswr::arg2::soft = true
iswr::arg2::min = 0
iswr::arg2::max = 1500
rswr::filter1 = min_max
rswr::arg1::min = -10
rswr::arg1::max = 1500
rswr::filter2 = min_max
rswr::arg2::soft = true
rswr::arg2::min = 0
rswr::arg2::max = 1500
ilwr::filter1 = min_max
ilwr::arg1::min = 188
ilwr::arg1::max = 600
ilwr::filter2 = min_max
ilwr::arg2::soft = true
ilwr::arg2::min = 200
ilwr::arg2::max = 400
tss::filter1 = min_max
tss::arg1::min = 200
tss::arg1::max = 320
tsg::filter1 = min_max
tsg::arg1::min = 200
tsg::arg1::max = 320
hs::filter1 = min
hs::arg1::soft = true
hs::arg1::min = 0.0
hs::filter2 = rate
hs::arg2::max = 5.55e-5 ;0.20 m/h
vw::filter1 = min_max
vw::arg1::min = -2
vw::arg1::max = 70
vw::filter2 = min_max
vw::arg2::soft = true
vw::arg2::min = 0.0
vw::arg2::max = 50.0

[Interpolations1D]
window_size = 86400
ta::resample = linear
rh::resample = linear
psum::resample = accumulate ;cf interractions with CALCULATION_STEP_LENGTH
psum::accumulate::period = 3600
hs::resample = linear
vw::resample = nearest
dw::resample = linear

[Interpolations2D]
DW::ALGORITHMS = LISTON_WIND AVG IDW_LAPSE
DW::LISTON_WIND::SOFT = FALSE

VW::ALGORITHMS = LISTON_WIND IDW_LAPSE AVG
VW::LISTON_WIND::SOFT = FALSE
VW_MAX::ALGORITHMS = IDW_LAPSE AVG
VW_MAX::IDW_LAPSE::SOFT = FALSE

ILWR::ALGORITHMS = AVG_LAPSE ;ILWR_EPS
;ILWR::ILWR_EPS::SOFT = true
;ILWR::ILWR_EPS::RATE = -1.8e-5
ILWR::AVG_LAPSE::RATE = -0.03125
ISWR::ALGORITHMS = IDW AVG ;SWRad I guess SWrad is doing the work twice since there is already the terrain accouted for in Ebalance... to check
RSWR::ALGORITHMS = IDW AVG

P::ALGORITHMS = STD_PRESS
P::STD_PRESS::USE_RESIDUALS = FALSE

PSUM::algorithms =  IDW_LAPSE AVG_LAPSE ;IDW ;AVG ; lapse rate not necesseraliy good for precip...
PSUM::IDW_LAPSE::frac   = true
PSUM::IDW_LAPSE::rate   = 0.0002
PSUM::AVG_LAPSE::rate = 0.0002
PSUM::AVG_LAPSE::frac = true

PSUM_PH::ALGORITHMS = PPHASE
PSUM_PH::PPHASE::SNOW = 274.35
PSUM_PH::PPHASE::TYPE = THRESH

RH::ALGORITHMS = LISTON_RH IDW_LAPSE AVG
RH::IDW_LAPSE::SOFT = FALSE
RH::LISTON_RH::SOFT = FALSE

TA::ALGORITHMS = IDW_LAPSE AVG_LAPSE
TA::AVG_LAPSE::RATE = -0.008
TA::IDW_LAPSE::RATE = -0.008
; ta::algorithms = idw_lapse
; ta::idw_lapse::soft = true
; ta::idw_lapse::rate = -0.008
; tss::algorithms = avg_lapse
; tss::avg_lapse::rate = -0.008
; tsg::algorithms = avg cst
; tsg::cst::value = 273.15
; rh::algorithms = liston_rh idw_lapse avg
; psum::algorithms = IDW_LAPSE AVG_LAPSE
; psum::psum_snow::base = avg_lapse
; psum::avg_lapse::rate = 0.0002
; psum::avg_lapse::frac = true
; psum::idw_lapse::frac = true
; psum::idw_lapse::rate = 0.0002
; psum_ph::algorithms = PPHASE
; psum_ph::pphase::snow = 274.35
; psum_ph::pphase::type = THRESH
; vw::algorithms = liston_wind
; dw::algorithms = idw
; p::algorithms = std_press
; rswr::algorithms = idw

[GridInterpolations1D]
ta::resample = linear
rh::resample = timeseries
rh::timeseries::algorithm = linear
rh::timeseries::extrapolate = true

; ISWR::generators = ISWR_ALBEDO
[GENERATORS]
ilwr::generator1 = clearsky_lw
ilwr::arg1::type = Dilley

"""

# =============================================================================
# Alpine3D Configuration Template (Complex - for terrain radiation)
# =============================================================================

A3D_INI_COMPLEX_TEMPLATE = """[General]
BUFF_CHUNK_SIZE =       370
BUFF_BEFORE     =       1.5

[Input]
COORDSYS	=	CH1903+
TIME_ZONE	=	1 # 1 = GMT + 1. Make sure input smet has tz = TIME_ZONE (here 1).

METEO		= SMET
METEOPATH	= ./input/meteo
; STATION1 = WFJ_b

ISWR_IS_NET	=	FALSE
SNOWPATH	=	./input/snowfiles
SNOW	=	SMET

GRID2D		= ARC
GRID2DPATH	= ./input/surface-grids

DEM		= ARC
DEMFILE		= ./input/surface-grids/totalp.dem

LANDUSE		= ARC
LANDUSEFILE	= ./input/surface-grids/totalp.lus

POI = SMET
POIFILE = input/meteo/poi.smet

PVP = SMET # COMPLEX

SLOPE_ALGORITHM= HORN
USE_IMIS_PSUM = TRUE
USE_SNOWPACK_PSUM = TRUE

[Output]
COORDSYS        =       CH1903+
TIME_ZONE       =       0 # Always output in UTC. Meteoio always stays in DST winter so GMT always = UTC.

METEO           = SMET
METEOPATH       = ./output

EXPERIMENT	=	totalp

SNOW_WRITE = FALSE
SNOW	=	SMET
SNOWPATH	= ./output/snowfiles
SNOW_DAYS_BETWEEN	=	365.0
FIRST_BACKUP	=	400.0

PROF_WRITE	=	False
PROFILE_FORMAT	=	PRO
PROF_START	=	0.0
PROF_DAYS_BETWEEN	=	1.
HARDNESS_IN_NEWTON	=	FALSE
CLASSIFY_PROFILE	=	FALSE

TS_WRITE	=	TRUE
TS_START	=	0.0
TS_DAYS_BETWEEN		= 1.
AVGSUM_TIME_SERIES	=	TRUE
CUMSUM_MASS	=	FALSE
PRECIP_RATES	=	FALSE
OUT_CANOPY	=	FALSE
OUT_HAZ	=	FALSE
OUT_HEAT	=	TRUE
OUT_T	=	TRUE
OUT_LW	=	TRUE
OUT_SW	=	TRUE
OUT_MASS	=	TRUE
OUT_METEO	=	TRUE
OUT_STAB	=	FALSE

GRIDS_WRITE = TRUE
; GRID2D		= ARC
GRID2D		= NETCDF
GRID2DFILE = out.nc
GRIDS_START = 0.0
GRIDS_DAYS_BETWEEN = 4.1666e-2 ; 1 hour
GRIDS_PARAMETERS = HS SURF_ALB ILWR ISWR ISWR_DIFF ISWR_DIR ISWR_TERRAIN ILWR_TERRAIN ; TOP_ALB
GRID2DPATH	= ./output/surface-grids
; GRID2DEXT = .txt
A3D_VIEW	= true

[SNOWPACK]
CALCULATION_STEP_LENGTH	=	60
ROUGHNESS_LENGTH	=	0.002
HEIGHT_OF_METEO_VALUES	=	4.5
HEIGHT_OF_WIND_VALUE	=	4.5
ENFORCE_MEASURED_SNOW_HEIGHTS	=	FALSE
SW_MODE	=	INCOMING
ATMOSPHERIC_STABILITY	=	NEUTRAL
CANOPY	=	TRUE
MEAS_TSS	=	FALSE
CHANGE_BC	=	TRUE
THRESH_CHANGE_BC = -1.2
SNP_SOIL	=	TRUE ;False
SOIL_FLUX	=	TRUE ;False
GEO_HEAT	=	0.046
GLACIER_KATABATIC_FLOW	=	FALSE

[SNOWPACKADVANCED]
ASSUME_RESPONSIBILITY	=	AGREE
VARIANT	=	DEFAULT
SNOW_EROSION	=	FALSE
WIND_SCALING_FACTOR	=	1.0
NUMBER_SLOPES	=	1
PERP_TO_SLOPE	=	FALSE
FORCE_RH_WATER	=	TRUE
THRESH_RAIN	=	1.2
THRESH_RH	=	0.5
THRESH_DTEMP_AIR_SNOW	=	3.0
HOAR_THRESH_RH	=	0.97
HOAR_THRESH_VW	=	3.5
HOAR_DENSITY_BURIED	=	125.0
HOAR_MIN_SIZE_BURIED	=	2.0
HOAR_DENSITY_SURF	=	100.0
MIN_DEPTH_SUBSURF	=	0.07
T_CRAZY_MIN	=	210.0
T_CRAZY_MAX	=	340.0
METAMORPHISM_MODEL	=	DEFAULT
NEW_SNOW_GRAIN_SIZE	=	0.3
HN_DENSITY	=	PARAMETERIZED
HN_DENSITY_PARAMETERIZATION	=	LEHNING_NEW
STRENGTH_MODEL	=	DEFAULT
VISCOSITY_MODEL	=	DEFAULT
SALTATION_MODEL	=	SORENSEN
WATERTRANSPORTMODEL_SNOW	=	BUCKET
WATERTRANSPORTMODEL_SOIL	=	BUCKET
SW_ABSORPTION_SCHEME	=	MULTI_BAND
HARDNESS_PARAMETERIZATION	=	MONTI
DETECT_GRASS	=	FALSE
PLASTIC	=	FALSE
JAM	=	FALSE
WATER_LAYER	=	FALSE
HEIGHT_NEW_ELEM	=	0.02
MINIMUM_L_ELEMENT	=	0.0025
COMBINE_ELEMENTS	=	TRUE
ADVECTIVE_HEAT	=	FALSE

[EBalance]
TERRAIN_RADIATION = TRUE
TERRAIN_RADIATION_METHOD = COMPLEX # SIMPLE , HELBIG

# input specific to TERRAIN_RADIATION_METHOD = COMPLEX
PVPFILE = ./input/surface-grids/Muttsee.pv # complex
BRDFPATH= ./input/brdf-files # complex

PV_SHADOWING=TRUE #complex

#FOR COMPLEX RADIATION MODEL
COMPLEX_ANISOTROPY	= TRUE
COMPLEX_MULTIPLE	= TRUE
COMPLEX_WRITE_VIEWLIST	= FALSE
COMPLEX_READ_VIEWLIST	= FALSE
GENERATE_PVP_SUM = TRUE
COMPLEX_VIEWLISTFILE = ./output/ViewList.rad

[FILTERS]
TA::filter1	= min_max
TA::arg1::min	= 230
TA::arg1::max	= 330

RH::filter1	= min_max
RH::arg1::min	= 0.01
RH::arg1::max	= 1.2
RH::filter2	= min_max
RH::arg2::soft	= true
RH::arg2::min	= 0.05
RH::arg2::max	=1.0

PSUM::filter1	= min
PSUM::arg1::min	= -0.1
PSUM::filter2	= min
PSUM::arg2::soft	= true
PSUM::arg2::min	= 0.
PSUM::filter3	= Undercatch_WMO
PSUM::arg3::type	= Hellmannsh

ISWR::filter1	= min_max
ISWR::arg1::min	= -10.
ISWR::arg1::max	= 1500.
ISWR::filter2	= min
ISWR::arg2::soft	= true
ISWR::arg2::min	= 0.

#for TA between 240 and 320 K
ILWR::filter1	= min_max
ILWR::arg1::min	= 80
ILWR::arg1::max	= 500
ILWR::filter2	= min_max
ILWR::arg2::soft	= true
ILWR::arg2::min	= 80
ILWR::arg2::max	= 450

HS::filter1	= min
HS::arg1::soft	= true
HS::arg1::min	= 0.0
HS::filter2	= rate
HS::arg2::max	= 5.55e-5 ;0.20 m/h


[INTERPOLATIONS1D]
WINDOW_SIZE	=	86400

[Interpolations2D]
TA::algorithms	= ODKRIG_LAPSE IDW_LAPSE AVG_LAPSE
TA::odkrig_lapse::vario = SPHERICVARIO LINVARIO
TA::avg_lapse::rate	= -0.008
TA::idw_lapse::soft	= true
TA::idw_lapse::rate	= -0.008

RH::algorithms	= LISTON_RH IDW_LAPSE AVG

ILWR::algorithms = AVG_LAPSE
ILWR::avg_lapse::rate = -0.03125

ISWR::algorithms = IDW AVG

PSUM::algorithms	= IDW_LAPSE AVG_LAPSE AVG CST
PSUM::avg_lapse::frac	= true
PSUM::avg_lapse::rate	= 0.0005
PSUM::cst::value = 0


PSUM_PH::algorithms = PPHASE
PSUM_PH::pphase::type = THRESH
PSUM_PH::pphase::snow = 274.35

VW::algorithms	= CST
VW::cst::value = 0

DW::algorithms	= CST
DW::cst::value = 0

VW_MAX::algorithms	= CST
VW_MAX::cst::value = 0

P::algorithms	= STD_PRESS


[GENERATORS]
ILWR::generator1	= ALLSKY_LW
ILWR::arg1::type	= Omstedt
;ILWR::generator1	= CLEARSKY_LW
"""

# =============================================================================
# SNO Templates
# =============================================================================

TEMPLATE_SNO = """SMET 1.1 ASCII
[HEADER]
station_id       = {{station_id}}
station_name     = {{station_name}}
latitude         = {{latitude}}
longitude        = {{longitude}}
altitude         = {{altitude}}
nodata           = {{nodata}}
tz               = {{tz}}
source           = {{source}}
ProfileDate      = 1990-10-01T00:00
HS_Last = 0.0
SlopeAngle = 0
SlopeAzi = 0
nSoilLayerData = 6
nSnowLayerData = 0
SoilAlbedo = 0.2
BareSoil_z0 = 0.02
CanopyHeight = 0
CanopyLeafAreaIndex = 0
CanopyDirectThroughfall = 0
WindScalingFactor = 0
ErosionLevel = 0
TimeCountDeltaHS = 0
fields = timestamp Layer_Thick T Vol_Frac_I Vol_Frac_W Vol_Frac_V Vol_Frac_S Rho_S Conduc_S HeatCapac_S rg rb dd sp mk mass_hoar ne CDot metamo
[DATA]
1990-10-01T00:00 2 278.15 0.0 0.02 0.01 0.97 2400.0 0.3 900.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 1 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.5 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.25 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.15 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.1 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0

"""

TEMPLATE_COMPLEX_SNO = """SMET 1.1 ASCII
[HEADER]
station_id       = {{station_id}}
station_name     = {{station_name}}
latitude         = {{latitude}}
longitude        = {{longitude}}
altitude         = {{altitude}}
nodata           = {{nodata}}
tz               = {{tz}}
ProfileDate      = 1990-10-01T00:00
HS_Last = 0.0
SlopeAngle = 0
SlopeAzi = 0
nSoilLayerData = 6
nSnowLayerData = 0
SoilAlbedo = 0.2
BareSoil_z0 = 0.02
CanopyHeight = 0
CanopyLeafAreaIndex = 0
CanopyDirectThroughfall = 0
WindScalingFactor = 0
ErosionLevel = 0
TimeCountDeltaHS = 0
fields = timestamp Layer_Thick T Vol_Frac_I Vol_Frac_W Vol_Frac_V Vol_Frac_S Rho_S Conduc_S HeatCapac_S rg rb dd sp mk mass_hoar ne CDot metamo
[DATA]
1990-10-01T00:00 2 278.15 0.0 0.02 0.01 0.97 2400.0 0.3 900.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 1 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.5 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.25 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.15 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
1990-10-01T00:00 0.1 278.15 0.0 0.025 0.22859 0.74641 2400.0 0.3 900.0 4096 0.0 0.0 0.0 0 0.0 1 0 0
"""

# =============================================================================
# PV Template
# =============================================================================

TEMPLATE_PV = """SMET 1.1 ASCII
[HEADER]
station_id      = my_pts
comment = This file contains location and orientation of PV-pannels for ISW
epsg    = 21781
nodata  = -999
fields = easting northing altitude inclination azimuth height width
[DATA]

"""

# =============================================================================
# POI Template
# =============================================================================

POI_SMET_TEMPLATE = """SMET 1.1 ASCII
[HEADER]
station_id = poi
epsg = {epsg}
nodata = -999
fields = easting northing altitude #altitude here is in epsg (~amsl)
[DATA]
"""

# =============================================================================
# LUS-specific SNO Templates
# =============================================================================

LUS_SNO_TEMPLATES = {
    10100: """SMET 1.1 ASCII
[HEADER]
station_id = {{station_id}}
station_name = {{station_name}}
longitude = {{longitude}}
latitude = {{latitude}}
altitude = {{altitude}}
nodata = {{nodata}}
tz = {{tz}}
ProfileDate = 1999-10-01T00:00
HS_Last = 0.0
SlopeAngle = 0
SlopeAzi = 0
nSoilLayerData = 19
nSnowLayerData = 0
SoilAlbedo = 0.4
BareSoil_z0 = 0.02
CanopyHeight = 0
CanopyLeafAreaIndex = 0
CanopyDirectThroughfall = 1
WindScalingFactor = 0
ErosionLevel = 0
TimeCountDeltaHS = 0
fields = timestamp Layer_Thick T Vol_Frac_I Vol_Frac_W Vol_Frac_V Vol_Frac_S Rho_S Conduc_S HeatCapac_S rg rb dd sp mk mass_hoar ne CDot metamo
[DATA]
1980-10-01T01:00 3.00 273.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 3.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 3.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.50 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.25 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.15 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.10 278.15 0.00 0.99 0.01 0.00 1000.0 0.6 4217.0 10000 0.0 0.0 0.0 0 0.0 1 0 0
""",
    10200: """SMET 1.1 ASCII
[HEADER]
station_id = {{station_id}}
station_name = {{station_name}}
longitude = {{longitude}}
latitude = {{latitude}}
altitude = {{altitude}}
nodata = {{nodata}}
tz = {{tz}}
ProfileDate = 1999-10-01T00:00
HS_Last = 0.0
SlopeAngle = 0
SlopeAzi = 0
nSoilLayerData = 19
nSnowLayerData = 0
SoilAlbedo = 0.16
BareSoil_z0 = 0.02
CanopyHeight = 0
CanopyLeafAreaIndex = 0
CanopyDirectThroughfall = 1
WindScalingFactor = 0
ErosionLevel = 0
TimeCountDeltaHS = 0
fields = timestamp Layer_Thick T Vol_Frac_I Vol_Frac_W Vol_Frac_V Vol_Frac_S Rho_S Conduc_S HeatCapac_S rg rb dd sp mk mass_hoar ne CDot metamo
[DATA]
1980-10-01T01:00 3.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 3.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 3.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.50 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.25 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.15 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.10 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
""",
    11500: """SMET 1.1 ASCII
[HEADER]
station_id = {{station_id}}
station_name = {{station_name}}
longitude = {{longitude}}
latitude = {{latitude}}
altitude = {{altitude}}
nodata = {{nodata}}
tz = {{tz}}
ProfileDate = 1999-10-01T00:00
HS_Last = 0.0
SlopeAngle = 0
SlopeAzi = 0
nSoilLayerData = 19
nSnowLayerData = 0
SoilAlbedo = 0.35
BareSoil_z0 = 0.02
CanopyHeight = 0
CanopyLeafAreaIndex = 0
CanopyDirectThroughfall = 1
WindScalingFactor = 0
ErosionLevel = 0
TimeCountDeltaHS = 0
fields = timestamp Layer_Thick T Vol_Frac_I Vol_Frac_W Vol_Frac_V Vol_Frac_S Rho_S Conduc_S HeatCapac_S rg rb dd sp mk mass_hoar ne CDot metamo
[DATA]
1980-10-01T01:00 3.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 3.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 3.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 2.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.01 0.87 2400.0 2.0 900.00 10000 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.20 0.02 0.20 0.58 1500.0 2.0 900.00 20.00 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 1.00 272.15 0.10 0.02 0.20 0.68 1700.0 2.0 900.00 150.0 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.50 272.15 0.10 0.02 0.20 0.68 1700.0 2.0 900.00 150.0 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.25 272.15 0.10 0.02 0.20 0.68 1700.0 2.0 900.00 150.0 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.15 272.15 0.10 0.02 0.20 0.68 1700.0 2.0 900.00 150.0 0.0 0.0 0.0 0 0.0 1 0 0
1980-10-01T01:00 0.10 272.15 0.10 0.02 0.20 0.68 1700.0 2.0 900.00 150.0 0.0 0.0 0.0 0 0.0 1 0 0
""",
}

# Note: Additional LUS SNO templates (10300-12900) follow the same pattern.
# They are loaded from files at runtime if available, falling back to 11500 as default.

# =============================================================================
# Template Registry
# =============================================================================

TEMPLATES = {
    'spConfig.ini': SNOWPACK_INI_TEMPLATE,
    'a3dConfig.ini': A3D_INI_TEMPLATE,
    'a3dConfigComplex.ini': A3D_INI_COMPLEX_TEMPLATE,
    'template.sno': TEMPLATE_SNO,
    'template_complex.sno': TEMPLATE_COMPLEX_SNO,
    'template.pv': TEMPLATE_PV,
    'poi.smet': POI_SMET_TEMPLATE,
}


def get_template(name: str, override_dir: Optional[Path] = None) -> str:
    """
    Get template content with optional file override capability.

    First checks if an override file exists in the specified directory or
    the default input/templates/ directory. If found, returns file content.
    Otherwise returns embedded template.

    Args:
        name: Template name (e.g., 'spConfig.ini', 'a3dConfig.ini')
        override_dir: Optional directory to check for override files.
                     If None, checks input/templates/

    Returns:
        Template content as string

    Raises:
        KeyError: If template name not found in embedded templates and no override exists
    """
    # Check for override file
    if override_dir is None:
        override_dir = Path('input/templates')

    override_path = override_dir / name
    if override_path.exists():
        return override_path.read_text()

    # Return embedded template
    if name in TEMPLATES:
        return TEMPLATES[name]

    raise KeyError(f"Template '{name}' not found in embedded templates or override directory")


def get_lus_sno_template(lus_code: int, override_dir: Optional[Path] = None) -> str:
    """
    Get LUS-specific SNO template.

    Args:
        lus_code: LUS code (e.g., 10100, 11500)
        override_dir: Optional directory to check for override files

    Returns:
        SNO template content
    """
    # Check for override file
    if override_dir is None:
        override_dir = Path('input/templates')

    override_path = override_dir / f'lus_{lus_code}.sno'
    if override_path.exists():
        return override_path.read_text()

    # Return embedded template if available
    if lus_code in LUS_SNO_TEMPLATES:
        return LUS_SNO_TEMPLATES[lus_code]

    # Fall back to default (11500 - alpine meadow/rock)
    return LUS_SNO_TEMPLATES.get(11500, TEMPLATE_SNO)
