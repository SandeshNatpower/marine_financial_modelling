from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

# Define consistent styling constants
PRIMARY_COLOR = "#0A4B8C"  # Deep navy for consistency
TEXT_COLOR = "#212121"
def layout():
    # Load CSV data
    regulations = pd.read_csv('data/regulations.csv')
    prices_data = pd.read_csv('data/PRICES_DATA.csv')
    fuel_data = pd.read_csv('data/FUEL_DATA.csv')
    fueleu_data = pd.read_csv('data/FUELEU.csv')
    
    # Define common table styles
    table_style = {
        'overflowX': 'auto',
        'border': '1px solid #ddd'
    }
    cell_style = {
        'textAlign': 'left',
        'padding': '8px',
        'fontFamily': 'Arial, sans-serif',
        'fontSize': '14px'
    }
    header_style = {
        'backgroundColor': PRIMARY_COLOR,
        'color': 'white',
        'fontWeight': 'bold',
        'padding': '8px',
        'fontFamily': 'Arial, sans-serif',
        'fontSize': '16px'
    }
    data_conditional = [
        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
    ]
    
    # Create tables
    regulations_table = dash_table.DataTable(
        id='regulations-table',
        columns=[{"name": col, "id": col} for col in regulations.columns],
        data=regulations.to_dict('records'),
        style_table=table_style,
        filter_action='native',
        style_cell=cell_style,
        style_header=header_style,
        style_data_conditional=data_conditional
    )
    
    prices_table = dash_table.DataTable(
        id='prices-table',
        columns=[{"name": col, "id": col} for col in prices_data.columns],
        data=prices_data.to_dict('records'),
        style_table=table_style,
        filter_action='native',
        style_cell=cell_style,
        style_header=header_style,
        style_data_conditional=data_conditional
    )
    
    fuel_data_table = dash_table.DataTable(
        id='fuel-data-table',
        columns=[{"name": col, "id": col} for col in fuel_data.columns],
        data=fuel_data.to_dict('records'),
        style_table=table_style,
        filter_action='native',
        style_cell=cell_style,
        style_header=header_style,
        style_data_conditional=data_conditional
    )
    
    fueleu_data_table = dash_table.DataTable(
        id='fueleu-data-table',
        columns=[{"name": col, "id": col} for col in fueleu_data.columns],
        data=fueleu_data.to_dict('records'),
        style_table=table_style,
        filter_action='native',
        style_cell=cell_style,
        style_header=header_style,
        style_data_conditional=data_conditional
    )
    
    # Build tab cards for each dataset
    regulations_tab = dbc.Tab(
        dbc.Card([
            dbc.CardHeader(
                html.H4("IMO Regulations Database", style={"color": "white", "margin": 0}),
                style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
            ),
            dbc.CardBody(regulations_table)
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        label="Regulations"
    )
    
    prices_tab = dbc.Tab(
        dbc.Card([
            dbc.CardHeader(
                html.H4("Fuel & Energy Prices Data", style={"color": "white", "margin": 0}),
                style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
            ),
            dbc.CardBody(prices_table)
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        label="Fuel Prices"
    )
    
    fuel_data_tab = dbc.Tab(
        dbc.Card([
            dbc.CardHeader(
                html.H4("Fuel Data", style={"color": "white", "margin": 0}),
                style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
            ),
            dbc.CardBody(fuel_data_table)
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        label="Fuel Data"
    )
    
    fueleu_data_tab = dbc.Tab(
        dbc.Card([
            dbc.CardHeader(
                html.H4("FUELEU Data", style={"color": "white", "margin": 0}),
                style={"backgroundColor": PRIMARY_COLOR, "padding": "10px 20px"}
            ),
            dbc.CardBody(fueleu_data_table)
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        label="FUELEU Data"
    )
    
    return dbc.Container([
        html.H2("Regulatory & Prices Database", className="mb-4", style={"color": PRIMARY_COLOR, "textAlign": "center"}),
        dbc.Tabs([regulations_tab, prices_tab, fuel_data_tab, fueleu_data_tab])
    ], fluid=True, className="py-4")