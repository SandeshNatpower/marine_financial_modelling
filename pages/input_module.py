import json
import requests
from urllib.parse import urlencode
from dash import html, dcc
import dash_bootstrap_components as dbc
import config

###############################################################################
# GLOBAL CONSTANTS AND DEFAULTS
###############################################################################
PRIMARY_COLOR = "#0A4B8C"
TEXT_COLOR = "#212121"
FUEL_OPTIONS = config.FUEL_OPTIONS
DEFAULT_VESSEL = config.DEFAULT_VESSEL

###############################################################################
# HELPER FOR CREATING INPUT GROUPS
###############################################################################
def create_input_group(label, id, value=None, input_type='number', options=None,
                       col_size=4, editable=True, info_text=None, units=None):
    col_settings = {"md": col_size, "xs": 12}
    
    # Create a label with an info icon if info_text is provided.
    label_contents = [label]
    if info_text:
        label_contents.append(
            html.I(id=f"{id}-info-icon", className="fa fa-info-circle ml-1",
                   style={"cursor": "pointer", "color": "grey", "fontSize": "0.85rem"})
        )
    label_component = dbc.Label(label_contents, style={"color": TEXT_COLOR})
    
    # Create input field. For dropdowns, build options accordingly.
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
        if units:
            input_field = html.Div([input_field, html.Span(units, className="ml-1", 
                                                            style={"lineHeight": "38px"})])
    else:
        input_component = dbc.Input(
            id=id,
            type=input_type,
            value=value,
            disabled=not editable,
            style={"backgroundColor": "#e9ecef"} if not editable else {}
        )
        if units:
            input_field = dbc.InputGroup([input_component, dbc.InputGroupText(units)])
        else:
            input_field = input_component

    children = [label_component, input_field]
    
    if info_text:
        children.append(
            dbc.Tooltip(info_text, target=f"{id}-info-icon", placement="top")
        )
    
    return dbc.Col(children, **col_settings)

###############################################################################
# VESSEL DETAILS FETCHER
###############################################################################
def get_vessel_details(search_term, search_type='imo'):
    url = config.VESSEL_ENDPOINT
    params = {"imo": search_term, "mmsi": search_term} if search_type == 'imo' \
             else {"vesselname": search_term}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                return data[0]
            return DEFAULT_VESSEL
        else:
            print("Error fetching vessel details:", response.status_code)
            return DEFAULT_VESSEL
    except Exception as e:
        print("Exception fetching vessel details:", e)
        return DEFAULT_VESSEL

###############################################################################
# INPUT MODULE LAYOUT
###############################################################################
def layout():
    return html.Div([
        html.H1("Step 1: Vessel Details", className="mb-4", style={"color": PRIMARY_COLOR}),
        
        # Vessel Search Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Search for Vessel Data", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Search Type", style={"color": TEXT_COLOR}),
                        dcc.Dropdown(
                            id='search-type',
                            options=[
                                {'label': 'Vessel Name', 'value': 'name'},
                                {'label': 'IMO/MMSI', 'value': 'imo'}
                            ],
                            value='imo'
                        )
                    ], md=3, xs=12),
                    dbc.Col([
                        dbc.Label("Search Term", style={"color": TEXT_COLOR}),
                        dbc.Input(id='search-term', type='text')
                    ], md=6, xs=12),
                    dbc.Col([
                        html.Br(),
                        dbc.Button("Search", id='search-button', color='primary', className='mt-2')
                    ], md=3, xs=12)
                ]),
                html.Div(id='search-results')
            ])
        ], className='mb-4', style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Basic Vessel Information Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Basic Vessel Information", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Vessel Name", "vessel-name", DEFAULT_VESSEL["vessel_name"],
                                       'text', col_size=4, editable=False, info_text="Full vessel name"),
                    create_input_group("IMO Number", "imo-number", DEFAULT_VESSEL["imo"],
                                       'number', col_size=4, editable=False, info_text="IMO/MMSI number"),
                    create_input_group("Vessel Category", "vessel-category", DEFAULT_VESSEL["vessel_category"],
                                       'text', col_size=4, editable=False, info_text="Category of the vessel")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Gross Tonnage", "gross-tonnage", DEFAULT_VESSEL["gross_tonnage"],
                                       'number', col_size=4, editable=False, info_text="Gross tonnage", units="GT"),
                    create_input_group("Deadweight", "dwt", DEFAULT_VESSEL["dwt"],
                                       'number', col_size=4, info_text="Deadweight (metric tons)", units="mT"),
                    create_input_group("Year Built", "year-built", DEFAULT_VESSEL["year_built"],
                                       'number', col_size=4, info_text="Year the vessel was built"),
                    create_input_group("Reporting Year", "reporting-year", DEFAULT_VESSEL.get("reporting_year", 2030),
                                       'number', col_size=4, info_text="Year for financial reporting")
                ], className="mb-3")
            ])
        ], className='mb-4', style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Technical Specifications & Engine Info Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Technical Specs & Engine Info", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Main Engine Power", "main-power", DEFAULT_VESSEL.get("main_engine_power_kw", 38400),
                                       'number', info_text="Enter main engine power (kW)", units="kW"),
                    create_input_group("Main Engine Type", "main-engine-type", DEFAULT_VESSEL["main_engine_type"],
                                       'text', col_size=4, info_text="Type of main engine"),
                    create_input_group("Main Fuel Type", "main-fuel-type", DEFAULT_VESSEL.get("main_fuel_type", "MDO"),
                                       'dropdown', options=FUEL_OPTIONS, col_size=4, info_text="Select main fuel type")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Auxiliary Engine Power", "aux-power", DEFAULT_VESSEL.get("aux_engine_power_kw", 4020),
                                       'number', info_text="Enter auxiliary engine power (kW)", units="kW"),
                    create_input_group("Auxiliary Engine Type", "aux-engine-type", DEFAULT_VESSEL["aux_engine_type"],
                                       'text', col_size=4, info_text="Type of auxiliary engine"),
                    create_input_group("Aux Fuel Type", "aux-fuel-type", DEFAULT_VESSEL.get("aux_fuel_type", "MDO"),
                                       'dropdown', options=FUEL_OPTIONS, col_size=4, info_text="Select auxiliary fuel type")
                ])
            ])
        ], className='mb-4', style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Operational Profile Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Operational Profile", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Sailing Days/Year", "sailing-days", DEFAULT_VESSEL.get("sailing_days", 199),
                                       'number', info_text="Number of sailing days per year", units="days"),
                    create_input_group("Working Days/Year", "working-days", DEFAULT_VESSEL.get("working_days", 40),
                                       'number', info_text="Number of working days per year", units="days"),
                    create_input_group("Idle Days/Year", "idle-days", DEFAULT_VESSEL.get("idle_days", 126),
                                       'number', info_text="Number of idle days per year", units="days"),
                    create_input_group("Shore Days/Year", "shore-days", DEFAULT_VESSEL.get("shore_days", 0),
                                       'number', info_text="Number of shore days per year", units="days")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Shore Port", "shore-port", DEFAULT_VESSEL.get("shore_port", 2),
                                       'number', col_size=4, info_text="Number of shore ports available"),
                    create_input_group("Shore Enable", "shore-enable", "Yes" if DEFAULT_VESSEL.get("shore_enable", True) else "No",
                                       'dropdown', options=["Yes", "No"], col_size=4, info_text="Enable or disable shore power")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Sailing Engine Load", "sailing-engine-load", DEFAULT_VESSEL.get("sailing_engine_load", 0.5),
                                       'number', info_text="Engine load during sailing (as decimal)"),
                    create_input_group("Working Engine Load", "working-engine-load", DEFAULT_VESSEL.get("working_engine_load", 0.3),
                                       'number', info_text="Engine load during working (as decimal)"),
                    create_input_group("Shore Engine Load", "shore-engine-load", DEFAULT_VESSEL.get("shore_engine_load", 0.395),
                                       'number', info_text="Engine load during shore power (as decimal)")
                ])
            ])
        ], className='mb-4', style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Maintenance & Costs Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Maintenance & Costs", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Engine Maintenance Cost", "engine-maint-cost",
                                       DEFAULT_VESSEL.get("ENGINE_MAINTENANCE_COSTS_PER_HOUR", 20),
                                       'number', info_text="Cost per engine hour", units="EUR/h"),
                    create_input_group("Spares/Consumables Cost", "spares-cost",
                                       DEFAULT_VESSEL.get("SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR", 2),
                                       'number', info_text="Cost per engine hour", units="EUR/h"),
                    create_input_group("FUELEU Current Penalty", "fueleu-penalty",
                                       DEFAULT_VESSEL.get("FUELEU_CURRENT_PENALTY_PER_YEAR", 729348.5444),
                                       'number', info_text="Annual penalty cost", units="EUR/yr")
                ], className="mb-3")
            ])
        ], className='mb-4', style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Future Inputs & Regulations Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Future Inputs & Fuel Blend", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Row([
                    create_input_group("Future Main Fuel Type", "future-main-fuel-type",
                                       DEFAULT_VESSEL.get("future_main_fuel_type", "Diesel-Bio-diesel"),
                                       'dropdown', options=FUEL_OPTIONS, col_size=4,
                                       info_text="Select future main fuel type"),
                    create_input_group("Future Aux Fuel Type", "future-aux-fuel-type",
                                       DEFAULT_VESSEL.get("future_aux_fuel_type", "Diesel-Bio-diesel"),
                                       'dropdown', options=FUEL_OPTIONS, col_size=4,
                                       info_text="Select future auxiliary fuel type")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("FUELEU Future Penalty", "fueleu-future-penalty",
                                       DEFAULT_VESSEL.get("FUELEU_FUTURE_PENALTY_PER_YEAR", 237950.5332),
                                       'number', info_text="Annual future penalty cost", units="EUR/yr"),
                    create_input_group("Biofuels Spares Cost", "biofuels-spares-cost",
                                       DEFAULT_VESSEL.get("BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR", 3),
                                       'number', info_text="Cost per engine hour", units="EUR/h")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Shore Power Maintenance/Day", "shore-maint-cost",
                                       DEFAULT_VESSEL.get("SHORE_POWER_MAINTENANCE_PER_DAY", 45.486),
                                       'number', info_text="Daily maintenance cost", units="EUR/day"),
                    create_input_group("Shore Power Spares/Day", "shore-spares-cost",
                                       DEFAULT_VESSEL.get("SHORE_POWER_SPARES_PER_DAY", 45.486),
                                       'number', info_text="Daily spares cost", units="EUR/day")
                ], className="mb-3"),
                dbc.Row([
                    create_input_group("Parasitic Load Engine", "parasitic-load",
                                       DEFAULT_VESSEL.get("PARASITIC_LOAD_ENGINE", 0.95),
                                       'number', info_text="Enter parasitic load factor"),
                    create_input_group("Biofuels Blend (%)", "biofuels-blend",
                                       DEFAULT_VESSEL.get("BIOFUELS_BLEND_PERCENTAGE", 0.0),
                                       'number', info_text="Enter biofuels blend percentage", units="%")
                ])
            ])
        ], className='mb-4', style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Calculation Button
        dbc.Button("Calculate Emissions & Costs", id="calculate-button", color="primary", className="mt-3")
    ])
