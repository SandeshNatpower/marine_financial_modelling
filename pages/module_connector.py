"""
Module connector that links input_module.py and output_module.py
"""
from dash import Input, Output, State, callback, no_update
from pages import output_module, api_functions

# Create callback to link input and output modules
@callback(
    # Output that updates the data store in output_module and switches to output tab
    [
        Output('emissions-data-store', 'data'),
        Output('tab-switch', 'data')
    ],
    # Input is the Calculate button click
    Input('calculate-button', 'n_clicks'),
    # States are all the input values we need to pass to output_module
    [
        State('main-power', 'value'),
        State('aux-power', 'value'),
        State('main-fuel-type', 'value'),
        State('aux-fuel-type', 'value'),
        State('sailing-days', 'value'),
        State('working-days', 'value'),
        State('shore-days', 'value'),
        State('sailing-engine-load', 'value'),
        State('working-engine-load', 'value'),
        State('shore-engine-load', 'value'),
        State('engine-maint-cost', 'value'),
        State('spares-cost', 'value'),
        State('fueleu-penalty', 'value'),
        State('vessel-data-store', 'data')
    ],
    prevent_initial_call=True
)
def connect_input_to_output(
    n_clicks, main_power, aux_power, main_fuel_type, aux_fuel_type,
    sailing_days, working_days, shore_days,
    sailing_engine_load, working_engine_load, shore_engine_load,
    engine_maint_cost, spares_cost, fueleu_penalty, vessel_data
):
    """
    When Calculate button is clicked, collect all input data and send it to output_module
    """
    if n_clicks is None:
        return no_update, no_update
        
    if not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
        return no_update, no_update

    # Prepare input data dictionary
    input_data = {
        "main_power": main_power,
        "aux_power": aux_power,
        "main_fuel_type": main_fuel_type,
        "aux_fuel_type": aux_fuel_type,
        "sailing_days": sailing_days,
        "working_days": working_days,
        "shore_days": shore_days,
        "sailing_engine_load": sailing_engine_load,
        "working_engine_load": working_engine_load,
        "shore_engine_load": shore_engine_load,
        "engine_maint_cost": engine_maint_cost,
        "spares_cost": spares_cost,
        "fueleu_penalty": fueleu_penalty
    }
    
    # Extract additional parameters from vessel_data
    if isinstance(vessel_data, dict):
        input_data["shore_port"] = vessel_data.get('shore_port', 1)
        input_data["reporting_year"] = vessel_data.get('reporting_year', 2030)
    
    # Call api_functions's function to update with this input data
    api_data = api_functions.update_from_input_module(input_data)
    
    # Return the API data and switch to output tab
    if api_data:
        return api_data, "output"
    else:
        return no_update, no_update