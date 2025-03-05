#data/sample_data.py

import pandas as pd

def load_regulations():
    return pd.DataFrame({
        'Regulation': ['EEXI', 'CII', 'EU ETS', 'FuelEU Maritime'],
        'Effective Date': ['2023-01-01', '2024-01-01', '2024-06-01', '2025-01-01'],
        'Target': [30, 20, 40, 50],
        'Metric': ['% Reduction', 'Rating', '€/tonne', '% Renewable']
    })