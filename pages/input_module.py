#pages/input_module.py 

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import config  # Assumes config has FUEL_OPTIONS, DEFAULT_VESSEL, FINANCIAL_ENDPOINT, etc.
import requests
from urllib.parse import urlencode

# -------------------------------------------------------------------------------
# GLOBAL CONSTANTS AND DEFAULTS
# -------------------------------------------------------------------------------
PRIMARY_COLOR = "#0A4B8C"
TEXT_COLOR = "#212121"
FUEL_OPTIONS = config.FUEL_OPTIONS  # For example, list of fuel options (as dictionaries)
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
DEFAULT_SAILING_ENGINE_LOAD = 0.5    # UI shows 50%
DEFAULT_WORKING_ENGINE_LOAD = 0.3    # UI shows 30%
DEFAULT_SHORE_ENGINE_LOAD = 0.395    # UI shows 39.5%
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

# -------------------------------------------------------------------------------
# HELPER FUNCTION: Create Input Group
# -------------------------------------------------------------------------------
def create_input_group(label, id, value=None, input_type='number', options=None,
                       col_size=4, editable=True, info_text=None, units=None,
                       min_val=None, max_val=None):
    """
    Creates a Bootstrap column containing a label and an input field.
    If an info_text is provided, an info icon with a tooltip is added.
    """
    col_settings = {"md": col_size, "xs": 12}
    
    # Create the label with an optional info icon
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
    
    # Create the input field based on type
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
    """
    Fetch vessel details using the provided search term and type.
    Example API call:
    https://natpower-marine-api-dev.azurewebsites.net/marinedata/getvesseldetails_engine?imo=9419163&mmsi=9419163
    """
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
    """
    Returns the image filename corresponding to the given vessel type.
    If the vessel type is not recognized, returns 'default_vessel.png'.
    """
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
        # Hidden store to keep vessel data across callbacks
        dcc.Store(id='vessel-data-store'),
        
        html.H1("Step 1: Vessel Details", className="mb-4", style={"color": PRIMARY_COLOR}),
        
        # Vessel Search Section
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
        
        # Basic Vessel Information Section
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
        
        # Technical Specifications & Engine Info Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Technical Specs & Engine Info", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Main Engine Power", "main-power", DEFAULT_MAIN_ENGINE_POWER,
                                       "number", info_text="Main engine power (kW)", units="kW"),
                    create_input_group("Main Engine Type", "main-engine-type", DEFAULT_VESSEL.get("main_engine_type", "Unknown"),
                                       "text", col_size=4, info_text="Type of main engine"),
                    create_input_group("Main Fuel Type", "main-fuel-type", DEFAULT_MAIN_FUEL_TYPE,
                                       "dropdown", options=FUEL_OPTIONS, col_size=4, info_text="Main fuel type")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Auxiliary Engine Power", "aux-power", DEFAULT_AUX_ENGINE_POWER,
                                       "number", info_text="Auxiliary engine power (kW)", units="kW"),
                    create_input_group("Auxiliary Engine Type", "aux-engine-type", DEFAULT_VESSEL.get("aux_engine_type", "Unknown"),
                                       "text", col_size=4, info_text="Type of auxiliary engine"),
                    create_input_group("Aux Fuel Type", "aux-fuel-type", DEFAULT_AUX_FUEL_TYPE,
                                       "dropdown", options=FUEL_OPTIONS, col_size=4, info_text="Auxiliary fuel type")
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Operational Profile Section
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
                    create_input_group("Sailing Engine Load", "sailing-engine-load", DEFAULT_SAILING_ENGINE_LOAD * 100,
                                       "number", info_text="Engine load during sailing (0-100%)", min_val=0, max_val=100, units="%"),
                    create_input_group("Working Engine Load", "working-engine-load", DEFAULT_WORKING_ENGINE_LOAD * 100,
                                       "number", info_text="Engine load during working (0-100%)", min_val=0, max_val=100, units="%"),
                    create_input_group("Shore Engine Load", "shore-engine-load", DEFAULT_SHORE_ENGINE_LOAD * 100,
                                       "number", info_text="Engine load at shore (0-100%)", min_val=0, max_val=100, units="%")
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Maintenance & Costs Section
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
        
        # Future Inputs & Fuel Blend Section
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
        
        # Calculate Button and Status (when clicked, the callback gathers final parameters)
        dbc.Button("Calculate Emissions & Costs", id="calculate-button", color="primary", className="mt-3"),
        html.Div(id="calculation-status", className="mt-3", style={"color": TEXT_COLOR}),
        
        # Debugging Section
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

# ------------------------------------------------------------------------------
# CALLBACK: Link the "Calculate Emissions & Costs" button to send final parameters
# ------------------------------------------------------------------------------
# Note: This callback should be registered with your Dash app.
# If you are using a separate callbacks file, you can move this function there.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

@app.callback(
    Output('calculation-status', 'children'),
    Input('calculate-button', 'n_clicks'),
    State('main-power', 'value'),
    State('aux-power', 'value'),
    State('main-fuel-type', 'value'),
    State('aux-fuel-type', 'value'),
    State('sailing-days', 'value'),
    State('working-days', 'value'),
    State('idle-days', 'value'),
    State('shore-days', 'value'),
    State('sailing-engine-load', 'value'),
    State('working-engine-load', 'value'),
    State('shore-engine-load', 'value'),
    State('engine-maint-cost', 'value'),
    State('spares-cost', 'value'),
    State('fueleu-penalty', 'value'),
    State('future-main-fuel-type', 'value'),
    State('future-aux-fuel-type', 'value'),
    State('biofuels-spares-cost', 'value'),
    State('fueleu-future-penalty', 'value'),
    State('parasitic-load', 'value'),
    State('biofuels-blend', 'value'),
    State('shore-maint-cost', 'value'),
    State('shore-spares-cost', 'value'),
    State('shore-enable', 'value'),
    State('npv-rate', 'value'),
    State('capex', 'value'),
    State('vessel-data-store', 'data')
)
def calculate_emissions(n_clicks, main_power, aux_power, main_fuel_type, aux_fuel_type,
                        sailing_days, working_days, idle_days, shore_days,
                        sailing_engine_load, working_engine_load, shore_engine_load,
                        engine_maint_cost, spares_cost, fueleu_penalty,
                        future_main_fuel_type, future_aux_fuel_type, biofuels_spares_cost,
                        fueleu_future_penalty, parasitic_load, biofuels_blend,
                        shore_maint_cost, shore_spares_cost, shore_enable, npv_rate, capex,
                        vessel_data):
    if not n_clicks:
        return ""
    # Build final parameters from the input states
    final_params = {
        "main_engine_power_kw": float(main_power) if main_power is not None else DEFAULT_MAIN_ENGINE_POWER,
        "aux_engine_power_kw": float(aux_power) if aux_power is not None else DEFAULT_AUX_ENGINE_POWER,
        "sailing_days": int(sailing_days) if sailing_days is not None else DEFAULT_SAILING_DAYS,
        "working_days": int(working_days) if working_days is not None else DEFAULT_WORKING_DAYS,
        "idle_days": int(idle_days) if idle_days is not None else DEFAULT_IDLE_DAYS,
        "shore_days": int(shore_days) if shore_days is not None else DEFAULT_SHORE_DAYS,
        "sailing_engine_load": float(sailing_engine_load) / 100.0 if sailing_engine_load is not None else DEFAULT_SAILING_ENGINE_LOAD,
        "working_engine_load": float(working_engine_load) / 100.0 if working_engine_load is not None else DEFAULT_WORKING_ENGINE_LOAD,
        "shore_engine_load": float(shore_engine_load) / 100.0 if shore_engine_load is not None else DEFAULT_SHORE_ENGINE_LOAD,
        "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(engine_maint_cost) if engine_maint_cost is not None else DEFAULT_ENGINE_MAINT_COST,
        "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(spares_cost) if spares_cost is not None else DEFAULT_SPARES_COST,
        "FUELEU_CURRENT_PENALTY_PER_YEAR": float(fueleu_penalty) if fueleu_penalty is not None else DEFAULT_FUELEU_CURRENT_PENALTY,
        "future_main_fuel_type": future_main_fuel_type if future_main_fuel_type is not None else DEFAULT_FUTURE_MAIN_FUEL_TYPE,
        "future_aux_fuel_type": future_aux_fuel_type if future_aux_fuel_type is not None else DEFAULT_FUTURE_AUX_FUEL_TYPE,
        "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(biofuels_spares_cost) if biofuels_spares_cost is not None else DEFAULT_BIOFUELS_SPARES_COST,
        "FUELEU_FUTURE_PENALTY_PER_YEAR": float(fueleu_future_penalty) if fueleu_future_penalty is not None else DEFAULT_FUELEU_FUTURE_PENALTY,
        "PARASITIC_LOAD_ENGINE": float(parasitic_load) if parasitic_load is not None else DEFAULT_PARASITIC_LOAD,
        "BIOFUELS_BLEND_PERCENTAGE": float(biofuels_blend) / 100.0 if biofuels_blend is not None else DEFAULT_BIOFUELS_BLEND,
        "SHORE_POWER_MAINTENANCE_PER_DAY": float(shore_maint_cost) if shore_maint_cost is not None else DEFAULT_SHORE_MAINT_COST,
        "SHORE_POWER_SPARES_PER_DAY": float(shore_spares_cost) if shore_spares_cost is not None else DEFAULT_SHORE_SPARES_COST,
        "shore_enable": "true" if (shore_enable and shore_enable.lower() == "yes") else "false",
        "npv_rate": float(npv_rate) / 100.0 if npv_rate is not None else DEFAULT_NPV_RATE,
        "CAPEX": float(capex) if capex is not None else DEFAULT_CAPEX,
        "main_fuel_type": main_fuel_type if main_fuel_type is not None else DEFAULT_MAIN_FUEL_TYPE,
        "aux_fuel_type": aux_fuel_type if aux_fuel_type is not None else DEFAULT_AUX_FUEL_TYPE,
        "reporting_year": DEFAULT_REPORTING_YEAR,  # Could be updated if vessel_data provides a different value.
        "vessel": vessel_data if vessel_data is not None else DEFAULT_VESSEL
    }
    
    print("DEBUG: Final parameters from inputs:", final_params)
    
    # Build the full API URL with query string
    qs = urlencode(final_params)
    full_url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    print("DEBUG: Full API URL:", full_url)
    
    try:
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        api_data = response.json()
        print("DEBUG: API Data received:", api_data)
        return "Calculation successful."
    except Exception as e:
        print("DEBUG: Error during API call:", e)
        return f"Calculation failed: {e}"

if __name__ == "__main__":
    app.layout = layout()
    app.run_server(debug=True)
