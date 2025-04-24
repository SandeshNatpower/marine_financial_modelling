
#pages/input_module.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import config  # Assumes config has FUEL_OPTIONS, DEFAULT_VESSEL, FINANCIAL_ENDPOINT, etc.
import requests
from urllib.parse import urlencode
import config
# -------------------------------------------------------------------------------
# GLOBAL CONSTANTS AND DEFAULTS
# -------------------------------------------------------------------------------
PRIMARY_COLOR = "#0A4B8C"
TEXT_COLOR = "#212121"
FUEL_OPTIONS = config.FUEL_OPTIONS

# The default vessel is still provided by config but can be overwritten
DEFAULT_VESSEL = config.DEFAULT_VESSEL
DEFAULT_PLACES = config.DEFAULT_PLACES

# Default values aligned with API requirements (used initially in the UI)
DEFAULT_SAILING_DAYS = 199
DEFAULT_WORKING_DAYS = 40
DEFAULT_IDLE_DAYS = 126
DEFAULT_SHORE_DAYS = 0
DEFAULT_REPORTING_YEAR = 2030
DEFAULT_FUELEU_CURRENT_PENALTY = 729348.5444
DEFAULT_FUELEU_FUTURE_PENALTY = 0
DEFAULT_PARASITIC_LOAD = 95
DEFAULT_BIOFUELS_BLEND = 30
DEFAULT_INFLATION_RATE = 2
DEFAULT_NPV_RATE = 0
DEFAULT_CAPEX = 19772750
DEFAULT_MAIN_ENGINE_POWER = 38400
DEFAULT_AUX_ENGINE_POWER = 2020

# IMPORTANT: Engine loads are now stored directly as percentages.
DEFAULT_SAILING_ENGINE_LOAD = 50    # instead of 0.5 (i.e. 50%)
DEFAULT_WORKING_ENGINE_LOAD = 30    # instead of 0.3 (i.e. 30%)
DEFAULT_SHORE_ENGINE_LOAD = 39.5    # instead of 0.395 (i.e. 39.5%)

DEFAULT_SHORE_PORT = 2
DEFAULT_MAIN_FUEL_TYPE = "MDO"
DEFAULT_AUX_FUEL_TYPE = "MDO"
DEFAULT_FUTURE_MAIN_FUEL_TYPE = "Diesel-Bio-diesel"
DEFAULT_FUTURE_AUX_FUEL_TYPE = "Diesel-Bio-diesel"
DEFAULT_ENGINE_MAINT_COST = 20
DEFAULT_SPARES_COST = 2
DEFAULT_SHORE_MAINT_COST = 480
DEFAULT_SHORE_SPARES_COST = 480
DEFAULT_BIOFUELS_SPARES_COST = 3
DEFAULT_SHORE_ENABLE = False

# New defaults for engine speed
DEFAULT_MAIN_ENGINE_SPEED = "MEDIUM"
DEFAULT_AUX_ENGINE_SPEED = "MEDIUM"

DEFAULT_SCENARIO_FUTURE_AUX_FUEL = "Diesel-Bio-diesel"

DEFAULT_CURRENCY = "EUR"
CURRENCY_OPTIONS=[{"label": "EUR", "value": "EUR"},
                  {"label": "USD", "value": "USD"},
                  {"label": "GBP", "value": "GBP"}],
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
    url = "https://natpower-marine-api-dev.azurewebsites.net/marinedata/getvesseldetails_engine_places?"
    params = {"imo": search_term, "mmsi": search_term} if search_type == 'imo' else {"vesselname": search_term}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "vessel_summary" and "places_summary"in data:
            if data["vessel_summary"] and data["places_summary"]:
                # Extract the first vessel and return it.
                return data["vessel_summary"][0], data["places_summary"]
            else:
                return DEFAULT_VESSEL, DEFAULT_PLACES
        else:
            return DEFAULT_VESSEL, DEFAULT_PLACES
    except requests.RequestException as e:
        print(f"Exception fetching vessel details: {e}")
        return DEFAULT_VESSEL, DEFAULT_PLACES


# -------------------------------------------------------------------------------
# VESSEL IMAGE HANDLER
# -------------------------------------------------------------------------------
# pages/input_module.py

def get_vessel_image_path(vessel_type):
    """
    Return the corresponding vessel image path based on the vessel type.
    If no match is found, return 'default_vessel.png'.
    """

    # Handle empty or None input
    if not vessel_type:
        return "default_vessel.png"
    
    # If vessel_type is a dict (e.g., from a Dropdown), extract 'value'
    if isinstance(vessel_type, dict):
        vessel_type = vessel_type.get('value', '')

    # Normalize for case-insensitive matching
    normalized_type = vessel_type.strip().lower()

    # Define the vessel type mapping (key = lowercase category, value = exact image filename)
    vessel_type_map = {
        "Auto carrier": "Auto Carrier.jpg",
        "Cargo vessels": "Cargo vessels.jpg",
        "chemical tankers": "Chemical Tankers.jpg",
        "Container vessels": "Container vessels.jpg",
        "crude oil tanker": "Crude oil tanker.jpg",
        "cruise ships": "Cruise ships.jpg",
        "ferry": "Ferry.jpg",
        "non-serviceble": "Non-serviceble.jpg",
        "offshore supply": "Offshore Supply.jpg",
        "other": "Other.jpg",
        "service": "Service.jpg"
    }

    # 1) Exact match check
    if normalized_type in vessel_type_map:
        return vessel_type_map[normalized_type]

    # 2) Fallback to partial match if no exact match
    #    e.g., user types "cargo vessels (large)"
    for key, image in vessel_type_map.items():
        if key in normalized_type or normalized_type in key:
            return image

    # 3) Final fallback: default image
    return "default_vessel.png"



def get_places_summary_table(vessel_data):
    import pandas as pd
    from dash import html, dash_table
    """
    Generate a Dash HTML layout showing:
      - A title header
      - A DataTable with columns for Port Name, Energy (MWh), % of Total, Idle Days, Working Days, and MWh/Working Day.
    
    Args:
        vessel_data (dict or list): The vessel data that contains 'places_summary' or is a list of place dicts.

    Returns:
        html.Div: A Dash HTML layout containing the table.
    """

    # 1. Extract or assume the list of places
    if isinstance(vessel_data, dict) and 'places_summary' in vessel_data:
        places_data = vessel_data['places_summary']
    elif isinstance(vessel_data, list):
        places_data = vessel_data
    else:
        places_data = []
    
    # Convert to DataFrame
    df = pd.DataFrame(places_data)
    
    # If empty, return a "no data" layout
    if df.empty:
        return html.Div([
            html.P("No port data available.")
        ])

    # 2. Prepare data for table
    # Ensure numeric columns are recognized
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    
    # Round numeric columns to 2 decimals
    for col in numeric_cols:
        df[col] = df[col].apply(lambda x: round(x, 2) if pd.notnull(x) else x)
    
    # Calculate total energy for later percentage computation
    total_energy = df['total_ci_mwh'].sum()
    
    # Create new columns for display:
    #   % of Total, MWh/Working Day
    df['percent_of_total'] = df['total_ci_mwh'] / total_energy * 100
    df['mwh_per_working_day'] = df.apply(
        lambda row: row['total_ci_mwh'] / row['working_days'] 
                    if (row.get('working_days') and row['working_days'] != 0) else None, 
        axis=1
    )

    # Round these new columns as well
    df['percent_of_total'] = df['percent_of_total'].apply(lambda x: round(x, 2) if pd.notnull(x) else x)
    df['mwh_per_working_day'] = df['mwh_per_working_day'].apply(lambda x: round(x, 2) if pd.notnull(x) else x)

    # 3. Reorder and rename columns for a friendlier display
    df_display = df[[ 
        'port_name',         # 1
        'total_ci_mwh',      # 2
        'percent_of_total',  # 3
        'idle_days',         # 4
        'working_days',      # 5
        'mwh_per_working_day'# 6
    ]].rename(columns={
        'port_name': 'Port Name',
        'total_ci_mwh': 'Energy (MWh)',
        'percent_of_total': '% of Total',
        'idle_days': 'Idle Days',
        'working_days': 'Working Days',
        'mwh_per_working_day': 'Cold Ironing MWh/Working Day'
    })

    # 4. Build the DataTable
    columns = [
        {"name": "Port Name",         "id": "Port Name",         "type": "text"},
        {"name": "Energy (MWh)",      "id": "Energy (MWh)",      "type": "numeric"},
        {"name": "% of Total",        "id": "% of Total",        "type": "numeric"},
        {"name": "Idle Days",         "id": "Idle Days",         "type": "numeric"},
        {"name": "Working Days",      "id": "Working Days",      "type": "numeric"},
        {"name": "MWh/Working Day",   "id": "MWh/Working Day",   "type": "numeric"},
    ]
    
    # Right-align numeric columns
    numeric_cols_conditional = [
        {'if': {'column_id': c}, 'textAlign': 'right'}
        for c in ["Energy (MWh)", "% of Total", "Idle Days", "Working Days", "MWh/Working Day"]
    ]

    data_table = dash_table.DataTable(
        data=df_display.to_dict("records"),
        columns=columns,
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={
            'width': '100%',
            'overflowX': 'auto'
        },
        style_header={
            'backgroundColor': '#0A4B8C',
            'fontWeight': 'bold',
            'color': 'white',
            'whiteSpace': 'normal',
            'textAlign': 'center'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '5px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'minWidth': '70px',
            'maxWidth': '120px',
            'fontSize': '20px'  # Increased font size
        },
        style_cell_conditional=numeric_cols_conditional,
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]
    )

    # 5. Construct the layout with title and table (summary statistics removed)
    layout = html.Div([
        data_table
    ], style={"margin": "20px"})
    
    return layout




def layout():
    return dbc.Container(
        [   
           
            html.H1(
                "Step 1: Vessel Details (version 1.3)",
                className="mb-4",
                style={"color": PRIMARY_COLOR, "textAlign": "center"}
            ),
    
            # -----------------------------
            # Vessel Data Search Card
            # -----------------------------
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Search for Vessel Data", style={"color": "white", "margin": 0}),
                        style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    create_input_group(
                                        label="Search Type",
                                        id="search-type",
                                        value="imo",
                                        input_type="dropdown",
                                        options=[
                                            {"label": "Vessel Name", "value": "name"},
                                            {"label": "IMO/MMSI", "value": "imo"}
                                        ],
                                        col_size=3,
                                        info_text="Select search type"
                                    ),
                                    create_input_group(
                                        label="Search Term",
                                        id="search-term",
                                        value=None,
                                        input_type="text",
                                        col_size=6,
                                        info_text="Enter IMO, MMSI, or vessel name"
                                    ),
                                    dbc.Col(
                                        [
                                            html.Br(),
                                            dbc.Button("Search", id="search-button", color="primary", className="mt-2", style={"width": "100%"})
                                        ],
                                        md=3, xs=12
                                    )
                                ],
                                className="mb-3"
                            ),
                            html.Div(id="search-results")
                        ],
                        style={"padding": "20px"}
                    ),
                ],
                className="mb-4",
                style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
            ),
    
            # -----------------------------
            # Basic Vessel Information Card
            # -----------------------------
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Basic Vessel Information", style={"color": "white", "margin": 0}),
                        style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
                    ),
                    dbc.CardBody(
                        [
                            # First Row: Image (Left) and Details (Right)
                            dbc.Row(
                                [
                                    # Vessel Image Column (Left)
                                    dbc.Col(
                                        [
                                            html.Div(
                                                html.Img(
                                                    id="vessel-image",
                                                    src="/assets/default_vessel.png",
                                                    style={
                                                        "width": "100%",
                                                        "height": "auto",
                                                        "maxHeight": "300px",
                                                        "objectFit": "contain",
                                                        "borderRadius": "8px",
                                                        "boxShadow": "0 2px 10px rgba(0,0,0,0.1)"
                                                    }
                                                ),
                                                className="text-center"
                                            ),
                                            html.Div(id="vessel-type-display", className="text-center mt-2")
                                        ],
                                        md=4, xs=12
                                    ),
                                    
                                    # Vessel Details Column (Right)
                                    dbc.Col(
                                        [
                                            dbc.Row(
                                                create_input_group(
                                                    label="Vessel Name",
                                                    id="vessel-name",
                                                    value=DEFAULT_VESSEL["vessel_name"],
                                                    input_type="text",
                                                    col_size=12,
                                                    editable=True,
                                                    info_text="Full vessel name"
                                                ),
                                                className="mb-3"
                                            ),
                                            dbc.Row(
                                                [
                                                    create_input_group(
                                                        label="IMO Number",
                                                        id="imo-number",
                                                        value=DEFAULT_VESSEL["imo"],
                                                        input_type="number",
                                                        col_size=6,
                                                        editable=True,
                                                        info_text="IMO/MMSI number"
                                                    ),
                                                    create_input_group(
                                                        label="Vessel Category",
                                                        id="vessel-category",
                                                        value=DEFAULT_VESSEL["vessel_category"],
                                                        input_type="text",
                                                        col_size=6,
                                                        editable=True,
                                                        info_text="Vessel category"
                                                    ),
                                                ],
                                                className="mb-3"
                                            ),
                                            dbc.Row(
                                                [
                                                    create_input_group(
                                                        label="Gross Tonnage",
                                                        id="gross-tonnage",
                                                        value=DEFAULT_VESSEL["gross_tonnage"],
                                                        input_type="number",
                                                        col_size=3,
                                                        editable=True,
                                                        info_text="Gross tonnage",
                                                        units="GT"
                                                    ),
                                                    create_input_group(
                                                        label="Deadweight",
                                                        id="dwt",
                                                        value=DEFAULT_VESSEL["dwt"],
                                                        input_type="number",
                                                        col_size=3,
                                                        editable=True,
                                                        info_text="Deadweight tonnage",
                                                        units="mT"
                                                    ),
                                                    create_input_group(
                                                        label="Year Built",
                                                        id="year-built",
                                                        value=DEFAULT_VESSEL["build"],
                                                        input_type="number",
                                                        col_size=3,
                                                        editable=True,
                                                        info_text="Year the vessel was built"
                                                    ),
                                                    create_input_group(
                                                        label="Reporting Year",
                                                        id="reporting-year",
                                                        value=DEFAULT_REPORTING_YEAR,
                                                        input_type="number",
                                                        col_size=3,
                                                        editable=True,
                                                        info_text="Year for financial reporting"
                                                    ),
                                                ],
                                                className="mb-3"
                                            ),
                                        ],
                                        md=8, xs=12
                                    ),
                                ],
                                className="mb-4"
                            ),
                            
                            # Second Row: Places Summary Table (Full Width)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H5("Port Activity Summary", className="mb-3"),
                                            html.Div(
                                                id="places-summary-table-container",  # Container for the table
                                                style={
                                                    "width": "100%",
                                                    "borderRadius": "8px",
                                                    "boxShadow": "0 2px 10px rgba(0,0,0,0.1)",
                                                    "overflowX": "auto"
                                                }
                                            )
                                        ],
                                        xs=12
                                    )
                                ]
                            )
                        ],
                        style={"padding": "20px"}
                    ),
                ],
                className="mb-4",
                style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
            ),
    
            # -----------------------------
            # Technical Specs & Engine Info Card
            # -----------------------------
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Technical Specs & Engine Info", style={"color": "white", "margin": 0}),
                        style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    create_input_group(
                                        label="Main Engine Power",
                                        id="main-power",
                                        value=DEFAULT_MAIN_ENGINE_POWER,
                                        input_type="number",
                                        info_text="Main engine power (kW)",
                                        units="kW",
                                        col_size=4
                                    ),
                                    create_input_group(
                                        label="Main Engine Type",
                                        id="main-engine-type",
                                        value=DEFAULT_VESSEL.get("main_engine_type", "4-STROKE"),
                                        input_type="text",
                                        info_text="Type of main engine",
                                        col_size=4
                                    ),
                                    create_input_group(
                                        label="Main Fuel Type",
                                        id="main-fuel-type",
                                        value=DEFAULT_MAIN_FUEL_TYPE,
                                        input_type="dropdown",
                                        options=FUEL_OPTIONS,
                                        info_text="Main fuel type",
                                        col_size=4
                                    ),
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                create_input_group(
                                    label="Main Engine Speed",
                                    id="main-engine-speed",
                                    value=DEFAULT_MAIN_ENGINE_SPEED,
                                    input_type="dropdown",
                                    options=[
                                        {"label": "SLOW", "value": "SLOW"},
                                        {"label": "MEDIUM", "value": "MEDIUM"},
                                        {"label": "FAST", "value": "FAST"}
                                    ],
                                    info_text="Main engine speed",
                                    col_size=4
                                ),
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group(
                                        label="Auxiliary Engine Power",
                                        id="aux-power",
                                        value=DEFAULT_AUX_ENGINE_POWER,
                                        input_type="number",
                                        info_text="Auxiliary engine power (kW)",
                                        units="kW",
                                        col_size=4
                                    ),
                                    create_input_group(
                                        label="Auxiliary Engine Type",
                                        id="aux-engine-type",
                                        value=DEFAULT_VESSEL.get("aux_engine_type", "4-STROKE"),
                                        input_type="text",
                                        info_text="Type of auxiliary engine",
                                        col_size=4
                                    ),
                                    create_input_group(
                                        label="Aux Fuel Type",
                                        id="aux-fuel-type",
                                        value=DEFAULT_AUX_FUEL_TYPE,
                                        input_type="dropdown",
                                        options=FUEL_OPTIONS,
                                        info_text="Auxiliary fuel type",
                                        col_size=4
                                    ),
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                create_input_group(
                                    label="Auxiliary Engine Speed",
                                    id="aux-engine-speed",
                                    value=DEFAULT_AUX_ENGINE_SPEED,
                                    input_type="dropdown",
                                    options=[
                                        {"label": "SLOW", "value": "SLOW"},
                                        {"label": "MEDIUM", "value": "MEDIUM"},
                                        {"label": "FAST", "value": "FAST"}
                                    ],
                                    info_text="Auxiliary engine speed",
                                    col_size=4
                                ),
                                className="mb-3"
                            ),
                        ],
                        style={"padding": "20px"}
                    ),
                ],
                className="mb-4",
                style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
            ),
    
            # -----------------------------
            # Operational Profile Card
            # -----------------------------
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Operational Profile", style={"color": "white", "margin": 0}),
                        style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    create_input_group("Sailing Days/Year", "sailing-days", DEFAULT_SAILING_DAYS, "number",
                                                       info_text="Days sailing per year (total must be 365)", units="days", min_val=0, max_val=365),
                                    create_input_group("Working Days/Year", "working-days", DEFAULT_WORKING_DAYS, "number",
                                                       info_text="Days working per year (total must be 365)", units="days", min_val=0, max_val=365),
                                    create_input_group("Idle Days/Year", "idle-days", DEFAULT_IDLE_DAYS, "number",
                                                       info_text="Days idle per year (total must be 365)", units="days", min_val=0, max_val=365),
                                    create_input_group("Shore Days/Year", "shore-days", DEFAULT_SHORE_DAYS, "number",
                                                       info_text="Days at shore per year (total must be 365)", units="days", min_val=0, max_val=365)
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group("Shore Port", "shore-port", DEFAULT_SHORE_PORT, "number",
                                                       col_size=4, info_text="Number of shore ports"),
                                    create_input_group("Shore Enable", "shore-enable", "Yes" if DEFAULT_SHORE_ENABLE else "No",
                                                       "dropdown", options=["Yes", "No"], col_size=4, info_text="Enable shore power")
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group("Sailing Engine Load", "sailing-engine-load", DEFAULT_SAILING_ENGINE_LOAD,
                                                       "number", info_text="Engine load during sailing (0-100)", min_val=0, max_val=100, units="%"),
                                    create_input_group("Working Engine Load", "working-engine-load", DEFAULT_WORKING_ENGINE_LOAD,
                                                       "number", info_text="Engine load during working (0-100)", min_val=0, max_val=100, units="%"),
                                    create_input_group("Shore Engine Load", "shore-engine-load", DEFAULT_SHORE_ENGINE_LOAD,
                                                       "number", info_text="Engine load at shore (0-100)", min_val=0, max_val=100, units="%")
                                ]
                            )
                        ],
                        style={"padding": "20px"}
                    )
                ],
                className="mb-4",
                style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
            ),
    
            # -----------------------------
            # Maintenance & Costs Card
            # -----------------------------
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Maintenance & Costs", style={"color": "white", "margin": 0}),
                        style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
                    ),
                    dbc.CardBody(
                        dbc.Row(
                            [
                                create_input_group("Engine Maintenance Cost", "engine-maint-cost", DEFAULT_ENGINE_MAINT_COST,
                                                   "number", info_text="Maintenance cost per engine hour", units="EUR/h", min_val=0),
                                create_input_group("Spares/Consumables Cost", "spares-cost", DEFAULT_SPARES_COST,
                                                   "number", info_text="Spares cost per engine hour", units="EUR/h", min_val=0)
                            ]
                        ),
                        style={"padding": "20px"}
                    ),
                ],
                className="mb-4",
                style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
            ),
    
            # -----------------------------
            # Future Inputs & Fuel Blend Card
            # -----------------------------
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H4("Future Inputs & Fuel Blend", style={"color": "white", "margin": 0}),
                        style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    create_input_group(
                                        "Future Main Fuel Type", 
                                        "future-main-fuel-type", 
                                        DEFAULT_FUTURE_MAIN_FUEL_TYPE,
                                        "dropdown", 
                                        options=FUEL_OPTIONS, 
                                        col_size=6, 
                                        info_text="Future main fuel type"
                                    ),
                                    create_input_group(
                                        "Future Aux Fuel Type", 
                                        "future-aux-fuel-type", 
                                        DEFAULT_FUTURE_AUX_FUEL_TYPE,
                                        "dropdown", 
                                        options=FUEL_OPTIONS, 
                                        col_size=6, 
                                        info_text="Future auxiliary fuel type"
                                    )
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [

                                    create_input_group(
                                        "Biofuels Spares Cost", 
                                        "biofuels-spares-cost", 
                                        DEFAULT_BIOFUELS_SPARES_COST,
                                        "number", 
                                        info_text="Biofuels spares cost per engine hour", 
                                        units="EUR/h", 
                                        min_val=0
                                    )
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group(
                                        "Shore Power Maintenance/Day", 
                                        "shore-maint-cost", 
                                        DEFAULT_SHORE_MAINT_COST,
                                        "number", 
                                        info_text="Daily shore power maintenance cost", 
                                        units="EUR/day", 
                                        min_val=0
                                    ),
                                    create_input_group(
                                        "Shore Power Spares/Day", 
                                        "shore-spares-cost", 
                                        DEFAULT_SHORE_SPARES_COST,
                                        "number", 
                                        info_text="Daily shore power spares cost", 
                                        units="EUR/day", 
                                        min_val=0
                                    )
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group(
                                        "Parasitic Load Engine", 
                                        "parasitic-load", 
                                        DEFAULT_PARASITIC_LOAD,
                                        "number", 
                                        info_text="Parasitic load percentage (0-100)", 
                                        min_val=0, 
                                        max_val=100,
                                        units = "%"
                                    ),
                                    create_input_group(
                                        "Biofuels Blend (%)", 
                                        "biofuels-blend", 
                                        DEFAULT_BIOFUELS_BLEND,
                                        "number", 
                                        info_text="Biofuels blend percentage (0-100)", 
                                        units="%", 
                                        min_val=0, 
                                        max_val=100     
                                    )
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group(
                                        "Inflation Rate", 
                                        "inflation-rate", 
                                        DEFAULT_INFLATION_RATE,
                                        "number", 
                                        info_text="Annual inflation rate (0-100)", 
                                        units="%", 
                                        min_val=0
                                    ),
                                    create_input_group(
                                        "NPV Rate", 
                                        "npv-rate", 
                                        DEFAULT_NPV_RATE * 100,
                                        "number", 
                                        info_text="Net present value discount rate (0-100)", 
                                        units="%", 
                                        min_val=0
                                    )
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    create_input_group(
                                        "CAPEX", 
                                        "capex", 
                                        DEFAULT_CAPEX, 
                                        "number",
                                        info_text="Capital expenditure", 
                                        units="EUR", 
                                        min_val=0, 
                                        col_size=6
                                    )
                                ],
                                className="mb-3"
                            ),
                            dbc.Row(
                                create_input_group(
                                    label="Currency",
                                    id="currency-choice",
                                    value=DEFAULT_CURRENCY,
                                    input_type="dropdown",
                                    options=[
                                        {"label": "EUR", "value": "EUR"},
                                        {"label": "USD", "value": "USD"},
                                        {"label": "GBP", "value": "GBP"}
                                    ],
                                    info_text="Select reporting currency",
                                    col_size=4
                                ),
                                className="mb-3"
                            ),
                        ],
                        style={"padding": "20px"}
                    ),
                ],
                className="mb-4",
                style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
            ),
                
            dbc.Button(
                "Calculate Emissions & Costs",
                id="calculate-button",
                color="primary",
                className="mt-3",
                style={"width": "100%"}
            ),
            html.Div(
                id="calculation-status",
                className="mt-3",
                style={"color": TEXT_COLOR, "textAlign": "center"}
            ),

            # -----------------------------
            # Debug Section
            # -----------------------------
            html.Div(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H4("Debugging Information", id="debug-header", style={"color": "white", "cursor": "pointer", "margin": 0}),
                            style={"backgroundColor": "#6c757d", "padding": "10px 20px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                    html.P("This section shows technical details about the calculation process.", className="text-muted"),
                                    html.Div(id="debug-info")
                                ]
                            ),
                            id="debug-collapse",
                            is_open=False
                        )
                    ]
                ),
                className="mt-3 mb-5",
                id="debug-section"
            ),

            # -----------------------------
            # Footer
            # -----------------------------
            html.Footer(
                "Version 1.3",
                style={
                    "textAlign": "center",
                    "color": "gray",
                    "padding": "10px",
                    "fontSize": "14px",
                    "marginTop": "20px"
                }
            )
        ],fluid= True
    )
