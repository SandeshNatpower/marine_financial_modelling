import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np


MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

import dash
from dash import html
import dash_bootstrap_components as dbc
import config

# =============================================================================
# HELPER FUNCTION
# =============================================================================
def format_number(value):
    """Formats a number with commas (e.g., 123456 -> '123,456')."""
    if value is None:
        return "-"
    return f"{value:,.0f}"


def format_days(day_value):
    """Formats the day value for header display."""
    if day_value is None:
        return "-"
    return f"{day_value} days / year"


def get_currency_symbol(currency):
    """Retrieve currency symbol from config; if not found, return the currency itself."""
    return config.CURRENCIES.get(currency, {}).get("symbol", currency)


def safe_format_percentage(value):
    """Format percentage safely."""
    if value is None:
        return "-"
    return f"{value:.0f}%"

def style_savings(value):
    """Return a CSS class for styling based on positive/negative savings."""
    try:
        # Try converting to a float for comparison
        num_val = float(value)
    except (TypeError, ValueError):
        # If conversion fails, return an empty class or a default
        return ""
    return "text-danger" if num_val < 0 else "text-success"





# =============================================================================
# TABLE FUNCTIONS
# =============================================================================
def get_current_output_table(api_data, currency):
    current = api_data.get("current_table", {})

    # ----- Header Days (override Idle and Shore as per sample) -----
    working_days_data = (current.get("working_days") or [{}])[0]
    sailing_days = working_days_data.get("sailing_days", 175)      # sample: 175
    working_days = working_days_data.get("working_days", 165)      # sample: 165
    idle_days    = working_days_data.get("current_idle_days", 75)
    shore_days   = 0   # override to sample value
    

    # ----- Engine / Power -----
    eng_data = (current.get("enginge_power") or [{}])[0]
    sailing_power = eng_data.get("sailing_power", 32000)
    working_power = eng_data.get("working_power", 19200)
    idle_power    = eng_data.get("idle_power", 6320)
    max_power     = eng_data.get("max_power_day", 32000)
    avg_power_req = eng_data.get("avg_power_req_day", 21733)

    # ----- Energy Requirements -----
    power_day = (current.get("power_calc_day") or [{}])[0]
    sailing_energy = power_day.get("sailing_energy_req_kwh_day", 768000)
    working_energy = power_day.get("working_energy_req_kwh_day", 460800)
    idle_energy    = power_day.get("idle_energy_req_kwh_day", 151680)
    avg_energy     = power_day.get("power_req_day", 521578)

    # ----- Average SFC -----
    sfc_data = (current.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    avg_sfc     = sfc_data.get("avg_sfc_day", 198)

    # ----- Fuel Consumption -----
    kg_data = (current.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 146482)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 101722)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 30561)
    avg_fuel_kg     = kg_data.get("avg_fuel_consumption_day", 101560)

    liter_data = (current.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = liter_data.get("sailing_fuel_consumption_liter", 164586)
    working_fuel_l = liter_data.get("working_fuel_consumption_liter", 114294)
    idle_fuel_l    = liter_data.get("idle_fuel_consumption_liter", 34338)
    avg_fuel_l     = liter_data.get("avg_fuel_consumption_liter_day", 114112)

    # Fuel consumption (kWh) – reuse energy requirement values
    sailing_fuel_kwh = sailing_energy
    working_fuel_kwh = working_energy
    idle_fuel_kwh    = idle_energy
    avg_fuel_kwh     = avg_energy

    # ----- Emissions -----
    co2_ttw_data = (current.get("co2_emission_ttw") or [{}])[0]
    sailing_co2_ttw = co2_ttw_data.get("sailing_co2_emission_ttw", 476811)
    working_co2_ttw = co2_ttw_data.get("working_co2_emission_ttw", 331114)
    idle_co2_ttw    = co2_ttw_data.get("idle_co2_emission_ttw", 99478)
    avg_co2_ttw     = co2_ttw_data.get("avg_co2_ttw_day", 330587)

    co2_wtw_data = (current.get("co2_emission_wtw") or [{}])[0]
    sailing_co2_wtw = co2_wtw_data.get("sailing_co2_emission_wtw", 566880)
    working_co2_wtw = co2_wtw_data.get("working_co2_emission_wtw", 393660)
    idle_co2_wtw    = co2_wtw_data.get("idle_co2_emission_wtw", 118269)
    avg_co2_wtw     = co2_wtw_data.get("avg_co2_wtw_day", 393034)

    nox_data = (current.get("nox_emission_ttw") or [{}])[0]
    sailing_nox = nox_data.get("sailing_nox_emission_ttw", 8039)
    working_nox = nox_data.get("working_nox_emission_ttw", 5583)
    idle_nox    = nox_data.get("idle_nox_emission_ttw", 1678)
    avg_nox     = nox_data.get("avg_nox_ttw_day", 5574)

    sox_data = (current.get("sox_emission_ttw") or [{}])[0]
    sailing_sox = sox_data.get("sailing_sox_emission_ttw", 315)
    working_sox = sox_data.get("working_sox_emission_ttw", 219)
    idle_sox    = sox_data.get("idle_sox_emission_ttw", 66)
    avg_sox     = sox_data.get("avg_sox_ttw_day", 219)

    pm_data = (current.get("pm_emission_ttw") or [{}])[0]
    sailing_pm = pm_data.get("sailing_pm_emission_ttw", 140)
    working_pm = pm_data.get("working_pm_emission_ttw", 97)
    idle_pm    = pm_data.get("idle_pm_emission_ttw", 30)
    avg_pm     = pm_data.get("avg_pm_ttw_day", 97)

    ch4_data = (current.get("ch4_emission_ttw") or [{}])[0]
    sailing_ch4 = ch4_data.get("sailing_ch4_emission_ttw", 8)
    working_ch4 = ch4_data.get("working_ch4_emission_ttw", 6)
    idle_ch4    = ch4_data.get("idle_ch4_emission_ttw", 2)
    avg_ch4     = ch4_data.get("avg_ch4_ttw_day", 6)

    n2o_data = (current.get("n2o_emission_ttw") or [{}])[0]
    sailing_n2o = n2o_data.get("sailing_n2o_emission_ttw", 27)
    working_n2o = n2o_data.get("working_n2o_emission_ttw", 19)
    idle_n2o    = n2o_data.get("idle_n2o_emission_ttw", 6)
    avg_n2o     = n2o_data.get("avg_n2o_ttw_day", 19)

    # ----- Costs -----
    fuel_price_data = (current.get("fuel_price") or [{}])[0]
    sailing_fuel_price = fuel_price_data.get("sailing_fuel_price", 134961)
    working_fuel_price = fuel_price_data.get("working_fuel_price", 93721)
    idle_fuel_price    = fuel_price_data.get("idle_fuel_price", 28157)
    avg_fuel_price     = fuel_price_data.get("avg_fuel_price_day", 93572)

    cost_data = (current.get("costs") or [{}])[0]
    engine_maintenance = cost_data.get("engine_maintenance_costs", 480)
    spares_costs       = cost_data.get("spares_consumables_costs", 48)
    fueleu_penalty     = cost_data.get("fueleu_current_penalty", 1999)
    financing          = 0
    euets              = cost_data.get("avg_eu_ets", {})
    

    maintenance_avg = cost_data.get("avg_engine_maintenance_costs_day", engine_maintenance)
    spares_avg      = cost_data.get("avg_spares_consumables_costs_day", spares_costs)
    fueleu_avg      = cost_data.get("avg_fueleu_day", fueleu_penalty)

    opex_day_data = (current.get("opex_day") or [{}])[0]
    sailing_opex_day = opex_day_data.get("sailing_opex_day", 137487)
    working_opex_day = opex_day_data.get("working_opex_day", 96247)
    idle_opex_day    = opex_day_data.get("idle_opex_day", 30684)
    avg_opex_day     = opex_day_data.get("avg_opex_day", 96098)

    opex_year_data = (current.get("opex_year") or [{}])[0]
    sailing_opex_year = opex_year_data.get("sailing_opex_year", 27359795)
    working_opex_year = opex_year_data.get("working_opex_year", 3849879)
    idle_opex_year    = opex_year_data.get("idle_opex_year", 3866063)
    avg_opex_year     = opex_year_data.get("total_opex_year", 35075736)

    # ----- Build Table Header (2 rows) -----
    table_header = html.Thead([
        html.Tr([
            html.Th("Current output table", colSpan=2, style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Propulsion", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Parked / Mooring", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Cold Ironing", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Shore Power", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Average", style={"backgroundColor": "#0A4B8C", "color": "white"})
        ]),
        html.Tr([
            html.Th("", colSpan=2),
            html.Th(format_days(sailing_days)),
            html.Th(format_days(working_days)),
            html.Th(format_days(idle_days)),
            html.Th(format_days(shore_days)),
            html.Th("per day")
        ])
    ])

    # ----- Build Table Body -----
    table_body = html.Tbody([
        # Block 1: Power & Energy
        html.Tr([
            html.Td("Average power"),
            html.Td("kW"),
            html.Td(format_number(sailing_power)),
            html.Td(format_number(working_power)),
            html.Td(format_number(idle_power)),
            html.Td("-"),
            html.Td(format_number(avg_power_req))
        ]),
        html.Tr([
            html.Td("Energy required"),
            html.Td("kWh"),
            html.Td(format_number(sailing_energy)),
            html.Td(format_number(working_energy)),
            html.Td(format_number(idle_energy)),
            html.Td("-"),
            html.Td(format_number(avg_energy))
        ]),
        html.Tr([
            html.Td("Average SFC"),
            html.Td("g/kWh"),
            html.Td(format_number(sailing_sfc)),
            html.Td(format_number(working_sfc)),
            html.Td(format_number(idle_sfc)),
            html.Td("-"),
            html.Td(format_number(avg_sfc))
        ]),
        # Block 1: Fuel Consumption (kg, liters, kWh)
        html.Tr([
            html.Td("Fuel consumption"),
            html.Td("kg"),
            html.Td(format_number(sailing_fuel_kg)),
            html.Td(format_number(working_fuel_kg)),
            html.Td(format_number(idle_fuel_kg)),
            html.Td("-"),
            html.Td(format_number(avg_fuel_kg))
        ]),
        html.Tr([
            html.Td("Fuel consumption"),
            html.Td("liters"),
            html.Td(format_number(sailing_fuel_l)),
            html.Td(format_number(working_fuel_l)),
            html.Td(format_number(idle_fuel_l)),
            html.Td("-"),
            html.Td(format_number(avg_fuel_l))
        ]),
        html.Tr([
            html.Td("Fuel consumption"),
            html.Td("kWh"),
            html.Td(format_number(sailing_fuel_kwh)),
            html.Td(format_number(working_fuel_kwh)),
            html.Td(format_number(idle_fuel_kwh)),
            html.Td("-"),
            html.Td(format_number(avg_fuel_kwh))
        ]),
        # Block 2: Emissions
        html.Tr([
            html.Td("CO2 Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_co2_ttw)),
            html.Td(format_number(working_co2_ttw)),
            html.Td(format_number(idle_co2_ttw)),
            html.Td("-"),
            html.Td(format_number(avg_co2_ttw))
        ]),
        html.Tr([
            html.Td("CO2 Emissions WtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_co2_wtw)),
            html.Td(format_number(working_co2_wtw)),
            html.Td(format_number(idle_co2_wtw)),
            html.Td("-"),
            html.Td(format_number(avg_co2_wtw))
        ]),
        html.Tr([
            html.Td("NOx Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_nox)),
            html.Td(format_number(working_nox)),
            html.Td(format_number(idle_nox)),
            html.Td("-"),
            html.Td(format_number(avg_nox))
        ]),
        html.Tr([
            html.Td("SOx Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_sox)),
            html.Td(format_number(working_sox)),
            html.Td(format_number(idle_sox)),
            html.Td("-"),
            html.Td(format_number(avg_sox))
        ]),
        html.Tr([
            html.Td("PM Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_pm)),
            html.Td(format_number(working_pm)),
            html.Td(format_number(idle_pm)),
            html.Td("-"),
            html.Td(format_number(avg_pm))
        ]),
        html.Tr([
            html.Td("CH4 Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_ch4)),
            html.Td(format_number(working_ch4)),
            html.Td(format_number(idle_ch4)),
            html.Td("-"),
            html.Td(format_number(avg_ch4))
        ]),
        html.Tr([
            html.Td("N2O Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_n2o)),
            html.Td(format_number(working_n2o)),
            html.Td(format_number(idle_n2o)),
            html.Td("-"),
            html.Td(format_number(avg_n2o))
        ]),
        # Block 3: Costs
        html.Tr([
            html.Td("Fuel"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(sailing_fuel_price)),
            html.Td(format_number(working_fuel_price)),
            html.Td(format_number(idle_fuel_price)),
            html.Td("-"),
            html.Td(format_number(avg_fuel_price))
        ]),
        html.Tr([
            html.Td("Financing"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(financing)),
            html.Td(format_number(financing)),
            html.Td(format_number(financing)),
            html.Td("-"),
            html.Td(format_number(financing))
        ]),
        html.Tr([
            html.Td("Maintenance"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(engine_maintenance)),
            html.Td(format_number(engine_maintenance)),
            html.Td(format_number(engine_maintenance)),
            html.Td("-"),
            html.Td(format_number(maintenance_avg))
        ]),
        html.Tr([
            html.Td("Spares / consumables"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(spares_costs)),
            html.Td(format_number(spares_costs)),
            html.Td(format_number(spares_costs)),
            html.Td("-"),
            html.Td(format_number(spares_avg))
        ]),
        html.Tr([
            html.Td("EU ETS"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(euets)),
            html.Td(format_number(euets)),
            html.Td(format_number(euets)),
            html.Td("-"),
            html.Td(format_number(euets))
        ]),
        html.Tr([
            html.Td("FuelEU"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(fueleu_penalty)),
            html.Td(format_number(fueleu_penalty)),
            html.Td(format_number(fueleu_penalty)),
            html.Td(""),
            html.Td(format_number(fueleu_avg))
        ]),
        # Block 4: OPEX Current (2 rows)
        html.Tr([
            html.Td("OPEX Current", rowSpan=2),
            html.Td(f"{get_currency_symbol(currency)} per day"),
            html.Td(format_number(sailing_opex_day)),
            html.Td(format_number(working_opex_day)),
            html.Td(format_number(idle_opex_day)),
            html.Td("-"),
            html.Td(format_number(avg_opex_day))
        ]),
        html.Tr([
            html.Td(f"{get_currency_symbol(currency)} per year"),
            html.Td(format_number(sailing_opex_year)),
            html.Td(format_number(working_opex_year)),
            html.Td(format_number(idle_opex_year)),
            html.Td("-"),
            html.Td(format_number(avg_opex_year))
        ])
    ])

    table = dbc.Table(
        [table_header, table_body],
        bordered=True,
        striped=True,
        hover=True,
        style={"width": "100%"}
    )

    return html.Div(table, className="table-responsive")




# ---------------------------------------------------------------------------
# Future Output Table
# ---------------------------------------------------------------------------
def get_future_output_table(api_data, currency):
    future = api_data.get("future_output_table", {})

    # Days information from API
    days_data = (future.get("working_days") or [{}])[0]
    sailing_days = days_data.get("sailing_days", 199)
    working_days = days_data.get("working_days", 40)
    idle_days    = days_data.get("idle_days", 126)
    shore_days   = days_data.get("adjusted_shore_days", 0)

    # Engine / Power Data
    power_data = (future.get("enginge_power") or [{}])[0]
    max_power     = power_data.get("max_power_day", 19200)
    sailing_power = power_data.get("sailing_power", 19200)
    working_power = power_data.get("working_power", 11520)
    idle_power    = power_data.get("idle_power", 798)
    shore_power   = power_data.get("shore_power", 0)
    avg_power     = power_data.get("avg_shore_power_req_day")
    
    # Energy Requirement Data
    energy_data = (future.get("power_calc_day") or [{}])[0]
    sailing_energy = energy_data.get("sailing_energy_req_kwh_day", 460800)
    working_energy = energy_data.get("working_energy_req_kwh_day", 276480)
    idle_energy    = energy_data.get("idle_energy_req_kwh_day", 19150)
    shore_energy   = energy_data.get("shore_energy_req_kwh_day", 0)
    avg_energy     = energy_data.get("shore_power_req_day", 0)

    # Average SFC Data
    sfc_data = (future.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    avg_sfc     = int((sailing_sfc + working_sfc + idle_sfc) / 3.0)

    # Fuel consumption in kg
    kg_data = (future.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 87889)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 61033)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 3859)
    shore_fuel_kg   = kg_data.get("-")
    avg_fuel_kg     = kg_data.get("avg_shore_fuel_consumption_day", 101560)

    # Fuel consumption in liters
    fuel_data = (future.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = fuel_data.get("future_sailing_fuel_consumption_liter", 99761)
    working_fuel_l = fuel_data.get("future_working_fuel_consumption_liter", 69277)
    idle_fuel_l    = fuel_data.get("future_idle_fuel_consumption_liter", 4336)
    shore_fuel_l   = "-"  # Assume 0
    avg_fuel_l     = fuel_data.get("future_avg_fuel_consumption_liter_day", 63479)

    # Fuel consumption in kWh (using energy requirement values)
    sailing_fuel_kwh = sailing_energy
    working_fuel_kwh = working_energy
    idle_fuel_kwh    = idle_energy
    shore_fuel_kwh   = shore_energy
    avg_fuel_kwh     = avg_energy

    # Emissions Data – CO2 Emissions TtW
    co2_ttw_data = (future.get("co2_emission_ttw") or [{}])[0]
    sailing_co2_ttw = co2_ttw_data.get("future_sailing_co2_emission_ttw", 200261)
    working_co2_ttw = co2_ttw_data.get("future_working_co2_emission_ttw", 139068)
    idle_co2_ttw    = co2_ttw_data.get("future_idle_co2_emission_ttw", 8792)
    avg_co2_ttw     = co2_ttw_data.get("future_avg_co2_ttw_day", 127459)

    # CO2 Emissions WtW
    co2_wtw_data = (future.get("co2_emission_wtw") or [{}])[0]
    sailing_co2_wtw = co2_wtw_data.get("future_sailing_co2_emission_wtw", 243002)
    working_co2_wtw = co2_wtw_data.get("future_working_co2_emission_wtw", 168748)
    idle_co2_wtw    = co2_wtw_data.get("future_idle_co2_emission_wtw", 14932)
    avg_co2_wtw     = co2_wtw_data.get("future_avg_co2_wtw_day", 156133)

    # NOx Emissions TtW
    nox_data = (future.get("nox_emission_ttw") or [{}])[0]
    sailing_nox = nox_data.get("future_sailing_nox_emission_ttw", 3377)
    working_nox = nox_data.get("future_working_nox_emission_ttw", 2345)
    idle_nox    = nox_data.get("future_idle_nox_emission_ttw", 212)
    avg_nox     = nox_data.get("future_avg_nox_ttw_day", 2171)

    # SOx Emissions TtW
    sox_data = (future.get("sox_emission_ttw") or [{}])[0]
    sailing_sox = sox_data.get("future_sailing_sox_emission_ttw", 133)
    working_sox = sox_data.get("future_working_sox_emission_ttw", 92)
    idle_sox    = sox_data.get("future_idle_sox_emission_ttw", 9)
    avg_sox     = sox_data.get("future_avg_sox_ttw_day", 86)

    # PM Emissions TtW
    pm_data = (future.get("pm_emission_ttw") or [{}])[0]
    sailing_pm = pm_data.get("future_sailing_pm_emission_ttw", 59)
    working_pm = pm_data.get("future_working_pm_emission_ttw", 41)
    idle_pm    = pm_data.get("future_idle_pm_emission_ttw", 4)
    avg_pm     = pm_data.get("future_avg_pm_ttw_day", 38)

    # CH4 Emissions TtW
    ch4_data = (future.get("ch4_emission_ttw") or [{}])[0]
    sailing_ch4 = ch4_data.get("future_sailing_ch4_emission_ttw", 5)
    working_ch4 = ch4_data.get("future_working_ch4_emission_ttw", 4)
    idle_ch4    = ch4_data.get("future_idle_ch4_emission_ttw", 1)
    avg_ch4     = ch4_data.get("future_avg_ch4_ttw_day", 3)

    # Costs – Fuel price Data
    fuel_price_data = (future.get("fuel_price") or [{}])[0]
    sailing_fuel_price = fuel_price_data.get("future_sailing_fuel_price", 87639)
    working_fuel_price = fuel_price_data.get("future_working_fuel_price", 60860)
    idle_fuel_price    = fuel_price_data.get("future_idle_fuel_price", 3375)
    shore_fuel_price   = fuel_price_data.get("future_shore_fuel_price", 0)
    avg_fuel_price     = fuel_price_data.get("future_avg_fuel_price_day", 55616)

    # Costs – Maintenance and Spares
    costs_data = (future.get("costs") or [{}])[0]
    maintenance_sailing = costs_data.get("engine_maintenance_costs", 480)
    maintenance_working = costs_data.get("engine_maintenance_costs", 480)
    maintenance_idle    = costs_data.get("engine_maintenance_costs", 480)
    maintenance_shore   = costs_data.get("shore_power_maintenance_per_day", 480)
    maintenance_avg     = costs_data.get("future_avg_engine_maintenance_costs_day", 480)

    spares_sailing = costs_data.get("future_spares_consumables_costs", 72)
    spares_working = costs_data.get("future_spares_consumables_costs", 72)
    spares_idle    = costs_data.get("future_spares_consumables_costs", 72)
    spares_shore   = costs_data.get("shore_power_spares_per_day", 480)
    spares_avg     = costs_data.get("future_avg_spares_consumables_costs_day", 72)
    
    #EUETS data
    
    future_euets_data = costs_data.get("future_eu_ets", {})

    # OPEX Data
    opex_day_data = (future.get("opex_day") or [{}])[0]
    sailing_opex_day = opex_day_data.get("future_sailing_opex_day", 88191)
    working_opex_day = opex_day_data.get("future_working_opex_day", 61412)
    idle_opex_day    = opex_day_data.get("future_idle_opex_day", 3927)
    shore_opex_day   = opex_day_data.get("future_shore_opex_day", 960)
    avg_opex_day     = opex_day_data.get("future_avg_opex_day", 56168)

    opex_year_data = (future.get("opex_year") or [{}])[0]
    sailing_opex_year = opex_year_data.get("future_sailing_opex_year", 17559547)
    working_opex_year = opex_year_data.get("future_working_opex_year", 2458374)
    idle_opex_year    = opex_year_data.get("future_idle_opex_year", 500811)
    shore_opex_year   = opex_year_data.get("future_shore_opex_year", 0)
    avg_opex_year     = opex_year_data.get("future_total_opex_year", 20518730)

    # Build table header with multi-row headings
    table_header = html.Thead([
        html.Tr([
            html.Th("Future output table", colSpan=2, style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Propulsion", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Parked / Mooring", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Cold Ironing", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Shore Power", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Average", style={"backgroundColor": "#0A4B8C", "color": "white"})
        ]),
        html.Tr([
            html.Th("", colSpan=2),
            html.Th(format_days(sailing_days)),
            html.Th(format_days(working_days)),
            html.Th(format_days(idle_days)),
            html.Th(format_days(shore_days)),
            html.Th("per day")
        ])
    ])

    # Build table body rows
    table_body = html.Tbody([
        # Max. power
        html.Tr([
            html.Td("Average power"),
            html.Td("kW"),
            html.Td(format_number(sailing_power)),
            html.Td(format_number(working_power)),
            html.Td(format_number(idle_power)),
            html.Td(format_number(shore_power) if shore_power else "-"),
            html.Td(format_number(avg_power))
        ]),
        # Energy required
        html.Tr([
            html.Td("Energy required"),
            html.Td("kWh"),
            html.Td(format_number(sailing_energy)),
            html.Td(format_number(working_energy)),
            html.Td(format_number(idle_energy)),
            html.Td(format_number(shore_energy) if shore_energy else "-"),
            html.Td(format_number(avg_energy))
        ]),
        # Average SFC
        html.Tr([
            html.Td("Average SFC"),
            html.Td("g/kWh"),
            html.Td(format_number(sailing_sfc)),
            html.Td(format_number(working_sfc)),
            html.Td(format_number(idle_sfc)),
            html.Td("-"),
            html.Td(format_number(avg_sfc))
        ]),
        # Fuel consumption (kg)
        html.Tr([
            html.Td("Fuel consumption"),
            html.Td("kg"),
            html.Td(format_number(sailing_fuel_kg)),
            html.Td(format_number(working_fuel_kg)),
            html.Td(format_number(idle_fuel_kg)),
            html.Td(format_number(shore_fuel_kg)),
            html.Td(format_number(avg_fuel_kg))
        ]),
        # Fuel consumption (liters)
        html.Tr([
            html.Td("Fuel consumption"),
            html.Td("liters"),
            html.Td(format_number(sailing_fuel_l)),
            html.Td(format_number(working_fuel_l)),
            html.Td(format_number(idle_fuel_l)),
            html.Td("-"),
            html.Td(format_number(avg_fuel_l))
        ]),
        # Fuel consumption (kWh)
        html.Tr([
            html.Td("Fuel consumption"),
            html.Td("kWh"),
            html.Td(format_number(sailing_fuel_kwh)),
            html.Td(format_number(working_fuel_kwh)),
            html.Td(format_number(idle_fuel_kwh)),
            html.Td(format_number(shore_fuel_kwh)),
            html.Td(format_number(avg_fuel_kwh))
        ]),
        # CO2 Emissions TtW
        html.Tr([
            html.Td("CO₂ Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_co2_ttw)),
            html.Td(format_number(working_co2_ttw)),
            html.Td(format_number(idle_co2_ttw)),
            html.Td("0"),
            html.Td(format_number(avg_co2_ttw))
        ]),
        # CO2 Emissions WtW
        html.Tr([
            html.Td("CO₂ Emissions WtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_co2_wtw)),
            html.Td(format_number(working_co2_wtw)),
            html.Td(format_number(idle_co2_wtw)),
            html.Td("0"),
            html.Td(format_number(avg_co2_wtw))
        ]),
        # NOx Emissions TtW
        html.Tr([
            html.Td("NOₓ Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_nox)),
            html.Td(format_number(working_nox)),
            html.Td(format_number(idle_nox)),
            html.Td("0"),
            html.Td(format_number(avg_nox))
        ]),
        # SOx Emissions TtW
        html.Tr([
            html.Td("SOₓ Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_sox)),
            html.Td(format_number(working_sox)),
            html.Td(format_number(idle_sox)),
            html.Td("0"),
            html.Td(format_number(avg_sox))
        ]),
        # PM Emissions TtW
        html.Tr([
            html.Td("PM Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_pm)),
            html.Td(format_number(working_pm)),
            html.Td(format_number(idle_pm)),
            html.Td("0"),
            html.Td(format_number(avg_pm))
        ]),
        # CH4 Emissions TtW
        html.Tr([
            html.Td("CH₄ Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_ch4)),
            html.Td(format_number(working_ch4)),
            html.Td(format_number(idle_ch4)),
            html.Td("0"),
            html.Td(format_number(avg_ch4))
        ]),
        # Cost rows – Fuel / electricity
        html.Tr([
            html.Td("Fuel / electricity"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(sailing_fuel_price)),
            html.Td(format_number(working_fuel_price)),
            html.Td(format_number(idle_fuel_price)),
            html.Td(format_number(shore_fuel_price)),
            html.Td(format_number(avg_fuel_price))
        ]),
        # Financing row
        html.Tr([
            html.Td("Financing"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0))
        ]),
        # Maintenance row
        html.Tr([
            html.Td("Maintenance"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(maintenance_sailing)),
            html.Td(format_number(maintenance_working)),
            html.Td(format_number(maintenance_idle)),
            html.Td(""),
            html.Td(format_number(maintenance_avg))
        ]),
        # Spares / consumables row
        html.Tr([
            html.Td("Spares / consumables"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(spares_sailing)),
            html.Td(format_number(spares_working)),
            html.Td(format_number(spares_idle)),
            html.Td(format_number(spares_shore)),
            html.Td(format_number(spares_avg))
        ]),
        # EU ETS row
        html.Tr([
            html.Td("EU ETS"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(future_euets_data)),
            html.Td(format_number(future_euets_data)),
            html.Td(format_number(future_euets_data)),
            html.Td("0"),
            html.Td(format_number(future_euets_data))
        ]),
        # FuelEU row
        html.Tr([
            html.Td("FuelEU"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0))
        ]),
        # OPEX Future rows (per day and per year)
        html.Tr([
            html.Td("OPEX Future", rowSpan=2),
            html.Td(f"{get_currency_symbol(currency)} per day"),
            html.Td(format_number(sailing_opex_day)),
            html.Td(format_number(working_opex_day)),
            html.Td(format_number(idle_opex_day)),
            html.Td(format_number(shore_opex_day)),
            html.Td(format_number(avg_opex_day))
        ]),
        html.Tr([
            html.Td(f"{get_currency_symbol(currency)} per year"),
            html.Td(format_number(sailing_opex_year)),
            html.Td(format_number(working_opex_year)),
            html.Td(format_number(idle_opex_year)),
            html.Td(format_number(shore_opex_year)),
            html.Td(format_number(avg_opex_year))
        ])
    ])

    table = dbc.Table(
        [table_header, table_body],
        bordered=True,
        striped=True,
        hover=True,
        style={"width": "100%"}
    )

    return html.Div(table, className="table-responsive")

# ---------------------------------------------------------------------------
# OPEX Comparison Table
# ---------------------------------------------------------------------------
def get_opex_comparison_table(api_data, currency):
    """
    Build an OPEX comparison table using:
      1) 'conventional' values from api_data["current_table"]
      2) 'future' values from api_data["future_output_table"]
      3) 'savings' & 'savings_perc' from api_data["opex_table"]
    """
    # 1) Extract Conventional (current) and Future (after measures) values
    conventional = (api_data.get("current_table", {}).get("costs") or [{}])[0]
    conv_fuel_price = (api_data.get("current_table", {}).get("fuel_price") or [{}])[0].get("avg_fuel_price_day", 0)
    conv_financing = conventional.get("avg_financing_day", 0)
    conv_maintenance = conventional.get("avg_engine_maintenance_costs_day", 0)
    conv_spares = conventional.get("spares_consumables_costs", 0)
    conv_eu_ets = conventional.get("avg_eu_ets", 0)
    conv_fuel_eu = conventional.get("avg_fueleu_day", 0)

    future = (api_data.get("future_output_table", {}).get("costs") or [{}])[0]
    fut_fuel_price = (api_data.get("future_output_table", {}).get("fuel_price") or [{}])[0].get("future_avg_fuel_price_day", 0)
    fut_financing = future.get("future_avg_financing_day", 0)
    fut_maintenance = future.get("future_avg_engine_maintenance_costs_day", 0)
    fut_spares = future.get("future_avg_spares_consumables_costs_day", 0)
    fut_eu_ets = future.get("future_eu_ets", 0)
    fut_fuel_eu = future.get("future_avg_fueleu_day", 0)

    # 2) Extract the Savings and Savings_perc from API
    opex_table = api_data.get("opex_table", {})
    savings_data = (opex_table.get("Savings") or [{}])[0]
    savings_perc_data = (opex_table.get("Savings_perc") or [{}])[0]

    fuel_elec_savings = savings_data.get("savings_fuel_price", 0)
    fuel_elec_savings_perc = savings_perc_data.get("perc_savings_fuel_price", 0)

    financing_savings = 0
    financing_savings_perc = 0

    maintenance_savings = savings_data.get("savings_maintenance_cost", 0)
    maintenance_savings_perc = savings_perc_data.get("perc_savings_maintenance_cost", 0)

    spares_savings = savings_data.get("savings_spare_cost", 0)
    spares_savings_perc = savings_perc_data.get("perc_savings_spare_cost", 0)

    eu_ets_savings = savings_data.get("savings_eu_ets")
    eu_ets_savings_perc = savings_perc_data.get("perc_savings_eu_ets", 0)

    fueleu_savings = savings_data.get("savings_fuel_eu", 0)
    fueleu_savings_perc = savings_perc_data.get("perc_savings_fuel_eu", 0)

    # 3) Build rows
    rows = [
        {
            "metric": "Fuel / electricity",
            "conv": conv_fuel_price,
            "fut": fut_fuel_price,
            "savings": fuel_elec_savings,
            "savings_perc": fuel_elec_savings_perc
        },
        {
            "metric": "Financing",
            "conv": conv_financing,
            "fut": fut_financing,
            "savings": financing_savings,
            "savings_perc": financing_savings_perc
        },
        {
            "metric": "Maintenance",
            "conv": conv_maintenance,
            "fut": fut_maintenance,
            "savings": maintenance_savings,
            "savings_perc": maintenance_savings_perc
        },
        {
            "metric": "Spares / consumables",
            "conv": conv_spares,
            "fut": fut_spares,
            "savings": spares_savings,
            "savings_perc": spares_savings_perc
        },
        {
            "metric": "EU ETS",
            "conv": conv_eu_ets,
            "fut": fut_eu_ets,
            "savings": eu_ets_savings,
            "savings_perc": eu_ets_savings_perc
        },
        {
            "metric": "FuelEU",
            "conv": conv_fuel_eu,
            "fut": fut_fuel_eu,
            "savings": fueleu_savings,
            "savings_perc": fueleu_savings_perc
        },
    ]

    total_conv = sum(r["conv"] for r in rows)
    total_fut = sum(r["fut"] for r in rows)
    total_savings = sum(r["savings"] for r in rows)
    total_savings_perc = (total_savings / total_conv * 100) if total_conv != 0 else 0

    rows.append({
        "metric": "OPEX Total",
        "conv": total_conv,
        "fut": total_fut,
        "savings": total_savings,
        "savings_perc": total_savings_perc
    })

    # 4) Build table rows
    table_rows = []
    for row in rows:
        formatted_conv = format_number(row["conv"])
        formatted_fut = format_number(row["fut"])
        formatted_savings = format_number(row["savings"])
        # Format percentage with a "-" sign if savings > 0 (indicating a reduction)
        savings_perc_val = float(row["savings_perc"])
        if savings_perc_val > 0:
            formatted_perc = f"-{abs(savings_perc_val):.0f}%"
        elif savings_perc_val < 0:
            formatted_perc = f"+{abs(savings_perc_val):.0f}%"
        else:
            formatted_perc = "0%"
        table_rows.append(html.Tr([
            html.Td(row["metric"]),
            html.Td(get_currency_symbol(currency)),
            html.Td(formatted_conv),
            html.Td(formatted_fut),
            html.Td(formatted_savings, className=style_savings(row["savings"])),
            html.Td(formatted_perc, className=style_savings(row["savings_perc"]))
        ]))

    header = html.Thead(html.Tr([
        html.Th("OPEX"),
        html.Th("per day"),
        html.Th(f"Conventional ({get_currency_symbol(currency)}/day)"),
        html.Th(f"After measures ({get_currency_symbol(currency)}/day)"),
        html.Th(f"Savings ({get_currency_symbol(currency)}/day)"),
        html.Th("Savings (%)")
    ]), style={"backgroundColor": "#0A4B8C", "color": "white"})

    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def get_opex_comparison_table_year(api_data, currency):
    # --- Data extraction ---
    # Use a dash string for missing breakdown values.
    dash_val = "–"

    
    current_fuel_price_year = (api_data.get("current_table", {}).get("fuel_price_year") or [{}])[0]
    current_maintenance_year = (api_data.get("current_table", {}).get("fuel_price_year") or [{}])[0]
    current_spares_year = (api_data.get("current_table", {}).get("fuel_price_year") or [{}])[0]
    current_euets_year = (api_data.get("current_table", {}).get("ets_penalty") or [{}])[0]
    current_fueleu_year = (api_data.get("current_table", {}).get("fueleu_penalty") or [{}])[0]
    current_opex = (api_data.get("current_table", {}).get("opex_year") or [{}])[0]
    
    future_fuel_price_year = (api_data.get("future_output_table", {}).get("fuel_price_year") or [{}])[0]
    future_maintenance_year = (api_data.get("future_output_table", {}).get("fuel_price_year") or [{}])[0]
    future_spares_year = (api_data.get("future_output_table", {}).get("fuel_price_year") or [{}])[0]
    future_euets_year = (api_data.get("future_output_table", {}).get("ets_penalty") or [{}])[0]
    future_fueleu_year = (api_data.get("future_output_table", {}).get("fueleu_penalty") or [{}])[0]
    future_opex = (api_data.get("future_output_table", {}).get("opex_year") or [{}])[0]
    
    
    
    

    # Extract savings breakdown values from the yearly table.
    # (If the "opex_table_year" object does not exist, default to zero values.)
    opex_year_table = api_data.get("opex_table_year", {})
    savings_obj = (opex_year_table.get("Savings") or [{}])[0]
    savings_perc_obj = (opex_year_table.get("Savings_perc") or [{}])[0]

    # --- Build the rows ---
    # For breakdown rows, use dash for conventional and future values.
    rows = [
        {
            "metric": "Fuel / electricity",
            "conv": current_fuel_price_year.get("avg_fuel_price_year", 0),
            "fut": future_fuel_price_year.get("future_avg_fuel_price_year", 0),
            "savings": savings_obj.get("savings_fuel_price_year", 0),
            "savings_perc": savings_perc_obj.get("perc_savings_fuel_price_year", 0)
        },
        {
            "metric": "Maintenance",
            "conv": current_maintenance_year.get("avg_engine_maintenance_costs_year", 0),
            "fut": future_maintenance_year.get("future_avg_engine_maintenance_costs_year", 0),
            "savings": savings_obj.get("savings_maintenance_cost_year", 0),
            "savings_perc": savings_perc_obj.get("perc_savings_maintenance_cost_year", 0)
        },
        {
            "metric": "Spares / consumables",
            "conv": current_spares_year.get("spares_consumables_costs_year", 0),
            "fut": future_spares_year.get("future_spares_consumables_costs_year", 0),
            "savings": savings_obj.get("savings_spare_cost_year", 0),
            "savings_perc": savings_perc_obj.get("perc_savings_spare_cost_year", 0)
        },
        {
            "metric": "EU ETS",
            "conv": current_euets_year.get("current_eu_ets_year", 0),
            "fut": future_euets_year.get("future_eu_ets_year", 0),
            "savings": savings_obj.get("savings_eu_ets_year", 0),
            "savings_perc": savings_perc_obj.get("perc_savings_eu_ets_year", 0)
        },
        {
            "metric": "FuelEU",
            "conv": current_fueleu_year.get("total_fueleu_year", 0),
            "fut": future_fueleu_year.get("future_total_fueleu_year", 0),
            "savings": savings_obj.get("savings_fuel_eu_year", 0),
            "savings_perc": savings_perc_obj.get("perc_savings_fuel_eu_year", 0)
        },
        {
            "metric": "OPEX Total",
            "conv": current_opex.get("total_opex_year", 0),
            "fut": future_opex.get("future_total_opex_year", 0),
            "savings": savings_obj.get("savings_total_opex_year", 0),
            "savings_perc": savings_perc_obj.get("perc_savings_total_opex_year", 0)
        }
    ]

    # --- Build table rows ---
    table_rows = []
    for row in rows:
        formatted_conv = format_number(row["conv"]) if isinstance(row["conv"], (int, float)) else row["conv"]
        formatted_fut = format_number(row["fut"]) if isinstance(row["fut"], (int, float)) else row["fut"]
        formatted_savings = format_number(row["savings"]) if isinstance(row["savings"], (int, float)) else row["savings"]

        # Format the savings percentage with a sign.
        if isinstance(row["savings_perc"], (int, float)):
            sp_val = float(row["savings_perc"])
            if sp_val > 0:
                formatted_perc = f"-{abs(sp_val):.0f}%"
            elif sp_val < 0:
                formatted_perc = f"+{abs(sp_val):.0f}%"
            else:
                formatted_perc = "0%"
        else:
            formatted_perc = row["savings_perc"]

        table_rows.append(
            html.Tr([
                html.Td(row["metric"]),
                html.Td(get_currency_symbol(currency)),
                html.Td(formatted_conv),
                html.Td(formatted_fut),
                html.Td(formatted_savings, className=style_savings(row["savings"])),
                html.Td(formatted_perc, className=style_savings(row["savings_perc"]))
            ])
        )

    header = html.Thead(
        html.Tr([
            html.Th("OPEX"),
            html.Th("per year"),
            html.Th(f"Conventional ({get_currency_symbol(currency)}/year)"),
            html.Th(f"After measures ({get_currency_symbol(currency)}/year)"),
            html.Th(f"Savings ({get_currency_symbol(currency)}/year)"),
            html.Th("Savings (%)")
        ]),
        style={"backgroundColor": "#0A4B8C", "color": "white"}
    )

    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")



# ---------------------------------------------------------------------------
# Emissions Comparison Table
# ---------------------------------------------------------------------------
def get_emissions_comparison_table(api_data):
    current = api_data.get("current_table", {})
    future = api_data.get("future_output_table", {})
    emissions_table = api_data.get("emissions_table", {})

    savings_data = (emissions_table.get("Savings") or [{}])[0]
    savings_perc_data = (emissions_table.get("Savings_perc") or [{}])[0]

    co2_ttw_conv = (current.get("co2_emission_ttw") or [{}])[0].get("avg_co2_ttw_day", 182084)
    co2_ttw_fut  = (future.get("co2_emission_ttw") or [{}])[0].get("future_avg_co2_ttw_day", 127459)
    co2_ttw_savings = savings_data.get("savings_avg_co2_ttw", 0)
    co2_ttw_savings_perc = savings_perc_data.get("perc_savings_avg_co2_ttw", 0)

    co2_wtw_conv = (current.get("co2_emission_wtw") or [{}])[0].get("avg_co2_wtw_day", 216479)
    co2_wtw_fut  = (future.get("co2_emission_wtw") or [{}])[0].get("future_avg_co2_wtw_day", 155692)
    co2_wtw_savings = savings_data.get("savings_avg_co2_wtw", 0)
    co2_wtw_savings_perc = savings_perc_data.get("perc_savings_avg_co2_wtw", 0)

    nox_conv = (current.get("nox_emission_ttw") or [{}])[0].get("avg_nox_ttw_day", 3070)
    nox_fut  = (future.get("nox_emission_ttw") or [{}])[0].get("future_avg_nox_ttw_day", 2164)
    nox_savings = savings_data.get("savings_avg_nox_ttw", 0)
    nox_savings_perc = savings_perc_data.get("perc_savings_avg_nox_ttw", 0)

    sox_conv = (current.get("sox_emission_ttw") or [{}])[0].get("avg_sox_ttw_day", 121)
    sox_fut  = (future.get("sox_emission_ttw") or [{}])[0].get("future_avg_sox_ttw_day", 85)
    sox_savings = savings_data.get("savings_avg_sox_ttw", 0)
    sox_savings_perc = savings_perc_data.get("perc_savings_avg_sox_ttw", 0)

    pm_conv = (current.get("pm_emission_ttw") or [{}])[0].get("avg_pm_ttw_day", 54)
    pm_fut  = (future.get("pm_emission_ttw") or [{}])[0].get("future_avg_pm_ttw_day", 37)
    pm_savings = savings_data.get("savings_avg_pm_ttw", 0)
    pm_savings_perc = savings_perc_data.get("perc_savings_avg_pm_ttw", 0)

    ch4_conv = (current.get("ch4_emission_ttw") or [{}])[0].get("avg_ch4_ttw_day", 3)
    ch4_fut  = (future.get("ch4_emission_ttw") or [{}])[0].get("future_avg_ch4_ttw_day", 3)
    ch4_savings = savings_data.get("savings_avg_ch4_ttw", 0)
    ch4_savings_perc = savings_perc_data.get("perc_savings_avg_ch4_ttw", 0)

    rows = [
        {"metric": "CO₂ Emissions TtW", "conv": co2_ttw_conv, "fut": co2_ttw_fut, "savings": co2_ttw_savings, "savings_perc": co2_ttw_savings_perc},
        {"metric": "CO₂ Emissions WtW", "conv": co2_wtw_conv, "fut": co2_wtw_fut, "savings": co2_wtw_savings, "savings_perc": co2_wtw_savings_perc},
        {"metric": "NOₓ Emissions TtW", "conv": nox_conv, "fut": nox_fut, "savings": nox_savings, "savings_perc": nox_savings_perc},
        {"metric": "SOₓ Emissions TtW", "conv": sox_conv, "fut": sox_fut, "savings": sox_savings, "savings_perc": sox_savings_perc},
        {"metric": "PM Emissions TtW", "conv": pm_conv, "fut": pm_fut, "savings": pm_savings, "savings_perc": pm_savings_perc},
        {"metric": "CH₄ Emissions TtW", "conv": ch4_conv, "fut": ch4_fut, "savings": ch4_savings, "savings_perc": ch4_savings_perc},
    ]

    table_rows = []
    for row in rows:
        conv_val = float(row.get("conv") or 0)
        fut_val = float(row.get("fut") or 0)
        savings_val = float(row.get("savings") or 0)
        savings_perc_val = float(row.get("savings_perc") or 0)
        formatted_conv = format_number(conv_val)
        formatted_fut = format_number(fut_val)
        formatted_savings = format_number(savings_val)
        if savings_perc_val > 0:
            formatted_perc = f"-{abs(savings_perc_val):.0f}%"
        elif savings_perc_val < 0:
            formatted_perc = f"+{abs(savings_perc_val):.0f}%"
        else:
            formatted_perc = "0%"
        table_rows.append(html.Tr([
            html.Td(row["metric"]),
            html.Td("kg"),
            html.Td(formatted_conv),
            html.Td(formatted_fut),
            html.Td(formatted_savings, className=style_savings(row["savings"])),
            html.Td(formatted_perc, className=style_savings(row["savings_perc"]))
        ]))

    
    header = html.Thead(html.Tr([
        html.Th("Emissions"),
        html.Th("per day"),
        html.Th("Conventional (kg/day)"),
        html.Th("After measures (kg/day)"),
        html.Th("Savings (kg/day)"),
        html.Th("Savings (%)")
    ]), style={"backgroundColor": "#0A4B8C", "color": "white"})
    
    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def get_emissions_comparison_table_year(api_data):
    """
    Build a yearly emissions comparison table using:
      - Yearly values from the "emissions_table_year" object in the API response.
    """
    emissions_year = api_data.get("emissions_table_year", {})
    savings_data = (emissions_year.get("Savings") or [{}])[0]
    savings_perc_data = (emissions_year.get("Savings_perc") or [{}])[0]

    # The yearly values are assumed to be provided already:
    co2_ttw_conv = savings_data.get("savings_avg_co2_ttw_year", 0)  # Here, you may need to use your API keys.
    # In many cases, the savings in the yearly table might be reported directly.
    # If you prefer to compute yearly conventional and future values from daily averages,
    # multiply the daily averages (from current_table and future_output_table) by 365.
    # For this example, we assume the yearly table contains the needed data.
    
    # For demonstration, we use the following keys from your sample:
    co2_ttw_conv = (api_data.get("current_table", {}).get("co2_emission_ttw") or [{}])[0].get("avg_co2_ttw_day", 182084) * 365
    co2_ttw_fut  = (api_data.get("future_output_table", {}).get("co2_emission_ttw") or [{}])[0].get("future_avg_co2_ttw_day", 143153) * 365
    co2_ttw_savings = (emissions_year.get("Savings") or [{}])[0].get("savings_avg_co2_ttw_year", 0)
    co2_ttw_savings_perc = (emissions_year.get("Savings_perc") or [{}])[0].get("perc_savings_avg_co2_ttw_year", 0)

    co2_wtw_conv = (api_data.get("current_table", {}).get("co2_emission_wtw") or [{}])[0].get("avg_co2_wtw_day", 216479) * 365
    co2_wtw_fut  = (api_data.get("future_output_table", {}).get("co2_emission_wtw") or [{}])[0].get("future_avg_co2_wtw_day", 174889) * 365
    co2_wtw_savings = (emissions_year.get("Savings") or [{}])[0].get("savings_avg_co2_wtw_year", 0)
    co2_wtw_savings_perc = (emissions_year.get("Savings_perc") or [{}])[0].get("perc_savings_avg_co2_wtw_year", 0)

    nox_conv = (api_data.get("current_table", {}).get("nox_emission_ttw") or [{}])[0].get("avg_nox_ttw_day", 3070) * 365
    nox_fut  = (api_data.get("future_output_table", {}).get("nox_emission_ttw") or [{}])[0].get("future_avg_nox_ttw_day", 2432) * 365
    nox_savings = (emissions_year.get("Savings") or [{}])[0].get("savings_avg_nox_ttw_year", 0)
    nox_savings_perc = (emissions_year.get("Savings_perc") or [{}])[0].get("perc_savings_avg_nox_ttw_year", 0)

    sox_conv = (api_data.get("current_table", {}).get("sox_emission_ttw") or [{}])[0].get("avg_sox_ttw_day", 136) * 365
    sox_fut  = (api_data.get("future_output_table", {}).get("sox_emission_ttw") or [{}])[0].get("future_avg_sox_ttw_day", 96) * 365
    sox_savings = (emissions_year.get("Savings") or [{}])[0].get("savings_avg_sox_ttw_year", 0)
    sox_savings_perc = (emissions_year.get("Savings_perc") or [{}])[0].get("perc_savings_avg_sox_ttw_year", 0)

    pm_conv = (api_data.get("current_table", {}).get("pm_emission_ttw") or [{}])[0].get("avg_pm_ttw_day", 54) * 365
    pm_fut  = (api_data.get("future_output_table", {}).get("pm_emission_ttw") or [{}])[0].get("future_avg_pm_ttw_day", 43) * 365
    pm_savings = (emissions_year.get("Savings") or [{}])[0].get("savings_avg_pm_ttw_year", 0)
    pm_savings_perc = (emissions_year.get("Savings_perc") or [{}])[0].get("perc_savings_avg_pm_ttw_year", 0)

    ch4_conv = (api_data.get("current_table", {}).get("ch4_emission_ttw") or [{}])[0].get("avg_ch4_ttw_day", 3) * 365
    ch4_fut  = (api_data.get("future_output_table", {}).get("ch4_emission_ttw") or [{}])[0].get("future_avg_ch4_ttw_day", 4) * 365
    ch4_savings = (emissions_year.get("Savings") or [{}])[0].get("savings_avg_ch4_ttw_year", 0)
    ch4_savings_perc = (emissions_year.get("Savings_perc") or [{}])[0].get("perc_savings_avg_ch4_ttw_year", 0)

    rows = [
        {"metric": "CO₂ Emissions TtW", "conv": co2_ttw_conv, "fut": co2_ttw_fut, "savings": co2_ttw_savings, "savings_perc": co2_ttw_savings_perc},
        {"metric": "CO₂ Emissions WtW", "conv": co2_wtw_conv, "fut": co2_wtw_fut, "savings": co2_wtw_savings, "savings_perc": co2_wtw_savings_perc},
        {"metric": "NOₓ Emissions TtW", "conv": nox_conv, "fut": nox_fut, "savings": nox_savings, "savings_perc": nox_savings_perc},
        {"metric": "SOₓ Emissions TtW", "conv": sox_conv, "fut": sox_fut, "savings": sox_savings, "savings_perc": sox_savings_perc},
        {"metric": "PM Emissions TtW", "conv": pm_conv, "fut": pm_fut, "savings": pm_savings, "savings_perc": pm_savings_perc},
        {"metric": "CH₄ Emissions TtW", "conv": ch4_conv, "fut": ch4_fut, "savings": ch4_savings, "savings_perc": ch4_savings_perc},
    ]

    table_rows = []
    for row in rows:
        conv_val = float(row.get("conv") or 0)
        fut_val = float(row.get("fut") or 0)
        savings_val = float(row.get("savings") or 0)
        savings_perc_val = float(row.get("savings_perc") or 0)
        formatted_conv = format_number(conv_val)
        formatted_fut = format_number(fut_val)
        formatted_savings = format_number(savings_val)
        if savings_perc_val > 0:
            formatted_perc = f"-{abs(savings_perc_val):.0f}%"
        elif savings_perc_val < 0:
            formatted_perc = f"+{abs(savings_perc_val):.0f}%"
        else:
            formatted_perc = "0%"
        table_rows.append(html.Tr([
            html.Td(row["metric"]),
            html.Td("kg"),
            html.Td(formatted_conv),
            html.Td(formatted_fut),
            html.Td(formatted_savings, className=style_savings(row["savings"])),
            html.Td(formatted_perc, className=style_savings(row["savings_perc"]))
        ]))

    header = html.Thead(html.Tr([
        html.Th("Emissions"),
        html.Th("per year"),
        html.Th("Conventional (kg/year)"),
        html.Th("After measures (kg/year)"),
        html.Th("Savings (kg/year)"),
        html.Th("Savings (%)")
    ]), style={"backgroundColor": "#0A4B8C", "color": "white"})

    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")

def get_carbon_footprint_table(api_data):

    # Grab the carbon_footprint_table from the API data
    carbon_footprint = api_data.get("current_table", {})

    # Extract data for each scope. 
    scope_1_data = (carbon_footprint.get("scope_1_co2") or [{}])[0]
    scope_2_data = (carbon_footprint.get("scope_2_co2") or [{}])[0]
    scope_3_data = (carbon_footprint.get("scope_3_co2") or [{}])[0]


    rows = [
        {
            "metric": "Scope 1 - Direct (Tank to Wake) - MT",
            "sailing": scope_1_data.get("sailing_co2_emission_ttw_year", 0),
            "working": scope_1_data.get("working_co2_emission_ttw_year", 0),
            "idle": scope_1_data.get("idle_co2_emission_ttw_year", 0),
        },
        {
            "metric": "Scope 2 - Indirect (Well to Tank) - MT",
            "sailing": scope_2_data.get("sailing_scope_2_co2_emission_ttw_year", 0),
            "working": scope_2_data.get("working_scope_2_co2_emission_ttw_year", 0),
            "idle": scope_2_data.get("idle_scope_2_co2_emission_ttw_year", 0),
        },
        {
            "metric": "Scope 3 - Upstream (Well to Well) - MT",
            "sailing": scope_3_data.get("sailing_scope_3_co2_emission_ttw_year", 0),
            "working": scope_3_data.get("working_scope_3_co2_emission_ttw_year", 0),
            "idle": scope_3_data.get("idle_scope_3_co2_emission_ttw_year", 0),
        },
    ]

    # Build the table rows
    table_rows = []
    for row in rows:
        sailing_val = format_number(row["sailing"] or 0)
        working_val = format_number(row["working"] or 0)
        idle_val    = format_number(row["idle"]    or 0)

        table_rows.append(
            html.Tr([
                html.Td(row["metric"]), 
                html.Td(sailing_val),
                html.Td(working_val),
                html.Td(idle_val),
            ])
        )

    # Create a styled header (similar to your emissions table style)
    header = html.Thead(
        html.Tr([
            html.Th("Carbon Footprint"),
            html.Th("Propulsion"),
            html.Th("Parked / Mooring"),
            html.Th("Cold Ironing"),
        ]),
        style={"backgroundColor": "#0A4B8C", "color": "white"}
    )

    # Wrap everything in a Dash Bootstrap Table for a nice style
    table = dbc.Table(
        [header, html.Tbody(table_rows)],
        bordered=True, 
        striped=True,
        hover=True
    )

    # Return a responsive container holding the table
    return html.Div(table, className="table-responsive")


def get_vessel_summary_table(api_data, currency):
    # --- Extract Engine Power from current_table ---
    
    energy_table = api_data.get("current_table", {})
    
    # Engine Power (from energy_table)

    engine_power_data = energy_table.get("enginge_power", [{}])[0]  # JSON object containing engine power info
    engine_power_sailing = engine_power_data.get("sailing_power", 0)
    engine_power_working = engine_power_data.get("working_power", 0)
    engine_power_idle    = engine_power_data.get("idle_power", 0)
    engine_power_avg = engine_power_data.get("avg_power_req_day")

    # Energy Requirements (from energy_table)
    energy_req_kwh_day = energy_table.get("power_calc_day", [{}])[0]
    energy_req_kwh_day_sailing = energy_req_kwh_day.get("sailing_energy_req_kwh_day", 0)
    energy_req_kwh_day_working = energy_req_kwh_day.get("working_energy_req_kwh_day", 0)
    energy_req_kwh_day_idle    = energy_req_kwh_day.get("idle_energy_req_kwh_day", 0)
    energy_req_kwh_day_avg = energy_req_kwh_day.get("power_req_day", 0)
    

    energy_req_mwh_year = energy_table.get("power_calc_year", [{}])[0]
    energy_req_mwh_year_sailing = energy_req_mwh_year.get("sailing_energy_req_mwh_year", 0)
    energy_req_mwh_year_working = energy_req_mwh_year.get("working_energy_req_mwh_year", 0)
    energy_req_mwh_year_idle    = energy_req_mwh_year.get("idle_energy_req_mwh_year", 0)
    energy_req_mwh_year_avg = energy_req_mwh_year.get("power_req_year", 0)

    # Fuel Consumption (kiloliters per year)
    fuel_consumption_kiloliters_year = energy_table.get("fuel_consumption_kiloliters_year", [{}])[0]
    fuel_consumption_kl_sailing = fuel_consumption_kiloliters_year.get("sailing_fuel_consumption_kiloliter_year", 0)
    fuel_consumption_kl_working = fuel_consumption_kiloliters_year.get("working_fuel_consumption_kiloliter_year", 0)
    fuel_consumption_kl_idle    = fuel_consumption_kiloliters_year.get("idle_fuel_consumption_kiloliter_year", 0)
    fuel_consumption_kiloliter_day_year = fuel_consumption_kiloliters_year.get("avg_fuel_consumption_kiloliter_day_year", 0)

    # Fuel Price (Euro per year)
    fuel_price_year = energy_table.get("fuel_price_year", [{}])[0]
    fuel_price_year_euro_sailing = fuel_price_year.get("sailing_fuel_price_year", 0)
    fuel_price_year_euro_working = fuel_price_year.get("working_fuel_price_year", 0)
    fuel_price_year_euro_idle    = fuel_price_year.get("idle_fuel_price_year", 0)
    fuel_price_year = fuel_price_year.get("fuel_price_year", 0)

    # Current EU ETS Year
    ets_penalty = energy_table.get("ets_penalty", [{}])[0]
    current_eu_ets_year = ets_penalty.get("current_eu_ets_year", 0)
    current_eu_ets_sailing = ets_penalty.get("current_sailing_eu_ets_year", 0)
    current_eu_ets_working = ets_penalty.get("current_working_eu_ets_year", 0)
    current_eu_ets_idle    = ets_penalty.get("current_idle_eu_ets_year", 0)

    # --- Build the rows for the table with an extra "unit" field ---
    rows = [
        {
            "metric": "Engine Power",
            "unit": "KW",
            "sailing": engine_power_sailing,
            "working": engine_power_working,
            "idle": engine_power_idle,
        },
        {
            "metric": "Energy Req Day",
            "unit": "KWh",
            "sailing": energy_req_kwh_day_sailing,
            "working": energy_req_kwh_day_working,
            "idle": energy_req_kwh_day_idle,
        },
        {
            "metric": "Energy Req Year",
            "unit": "MWh",
            "sailing": energy_req_mwh_year_sailing,
            "working": energy_req_mwh_year_working,
            "idle": energy_req_mwh_year_idle,
        },
        {
            "metric": "Fuel Consumption Year",
            "unit": "KiloLiters",
            "sailing": fuel_consumption_kl_sailing,
            "working": fuel_consumption_kl_working,
            "idle": fuel_consumption_kl_idle,
        },
        {
            "metric": "Fuel Price Year",
            "unit": get_currency_symbol(currency),
            "sailing": fuel_price_year_euro_sailing,
            "working": fuel_price_year_euro_working,
            "idle": fuel_price_year_euro_idle,
        },
        {
            "metric": "Current EU ETS Penalty Year",
            "unit": get_currency_symbol(currency),  # Unit can be added if applicable
            "sailing": current_eu_ets_sailing,
            "working": current_eu_ets_working,
            "idle": current_eu_ets_idle,
        }
    ]

    # --- Build the Dash table rows ---
    table_rows = []
    for row in rows:
        table_rows.append(
            html.Tr([
                html.Td(row["metric"]),
                html.Td(row["unit"]),
                html.Td(format_number(row["sailing"])),
                html.Td(format_number(row["working"])),
                html.Td(format_number(row["idle"])),
            ])
        )

    # --- Build the table header with an extra column for Unit ---
    header = html.Thead(
        html.Tr([
            html.Th("Operation Profile"),
            html.Th("Unit"),
            html.Th("Propulsion"),
            html.Th("Parked / Mooring"),
            html.Th("Cold Ironing"),
        ]),
        style={"backgroundColor": "#0A4B8C", "color": "white"}
    )

    # --- Wrap the header and rows in a Bootstrap Table ---
    table = dbc.Table(
        [header, html.Tbody(table_rows)],
        bordered=True,
        striped=True,
        hover=True
    )

    # --- Return the table in a responsive container ---
    return html.Div(table, className="table-responsive")

def set_figure_layout(fig, title, xaxis_title=None, yaxis_title=None):
    """Centralized layout configuration with fixed sizing to avoid compression."""
    fig.update_layout(
        title=dict(text="<b>" + title + "</b>", x=0.5, xanchor="center", font=dict(color="#0A4B8C")),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=TEMPLATE_STYLE,
        margin=MARGIN_STYLE,
        autosize=False,
        width=1000,    # Fixed width – adjust as needed
        height=500,    # Fixed height – adjust as needed
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified"
    )
    return fig


# ---------------------------------------------------------------------------
# Figure Functions Updated with Currency Symbol in Labels
# ---------------------------------------------------------------------------
def fuel_consumption_figure(api_data=None, currency="EUR"):
    """Create a visualization for fuel consumption costs from 2025 to 2050."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    current_ts = sorted(api_data["current_timeseries"], key=lambda x: x.get("year", 0))
    future_ts = sorted(api_data["future_timeseries"], key=lambda x: x.get("year", 0))
    years = list(range(2025, 2051))
    current_fuel = {entry.get("year"): entry.get("total_fuel_current_inflated", 0) for entry in current_ts}
    future_fuel = {entry.get("year"): entry.get("total_fuel_future_inflated", 0) for entry in future_ts}
    
    current_values = [current_fuel.get(year, 0) for year in years]
    future_values = [future_fuel.get(year, 0) for year in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current Fuel Cost",
        x=years,
        y=current_values,
        marker_color="blue"
    ))
    fig.add_trace(go.Bar(
        name="Future Fuel Cost",
        x=years,
        y=future_values,
        marker_color="orange"
    ))
    
    ylabel = f"Cost ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "Fuel Cost Comparison (2025-2050)", "Year", ylabel)
    return fig


def spares_figure(api_data=None, currency="EUR"):
    """Create a visualization for spares/consumables costs from 2025 to 2050."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    current_ts = sorted(api_data["current_timeseries"], key=lambda x: x.get("year", 0))
    future_ts = sorted(api_data["future_timeseries"], key=lambda x: x.get("year", 0))
    years = list(range(2025, 2051))
    
    current_spares = {entry.get("year"): entry.get("total_spare_current_inflated", 0) for entry in current_ts}
    future_spares = {entry.get("year"): entry.get("total_spare_future_inflated", 0) for entry in future_ts}
    current_values = [current_spares.get(year, 0) for year in years]
    future_values = [future_spares.get(year, 0) for year in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current Spares Cost",
        x=years,
        y=current_values,
        marker_color="blue"
    ))
    fig.add_trace(go.Bar(
        name="Future Spares Cost",
        x=years,
        y=future_values,
        marker_color="orange"
    ))
    
    ylabel = f"Cost ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "Spares & Consumables Cost Comparison (2025-2050)", "Year", ylabel)
    return fig


def penalty_cost_figure(api_data=None, currency="EUR"):
    """Create a visualization for penalty cost from 2025 to 2050."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    current_ts = sorted(api_data["current_timeseries"], key=lambda x: x.get("year", 0))
    future_ts = sorted(api_data["future_timeseries"], key=lambda x: x.get("year", 0))
    years = list(range(2025, 2051))
    
    current_penalty = {entry.get("year"): entry.get("current_penalty", 0) for entry in current_ts}
    future_penalty = {entry.get("year"): entry.get("future_penalty", 0) for entry in future_ts}
    current_values = [current_penalty.get(year, 0) for year in years]
    future_values = [future_penalty.get(year, 0) for year in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current Penalty Cost",
        x=years,
        y=current_values,
        marker_color="blue"
    ))
    fig.add_trace(go.Bar(
        name="Future Penalty Cost",
        x=years,
        y=future_values,
        marker_color="orange"
    ))
    
    ylabel = f"Penalty Cost ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "Fuel EU Penalty", "Year", ylabel)
    return fig


def maintenance_cost_figure(api_data=None, currency="EUR"):
    """Create a visualization for maintenance cost from 2025 to 2050."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    current_ts = sorted(api_data["current_timeseries"], key=lambda x: x.get("year", 0))
    future_ts = sorted(api_data["future_timeseries"], key=lambda x: x.get("year", 0))
    years = list(range(2025, 2051))
    
    current_maintenance = {entry.get("year"): entry.get("total_maintenance_current_inflated", 0) for entry in current_ts}
    future_maintenance = {entry.get("year"): entry.get("total_maintenance_future_inflated", 0) for entry in future_ts}
    current_values = [current_maintenance.get(year, 0) for year in years]
    future_values = [future_maintenance.get(year, 0) for year in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current Maintenance Cost",
        x=years,
        y=current_values,
        marker_color="green"
    ))
    fig.add_trace(go.Bar(
        name="Future Maintenance Cost",
        x=years,
        y=future_values,
        marker_color="red"
    ))
    
    ylabel = f"Cost ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "Maintenance Cost Comparison (2025-2050)", "Year", ylabel)
    return fig


def min_future_opex_figure(api_data=None, currency="EUR"):
    """Create a visualization for total expenditure (MIN_FUTURE_OPEX) over time."""
    if not api_data or "result" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    results = sorted(api_data["result"], key=lambda x: x.get("year", 0))
    years = [res["year"] for res in results]
    cumulative_values = [res["cumulative"] for res in results]
    npv_values = [res.get("npv", 0) for res in results]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=cumulative_values,
        name="Cumulative",
        marker_color="navy"
    ))
    fig.add_trace(go.Scatter(
        x=years,
        y=npv_values,
        mode="lines+markers",
        name="NPV",
        line=dict(color="gray", width=2)
    ))
    
    ylabel = f"Amount ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "Cashflow", "Year", ylabel)
    return fig


def opex_cost_figure(api_data=None, currency="EUR"):
    """Create a visualization for OPEX cost from 2025 to 2050."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    current_ts = sorted(api_data["current_timeseries"], key=lambda x: x.get("year", 0))
    future_ts = sorted(api_data["future_timeseries"], key=lambda x: x.get("year", 0))
    years = list(range(2025, 2051))
    
    current_opex = {entry.get("year"): entry.get("current_opex", 0) for entry in current_ts}
    future_opex = {entry.get("year"): entry.get("future_opex", 0) for entry in future_ts}
    current_values = [current_opex.get(year, 0) for year in years]
    future_values = [future_opex.get(year, 0) for year in years]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name="Current OPEX",
        x=years,
        y=current_values,
        mode="lines+markers",
        line=dict(color="blue", width=2),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        name="Future OPEX",
        x=years,
        y=future_values,
        mode="lines+markers",
        line=dict(color="orange", width=2, dash="dash"),
        marker=dict(size=6)
    ))
    
    ylabel = f"Cost ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "OPEX Cost Comparison (2025-2050)", "Year", ylabel)
    return fig


def cashflow_figure(api_data=None, currency="EUR"):
    """Create a visualization for yearly cash flow."""
    if not api_data or "result" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    results = sorted(api_data["result"], key=lambda x: x.get("year", 0))
    years = [res["year"] for res in results]
    cash_values = [res["result"] for res in results]
    
    positive_values = [max(0, v) for v in cash_values]
    negative_values = [min(0, v) for v in cash_values]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=positive_values,
        name="Positive Cash Flow",
        marker_color="green"
    ))
    fig.add_trace(go.Bar(
        x=years,
        y=negative_values,
        name="Negative Cash Flow",
        marker_color="red"
    ))
    fig.add_trace(go.Scatter(
        x=years,
        y=cash_values,
        mode="lines+markers",
        name="Net Cash Flow",
        line=dict(color="blue", width=2)
    ))
    
    ylabel = f"Cash Flow ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "Post-Conventional OPEX Balance", "Year", ylabel)
    return fig


def dwelling_at_berth_pie_figure(api_data, currency="EUR"):
    """Generate the current dwelling at berth pie chart."""
    if not api_data or "current_table" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    costs = api_data["current_table"].get("costs", [{}])[0]
    fuel = api_data["current_table"].get("fuel_price", [{}])[0]
    labels = ["Fuel","Maintenance", "Spares/consumables", "EU ETS", "FuelEU"]
    values = [
        fuel.get("avg_fuel_price_day", 0),
        costs.get("avg_engine_maintenance_costs_day", 0),
        costs.get("avg_spares_consumables_costs_day", 0),
        costs.get("avg_eu_ets",0),
        costs.get("avg_fueleu_day", 0)
    ]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+value"
    ))
    fig.update_layout(
        title=f"Current Costs Breakdown ({get_currency_symbol(currency)})",
        template="plotly_white"
    )
    return fig


def future_dwelling_at_berth_pie_figure(api_data, currency="EUR"):
    """Generate the future dwelling at berth pie chart."""
    if not api_data or "future_output_table" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    costs = api_data["future_output_table"].get("costs", [{}])[0]
    fuel = api_data["future_output_table"].get("fuel_price", [{}])[0]
    labels = ["Fuel","Maintenance", "Spares/consumables", "EU ETS", "FuelEU"]
    values = [
        fuel.get("future_avg_fuel_price_day", 0),
        costs.get("future_avg_engine_maintenance_costs_day", 0),
        costs.get("future_avg_spares_consumables_costs_day", 0),
        costs.get("future_eu_ets",0),
        costs.get("future_avg_fueleu_day", 0)
    ]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+value"
    ))
    fig.update_layout(
        title=f"Future Costs Breakdown ({get_currency_symbol(currency)})",
        template="plotly_white"
    )
    return fig

def eu_ets_cost_figure(api_data=None, currency="EUR"):
    """Create a visualization for EU ETS costs over time."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    current_ts = sorted(api_data["current_timeseries"], key=lambda x: x.get("year", 0))
    future_ts = sorted(api_data["future_timeseries"], key=lambda x: x.get("year", 0))
    years = list(range(2025, 2051))
    
    current_ets = {entry.get("year"): entry.get("current_eu_ets", 0) for entry in current_ts}
    future_ets = {entry.get("year"): entry.get("future_eu_ets", 0) for entry in future_ts}
    current_values = [current_ets.get(year, 0) for year in years]
    future_values = [future_ets.get(year, 0) for year in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current EU ETS Cost",
        x=years,
        y=current_values,
        marker_color="blue"
    ))
    fig.add_trace(go.Bar(
        name="Future EU ETS Cost",
        x=years,
        y=future_values,
        marker_color="orange"
    ))
    
    ylabel = f"Cost ({get_currency_symbol(currency)})"
    set_figure_layout(fig, "EU ETS Cost Comparison (2025-2050)", "Year", ylabel)
    return fig

def dashboard_layout(api_data, currency="EUR"):
    """Create dashboard layout with multiple visualizations."""
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader(
                html.H4("Dashboard", className="card-title", style={"color": "white"}),
                style={"backgroundColor": "#0A4B8C"}
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=min_future_opex_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width":"100%","height":"100%"}
                    ), md=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=cashflow_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width":"100%","height":"100%"}
                        
                    ), md=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=penalty_cost_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width":"100%", "height":"100%"}
                    ), md=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=eu_ets_cost_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width":"100%","height":"100%"}
                    ), md=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=dwelling_at_berth_pie_figure(api_data, currency),
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width": "100%", "height": "100%"}
                    ), md=6),
                    dbc.Col(dcc.Graph(
                        figure=future_dwelling_at_berth_pie_figure(api_data, currency),
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width": "100%", "height": "100%"}
                    ), md=6)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=maintenance_cost_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width": "100%", "height": "100%"}
                    ), md=6),
                    dbc.Col(dcc.Graph(
                        figure=spares_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width": "100%", "height": "100%"}
                    ), md=6)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=fuel_consumption_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width": "100%", "height": "100%"}
                    ), md=6),
                    dbc.Col(dcc.Graph(
                        figure=opex_cost_figure(api_data, currency), 
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"width": "100%", "height": "100%"}
                    ), md=6)
                ], className="mb-4")
            ])
        ], className="mb-4")
    ], fluid=True)  # dbc.Container accepts fluid=True

def layout():
    return dbc.Container([
        html.H1("Key Output Metrics", className="mb-4", 
                style={"color": "#0A4B8C", "textAlign": "center"}),
        dbc.Row([
            dbc.Col([
                html.Label("Select Tables", className="font-weight-bold"),
                dcc.Checklist(
                    id='table-selection-dropdown',
                    options=[
                        {"label": "Vessel Summary", "value": "vessel_summary"},
                        {"label": "Current Output", "value": "current"},
                        {"label": "Future Output", "value": "future"},
                        {"label": "OPEX Comparison", "value": "opex"},
                        {"label": "Emissions Comparison", "value": "emissions"},
                        {"label": "Carbon Footprint", "value": "carbon_footprint"}
                    ],
                    value=['opex', 'emissions'],
                    labelStyle={"display": "inline-block", "marginRight": "10px"},
                    inputStyle={"marginRight": "5px"}
                ),
                html.Br(),
                html.Label("Timeframe", className="font-weight-bold"),
                dcc.RadioItems(
                    id="timeframe-toggle",
                    options=[
                        {"label": "Daily", "value": "day"},
                        {"label": "Yearly", "value": "year"}
                    ],
                    value="day",
                    labelStyle={"display": "inline-block", "marginRight": "10px"}
                )
            ], md=12, xs=12)
        ], className="mb-4"),
        html.Div(id='output-content', 
                 style={"padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "8px"})
    ], fluid=True, className="py-4")  # Use dbc.Container here, not html.Div