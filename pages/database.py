from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

# Define consistent styling constants
PRIMARY_COLOR = "#0A4B8C"  # Updated deep navy for consistency
TEXT_COLOR = "#212121"

def layout():
    # Load sample data from the CSV files in the data folder
    regulations = pd.read_csv('data/regulations.csv')
    prices_data = pd.read_csv('data/PRICES_DATA.csv')
    fuel_data = pd.read_csv('data/FUEL_DATA.csv')
    
    # Create a DataTable for the Regulations data
    regulations_table = dash_table.DataTable(
        id='regulations-table',
        columns=[{"name": col, "id": col} for col in regulations.columns],
        data=regulations.to_dict('records'),
        style_table={'overflowX': 'auto'},
        filter_action='native',
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={
            'backgroundColor': PRIMARY_COLOR,
            'color': 'white',
            'fontWeight': 'bold'
        }
    )
    
    # Create a DataTable for the Prices data
    prices_table = dash_table.DataTable(
        id='prices-table',
        columns=[{"name": col, "id": col} for col in prices_data.columns],
        data=prices_data.to_dict('records'),
        style_table={'overflowX': 'auto'},
        filter_action='native',
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={
            'backgroundColor': PRIMARY_COLOR,
            'color': 'white',
            'fontWeight': 'bold'
        }
    )
    
    # Create a DataTable for the Fuel data with a unique id
    fuel_data_table = dash_table.DataTable(
        id='fuel-data-table',
        columns=[{"name": col, "id": col} for col in fuel_data.columns],
        data=fuel_data.to_dict('records'),
        style_table={'overflowX': 'auto'},
        filter_action='native',
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={
            'backgroundColor': PRIMARY_COLOR,
            'color': 'white',
            'fontWeight': 'bold'
        }
    )
    
    # Define cards for each dataset inside separate tabs
    regulations_tab = dbc.Tab(
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("IMO Regulations Database", style={"color": "white"}),
                    style={"backgroundColor": PRIMARY_COLOR}
                ),
                dbc.CardBody(regulations_table)
            ],
            className="mb-4",
            style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
        ),
        label="Regulations"
    )
    
    prices_tab = dbc.Tab(
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Fuel & Energy Prices Data", style={"color": "white"}),
                    style={"backgroundColor": PRIMARY_COLOR}
                ),
                dbc.CardBody(prices_table)
            ],
            className="mb-4",
            style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
        ),
        label="Fuel Prices"
    )
    
    fuel_data_tab = dbc.Tab(
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Fuel Data", style={"color": "white"}),
                    style={"backgroundColor": PRIMARY_COLOR}
                ),
                dbc.CardBody(fuel_data_table)
            ],
            className="mb-4",
            style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}
        ),
        label="Fuel Data"
    )
    
    return dbc.Container([
        html.H2("Regulatory & Prices Database", className="mb-4", style={"color": PRIMARY_COLOR}),
        dbc.Tabs([regulations_tab, prices_tab, fuel_data_tab])
    ], fluid=True, className="py-4")
