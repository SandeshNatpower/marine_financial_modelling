import pandas as pd

def load_regulations():
    data = [
        {
            "Regulation": "EEXI",
            "Effective Date": pd.to_datetime("2023-01-01"),
            "Target": 30,
            "Metric": "% Reduction",
            "Description": "Energy Efficiency Existing Ship Index aimed at reducing fuel consumption and greenhouse gas emissions.",
            "Region": "International",
            "Status": "Implemented"
        },
        {
            "Regulation": "CII",
            "Effective Date": pd.to_datetime("2024-01-01"),
            "Target": 20,
            "Metric": "Rating",
            "Description": "Carbon Intensity Indicator used to assess and rate vessel efficiency on a yearly basis.",
            "Region": "International",
            "Status": "Phased Implementation"
        },
        {
            "Regulation": "EU ETS",
            "Effective Date": pd.to_datetime("2024-06-01"),
            "Target": 40,
            "Metric": "€/tonne",
            "Description": "European Union Emissions Trading System designed to incentivize emission reductions through a cap-and-trade system.",
            "Region": "Europe",
            "Status": "Operational"
        },
        {
            "Regulation": "FuelEU Maritime",
            "Effective Date": pd.to_datetime("2025-01-01"),
            "Target": 50,
            "Metric": "% Renewable",
            "Description": "Regulation to increase the share of renewable energy in maritime fuels, supporting the EU's sustainability goals.",
            "Region": "Europe",
            "Status": "Proposed"
        }
    ]
    return pd.DataFrame(data)
