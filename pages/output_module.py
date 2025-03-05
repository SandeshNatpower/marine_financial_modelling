from dash import html, dcc
import dash_bootstrap_components as dbc
import config

# Helper Functions
def format_number(num):
    try:
        num = float(num)
        if num == int(num):
            return f"{int(num):,}"
        return f"{num:,.0f}"
    except Exception:
        return str(num)

def get_currency_symbol(currency):
    return config.CURRENCIES.get(currency, {}).get("symbol", currency)

def get_conversion_factor(currency):
    return config.CURRENCIES.get(currency, {}).get("conversion", 1.0)

def format_currency_value(value, currency, factor):
    try:
        value = float(value) * factor
        return f"{format_number(value)}"
    except Exception:
        return str(value)

def style_savings(val):
    try:
        num = float(val)
        if num > 0:
            return "text-success fw-bold"
        elif num < 0:
            return "text-danger fw-bold"
    except Exception:
        pass
    return ""

# TABLE FUNCTIONS
def get_current_output_table(api_data):
    current = api_data.get("current_table", {})
    
    # SFC Data
    sfc_data = (current.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    avg_sfc     = sfc_data.get("avg_sfc_day", 198)
    
    # Emissions Data
    co2_data  = (current.get("co2_emission_ttw") or [{}])[0]
    sailing_co2_ttw = co2_data.get("sailing_co2_emission_ttw", 286088)
    working_co2_ttw = co2_data.get("working_co2_emission_ttw", 198669)
    idle_co2_ttw    = co2_data.get("idle_co2_emission_ttw", 12562)
    avg_co2_ttw     = co2_data.get("avg_co2_ttw_day", 182086)
    
    # Engine Power Data
    eng_data  = (current.get("enginge_power") or [{}])[0]
    sailing_power = eng_data.get("sailing_power", 19200)
    working_power = eng_data.get("working_power", 11520)
    idle_power    = eng_data.get("idle_power", 798)
    max_power     = eng_data.get("max_power_day", 19200)
    avg_power     = eng_data.get("avg_power_req_day", 12006)
    
    # Energy Requirement Data
    power_day = (current.get("power_calc_day") or [{}])[0]
    sailing_energy = power_day.get("sailing_eneregy_req_kwh_day", 460800)
    working_energy = power_day.get("working_eneregy_req_kwh_day", 276480)
    shore_energy   = power_day.get("idle_eneregy_req_kwh_day", 19152)
    avg_energy     = power_day.get("power_req_day", 288142)
    
    # Fuel Consumption Data
    kg_data = (current.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 87889)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 61033)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 3859)
    avg_fuel_kg     = kg_data.get("avg_fuel_consumption_day", 55939)
    
    fuel_data = (current.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = fuel_data.get("sailing_fuel_consumption_liter", 98752)
    working_fuel_l = fuel_data.get("working_fuel_consumption_liter", 68577)
    idle_fuel_l    = fuel_data.get("idle_fuel_consumption_liter", 4336)
    avg_fuel_l     = fuel_data.get("avg_fuel_consumption_liter_day", 62853)
    
    engine_hours = {
        "sailing": 24,
        "working": 24,
        "idle": 24,
        "shore": 75,
        "average": 27
    }
    
    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Metric", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Sailing (199 days/yr)"),
            html.Th("Working (40 days/yr)"),
            html.Th("Idle/Moored (126 days/yr)"),
            html.Th("Shore Power"),
            html.Th("Average (per day)")
        ]), style={"backgroundColor": "#0A4B8C", "color": "white"}),
        html.Tbody([
            html.Tr([
                html.Td("Max. Power (kW)"),
                html.Td(format_number(sailing_power)),
                html.Td(format_number(working_power)),
                html.Td(format_number(idle_power)),
                html.Td("-"),
                html.Td(format_number(max_power))
            ]),
            html.Tr([
                html.Td("Avg. Power (kW)"),
                html.Td(format_number(sailing_power)),
                html.Td(format_number(working_power)),
                html.Td(format_number(idle_power)),
                html.Td("-"),
                html.Td(format_number(avg_power))
            ]),
            html.Tr([
                html.Td("Energy Req. (kWh)"),
                html.Td(format_number(sailing_energy)),
                html.Td(format_number(working_energy)),
                html.Td(format_number(shore_energy)),
                html.Td("-"),
                html.Td(format_number(avg_energy))
            ]),
            html.Tr([
                html.Td("Engine Hours (hrs)"),
                html.Td(format_number(engine_hours["sailing"])),
                html.Td(format_number(engine_hours["working"])),
                html.Td(format_number(engine_hours["idle"])),
                html.Td(format_number(engine_hours["shore"])),
                html.Td(format_number(engine_hours["average"]))
            ]),
            html.Tr([
                html.Td("Avg. SFC (g/kWh)"),
                html.Td(format_number(sailing_sfc)),
                html.Td(format_number(working_sfc)),
                html.Td(format_number(idle_sfc)),
                html.Td("-"),
                html.Td(format_number(avg_sfc))
            ]),
            html.Tr([
                html.Td("Fuel (kg)"),
                html.Td(format_number(sailing_fuel_kg)),
                html.Td(format_number(working_fuel_kg)),
                html.Td(format_number(idle_fuel_kg)),
                html.Td("-"),
                html.Td(format_number(avg_fuel_kg))
            ]),
            html.Tr([
                html.Td("Fuel (liters)"),
                html.Td(format_number(sailing_fuel_l)),
                html.Td(format_number(working_fuel_l)),
                html.Td(format_number(idle_fuel_l)),
                html.Td("-"),
                html.Td(format_number(avg_fuel_l))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (kg)"),
                html.Td(format_number(sailing_co2_ttw)),
                html.Td(format_number(working_co2_ttw)),
                html.Td(format_number(idle_co2_ttw)),
                html.Td("-"),
                html.Td(format_number(avg_co2_ttw))
            ]),
        ]),
    ], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def get_future_output_table(api_data):
    future = api_data.get("future_output_table", {})
    
    sfc_data = (future.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    avg_sfc     = sfc_data.get("avg_shore_sfc_day", 0)
    
    eng_data = (future.get("enginge_power") or [{}])[0]
    sailing_power = eng_data.get("sailing_power", 19200)
    working_power = eng_data.get("working_power", 11520)
    idle_power    = eng_data.get("idle_power", 798)
    max_power     = eng_data.get("max_power_day", 19200)
    avg_power     = eng_data.get("avg_shore_power_req_day", 0)
    
    power_day = (future.get("power_calc_day") or [{}])[0]
    sailing_energy = power_day.get("sailing_eneregy_req_kwh_day", 460800)
    working_energy = power_day.get("working_eneregy_req_kwh_day", 276480)
    shore_energy   = power_day.get("shore_eneregy_req_kwh_day", 0)
    avg_energy     = power_day.get("power_req_day", 288142)
    
    kg_data = (future.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 87889)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 61033)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 3859)
    avg_fuel_kg     = kg_data.get("avg_shore_fuel_consumption_day", 0)
    
    fuel_data = (future.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = fuel_data.get("future_sailing_fuel_consumption_liter", 99761)
    working_fuel_l = fuel_data.get("future_working_fuel_consumption_liter", 69277)
    idle_fuel_l    = fuel_data.get("future_idle_fuel_consumption_liter", 4381)
    avg_fuel_l     = fuel_data.get("future_avg_fuel_consumption_liter_day", 63495)
    
    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Metric"),
            html.Th("Sailing (199 days/yr)"),
            html.Th("Working (40 days/yr)"),
            html.Th("Idle/Moored (126 days/yr)"),
            html.Th("Shore Power"),
            html.Th("Average (per day)")
        ]), style={"backgroundColor": "#0A4B8C", "color": "white"}),
        html.Tbody([
            html.Tr([
                html.Td("Max. Power (kW)"),
                html.Td(format_number(sailing_power)),
                html.Td(format_number(working_power)),
                html.Td(format_number(idle_power)),
                html.Td("-"),
                html.Td(format_number(max_power))
            ]),
            html.Tr([
                html.Td("Avg. Power (kW)"),
                html.Td(format_number(sailing_power)),
                html.Td(format_number(working_power)),
                html.Td(format_number(idle_power)),
                html.Td("-"),
                html.Td(format_number(avg_power))
            ]),
            html.Tr([
                html.Td("Energy Req. (kWh)"),
                html.Td(format_number(sailing_energy)),
                html.Td(format_number(working_energy)),
                html.Td(format_number(shore_energy)),
                html.Td("-"),
                html.Td(format_number(avg_energy))
            ]),
            html.Tr([
                html.Td("Avg. SFC (g/kWh)"),
                html.Td(format_number(sailing_sfc)),
                html.Td(format_number(working_sfc)),
                html.Td(format_number(idle_sfc)),
                html.Td("-"),
                html.Td(format_number(avg_sfc))
            ]),
            html.Tr([
                html.Td("Fuel (kg)"),
                html.Td(format_number(sailing_fuel_kg)),
                html.Td(format_number(working_fuel_kg)),
                html.Td(format_number(idle_fuel_kg)),
                html.Td("-"),
                html.Td(format_number(avg_fuel_kg))
            ]),
            html.Tr([
                html.Td("Fuel (liters)"),
                html.Td(format_number(sailing_fuel_l)),
                html.Td(format_number(working_fuel_l)),
                html.Td(format_number(idle_fuel_l)),
                html.Td("-"),
                html.Td(format_number(avg_fuel_l))
            ]),
        ]),
    ], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def get_opex_comparison_table(api_data, currency, conv_factor):
    current_costs = (api_data.get("current_table", {}).get("costs") or [{}])[0]
    future_costs = (api_data.get("future_output_table", {}).get("costs") or [{}])[0]

    currency_symbol = get_currency_symbol(currency)

    current_fuel = current_costs.get("avg_fueleu_day", 1999)
    current_maint = current_costs.get("engine_maintenance_costs", 480)
    current_spares = current_costs.get("spares_consumables_costs", 48)
    current_total = current_fuel + current_maint + current_spares

    future_fuel = future_costs.get("future_avg_fueleu_day", 0)
    future_maint = future_costs.get("future_avg_engine_maintenance_costs_day", 480)
    future_spares = future_costs.get("future_avg_spares_consumables_costs_day", 72)
    future_total = future_fuel + future_maint + future_spares

    fuel_savings = current_fuel - future_fuel
    maint_savings = current_maint - future_maint
    spares_savings = current_spares - future_spares
    total_savings = current_total - future_total

    current_fuel_fmt = format_currency_value(current_fuel, currency, conv_factor)
    current_maint_fmt = format_currency_value(current_maint, currency, conv_factor)
    current_spares_fmt = format_currency_value(current_spares, currency, conv_factor)
    current_total_fmt = format_currency_value(current_total, currency, conv_factor)

    future_fuel_fmt = format_currency_value(future_fuel, currency, conv_factor)
    future_maint_fmt = format_currency_value(future_maint, currency, conv_factor)
    future_spares_fmt = format_currency_value(future_spares, currency, conv_factor)
    future_total_fmt = format_currency_value(future_total, currency, conv_factor)

    fuel_savings_fmt = format_currency_value(fuel_savings, currency, conv_factor)
    maint_savings_fmt = format_currency_value(maint_savings, currency, conv_factor)
    spares_savings_fmt = format_currency_value(spares_savings, currency, conv_factor)
    total_savings_fmt = format_currency_value(total_savings, currency, conv_factor)

    fuel_savings_style = style_savings(fuel_savings)
    maint_savings_style = style_savings(maint_savings)
    spares_savings_style = style_savings(spares_savings)
    total_savings_style = style_savings(total_savings)

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Metric"),
            html.Th(f"Current ({currency_symbol})"),
            html.Th(f"Future ({currency_symbol})"),
            html.Th(f"Savings ({currency_symbol})")
        ]), style={"backgroundColor": "#0A4B8C", "color": "white"}),
        html.Tbody([
            html.Tr([
                html.Td("Fuel Cost"),
                html.Td(current_fuel_fmt),
                html.Td(future_fuel_fmt),
                html.Td(fuel_savings_fmt, className=fuel_savings_style)
            ]),
            html.Tr([
                html.Td("Maintenance Cost"),
                html.Td(current_maint_fmt),
                html.Td(future_maint_fmt),
                html.Td(maint_savings_fmt, className=maint_savings_style)
            ]),
            html.Tr([
                html.Td("Spares & Consumables"),
                html.Td(current_spares_fmt),
                html.Td(future_spares_fmt),
                html.Td(spares_savings_fmt, className=spares_savings_style)
            ]),
            html.Tr([
                html.Td("Total OPEX", className="fw-bold"),
                html.Td(current_total_fmt, className="fw-bold"),
                html.Td(future_total_fmt, className="fw-bold"),
                html.Td(total_savings_fmt, className=total_savings_style)
            ]),
        ]),
    ], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def get_emissions_comparison_table(api_data):
    savings_data = (api_data.get("emissions_table", {}).get("Savings") or [{}])[0]
    savings_perc_data = (api_data.get("emissions_table", {}).get("Savings_perc") or [{}])[0]

    ch4 = savings_data.get("savings_avg_ch4_ttw", 0)
    co2_ttw = savings_data.get("savings_avg_co2_ttw", 54625)
    co2_wtw = savings_data.get("savings_avg_co2_wtw", 60787)
    nox = savings_data.get("savings_avg_nox_ttw", 906)
    pm = savings_data.get("savings_avg_pm_ttw", 15)
    sox = savings_data.get("savings_avg_sox_ttw", 35)

    perc_ch4 = savings_perc_data.get("perc_savings_avg_ch4_ttw", 0)
    perc_co2_ttw = savings_perc_data.get("perc_savings_avg_co2_ttw", 30)
    perc_co2_wtw = savings_perc_data.get("perc_savings_avg_co2_wtw", 29)
    perc_nox = savings_perc_data.get("perc_savings_avg_nox_ttw", 30)
    perc_pm = savings_perc_data.get("perc_savings_avg_pm_ttw", 28)
    perc_sox = savings_perc_data.get("perc_savings_avg_sox_ttw", 29)

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Pollutant"),
            html.Th("Savings (kg)"),
            html.Th("Savings (%)")
        ]), style={"backgroundColor": "#0A4B8C", "color": "white"}),
        html.Tbody([
            html.Tr([
                html.Td("CH₄ Emissions"),
                html.Td(format_number(ch4), className=style_savings(ch4)),
                html.Td(f"{perc_ch4:.1f}%", className=style_savings(perc_ch4))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (TtW)"),
                html.Td(format_number(co2_ttw), className=style_savings(co2_ttw)),
                html.Td(f"{perc_co2_ttw:.1f}%", className=style_savings(perc_co2_ttw))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (WtW)"),
                html.Td(format_number(co2_wtw), className=style_savings(co2_wtw)),
                html.Td(f"{perc_co2_wtw:.1f}%", className=style_savings(perc_co2_wtw))
            ]),
            html.Tr([
                html.Td("NOₓ Emissions"),
                html.Td(format_number(nox), className=style_savings(nox)),
                html.Td(f"{perc_nox:.1f}%", className=style_savings(perc_nox))
            ]),
            html.Tr([
                html.Td("PM Emissions"),
                html.Td(format_number(pm), className=style_savings(pm)),
                html.Td(f"{perc_pm:.1f}%", className=style_savings(perc_pm))
            ]),
            html.Tr([
                html.Td("SOₓ Emissions"),
                html.Td(format_number(sox), className=style_savings(sox)),
                html.Td(f"{perc_sox:.1f}%", className=style_savings(perc_sox))
            ]),
        ])
    ], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def layout():
    return html.Div([
        html.H1("Step 2: Key Output Metrics", className="mb-4", style={"color": "#0A4B8C"}),
        dbc.Card([
            dbc.CardHeader(
                html.H4("Dashboard Controls", style={"color": "white"}),
                style={"backgroundColor": "#0A4B8C"}
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Tables to Display:", className="fw-bold"),
                        dcc.Dropdown(
                            id='table-selection-dropdown',
                            options=[
                                {"label": "Current Output Table", "value": "current"},
                                {"label": "Future Output Table", "value": "future"},
                                {"label": "OPEX Comparison", "value": "opex"},
                                {"label": "Emissions Comparison", "value": "emissions"}
                            ],
                            value=['current', 'opex'],
                            multi=True,
                            placeholder="Select tables to display..."
                        )
                    ], md=6, xs=12),
                    dbc.Col([
                        html.Label("Currency:", className="fw-bold"),
                        dcc.Dropdown(
                            id='currency-choice',
                            options=[{"label": f"{k} ({v['symbol']})", "value": k} for k, v in config.CURRENCIES.items()],
                            value="EUR",
                            clearable=False
                        )
                    ], md=3, xs=12)
                ], className="g-3")
            ])
        ], className="mb-4"),
        html.Div(id='output-content')
    ])
