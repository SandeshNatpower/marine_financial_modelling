import os

# API Endpoints
API_BASE = os.getenv("API_BASE", "https://natpower-marine-api-dev.azurewebsites.net/marinedata")
VESSEL_ENDPOINT = f"{API_BASE}/getvesseldetails_engine"
FINANCIAL_ENDPOINT = f"{API_BASE}/financialmodelling"

# Default Vessel Data with Extended Engine and Operational Parameters
DEFAULT_VESSEL = {
    "imo": 9803613,
    "vessel_name": "MSC GRANDIOSA",
    "vessel_category": "CRUISE PASSENGER SHIP",
    "gross_tonnage": 181541,
    "year_built": 2019,
    "cruising_speed": 21.3,
    "dwt": 13610,
    "draught": 9.0,
    "beam": 43,
    "length": 331,
    "depth": 15.5,
    "displacement": 0,
    "main_engine_type": "4-Stroke",
    "aux_engine_type": "4-Stroke",
    "total_engine_power": 38400,
    "shore_power_kw": 2020,
    "main_engine_power_kw": 38400,
    "aux_engine_power_kw": 2020,
    "sailing_engine_load": 0.5,
    "working_engine_load": 0.3,
    "shore_engine_load": 0.395,
    "sailing_days": 199,
    "working_days": 40,
    "idle_days": 126,
    "shore_days": 0,
    "shore_port": 2,
    "main_fuel_type": "MDO",
    "aux_fuel_type": "MDO",
    "future_main_fuel_type": "Diesel-Bio-diesel",
    "future_aux_fuel_type": "Diesel-Bio-diesel",
    "reporting_year": 2030,
    "ENGINE_MAINTENANCE_COSTS_PER_HOUR": 20,
    "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 2,
    "SHORE_POWER_MAINTENANCE_PER_DAY": 45.486,
    "SHORE_POWER_SPARES_PER_DAY": 45.486,
    "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 3,
    "FUELEU_CURRENT_PENALTY_PER_YEAR": 729348.5444,
    "FUELEU_FUTURE_PENALTY_PER_YEAR": 237950.5332,
    "PARASITIC_LOAD_ENGINE": 0.95,
    "BIOFUELS_BLEND_PERCENTAGE": 0.0,
    "shore_enable": True
}

# Fuel Options
FUEL_OPTIONS = [
    {"label": "Marine Diesel Oil (MDO)",                       "value": "MDO"},
    {"label": "Marine Gas Oil (MGO)",                         "value": "MGO"},
    {"label": "Low Sulfur Fuel Oil (LFO)",                    "value": "LFO"},
    {"label": "Heavy Fuel Oil (HFO)",                         "value": "HFO"},
    {"label": "Liquefied Natural Gas - Medium (LNG med.)",    "value": "LNG med."},
    {"label": "Liquefied Natural Gas - Slow (LNG slow)",      "value": "LNG slow"},
    {"label": "Liquefied Natural Gas - Diesel (LNG Diesel)",  "value": "LNG Diesel"},
    {"label": "Liquefied Natural Gas - LBSI (LNG LBSI)",      "value": "LNG LBSI"},
    {"label": "Liquefied Petroleum Gas (LPG)",                "value": "LPG"},
    {"label": "Hydrogen (H2)",                                "value": "H2"},
    {"label": "Ammonia (NH3)",                                "value": "NH3"},
    {"label": "Methanol",                                     "value": "Methanol"},
    {"label": "Ethanol",                                      "value": "Ethanol"},
    {"label": "Biodiesel (Bio-diesel)",                       "value": "Bio-diesel"},
    {"label": "Hydrotreated Vegetable Oil (HVO)",             "value": "HVO"},
    {"label": "Bio-LNG (Medium) (Bio-LNG med.)",              "value": "Bio-LNG med."},
    {"label": "Bio-LNG (Slow) (Bio-LNG slow)",                "value": "Bio-LNG slow"},
    {"label": "Bio-LNG (Diesel) (Bio-LNG Diesel)",            "value": "Bio-LNG Diesel"},
    {"label": "Bio-LNG (LBSI) (Bio-LNG LBSI)",                "value": "Bio-LNG LBSI"},
    {"label": "Biomethanol (Bio-methanol)",                   "value": "Bio-methanol"},
    {"label": "Other",                                        "value": "Other"},
    {"label": "Bio-Hydrogen (Bio-H2)",                        "value": "Bio-H2"},
    {"label": "Electro-Diesel (e-diesel)",                    "value": "e-diesel"},
    {"label": "Electro-Methanol (e-methanol)",                "value": "e-methanol"},
    {"label": "Electro-LNG (Medium) (e-LNG med.)",            "value": "e-LNG med."},
    {"label": "Electro-LNG (Slow) (e-LNG slow)",              "value": "e-LNG slow"},
    {"label": "Electro-LNG (Diesel) (e-LNG Diesel)",          "value": "e-LNG Diesel"},
    {"label": "Electro-LNG (LBSI) (e-LNG LBSI)",              "value": "e-LNG LBSI"},
    {"label": "Electro-Hydrogen (e-H2)",                      "value": "e-H2"},
    {"label": "Electro-Ammonia (e-NH3)",                      "value": "e-NH3"},
    {"label": "Electro-LPG (e-LPG)",                          "value": "e-LPG"},
    {"label": "Electro-DME (e-DME)",                          "value": "e-DME"},
    {"label": "Hydrogen",                                     "value": "Hydrogen"},
    {"label": "Full Electric (Full_Electric)",                "value": "Full_Electric"},
    {"label": "Methanol / MDO / e-Methanol Mix",              "value": "Methanol MDO e-methanol"},
    {"label": "Electricity (Natpower)",                       "value": "Electricity Natpower"},
    {"label": "Diesel / Bio-Diesel Blend",                    "value": "Diesel-Bio-diesel"},
    {"label": "Electricity (Grid)",                           "value": "Electricity"},
]
# Currencies
CURRENCIES = {
    "EUR": {"symbol": "€", "conversion": 1.0},
    "USD": {"symbol": "$", "conversion": 1.07},
    "GBP": {"symbol": "£", "conversion": 0.85}
}

# General Options
BOOLEAN_YES_NO_OPTIONS = ["Yes", "No"]
BOOLEAN_TRUE_FALSE_OPTIONS = ["TRUE", "FALSE"]
BOOLEAN_0_1_OPTIONS = ["0", "1"]
REFIT_COMPLEXITY_OPTIONS = ["1", "2", "3", "4", "5"]
FINANCE_OPTIONS = ["Purchase", "Lease"]

# Model Options
VISUALIZATION_OPTIONS = [
    "Standard table", "CAPEX/OPEX Yearly", "EU ETS", "Volume vs. Weight"
]
FUEL_COMPARISON_OPTIONS = ["[€]", "[kg]", "[liter]", "[kWh]"]
DAY_YEAR_OPTIONS = ["1", "365"]
DAY_YEAR_OPTION_LABELS = ["day", "year"]
UNIT_OPTIONS = ["1", "1000"]
UNIT_OPTION_LABELS = ["[kg] / [liter]", "[mT] / [m3]"]

# Ship Options
SHIP_MAIN_TYPE_OPTIONS = [
    "RORO_SHIPS", "CONTAINER_SHIP", "DREDGING", "GENERAL_CARGO",
    "CRUISE_PASSENGER_SHIP", "TANKER", "GAS_CARRIER", "PORT_AND_TUGS",
    "REFRIGERATED_CARGO_CARRIER", "PASSENGER_SHIP", "OFFSHORE",
    "MISCELLANEOUS", "FISHING", "LNG_CARRIER", "BULK_CARRIER",
    "COMBINATION_CARRIER", "INLAND_WATERWAYS"
]
SHIP_MAIN_TYPE_OPTION_LABELS = [
    "Roro ships", "Bulk Carrier", "Combination Carrier", "Container Ship",
    "General Cargo", "Gas Carrier", "LNG Carrier", "RoRo Ships",
    "Refrigerated Cargo Carrier", "Passenger Ship", "Cruise Passenger Ship",
    "Miscellaneous", "Fishing", "Inland Waterways", "Bulk carrier", "Port and Tugs"
]

SHIP_TYPE_ALL_OPTIONS = [
    "RoRo_Cargo", "Cruise_Passenger", "Refrigerated_Cargo_Carrier",
    "Passenger_General_Cargo", "Passenger_Container", "Semi_Submersible",
    "LNG_Carrier", "RoRo_Passenger_and_Cargo", "Container_Ship", "Jackup",
    "Construction_Vessel", "LPG_Carrier", "RoRo_Passenger", "Support_Vessel",
    "General_Liquid_Carrier", "Crude_Oil_Tanker", "FPSO", "Pipe_Layer",
    "Heavy_Cargo_Vessel", "Trailing_Suction_Hopper", "General_Bulk_Carrier",
    "Standby_Safety_Vessel", "Oil_Products_Tanker", "Self_Discharging_Bulk_Carrier",
    "Ore_Bulk_Oil_Carrier", "Passenger_and_Car_Ferry", "Ore_Carrier",
    "Passenger_Ferry", "Trawler", "Fish_Carrier", "Seagoing_Tug",
    "Multi_Purpose_Ship", "Chemical_Tanker", "Liquefied_Gas_Carrier",
    "Crew_Boat", "Cutter_Suction_Dredger", "RoRo_Cargo_Vehicle_Carrier",
    "Reefer", "Feeder", "Fish_Factory_Ship", "Coast_Guard_Vessel",
    "CO2_Carrier", "Inland_Cruise_Ship", "Inland_Tanker", "Inland_General_Cargo",
    "Inland_RoRo_Cargo", "Inland_Passenger_Ferry", "General_Cargo_Ship",
    "Inland_Dredging", "Harbor_Tug", "Pilot_Vessel", "Pusher_Tug"
]

DRIVE_TRAIN_OPTIONS = ["Direct_Drive", "Diesel_Electric", "Non_Propelled"]
DRIVE_TRAIN_OPTION_LABELS = ["Direct Drive", "Diesel Electric", "Non Propelled"]

OPERATIONAL_PROFILE_OPTIONS = ["Sailing", "Working", "Idle_moored", "COMBINATION"]
OPERATIONAL_PROFILE_OPTION_LABELS = ["Sailing", "Working", "Idle / moored", "Combination"]

# Extended fuel type options for ship fuel selection
FUEL_TYPE_OPTIONS_SHIP = [
    "HFO",
    "LFO",
    "MDO",
    "MGO",
    "LNG med.",
    "LNG slow",
    "LNG Diesel",
    "LNG LBSI",
    "LPG",
    "H2",
    "NH3",
    "Methanol",
    "Ethanol",
    "Bio-diesel",
    "HVO",
    "Bio-LNG med.",
    "Bio-LNG slow",
    "Bio-LNG Diesel",
    "Bio-LNG LBSI",
    "Bio-methanol",
    "Other",
    "Bio-H2",
    "e-diesel",
    "e-methanol",
    "e-LNG med.",
    "e-LNG slow",
    "e-LNG Diesel",
    "e-LNG LBSI",
    "e-H2",
    "e-NH3",
    "e-LPG",
    "e-DME",
    "Electricity",
    "Full_Electric",
    "Methanol MDO e-methanol",
    "Diesel-Bio-diesel"
]

ENGINE_SPEED_OPTIONS = ["High", "Medium", "Low"]
ENGINE_TYPE_OPTIONS = ["2-Stroke", "4-Stroke"]

# Measures Options
ALL_MEASURES_OPTIONS = [
    "Shore_Power", "Shore_Battery", "Solar_PV", "Wind_Propulsion",
    "Hull_Coating", "Battery_Hybrid", "Biofuels", "Methanol", "Hydrogen",
    "Full_Electric"
]
SHORE_POWER_OPTIONS = ["-", "#N/A"]
PREVENT_OPTIONS = ["-", "#N/A"]
CHANGE_OPTIONS = ["-", "#N/A"]
SHORE_POWER_OPTION_LABELS = ["-"]
PREVENT_OPTION_LABELS = ["-"]
CHANGE_OPTION_LABELS = ["-"]

SHORE_POWER_SWITCHOVER_PHILOSOPHY_OPTIONS = ["Synchronization", "Blackout"]
SOLAR_PV_DATE_OPTIONS = ["45281", "45006", "45098"]
SOLAR_PV_DATE_OPTION_LABELS = ["21-Dec", "21-Mar", "21-Jun"]
BATTERY_HYBRID_OPTIONS = ["Spinning reserve", "Peakshaving", "Hybrid sailing"]
BIOFUELS_OPTIONS = ["HVO", "GTL", "Bio_HFO", "Bio_LNG"]
HYDROGEN_PRESSURE_OPTIONS = ["200", "350", "700", "1,400", "liquid"]
FULL_ELECTRIC_OPERATING_FREQUENCY = ["DC", "50", "60"]
BATTERY_CHEMISTRY_OPTIONS = ["LFP", "NMC"]

# Regulations Options
AREA_OPTIONS = [
    "North-Americas", "South-Americas", "Europe", "Africa", "Middle-East",
    "Asia-Pacific", "Australia", "Global"
]
ORGANIZATION_OPTIONS = [
    "IMO", "Government", "Energy Major", "Shipping Company", "Port", "All"
]
COMPLIANCE_BENCHMARK_OPTIONS = [
    "CO2 Target", "IMO Total Emissions", "IMO Carbon Intensity",
    "FuelEU Maritime", "US Clean Shipping Act", "China Carbon Neutral",
    "EU Fit for 55", "Paris Agreement", "Ørsted", "Equinor", "Repsol",
    "Eni", "Total", "Shell", "BP", "Aramco", "ExxonMobil", "Chevron"
]
COMPLIANCE_BENCHMARK_OPTION_LABELS = [
    "IMO", "IMO Total Emissions", "IMO Carbon Intensity", "China",
    "US Clean Shipping Act", "China Carbon Neutral", "EU Fit for 55",
    "Paris Agreement", "Ørsted", "Equinor", "Repsol", "Eni", "Total",
    "Shell", "BP", "Aramco", "ExxonMobil", "Chevron"
]
COMPANIES_SCOPE_OPTIONS = ["Do not include", "Scope 1 and 2", "Scope 3"]

# Additional Option for dual fuel engine installation
DUAL_FUEL_ENGINE_INSTALLED = ["Yes", "No"]

# wkhtmltopdf configuration for pdfkit (default path or from environment variable)
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

# SMTP settings (should be set via environment variables in production)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "your_email@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_email_password")