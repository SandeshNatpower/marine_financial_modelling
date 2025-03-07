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
        if val is None:
            return ""
        num = float(val)
        if num > 0:
            return "text-success fw-bold"
        elif num < 0:
            return "text-danger fw-bold"
    except Exception:
        pass
    return ""

def safe_format_percentage(val):
    if isinstance(val, (int, float)):
        return f"{val:.1f}%"
    return "N/A"

# TABLE FUNCTIONS
def get_current_output_table(api_data):
    current = api_data.get("current_table", {})

    # SFC Data
    sfc_data = (current.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    avg_sfc     = sfc_data.get("avg_sfc_day", 198)
    
    # CH₄ Emissions Data (Current)
    ch4_data = (current.get("ch4_emission_ttw") or [{}])[0]
    sailing_ch4 = ch4_data.get("sailing_ch4_emission_ttw", 5)
    working_ch4 = ch4_data.get("working_ch4_emission_ttw", 4)
    idle_ch4    = ch4_data.get("idle_ch4_emission_ttw", 1)
    avg_ch4     = ch4_data.get("avg_ch4_ttw_day", 4)
    
    # CO₂ Emissions (TTW, Current)
    co2_ttw_data  = (current.get("co2_emission_ttw") or [{}])[0]
    sailing_co2_ttw = co2_ttw_data.get("sailing_co2_emission_ttw", 286088)
    working_co2_ttw = co2_ttw_data.get("working_co2_emission_ttw", 198669)
    idle_co2_ttw    = co2_ttw_data.get("idle_co2_emission_ttw", 12562)
    avg_co2_ttw     = co2_ttw_data.get("avg_co2_ttw_day", 182086)
    
    # CO₂ Emissions (WtW, Current)
    co2_wtw_data = (current.get("co2_emission_wtw") or [{}])[0]
    sailing_co2_wtw = co2_wtw_data.get("sailing_co2_emission_wtw", 340129)
    working_co2_wtw = co2_wtw_data.get("working_co2_emission_wtw", 236197)
    idle_co2_wtw    = co2_wtw_data.get("idle_co2_emission_wtw", 14935)
    avg_co2_wtw     = co2_wtw_data.get("avg_co2_wtw_day", 216481)
    
    # N₂O Emissions Data (Current)
    n2o_data = (current.get("n2o_emission_ttw") or [{}])[0]
    sailing_n2o = n2o_data.get("sailing_n2o_emission_ttw", 16)
    working_n2o = n2o_data.get("working_n2o_emission_ttw", 11)
    idle_n2o    = n2o_data.get("idle_n2o_emission_ttw", 1)
    avg_n2o     = n2o_data.get("avg_n2o_ttw_day", 11)
    
    # SOₓ Emissions Data (Current)
    sox_data = (current.get("sox_emission_ttw") or [{}])[0]
    sailing_sox = sox_data.get("sailing_sox_emission_ttw", 189)
    working_sox = sox_data.get("working_sox_emission_ttw", 132)
    idle_sox    = sox_data.get("idle_sox_emission_ttw", 9)
    avg_sox     = sox_data.get("avg_sox_ttw_day", 121)
    
    # Fuel Price Data (Current)
    fuel_price_data = (current.get("fuel_price") or [{}])[0]
    sailing_fuel_price = fuel_price_data.get("sailing_fuel_price", 76874)
    working_fuel_price = fuel_price_data.get("working_fuel_price", 53384)
    idle_fuel_price    = fuel_price_data.get("idle_fuel_price", 3849)
    avg_fuel_price     = fuel_price_data.get("avg_fuel_price_day", 49092)
    
    # Engine Power Data (Current)
    eng_data  = (current.get("engine_power") or current.get("enginge_power") or [{}])[0]
    sailing_power = eng_data.get("sailing_power", 19200)
    working_power = eng_data.get("working_power", 11520)
    idle_power    = eng_data.get("idle_power", 798)
    max_power     = eng_data.get("max_power_day", 19200)
    avg_power     = eng_data.get("avg_power_req_day", 12006)
    
    # Energy Requirement Data (Current)
    power_day = (current.get("power_calc_day") or [{}])[0]
    sailing_energy = power_day.get("sailing_eneregy_req_kwh_day", 460800)
    working_energy = power_day.get("working_eneregy_req_kwh_day", 276480)
    idle_energy   = power_day.get("idle_eneregy_req_kwh_day", 19152)
    avg_energy    = power_day.get("power_req_day", 288142)
    
    # Fuel Consumption Data (kg, Current)
    kg_data = (current.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 87889)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 61033)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 3859)
    avg_fuel_kg     = kg_data.get("avg_fuel_consumption_day", 55939)
    
    # Fuel Consumption Data (liters, Current)
    fuel_data = (current.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = fuel_data.get("sailing_fuel_consumption_liter", 98752)
    working_fuel_l = fuel_data.get("working_fuel_consumption_liter", 68577)
    idle_fuel_l    = fuel_data.get("idle_fuel_consumption_liter", 4336)
    avg_fuel_l     = fuel_data.get("avg_fuel_consumption_liter_day", 62853)
    
    # Example Static Engine Hours
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
                html.Td(format_number(idle_energy)),
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
                html.Td("CH₄ Emissions (kg)"),
                html.Td(format_number(sailing_ch4)),
                html.Td(format_number(working_ch4)),
                html.Td(format_number(idle_ch4)),
                html.Td("-"),
                html.Td(format_number(avg_ch4))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (TTW, kg)"),
                html.Td(format_number(sailing_co2_ttw)),
                html.Td(format_number(working_co2_ttw)),
                html.Td(format_number(idle_co2_ttw)),
                html.Td("-"),
                html.Td(format_number(avg_co2_ttw))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (WtW, kg)"),
                html.Td(format_number(sailing_co2_wtw)),
                html.Td(format_number(working_co2_wtw)),
                html.Td(format_number(idle_co2_wtw)),
                html.Td("-"),
                html.Td(format_number(avg_co2_wtw))
            ]),
            html.Tr([
                html.Td("N₂O Emissions (kg)"),
                html.Td(format_number(sailing_n2o)),
                html.Td(format_number(working_n2o)),
                html.Td(format_number(idle_n2o)),
                html.Td("-"),
                html.Td(format_number(avg_n2o))
            ]),
            html.Tr([
                html.Td("SOₓ Emissions (kg)"),
                html.Td(format_number(sailing_sox)),
                html.Td(format_number(working_sox)),
                html.Td(format_number(idle_sox)),
                html.Td("-"),
                html.Td(format_number(avg_sox))
            ]),
            html.Tr([
                html.Td("Fuel Price"),
                html.Td(format_number(sailing_fuel_price)),
                html.Td(format_number(working_fuel_price)),
                html.Td(format_number(idle_fuel_price)),
                html.Td("-"),
                html.Td(format_number(avg_fuel_price))
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


def get_future_output_table(api_data):
    future = api_data.get("future_output_table", {})
    
    # SFC Data
    sfc_data = (future.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    avg_sfc     = sfc_data.get("avg_shore_sfc_day", 0)
    
    # CH₄ Emissions Data (Future)
    ch4_data = (future.get("ch4_emission_ttw") or [{}])[0]
    sailing_ch4 = ch4_data.get("future_sailing_ch4_emission_ttw", 5)
    working_ch4 = ch4_data.get("future_working_ch4_emission_ttw", 4)
    idle_ch4    = ch4_data.get("future_idle_ch4_emission_ttw", 1)
    avg_ch4     = ch4_data.get("future_avg_ch4_ttw_day", 4)
    
    # CO₂ Emissions (TTW)
    co2_ttw_data  = (future.get("co2_emission_ttw") or [{}])[0]
    sailing_co2_ttw = co2_ttw_data.get("future_sailing_co2_emission_ttw", 200262)
    working_co2_ttw = co2_ttw_data.get("future_working_co2_emission_ttw", 139068)
    idle_co2_ttw    = co2_ttw_data.get("future_idle_co2_emission_ttw", 8794)
    avg_co2_ttw     = co2_ttw_data.get("future_avg_co2_ttw_day", 127461)
    
    # CO₂ Emissions (WtW)
    co2_wtw_data = (future.get("co2_emission_wtw") or [{}])[0]
    sailing_co2_wtw = co2_wtw_data.get("future_sailing_co2_emission_wtw", 243003)
    working_co2_wtw = co2_wtw_data.get("future_working_co2_emission_wtw", 168749)
    idle_co2_wtw    = co2_wtw_data.get("future_idle_co2_emission_wtw", 13655)
    avg_co2_wtw     = co2_wtw_data.get("future_avg_co2_wtw_day", 155694)
    
    # N₂O Emissions Data
    n2o_data = (future.get("n2o_emission_ttw") or [{}])[0]
    sailing_n2o = n2o_data.get("future_sailing_n2o_emission_ttw", 16)
    working_n2o = n2o_data.get("future_working_n2o_emission_ttw", 11)
    idle_n2o    = n2o_data.get("future_idle_n2o_emission_ttw", 1)
    avg_n2o     = n2o_data.get("future_avg_n2o_ttw_day", 11)
    
    # SOₓ Emissions Data
    sox_data = (future.get("sox_emission_ttw") or [{}])[0]
    sailing_sox = sox_data.get("future_sailing_sox_emission_ttw", 133)
    working_sox = sox_data.get("future_working_sox_emission_ttw", 92)
    idle_sox    = sox_data.get("future_idle_sox_emission_ttw", 8)
    avg_sox     = sox_data.get("future_avg_sox_ttw_day", 86)
    
    # Fuel Price Data
    fuel_price_data = (future.get("fuel_price") or [{}])[0]
    sailing_fuel_price = fuel_price_data.get("future_sailing_fuel_price", 87640)
    working_fuel_price = fuel_price_data.get("future_working_fuel_price", 60860)
    idle_fuel_price    = fuel_price_data.get("future_idle_fuel_price", 3849)
    shore_fuel_price   = fuel_price_data.get("future_shore_fuel_price", 0)
    avg_fuel_price     = fuel_price_data.get("future_avg_fuel_price_day", 55781)
    
    # Engine Power Data – try "engine_power" first, then fallback
    eng_data = (future.get("engine_power") or future.get("enginge_power") or [{}])[0]
    sailing_power = eng_data.get("sailing_power", 19200)
    working_power = eng_data.get("working_power", 11520)
    idle_power    = eng_data.get("idle_power", 798)
    shore_power   = eng_data.get("shore_power", 0)
    max_power     = eng_data.get("max_power_day", 19200)
    avg_power     = eng_data.get("avg_shore_power_req_day", 0)
    
    # Energy Requirement Data
    power_day = (future.get("power_calc_day") or [{}])[0]
    sailing_energy = power_day.get("sailing_eneregy_req_kwh_day", 460800)
    working_energy = power_day.get("working_eneregy_req_kwh_day", 276480)
    shore_energy   = power_day.get("shore_eneregy_req_kwh_day", 0)
    avg_energy     = power_day.get("power_req_day", 288142)
    
    # Fuel Consumption Data (kg)
    kg_data = (future.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 87889)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 61033)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 3859)
    avg_fuel_kg     = kg_data.get("avg_shore_fuel_consumption_day", 0)
    
    # Fuel Consumption Data (liters)
    fuel_data = (future.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = fuel_data.get("future_sailing_fuel_consumption_liter", 99761)
    working_fuel_l = fuel_data.get("future_working_fuel_consumption_liter", 69277)
    idle_fuel_l    = fuel_data.get("future_idle_fuel_consumption_liter", 4381)
    avg_fuel_l     = fuel_data.get("future_avg_fuel_consumption_liter_day", 63495)
    
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
                html.Td(format_number(shore_power)),
                html.Td(format_number(max_power))
            ]),
            html.Tr([
                html.Td("Avg. Power (kW)"),
                html.Td(format_number(sailing_power)),
                html.Td(format_number(working_power)),
                html.Td(format_number(idle_power)),
                html.Td(format_number(avg_power)),
                html.Td(format_number(avg_power))
            ]),
            html.Tr([
                html.Td("Energy Req. (kWh)"),
                html.Td(format_number(sailing_energy)),
                html.Td(format_number(working_energy)),
                html.Td(format_number(shore_energy)),
                html.Td(format_number(shore_energy)),
                html.Td(format_number(avg_energy))
            ]),
            html.Tr([
                html.Td("CH₄ Emissions (kg)"),
                html.Td(format_number(sailing_ch4)),
                html.Td(format_number(working_ch4)),
                html.Td(format_number(idle_ch4)),
                html.Td("-"),
                html.Td(format_number(avg_ch4))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (TTW, kg)"),
                html.Td(format_number(sailing_co2_ttw)),
                html.Td(format_number(working_co2_ttw)),
                html.Td(format_number(idle_co2_ttw)),
                html.Td("-"),
                html.Td(format_number(avg_co2_ttw))
            ]),
            html.Tr([
                html.Td("CO₂ Emissions (WtW, kg)"),
                html.Td(format_number(sailing_co2_wtw)),
                html.Td(format_number(working_co2_wtw)),
                html.Td(format_number(idle_co2_wtw)),
                html.Td("-"),
                html.Td(format_number(avg_co2_wtw))
            ]),
            html.Tr([
                html.Td("N₂O Emissions (kg)"),
                html.Td(format_number(sailing_n2o)),
                html.Td(format_number(working_n2o)),
                html.Td(format_number(idle_n2o)),
                html.Td("-"),
                html.Td(format_number(avg_n2o))
            ]),
            html.Tr([
                html.Td("SOₓ Emissions (kg)"),
                html.Td(format_number(sailing_sox)),
                html.Td(format_number(working_sox)),
                html.Td(format_number(idle_sox)),
                html.Td("-"),
                html.Td(format_number(avg_sox))
            ]),
            html.Tr([
                html.Td("Fuel Price"),
                html.Td(format_number(sailing_fuel_price)),
                html.Td(format_number(working_fuel_price)),
                html.Td(format_number(idle_fuel_price)),
                html.Td(format_number(shore_fuel_price)),
                html.Td(format_number(avg_fuel_price))
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
    # Extract conventional cost data from current_table costs
    conventional = (api_data.get("current_table", {}).get("costs") or [{}])[0]
    conv_fuel_eu = conventional.get("avg_fueleu_day", 0)
    conv_maintenance = conventional.get("avg_engine_maintenance_costs_day", 0)
    conv_spare = conventional.get("avg_spares_consumables_costs_day", 0)
    
    # Extract fuel price from current_table fuel_price
    current_fuel_price = (api_data.get("current_table", {}).get("fuel_price") or [{}])[0]
    conv_fuel_price = current_fuel_price.get("avg_fuel_price_day", 0)
    
    # Extract future cost data from future_output_table costs
    future = (api_data.get("future_output_table", {}).get("costs") or [{}])[0]
    fut_fuel_eu = future.get("future_avg_fueleu_day", 0)
    fut_maintenance = future.get("future_avg_engine_maintenance_costs_day", 0)
    fut_spare = future.get("future_avg_spares_consumables_costs_day", 0)
    
    # Extract fuel price from future_output_table fuel_price
    future_fuel_price = (api_data.get("future_output_table", {}).get("fuel_price") or [{}])[0]
    fut_fuel_price = future_fuel_price.get("future_avg_fuel_price_day", 0)
    
    # Build rows for each cost component
    rows = [
        {"metric": "Fuel / electricity", "conv": conv_fuel_eu, "fut": fut_fuel_eu},
        {"metric": "Fuel Price", "conv": conv_fuel_price, "fut": fut_fuel_price},
        {"metric": "Maintenance", "conv": conv_maintenance, "fut": fut_maintenance},
        {"metric": "Spares / consumables", "conv": conv_spare, "fut": fut_spare},
    ]
    
    # Total row
    total_conv = sum(row["conv"] for row in rows)
    total_fut = sum(row["fut"] for row in rows)
    rows.append({"metric": "OPEX Total", "conv": total_conv, "fut": total_fut})
    
    # Build table rows by computing Savings and Savings (%)
    table_rows = []
    for row in rows:
        conv_val = row["conv"]
        fut_val = row["fut"]
        savings = conv_val - fut_val
        perc = (fut_val / conv_val - 1) * 100 if conv_val != 0 else None
        table_rows.append(html.Tr([
            html.Td(row["metric"]),
            html.Td(format_currency_value(conv_val, currency, conv_factor)),
            html.Td(format_currency_value(fut_val, currency, conv_factor)),
            html.Td(format_currency_value(savings, currency, conv_factor), className=style_savings(savings)),
            html.Td(safe_format_percentage(perc), className=style_savings(perc))
        ]))
        
    currency_symbol = get_currency_symbol(currency)
    header = html.Thead(html.Tr([
        html.Th("OPEX"),
        html.Th(f"Conventional ({currency_symbol}/day)"),
        html.Th(f"After measures ({currency_symbol}/day)"),
        html.Th(f"Savings ({currency_symbol}/day)"),
        html.Th("Savings (%)")
    ]), style={"backgroundColor": "#0A4B8C", "color": "white"})
    
    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")


def get_emissions_comparison_table(api_data):
    # Get conventional emissions from current_table and after-measures from future_output_table,
    # using the average values for every metric.
    current = api_data.get("current_table", {})
    future = api_data.get("future_output_table", {})

    rows = []
    # CO₂ Emissions TtW
    co2_ttw_conv = (current.get("co2_emission_ttw") or [{}])[0].get("avg_co2_ttw_day", 182086)
    co2_ttw_fut = (future.get("co2_emission_ttw") or [{}])[0].get("future_avg_co2_ttw_day", 127461)
    rows.append({"metric": "CO₂ Emissions TtW", "conv": co2_ttw_conv, "fut": co2_ttw_fut})

    # CO₂ Emissions WtW
    co2_wtw_conv = (current.get("co2_emission_wtw") or [{}])[0].get("avg_co2_wtw_day", 216481)
    co2_wtw_fut = (future.get("co2_emission_wtw") or [{}])[0].get("future_avg_co2_wtw_day", 155694)
    rows.append({"metric": "CO₂ Emissions WtW", "conv": co2_wtw_conv, "fut": co2_wtw_fut})

    # NOₓ Emissions TtW
    nox_conv = (current.get("nox_emission_ttw") or [{}])[0].get("avg_nox_ttw_day", 3071)
    nox_fut = (future.get("nox_emission_ttw") or [{}])[0].get("future_avg_nox_ttw_day", 2165)
    rows.append({"metric": "NOₓ Emissions TtW", "conv": nox_conv, "fut": nox_fut})

    # SOₓ Emissions TtW
    sox_conv = (current.get("sox_emission_ttw") or [{}])[0].get("avg_sox_ttw_day", 121)
    sox_fut = (future.get("sox_emission_ttw") or [{}])[0].get("future_avg_sox_ttw_day", 86)
    rows.append({"metric": "SOₓ Emissions TtW", "conv": sox_conv, "fut": sox_fut})

    # PM Emissions TtW
    pm_conv = (current.get("pm_emission_ttw") or [{}])[0].get("avg_pm_ttw_day", 54)
    pm_fut = (future.get("pm_emission_ttw") or [{}])[0].get("future_avg_pm_ttw_day", 39)
    rows.append({"metric": "PM Emissions TtW", "conv": pm_conv, "fut": pm_fut})

    # CH₄ Emissions TtW (using average values)
    ch4_conv = (current.get("ch4_emission_ttw") or [{}])[0].get("avg_ch4_ttw_day", 4)
    ch4_fut = (future.get("ch4_emission_ttw") or [{}])[0].get("future_avg_ch4_ttw_day", 4)
    rows.append({"metric": "CH₄ Emissions TtW", "conv": ch4_conv, "fut": ch4_fut})

    # Build table rows: calculate savings (conventional - after measures)
    table_rows = []
    for row in rows:
        conv_val = float(row["conv"]) if row["conv"] is not None else 0
        fut_val = float(row["fut"]) if row["fut"] is not None else 0
        savings = conv_val - fut_val
        perc = (fut_val / conv_val - 1) * 100 if conv_val != 0 else None

        table_rows.append(
            html.Tr([
                html.Td(row["metric"]),
                html.Td(f"{format_number(conv_val)}"),
                html.Td(f"{format_number(fut_val)}"),
                html.Td(f"{format_number(savings)}", className=style_savings(savings)),
                html.Td(safe_format_percentage(perc), className=style_savings(perc))
            ])
        )

    header = html.Thead(html.Tr([
        html.Th("Emissions"),
        html.Th("Conventional (kg/day)"),
        html.Th("After measures (kg/day)"),
        html.Th("Savings (kg/day)"),
        html.Th("Savings (%)")
    ]), style={"backgroundColor": "#0A4B8C", "color": "white"})

    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
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
                            value=['opex', 'emissions'],
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