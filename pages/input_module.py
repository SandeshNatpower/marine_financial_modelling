import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import config  # Assumes config has FUEL_OPTIONS, DEFAULT_VESSEL, FINANCIAL_ENDPOINT, etc.
import requests
from urllib.parse import urlencode

# -------------------------------------------------------------------------------
# GLOBAL CONSTANTS AND DEFAULTS
# -------------------------------------------------------------------------------
PRIMARY_COLOR = "#0A4B8C"
TEXT_COLOR = "#212121"
FUEL_OPTIONS = config.FUEL_OPTIONS

# The default vessel is still provided by config but can be overwritten
DEFAULT_VESSEL = config.DEFAULT_VESSEL

# Default values aligned with API requirements (used initially in the UI)
DEFAULT_SAILING_DAYS = 199
DEFAULT_WORKING_DAYS = 40
DEFAULT_IDLE_DAYS = 126
DEFAULT_SHORE_DAYS = 0
DEFAULT_REPORTING_YEAR = 2030
DEFAULT_FUELEU_CURRENT_PENALTY = 729348.5444
DEFAULT_FUELEU_FUTURE_PENALTY = 0
DEFAULT_PARASITIC_LOAD = 0.95
DEFAULT_BIOFUELS_BLEND = 0.3
DEFAULT_INFLATION_RATE = 0.02
DEFAULT_NPV_RATE = 0
DEFAULT_CAPEX = 19772750
DEFAULT_MAIN_ENGINE_POWER = 38400
DEFAULT_AUX_ENGINE_POWER = 2020

# IMPORTANT: Engine loads are now stored directly as percentages.
DEFAULT_SAILING_ENGINE_LOAD = 50    # instead of 0.5 (i.e. 50%)
DEFAULT_WORKING_ENGINE_LOAD = 30    # instead of 0.3 (i.e. 30%)
DEFAULT_SHORE_ENGINE_LOAD = 39.5    # instead of 0.395 (i.e. 39.5%)

DEFAULT_SHORE_PORT = 1
DEFAULT_MAIN_FUEL_TYPE = "MDO"
DEFAULT_AUX_FUEL_TYPE = "MDO"
DEFAULT_FUTURE_MAIN_FUEL_TYPE = "Diesel-Bio-diesel"
DEFAULT_FUTURE_AUX_FUEL_TYPE = "Diesel-Bio-diesel"
DEFAULT_ENGINE_MAINT_COST = 20
DEFAULT_SPARES_COST = 2
DEFAULT_SHORE_MAINT_COST = 45.486
DEFAULT_SHORE_SPARES_COST = 45.486
DEFAULT_BIOFUELS_SPARES_COST = 3
DEFAULT_SHORE_ENABLE = False

# New defaults for engine speed
DEFAULT_MAIN_ENGINE_SPEED = "MEDIUM"
DEFAULT_AUX_ENGINE_SPEED = "MEDIUM"

# -------------------------------------------------------------------------------
# HELPER FUNCTION: Create Input Group
# -------------------------------------------------------------------------------
def create_input_group(label, id, value=None, input_type='number', options=None,
                       col_size=4, editable=True, info_text=None, units=None,
                       min_val=None, max_val=None):
    col_settings = {"md": col_size, "xs": 12}
    
    label_contents = [label]
    if info_text:
        label_contents.append(
            html.I(
                id=f"{id}-info-icon",
                className="fa fa-info-circle ml-1",
                style={"cursor": "pointer", "color": "grey", "fontSize": "0.85rem"}
            )
        )
    label_component = dbc.Label(label_contents, style={"color": TEXT_COLOR})
    
    if input_type == 'dropdown':
        opts = options if isinstance(options, list) and isinstance(options[0], dict) \
            else [{"label": opt, "value": opt} for opt in options] if options else []
        input_field = dcc.Dropdown(
            id=id,
            options=opts,
            value=value,
            clearable=False,
            disabled=not editable,
            style={"backgroundColor": "#e9ecef"} if not editable else {}
        )
    else:
        input_component = dbc.Input(
            id=id,
            type=input_type,
            value=value,
            disabled=not editable,
            placeholder=str(value) if value is not None else "",
            style={"backgroundColor": "#e9ecef"} if not editable else {},
            min=min_val,
            max=max_val
        )
        if units:
            input_field = dbc.InputGroup([input_component, dbc.InputGroupText(units)])
        else:
            input_field = input_component

    children = [label_component, input_field]
    if info_text:
        children.append(dbc.Tooltip(info_text, target=f"{id}-info-icon", placement="top"))
    
    return dbc.Col(children, **col_settings)

# -------------------------------------------------------------------------------
# VESSEL DETAILS FETCHER
# -------------------------------------------------------------------------------
def get_vessel_details(search_term, search_type='imo'):
    url = "https://natpower-marine-api-dev.azurewebsites.net/marinedata/getvesseldetails_engine?"
    params = {"imo": search_term, "mmsi": search_term} if search_type == 'imo' else {"vesselname": search_term}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            return data[0]
        else:
            return DEFAULT_VESSEL
    except requests.RequestException as e:
        print(f"Exception fetching vessel details: {e}")
        return DEFAULT_VESSEL

# -------------------------------------------------------------------------------
# VESSEL IMAGE HANDLER
# -------------------------------------------------------------------------------
def get_vessel_image_path(vessel_type):
    if not vessel_type:
        return "default_vessel.png"
    if isinstance(vessel_type, dict):
        vessel_type = vessel_type.get('value', '')
    normalized_type = vessel_type.strip().upper()
    vessel_type_map = {
        'PASSENGER RO/RO': 'passenger_roro.png',
        'PASSENGER SHIP': 'passenger_ship.png',
        'CRUISE PASSENGER SHIP': 'cruise_ship.png',
        'RO/RO PASSENGER': 'roro_passenger.png',
        'FERRY': 'ferry.png',
        'CONTAINER SHIP': 'container_ship.png',
        'BULK CARRIER': 'bulk_carrier.png',
        'GENERAL CARGO': 'general_cargo.png',
        'REFRIGERATED CARGO CARRIER': 'refrigerated_cargo.png',
        'TANKER': 'tanker.png',
        'CRUDE OIL TANKER': 'crude_oil_tanker.png',
        'CHEMICAL TANKER': 'chemical_tanker.png',
        'GAS CARRIER': 'gas_carrier.png',
        'LNG CARRIER': 'lng_carrier.png',
        'DREDGING': 'dredger.png',
        'FISHING': 'fishing_vessel.png',
        'OFFSHORE': 'offshore_vessel.png',
        'TUG': 'tug.png',
        'PORT AND TUGS': 'tug.png',
        'MISCELLANEOUS': 'general_vessel.png',
        'COMBINATION CARRIER': 'combination_carrier.png',
        'INLAND WATERWAYS': 'inland_vessel.png'
    }
    if normalized_type in vessel_type_map:
        return vessel_type_map[normalized_type]
    for key, image in vessel_type_map.items():
        if key in normalized_type or normalized_type in key:
            return image
    return "default_vessel.png"

# -------------------------------------------------------------------------------
# INPUT MODULE LAYOUT
# -------------------------------------------------------------------------------
def layout():
    return html.Div([
        html.H1("Step 1: Vessel Details (version 1.1)", className="mb-4", style={"color": PRIMARY_COLOR}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Search for Vessel Data", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Search Type", "search-type", "imo", "dropdown",
                                       options=[{"label": "Vessel Name", "value": "name"},
                                                {"label": "IMO/MMSI", "value": "imo"}],
                                       col_size=3, info_text="Select search type"),
                    create_input_group("Search Term", "search-term", None, "text", col_size=6,
                                       info_text="Enter IMO, MMSI, or vessel name"),
                    dbc.Col([html.Br(), dbc.Button("Search", id="search-button", color="primary", className="mt-2")],
                            md=3, xs=12)
                ]),
                html.Div(id="search-results")
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Basic Vessel Information", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Img(id="vessel-image", src="/assets/default_vessel.png",
                                     style={"width": "100%", "maxHeight": "200px", "objectFit": "contain",
                                            "borderRadius": "8px", "boxShadow": "0 2px 10px rgba(0,0,0,0.1)"}),
                            html.Div(id="vessel-type-display", className="text-center mt-2")
                        ], className="text-center")
                    ], md=4, xs=12),
                    dbc.Col([
                        dbc.Row([
                            create_input_group("Vessel Name", "vessel-name", DEFAULT_VESSEL["vessel_name"],
                                               "text", col_size=12, editable=True, info_text="Full vessel name")
                        ], className="mb-3"),
                        dbc.Row([
                            create_input_group("IMO Number", "imo-number", DEFAULT_VESSEL["imo"], "number", col_size=6,
                                               editable=True, info_text="IMO/MMSI number"),
                            create_input_group("Vessel Category", "vessel-category", DEFAULT_VESSEL["vessel_category"],
                                               "text", col_size=6, editable=True, info_text="Vessel category")
                        ], className="mb-3"),
                        dbc.Row([
                            create_input_group("Gross Tonnage", "gross-tonnage", DEFAULT_VESSEL["gross_tonnage"],
                                               "number", col_size=4, editable=True, info_text="Gross tonnage", units="GT"),
                            create_input_group("Deadweight", "dwt", DEFAULT_VESSEL["dwt"], "number", col_size=4,
                                               editable=True, info_text="Deadweight tonnage", units="mT"),
                            create_input_group("Year Built", "year-built", DEFAULT_VESSEL["year_built"], "number", col_size=4,
                                               editable=True, info_text="Year the vessel was built"),
                            create_input_group("Reporting Year", "reporting-year", DEFAULT_REPORTING_YEAR, "number", col_size=4,
                                               editable=True, info_text="Year for financial reporting")
                        ], className="mb-3")
                    ], md=8, xs=12)
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Technical Specs & Engine Info", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Main Engine Power", "main-power", DEFAULT_MAIN_ENGINE_POWER,
                                       "number", info_text="Main engine power (kW)", units="kW"),
                    create_input_group("Main Engine Type", "main-engine-type", DEFAULT_VESSEL.get("main_engine_type", "4-STROKE"),
                                       "text", col_size=4, info_text="Type of main engine"),
                    create_input_group("Main Fuel Type", "main-fuel-type", DEFAULT_MAIN_FUEL_TYPE,
                                       "dropdown", options=FUEL_OPTIONS, col_size=4, info_text="Main fuel type")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Main Engine Speed", "main-engine-speed", DEFAULT_MAIN_ENGINE_SPEED,
                                       "dropdown", options=[{"label": "SLOW", "value": "SLOW"},
                                                             {"label": "MEDIUM", "value": "MEDIUM"},
                                                             {"label": "FAST", "value": "FAST"}],
                                       col_size=4, info_text="Main engine speed")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Auxiliary Engine Power", "aux-power", DEFAULT_AUX_ENGINE_POWER,
                                       "number", info_text="Auxiliary engine power (kW)", units="kW"),
                    create_input_group("Auxiliary Engine Type", "aux-engine-type", DEFAULT_VESSEL.get("aux_engine_type", "4-STROKE"),
                                       "text", col_size=4, info_text="Type of auxiliary engine"),
                    create_input_group("Aux Fuel Type", "aux-fuel-type", DEFAULT_AUX_FUEL_TYPE,
                                       "dropdown", options=FUEL_OPTIONS, col_size=4, info_text="Auxiliary fuel type")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Auxiliary Engine Speed", "aux-engine-speed", DEFAULT_AUX_ENGINE_SPEED,
                                       "dropdown", options=[{"label": "SLOW", "value": "SLOW"},
                                                             {"label": "MEDIUM", "value": "MEDIUM"},
                                                             {"label": "FAST", "value": "FAST"}],
                                       col_size=4, info_text="Auxiliary engine speed")
                ], className="mb-3")
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Operational Profile", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Sailing Days/Year", "sailing-days", DEFAULT_SAILING_DAYS, "number",
                                       info_text="Days sailing per year (total must be 365)", units="days", min_val=0, max_val=365),
                    create_input_group("Working Days/Year", "working-days", DEFAULT_WORKING_DAYS, "number",
                                       info_text="Days working per year (total must be 365)", units="days", min_val=0, max_val=365),
                    create_input_group("Idle Days/Year", "idle-days", DEFAULT_IDLE_DAYS, "number",
                                       info_text="Days idle per year (total must be 365)", units="days", min_val=0, max_val=365),
                    create_input_group("Shore Days/Year", "shore-days", DEFAULT_SHORE_DAYS, "number",
                                       info_text="Days at shore per year (total must be 365)", units="days", min_val=0, max_val=365)
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Shore Port", "shore-port", DEFAULT_SHORE_PORT, "number",
                                       col_size=4, info_text="Number of shore ports"),
                    create_input_group("Shore Enable", "shore-enable", "Yes" if DEFAULT_SHORE_ENABLE else "No",
                                       "dropdown", options=["Yes", "No"], col_size=4, info_text="Enable shore power")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Sailing Engine Load", "sailing-engine-load", DEFAULT_SAILING_ENGINE_LOAD,
                                       "number", info_text="Engine load during sailing (0-100%)", min_val=0, max_val=100, units="%"),
                    create_input_group("Working Engine Load", "working-engine-load", DEFAULT_WORKING_ENGINE_LOAD,
                                       "number", info_text="Engine load during working (0-100%)", min_val=0, max_val=100, units="%"),
                    create_input_group("Shore Engine Load", "shore-engine-load", DEFAULT_SHORE_ENGINE_LOAD,
                                       "number", info_text="Engine load at shore (0-100%)", min_val=0, max_val=100, units="%")
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Maintenance & Costs", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Engine Maintenance Cost", "engine-maint-cost", DEFAULT_ENGINE_MAINT_COST,
                                       "number", info_text="Maintenance cost per engine hour", units="EUR/h", min_val=0),
                    create_input_group("Spares/Consumables Cost", "spares-cost", DEFAULT_SPARES_COST,
                                       "number", info_text="Spares cost per engine hour", units="EUR/h", min_val=0),
                    create_input_group("FUELEU Current Penalty", "fueleu-penalty", DEFAULT_FUELEU_CURRENT_PENALTY,
                                       "number", info_text="Current annual penalty", units="EUR/yr", min_val=0)
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Future Inputs & Fuel Blend", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Future Main Fuel Type", "future-main-fuel-type", DEFAULT_FUTURE_MAIN_FUEL_TYPE,
                                       "dropdown", options=FUEL_OPTIONS, col_size=4, info_text="Future main fuel type"),
                    create_input_group("Future Aux Fuel Type", "future-aux-fuel-type", DEFAULT_FUTURE_AUX_FUEL_TYPE,
                                       "dropdown", options=FUEL_OPTIONS, col_size=4, info_text="Future auxiliary fuel type")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("FUELEU Future Penalty", "fueleu-future-penalty", DEFAULT_FUELEU_FUTURE_PENALTY,
                                       "number", info_text="Future annual penalty", units="EUR/yr", min_val=0),
                    create_input_group("Biofuels Spares Cost", "biofuels-spares-cost", DEFAULT_BIOFUELS_SPARES_COST,
                                       "number", info_text="Biofuels spares cost per engine hour", units="EUR/h", min_val=0)
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Shore Power Maintenance/Day", "shore-maint-cost", DEFAULT_SHORE_MAINT_COST,
                                       "number", info_text="Daily shore power maintenance cost", units="EUR/day", min_val=0),
                    create_input_group("Shore Power Spares/Day", "shore-spares-cost", DEFAULT_SHORE_SPARES_COST,
                                       "number", info_text="Daily shore power spares cost", units="EUR/day", min_val=0)
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Parasitic Load Engine", "parasitic-load", DEFAULT_PARASITIC_LOAD,
                                       "number", info_text="Parasitic load factor (0-1)", min_val=0, max_val=1),
                    create_input_group("Biofuels Blend (%)", "biofuels-blend", DEFAULT_BIOFUELS_BLEND * 100,
                                       "number", info_text="Biofuels blend percentage (0-100)", units="%", min_val=0, max_val=100)
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Inflation Rate", "inflation-rate", DEFAULT_INFLATION_RATE * 100,
                                       "number", info_text="Annual inflation rate (0-100)", units="%", min_val=0),
                    create_input_group("NPV Rate", "npv-rate", DEFAULT_NPV_RATE * 100,
                                       "number", info_text="Net present value discount rate (0-100)", units="%", min_val=0)
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("CAPEX", "capex", DEFAULT_CAPEX, "number",
                                       info_text="Capital expenditure", units="EUR", min_val=0)
                ], className="mb-3")
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        dbc.Button("Calculate Emissions & Costs", id="calculate-button", color="primary", className="mt-3"),
        html.Div(id="calculation-status", className="mt-3", style={"color": TEXT_COLOR}),
        html.Div([
            dbc.Card([
                dbc.CardHeader(
                    html.H4("Debugging Information", id="debug-header", style={"color": "white", "cursor": "pointer"}),
                    style={"backgroundColor": "#6c757d"}
                ),
                dbc.Collapse(
                    dbc.CardBody([
                        html.P("This section shows technical details about the calculation process.", className="text-muted"),
                        html.Div(id="debug-info")
                    ]),
                    id="debug-collapse", is_open=False
                )
            ])
        ], className="mt-3 mb-5", id="debug-section", style={"display": "block"})
    ])
