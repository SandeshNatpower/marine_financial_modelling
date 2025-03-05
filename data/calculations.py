#data/calculations.py

# IMO Emission Factors (g/kWh)
EMISSION_FACTORS = {
    'hfo': {'co2': 3.114, 'nox': 14.4, 'sox': 4.2},
    'lng': {'co2': 2.750, 'nox': 2.0, 'sox': 0.0},
    'mdo': {'co2': 3.206, 'nox': 13.2, 'sox': 2.0},
    'battery': {'co2': 0.0, 'nox': 0.0, 'sox': 0.0}
}

def calculate_baseline_emissions(power, fuel_type, operating_hours, load_factor):
    """Calculate baseline emissions using IMO formulas"""
    if fuel_type not in EMISSION_FACTORS:
        raise ValueError("Invalid fuel type")
    
    # Calculate energy consumption
    energy_kwh = power * operating_hours * load_factor
    
    # Calculate emissions
    emissions = {
        'co2': energy_kwh * EMISSION_FACTORS[fuel_type]['co2'] / 1000,  # tonnes
        'nox': energy_kwh * EMISSION_FACTORS[fuel_type]['nox'] / 1e6,  # tonnes
        'sox': energy_kwh * EMISSION_FACTORS[fuel_type]['sox'] / 1e6   # tonnes
    }
    
    # Calculate CII parameters
    cii = calculate_cii(emissions['co2'], power, operating_hours)
    
    return {
        **emissions,
        'cii_rating': determine_cii_rating(cii),
        'eexi_compliance': check_eexi_compliance(power, fuel_type)
    }

def calculate_cii(co2_emissions, power, hours):
    """Calculate Carbon Intensity Indicator"""
    return co2_emissions / (power * hours / 1000)  # gCO2/tonne-mile

def determine_cii_rating(cii_value):
    """Determine CII rating based on IMO 2023 thresholds"""
    if cii_value < 3.5: return 'A'
    elif 3.5 <= cii_value < 4.5: return 'B'
    elif 4.5 <= cii_value < 5.5: return 'C'
    elif 5.5 <= cii_value < 6.5: return 'D'
    else: return 'E'

def check_eexi_compliance(power, fuel_type):
    """Check EEXI compliance based on vessel type and power"""
    # Simplified compliance check
    ref_lines = {
        'container': 0.081,
        'bulk': 0.094,
        'tanker': 0.119
    }
    return power * ref_lines.get(fuel_type, 0.1) < 1.0