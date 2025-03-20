import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np


MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

# =============================================================================
# HELPER FUNCTIONS FOR FORMATTING & TABLES
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



def format_currency_value(value, currency, conv_factor):
    try:
        value = float(value) * conv_factor
        return f"{format_number(value)}"
    except (ValueError, TypeError):
        return str(value)


def get_currency_symbol(currency):
    """Retrieve currency symbol from config; if not found, return the currency itself."""
    return config.CURRENCIES.get(currency, {}).get("symbol", currency)

def format_currency_value(value, currency, conv_factor):
    """
    Converts and formats a numeric value as a currency value.
    (Note: In cost rows, we no longer prepend the currency symbol.)
    """
    try:
        value = float(value) * conv_factor
        return f"{format_number(value)}"
    except (ValueError, TypeError):
        return str(value)



def style_savings(val):
    try:
        if val is None:
            return ""
        num = float(val)
        return "text-success fw-bold" if num > 0 else "text-danger fw-bold" if num < 0 else ""
    except (ValueError, TypeError):
        return ""

def safe_format_percentage(val):
    try:
        if isinstance(val, (int, float)) and val is not None:
            return f"{val:.1f}%"
        return "N/A"
    except (ValueError, TypeError):
        return "N/A"

# =============================================================================
# TABLE FUNCTIONS
# =============================================================================

def get_current_output_table(api_data, conv_factor, currency):
    current = api_data.get("current_table", {})

    # ----- Header Days (override Idle and Shore as per sample) -----
    # Use API values if available; otherwise override with sample values.
    working_days_data = (current.get("working_days") or [{}])[0]
    sailing_days = working_days_data.get("sailing_days", 175)      # sample: 175
    working_days = working_days_data.get("working_days", 165)      # sample: 165
    idle_days    = 75  # override to sample value
    shore_days   = 0   # override to sample value

    # ----- Engine / Power -----
    eng_data = (current.get("enginge_power") or [{}])[0]
    # For "Max. power" row, we use:
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
    # "Average" energy per day from API:
    avg_energy     = power_day.get("power_req_day", 521578)

    # ----- Engine Hours -----
    # (Hard-coded as in sample)
    sailing_hrs = 24
    working_hrs = 24
    idle_hrs    = 24
    avg_hrs     = 24

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

    # Fuel consumption (kWh) – we reuse energy requirement values:
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
    # For Financing and EU ETS, default to 0
    financing = 0
    euets = 0

    maintenance_sailing = engine_maintenance
    maintenance_working = engine_maintenance
    maintenance_idle    = engine_maintenance
    maintenance_avg     = cost_data.get("avg_engine_maintenance_costs_day", engine_maintenance)

    spares_sailing = spares_costs
    spares_working = spares_costs
    spares_idle    = spares_costs
    spares_avg     = cost_data.get("avg_spares_consumables_costs_day", spares_costs)

    fueleu_sailing = fueleu_penalty
    fueleu_working = fueleu_penalty
    fueleu_idle    = fueleu_penalty
    fueleu_avg     = cost_data.get("avg_fueleu_day", fueleu_penalty)

    # ----- OPEX Current -----
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
            html.Th("Sailing", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Working", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Idle / Moored", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Shore Power", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Average", style={"backgroundColor": "#0A4B8C", "color": "white"})
        ]),
        html.Tr([
            html.Th("", colSpan=2),
            html.Th(f"{sailing_days} days / year"),
            html.Th(f"{working_days} days / year"),
            html.Th(f"{idle_days} days / year"),
            html.Th(f"{shore_days} days / year"),
            html.Th("per day")
        ])
    ])

    # ----- Build Table Body -----
    table_body = html.Tbody([

        # Block 1: Power & Energy
        html.Tr([
            html.Td("Max. power"),
            html.Td("kW"),
            html.Td(format_number(sailing_power)),
            html.Td(format_number(working_power)),
            html.Td(format_number(idle_power)),
            html.Td("-"),
            html.Td(format_number(max_power))
        ]),
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
            html.Td("Engine hours"),
            html.Td("hrs"),
            html.Td(format_number(sailing_hrs)),
            html.Td(format_number(working_hrs)),
            html.Td(format_number(idle_hrs)),
            html.Td("-"),
            html.Td(format_number(avg_hrs))
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
            html.Td(f"{get_currency_symbol(currency)}"),
            html.Td(format_currency_value(sailing_fuel_price, currency, conv_factor)),
            html.Td(format_currency_value(working_fuel_price, currency, conv_factor)),
            html.Td(format_currency_value(idle_fuel_price, currency, conv_factor)),
            html.Td("-"),
            html.Td(format_currency_value(avg_fuel_price, currency, conv_factor))
        ]),
        html.Tr([
            html.Td("Financing"),
            html.Td(f"{get_currency_symbol(currency)}"),
            html.Td(format_number(financing)),
            html.Td(format_number(financing)),
            html.Td(format_number(financing)),
            html.Td("-"),
            html.Td(format_number(financing))
        ]),
        html.Tr([
            html.Td("Maintenance"),
            html.Td(f"{get_currency_symbol(currency)}"),
            html.Td(format_currency_value(maintenance_sailing, currency, conv_factor)),
            html.Td(format_currency_value(maintenance_working, currency, conv_factor)),
            html.Td(format_currency_value(maintenance_idle, currency, conv_factor)),
            html.Td("-"),
            html.Td(format_currency_value(maintenance_avg, currency, conv_factor))
        ]),
        html.Tr([
            html.Td("Spares / consumables"),
            html.Td(f"{get_currency_symbol(currency)}"),
            html.Td(format_currency_value(spares_sailing, currency, conv_factor)),
            html.Td(format_currency_value(spares_working, currency, conv_factor)),
            html.Td(format_currency_value(spares_idle, currency, conv_factor)),
            html.Td("-"),
            html.Td(format_currency_value(spares_avg, currency, conv_factor))
        ]),
        html.Tr([
            html.Td("EU ETS"),
            html.Td(f"{get_currency_symbol(currency)}"),
            html.Td(format_number(euets)),
            html.Td(format_number(euets)),
            html.Td(format_number(euets)),
            html.Td("-"),
            html.Td(format_number(euets))
        ]),
        html.Tr([
            html.Td("FuelEU"),
            html.Td(f"{get_currency_symbol(currency)}"),
            html.Td(format_currency_value(fueleu_sailing, currency, conv_factor)),
            html.Td(format_currency_value(fueleu_working, currency, conv_factor)),
            html.Td(format_currency_value(fueleu_idle, currency, conv_factor)),
            html.Td(""),
            html.Td(format_currency_value(fueleu_avg, currency, conv_factor))
        ]),

        # Block 4: OPEX Current (2 rows)
        html.Tr([
            html.Td("OPEX Current", rowSpan=2),
            html.Td(f"{get_currency_symbol(currency)} per day"),
            html.Td(format_currency_value(sailing_opex_day, currency, conv_factor)),
            html.Td(format_currency_value(working_opex_day, currency, conv_factor)),
            html.Td(format_currency_value(idle_opex_day, currency, conv_factor)),
            html.Td("-"),
            html.Td(format_currency_value(avg_opex_day, currency, conv_factor))
        ]),
        html.Tr([
            html.Td(f"{get_currency_symbol(currency)} per year"),
            html.Td(format_currency_value(sailing_opex_year, currency, conv_factor)),
            html.Td(format_currency_value(working_opex_year, currency, conv_factor)),
            html.Td(format_currency_value(idle_opex_year, currency, conv_factor)),
            html.Td("-"),
            html.Td(format_currency_value(avg_opex_year, currency, conv_factor))
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

def get_future_output_table(api_data, conv_factor, currency):
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
    # Use the provided shore power (or 0 if not available)
    shore_power   = power_data.get("shore_power", 0)
    
    # Energy Requirement Data (from power_calc_day)
    energy_data = (future.get("power_calc_day") or [{}])[0]
    sailing_energy = energy_data.get("sailing_energy_req_kwh_day", 460800)
    working_energy = energy_data.get("working_energy_req_kwh_day", 276480)
    idle_energy    = energy_data.get("idle_energy_req_kwh_day", 19150)
    shore_energy   = energy_data.get("shore_energy_req_kwh_day", 0)
    avg_energy     = int((sailing_energy + working_energy + idle_energy + shore_energy) / 4.0)

    # Engine hours (hard-coded per sample)
    sailing_engine_hrs = 24
    working_engine_hrs = 0
    idle_engine_hrs    = 24
    shore_engine_hrs   = 0
    avg_engine_hrs     = 12

    # Average SFC Data
    sfc_data = (future.get("average_sfc") or [{}])[0]
    sailing_sfc = sfc_data.get("sailing_avg_sfc", 191)
    working_sfc = sfc_data.get("working_avg_sfc", 221)
    idle_sfc    = sfc_data.get("idle_avg_sfc", 202)
    # Since no shore SFC is provided, average over three states
    avg_sfc     = int((sailing_sfc + working_sfc + idle_sfc) / 3.0)

    # Fuel consumption in kg
    kg_data = (future.get("fuel_consumption_kg") or [{}])[0]
    sailing_fuel_kg = kg_data.get("sailing_fuel_consumption_kg", 87889)
    working_fuel_kg = kg_data.get("working_fuel_consumption_kg", 61033)
    idle_fuel_kg    = kg_data.get("idle_fuel_consumption_kg", 3859)
    shore_fuel_kg   = kg_data.get("avg_shore_fuel_consumption_day", 0)
    avg_fuel_kg     = int((sailing_fuel_kg + working_fuel_kg + idle_fuel_kg + shore_fuel_kg) / 4.0)

    # Fuel consumption in liters
    fuel_data = (future.get("fuel_consumption_liters") or [{}])[0]
    sailing_fuel_l = fuel_data.get("future_sailing_fuel_consumption_liter", 99761)
    working_fuel_l = fuel_data.get("future_working_fuel_consumption_liter", 69277)
    idle_fuel_l    = fuel_data.get("future_idle_fuel_consumption_liter", 4336)
    shore_fuel_l   = 0  # Not provided in sample; assume 0
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

    # Costs – Maintenance and Spares from costs key
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
            html.Th("Sailing", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Working", style={"backgroundColor": "#0A4B8C", "color": "white"}),
            html.Th("Idle / Moored", style={"backgroundColor": "#0A4B8C", "color": "white"}),
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
            html.Td("Max. power"),
            html.Td("kW"),
            html.Td(format_number(sailing_power)),
            html.Td(format_number(working_power)),
            html.Td(format_number(idle_power)),
            html.Td(format_number(shore_power) if shore_power else "-"),
            html.Td(format_number(max_power))
        ]),
        # Average power (assuming same as operating modes, no overall average provided)
        html.Tr([
            html.Td("Average power"),
            html.Td("kW"),
            html.Td(format_number(sailing_power)),
            html.Td(format_number(working_power)),
            html.Td(format_number(idle_power)),
            html.Td(format_number(shore_power) if shore_power else "-"),
            html.Td("N/A")
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
        # Engine hours
        html.Tr([
            html.Td("Engine hours"),
            html.Td("hrs/day"),
            html.Td(format_number(sailing_engine_hrs)),
            html.Td(format_number(working_engine_hrs)),
            html.Td(format_number(idle_engine_hrs)),
            html.Td(format_number(shore_engine_hrs)),
            html.Td(format_number(avg_engine_hrs))
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
            html.Td("CO2 Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_co2_ttw)),
            html.Td(format_number(working_co2_ttw)),
            html.Td(format_number(idle_co2_ttw)),
            html.Td("0"),
            html.Td(format_number(avg_co2_ttw))
        ]),
        # CO2 Emissions WtW
        html.Tr([
            html.Td("CO2 Emissions WtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_co2_wtw)),
            html.Td(format_number(working_co2_wtw)),
            html.Td(format_number(idle_co2_wtw)),
            html.Td("0"),
            html.Td(format_number(avg_co2_wtw))
        ]),
        # NOx Emissions TtW
        html.Tr([
            html.Td("NOx Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_nox)),
            html.Td(format_number(working_nox)),
            html.Td(format_number(idle_nox)),
            html.Td("0"),
            html.Td(format_number(avg_nox))
        ]),
        # SOx Emissions TtW
        html.Tr([
            html.Td("SOx Emissions TtW"),
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
            html.Td("CH4 Emissions TtW"),
            html.Td("kg"),
            html.Td(format_number(sailing_ch4)),
            html.Td(format_number(working_ch4)),
            html.Td(format_number(idle_ch4)),
            html.Td("0"),
            html.Td(format_number(avg_ch4))
        ]),
        # Cost rows (currency symbol is now only in the row header)
        html.Tr([
            html.Td("Fuel / electricity"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(sailing_fuel_price * conv_factor)),
            html.Td(format_number(working_fuel_price * conv_factor)),
            html.Td(format_number(idle_fuel_price * conv_factor)),
            html.Td(format_number(shore_fuel_price * conv_factor)),
            html.Td(format_number(avg_fuel_price * conv_factor))
        ]),
        html.Tr([
            html.Td("Financing"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0))
        ]),
        html.Tr([
            html.Td("Maintenance"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(maintenance_sailing * conv_factor)),
            html.Td(format_number(maintenance_working * conv_factor)),
            html.Td(format_number(maintenance_idle * conv_factor)),
            html.Td(""),
            html.Td(format_number(maintenance_avg * conv_factor))
        ]),
        html.Tr([
            html.Td("Spares / consumables"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(spares_sailing * conv_factor)),
            html.Td(format_number(spares_working * conv_factor)),
            html.Td(format_number(spares_idle * conv_factor)),
            html.Td(format_number(spares_shore * conv_factor)),
            html.Td(format_number(spares_avg * conv_factor))
        ]),
        html.Tr([
            html.Td("EU ETS"),
            html.Td(get_currency_symbol(currency)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0)),
            html.Td(format_number(0))
        ]),
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
            html.Td(format_number(sailing_opex_day * conv_factor)),
            html.Td(format_number(working_opex_day * conv_factor)),
            html.Td(format_number(idle_opex_day * conv_factor)),
            html.Td(format_number(shore_opex_day * conv_factor)),
            html.Td(format_number(avg_opex_day * conv_factor))
        ]),
        html.Tr([
            html.Td(f"{get_currency_symbol(currency)} per year"),
            html.Td(format_number(sailing_opex_year * conv_factor)),
            html.Td(format_number(working_opex_year * conv_factor)),
            html.Td(format_number(idle_opex_year * conv_factor)),
            html.Td(format_number(shore_opex_year * conv_factor)),
            html.Td(format_number(avg_opex_year * conv_factor))
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


def get_opex_comparison_table(api_data, currency, conv_factor):
    # Extract conventional (current) values from "costs" and "fuel_price"
    conventional = (api_data.get("current_table", {}).get("costs") or [{}])[0]
    conv_fuel_eu = conventional.get("avg_fueleu_day", 0)
    conv_maintenance = conventional.get("avg_engine_maintenance_costs_day", 0)
    conv_spare = conventional.get("avg_spares_consumables_costs_per_engine_hour", 0)
    
    current_fuel_price = (api_data.get("current_table", {}).get("fuel_price") or [{}])[0]
    conv_fuel_price = current_fuel_price.get("avg_fuel_price_day", 0)
    
    # Extract future values from "costs" and "fuel_price"
    future = (api_data.get("future_output_table", {}).get("costs") or [{}])[0]
    fut_fuel_eu = future.get("future_avg_fueleu_day", 0)
    fut_maintenance = future.get("future_avg_engine_maintenance_costs_day", 0)
    fut_spare = future.get("future_avg_spares_consumables_costs_day", 0)
    
    future_fuel_price = (api_data.get("future_output_table", {}).get("fuel_price") or [{}])[0]
    fut_fuel_price = future_fuel_price.get("future_avg_fuel_price_day", 0)
    
    # Build rows (note that a positive savings means conventional is higher)
    rows = [
        {"metric": "Fuel / electricity", "conv": conv_fuel_eu, "fut": fut_fuel_eu},
        {"metric": "Fuel Price", "conv": conv_fuel_price, "fut": fut_fuel_price},
        {"metric": "Maintenance", "conv": conv_maintenance, "fut": fut_maintenance},
        {"metric": "Spares / consumables", "conv": conv_spare, "fut": fut_spare},
    ]
    total_conv = sum(row["conv"] for row in rows)
    total_fut = sum(row["fut"] for row in rows)
    rows.append({"metric": "OPEX Total", "conv": total_conv, "fut": total_fut})
    
    table_rows = []
    for row in rows:
        conv_val = row["conv"]
        fut_val = row["fut"]
        savings = conv_val - fut_val
        # Use (1 - fut/conv)*100 so that if future is 0 (saving 100%), percentage becomes 100%
        perc = (1 - fut_val/conv_val) * 100 if conv_val != 0 else None
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
    current = api_data.get("current_table", {})
    future = api_data.get("future_output_table", {})
    
    # Use the appropriate keys and defaults from the sample response.
    rows = [
        {"metric": "CO₂ Emissions TtW", 
         "conv": (current.get("co2_emission_ttw") or [{}])[0].get("avg_co2_ttw_day", 330590),
         "fut": (future.get("co2_emission_ttw") or [{}])[0].get("future_avg_co2_ttw_day", 231413)},
        {"metric": "CO₂ Emissions WtW", 
         "conv": (current.get("co2_emission_wtw") or [{}])[0].get("avg_co2_wtw_day", 393037),
         "fut": (future.get("co2_emission_wtw") or [{}])[0].get("future_avg_co2_wtw_day", 288963)},
        {"metric": "NOₓ Emissions TtW", 
         "conv": (current.get("nox_emission_ttw") or [{}])[0].get("avg_nox_ttw_day", 5574),
         "fut": (future.get("nox_emission_ttw") or [{}])[0].get("future_avg_nox_ttw_day", 4024)},
        {"metric": "SOₓ Emissions TtW", 
         "conv": (current.get("sox_emission_ttw") or [{}])[0].get("avg_sox_ttw_day", 219),
         "fut": (future.get("sox_emission_ttw") or [{}])[0].get("future_avg_sox_ttw_day", 159)},
        {"metric": "PM Emissions TtW", 
         "conv": (current.get("pm_emission_ttw") or [{}])[0].get("avg_pm_ttw_day", 98),
         "fut": (future.get("pm_emission_ttw") or [{}])[0].get("future_avg_pm_ttw_day", 71)},
        {"metric": "CH₄ Emissions TtW", 
         "conv": (current.get("ch4_emission_ttw") or [{}])[0].get("avg_ch4_ttw_day", 6),
         "fut": (future.get("ch4_emission_ttw") or [{}])[0].get("future_avg_ch4_ttw_day", 6)},
    ]
    
    table_rows = []
    for row in rows:
        conv_val = float(row["conv"]) if row["conv"] is not None else 0
        fut_val = float(row["fut"]) if row["fut"] is not None else 0
        savings = conv_val - fut_val
        perc = (1 - fut_val/conv_val) * 100 if conv_val != 0 else None
        table_rows.append(html.Tr([
            html.Td(row["metric"]),
            html.Td(format_number(conv_val)),
            html.Td(format_number(fut_val)),
            html.Td(format_number(savings), className=style_savings(savings)),
            html.Td(safe_format_percentage(perc), className=style_savings(perc))
        ]))
    
    header = html.Thead(html.Tr([
        html.Th("Emissions"),
        html.Th("Conventional (kg/day)"),
        html.Th("After measures (kg/day)"),
        html.Th("Savings (kg/day)"),
        html.Th("Savings (%)")
    ]), style={"backgroundColor": "#0A4B8C", "color": "white"})
    
    table = dbc.Table([header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True)
    return html.Div(table, className="table-responsive")



def set_figure_layout(fig, title, xaxis_title=None, yaxis_title=None):
    """Centralized layout configuration with fixed sizing to avoid compression."""
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(color="#0A4B8C")),
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

def fuel_consumption_figure(api_data=None):
    """Create a visualization for fuel consumption costs from 2025 to 2050."""
    if not api_data or "current_timeseries" not in api_data or "future_timeseries" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    # Sort timeseries data by year
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
    
    set_figure_layout(fig, "Fuel Cost Comparison (2025-2050)", "Year", "Cost (USD)")
    return fig



def spares_figure(api_data=None):
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
    
    set_figure_layout(fig, "Spares & Consumables Cost Comparison (2025-2050)", "Year", "Cost (USD)")
    return fig

def penalty_cost_figure(api_data=None):
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
    
    set_figure_layout(fig, "Penalty Cost Comparison (2025-2050)", "Year", "Penalty Cost (USD)")
    return fig

def maintenance_cost_figure(api_data=None):
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
    
    set_figure_layout(fig, "Maintenance Cost Comparison (2025-2050)", "Year", "Cost (USD)")
    return fig

def totex_figure(api_data=None):
    """Create a visualization for total expenditure (TOTEX) over time."""
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
    
    set_figure_layout(fig, "Yearly TOTEX", "Year", "Amount (USD)")
    return fig

def opex_cost_figure(api_data=None):
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
    
    set_figure_layout(fig, "OPEX Cost Comparison (2025-2050)", "Year", "Cost (USD)")
    return fig

def cashflow_figure(api_data=None):
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
    
    set_figure_layout(fig, "Yearly Cash Flow", "Year", "Cash Flow (USD)")
    return fig

def dwelling_at_berth_pie_figure(api_data):
    """Generate the current dwelling at berth pie chart."""
    if not api_data or "current_table" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    costs = api_data["current_table"].get("costs", [{}])[0]
    labels = ["Engine Maintenance", "Spares", "FuelEU Penalty"]
    values = [
        costs.get("engine_maintenance_costs", 0),
        costs.get("spares_consumables_costs", 0),
        costs.get("fueleu_current_penalty", 0)
    ]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+value"
    ))
    fig.update_layout(title="Current Berth Costs Breakdown", template=TEMPLATE_STYLE, margin=MARGIN_STYLE)
    return fig

def future_dwelling_at_berth_pie_figure(api_data):
    """Generate the future dwelling at berth pie chart."""
    if not api_data or "future_output_table" not in api_data:
        return go.Figure().update_layout(title="No Data Available")
    
    costs = api_data["future_output_table"].get("costs", [{}])[0]
    labels = ["Engine Maintenance", "Spares", "FuelEU Penalty", "Shore Power"]
    values = [
        costs.get("future_avg_engine_maintenance_costs_day", 0),
        costs.get("future_avg_spares_consumables_costs_day", 0),
        costs.get("future_avg_fueleu_day", 0),
        costs.get("shore_power_maintenance_per_day", 0) + costs.get("shore_power_spares_per_day", 0)
    ]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+value"
    ))
    fig.update_layout(title="Future Berth Costs Breakdown", template=TEMPLATE_STYLE, margin=MARGIN_STYLE)
    return fig

def dashboard_layout(api_data, currency):
    """Create dashboard layout with multiple visualizations."""
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader(
                html.H4("Dashboard", className="card-title", style={"color": "white"}),
                style={"backgroundColor": "#0A4B8C"}
            ),
            dbc.CardBody([
                # Top-level financial charts
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=totex_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=12)
                ], className="mb-4"),
                
                # Cashflow and Penalty Cost Charts
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=cashflow_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=penalty_cost_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=12)
                ], className="mb-4"),
                                # Dwelling at Berth (Current vs Future) - Side by Side View
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=dwelling_at_berth_pie_figure(api_data),
                        config={"displayModeBar": False},
                        style={"width": "100%", "height": "600px"}
                    ), md=6),
                    dbc.Col(dcc.Graph(
                        figure=future_dwelling_at_berth_pie_figure(api_data),
                        config={"displayModeBar": False},
                        style={"width": "100%", "height": "600px"}
                    ), md=6)
                ], className="mb-4"),
                # Maintenance & Spares Cost Side by Side
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=maintenance_cost_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=6),
                    dbc.Col(dcc.Graph(
                        figure=spares_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=6)
                ], className="mb-4"),
                # Fuel Consumption & OPEX Costs
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=fuel_consumption_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=6),
                    dbc.Col(dcc.Graph(
                        figure=opex_cost_figure(api_data), 
                        config={"displayModeBar": False}
                    ), md=6)
                ], className="mb-4"),

            ])
        ], className="mb-4")
    ], fluid=True)

def layout():
    return dbc.Container([
        html.H1("Key Output Metrics", className="mb-4", style={"color": "#0A4B8C", "textAlign": "center"}),
        dbc.Row([
            dbc.Col([
                html.Label("Select Currency", className="font-weight-bold"),
                dcc.Dropdown(
                    id="currency-choice",
                    options=[{"label": key, "value": key} for key in config.CURRENCIES.keys()],
                    value=list(config.CURRENCIES.keys())[0],
                    clearable=False,
                    style={"marginBottom": "15px"}
                )
            ], md=6, xs=12),
            dbc.Col([
                html.Label("Select Tables", className="font-weight-bold"),
                dcc.Checklist(
                    id="table-selection-dropdown",
                    options=[
                        {"label": "Current Output", "value": "current"},
                        {"label": "Future Output", "value": "future"},
                        {"label": "OPEX Comparison", "value": "opex"},
                        {"label": "Emissions Comparison", "value": "emissions"}
                    ],
                    value=["opex", "emissions"],
                    labelStyle={"display": "inline-block", "marginRight": "10px"},
                    inputStyle={"marginRight": "5px"}
                )
            ], md=6, xs=12)
        ], className="mb-4"),
        html.Div(id="output-content", style={"padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "8px"})
    ], fluid=True, className="py-4")
