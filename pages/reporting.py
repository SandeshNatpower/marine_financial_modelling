# pages/reporting.py

import io
import config
import smtplib
import tempfile
from email.message import EmailMessage

from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dcc import send_bytes

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.units import inch

import plotly.graph_objects as go
import pandas as pd

PRIMARY_COLOR   = "#0A4B8C"
SECONDARY_COLOR = "#6c757d"
TEXT_COLOR      = "#212121"

# -----------------------------------------------------------------------------
# Styles (using built-in PDF fonts)
# -----------------------------------------------------------------------------
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='Header',
    fontName='Helvetica-Bold',
    fontSize=14,
    textColor=PRIMARY_COLOR,
    spaceAfter=12
))
styles.add(ParagraphStyle(
    name='Body',
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=TEXT_COLOR
))
styles.add(ParagraphStyle(
    name='Footer',
    fontName='Helvetica',
    fontSize=8,
    textColor=SECONDARY_COLOR
))

# -----------------------------------------------------------------------------
# PDF Generation
# -----------------------------------------------------------------------------
def build_pdf(report_scope, start_date, end_date, scenarios, currency,
              vessel_data, dashboard_data):
    """PDF generation using actual data from callback stores"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Decarbonization Report")

    # Header with vessel info from vessel-data-store
    def header(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawString(1*inch, doc.height + 1.2*inch, "Marine Decarbonization Report")
        canvas.setFont('Helvetica', 10)
        canvas.drawString(1*inch, doc.height + 1*inch, 
                         f"Vessel: {vessel_data.get('vessel_name', 'N/A')} | IMO: {vessel_data.get('imo', 'N/A')}")
        canvas.restoreState()

    elements = []

    # 1. Vessel Technical Specifications from vessel-data-store
    elements.append(Paragraph("1. Vessel Specifications", styles['Header']))
    tech_specs = [
        ["Gross Tonnage", vessel_data.get('gross_tonnage', 'N/A')],
        ["DWT", vessel_data.get('dwt', 'N/A')],
        ["Main Engine Power", f"{vessel_data.get('total_engine_power', 'N/A')} kW"],
        ["Auxiliary Power", f"{vessel_data.get('average_hoteling_kw', 'N/A')} kW"],
        ["Fuel Types", f"Main: {vessel_data.get('main_fuel_type', 'N/A')}, Aux: {vessel_data.get('aux_fuel_type', 'N/A')}"]
    ]
    elements.append(Table(tech_specs, style=[
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
    ]))
    elements.append(Spacer(1, 0.5*inch))

    # 2. Operational Profile from vessel-data-store
    elements.append(Paragraph("2. Operational Profile", styles['Header']))
    op_profile = [
        ["Sailing Days", vessel_data.get('sailing_days', 'N/A')],
        ["Working Days", vessel_data.get('working_days', 'N/A')],
        ["Idle Days", vessel_data.get('idle_days', 'N/A')],
        ["Shore Days", vessel_data.get('shore_days', 'N/A')],
        ["Engine Load Factors", f"Sailing: {vessel_data.get('sailing_engine_load', 'N/A')}%"]
    ]
    elements.append(Table(op_profile, style=[
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
    ]))
    elements.append(Spacer(1, 0.5*inch))

    # 3. Financial Analysis from dashboard-scenarios-store
    if dashboard_data and scenarios:
        elements.append(Paragraph("3. Scenario Analysis", styles['Header']))
        
        # Filter selected scenarios
        selected_data = {k: v for k, v in dashboard_data.items() if k in scenarios}
        
        # Proceed with selected_data instead of full dashboard_data
        scenario_dfs = {}
        for scenario, data in selected_data.items():
            df = pd.DataFrame(data)
            scenario_dfs[scenario] = df

        # Create comparison table
        comparison_data = [["Scenario", "Avg OPEX", "Total Emissions", "CII Rating"]]
        for scenario, df in scenario_dfs.items():
            avg_opex = df['opex'].mean()
            total_emissions = df['total_emissions'].sum()
            cii_rating = df['cii_rating'].mode()[0] if not df.empty else 'N/A'
            
            comparison_data.append([
                scenario,
                f"€{avg_opex:,.0f}",
                f"{total_emissions:,.0f} tCO₂",
                cii_rating
            ])

        elements.append(Table(comparison_data, style=[
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ]))
        elements.append(Spacer(1, 0.5*inch))

        # Add charts using scenario data
        img_tmp = tempfile.NamedTemporaryFile(delete=True, suffix=".png")
        
        # OPEX Trend Chart
        fig = go.Figure()
        for scenario, df in scenario_dfs.items():
            fig.add_trace(go.Scatter(
                x=df['year'],
                y=df['opex'],
                mode='lines+markers',
                name=scenario
            ))
        fig.update_layout(title='OPEX Trend Comparison', xaxis_title='Year', yaxis_title='OPEX (€)')
        fig.write_image(img_tmp.name)
        elements.append(Image(img_tmp.name, width=6*inch, height=3*inch))
        elements.append(Spacer(1, 0.5*inch))

    # Build the PDF
    doc.build(elements, onFirstPage=header)
    buf.seek(0)
    return buf.getvalue()



def calculate_kpis(dashboard_data, conversion_rate, currency_symbol):
    rows = [["Scenario", "Avg OPEX", "Total Emissions", "CII Rating"]]
    for scenario, data in dashboard_data.items():
        df = pd.DataFrame(data)
        avg_opex = df['opex'].mean() * conversion_rate
        total_em = df.get('total_emissions', pd.Series([0])).sum()
        cii     = df.get('cii_rating', pd.Series(["N/A"])).mode().iloc[0]
        rows.append([
            scenario,
            f"{currency_symbol}{avg_opex:,.0f}",
            f"{total_em:,.0f} tCO₂e",
            str(cii)
        ])
    return rows


def generate_opex_chart(dashboard_data, rate, symbol):
    fig = go.Figure()
    for scen, data in dashboard_data.items():
        df = pd.DataFrame(data)
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df['opex'] * rate,
            mode='lines+markers',
            name=scen
        ))
    fig.update_layout(
        title=f"OPEX Trend ({symbol})",
        xaxis_title="Year",
        yaxis_title="OPEX",
        template="plotly_white",
        height=350
    )
    return fig


def generate_cost_breakdown_chart(dashboard_data, rate, symbol):
    fig = go.Figure()
    comps = ['fuel_price', 'maintenance', 'eu_ets', 'penalty']
    for scen, data in dashboard_data.items():
        df = pd.DataFrame(data)
        last = df[df['year']==df['year'].max()].iloc[0]
        vals = [last[c]*rate for c in comps]
        fig.add_trace(go.Bar(
            x=[scen],
            y=vals,
            name=scen,
            text=[f"{symbol}{v:,.0f}" for v in vals],
            textposition="auto"
        ))
    fig.update_layout(
        title=f"Latest Cost Breakdown ({symbol})",
        barmode="group",
        xaxis_title="Scenario",
        yaxis_title="Cost",
        template="plotly_white",
        height=350
    )
    return fig


def create_scenario_table(dashboard_data, rate, symbol):
    header = ["Scenario", "CAPEX", "OPEX (sum)", "Emissions", "CII", "ROI"]
    data = [header]
    for scen, dat in dashboard_data.items():
        df = pd.DataFrame(dat)
        capex = df.get('capex', pd.Series([0])).iloc[0] * rate
        opex  = df['opex'].sum() * rate
        em    = df.get('total_emissions', pd.Series([0])).sum()
        cii   = df.get('cii_rating', pd.Series(["N/A"])).mode().iloc[0]
        roi   = (df.get('savings', pd.Series([0])).sum() / capex * 100) if capex else 0
        data.append([
            scen,
            f"{symbol}{capex:,.0f}",
            f"{symbol}{opex:,.0f}",
            f"{em:,.0f} tCO₂e",
            str(cii),
            f"{roi:.1f}%"
        ])
    tbl = Table(data, colWidths=[1.2*inch]*len(header))
    tbl.setStyle(TableStyle([
        ('FONTNAME',   (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0),   PRIMARY_COLOR),
        ('TEXTCOLOR',  (0,0), (-1,0),   colors.white),
        ('GRID',       (0,0), (-1,-1), 0.25, colors.grey),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
    ]))
    return tbl

from datetime import datetime

SCENARIOS = [
    {'label': 'Scenario A', 'value': 'A'},
    {'label': 'Scenario B', 'value': 'B'},
    {'label': 'Scenario C', 'value': 'C'}
]
def layout():
    """Updated reporting interface matching callback data"""
    return dbc.Container([
    dcc.Store(id='report-config-store'),
    dcc.Download(id='download-report'),

    html.H2("Generate Compliance Report", className="mb-4 text-primary"),

    dbc.Card([
        dbc.CardHeader("Report Configuration", className="bg-primary text-white"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Report Scope"),
                    dcc.Dropdown(
                        id='report-scope',
                        options=[
                            {'label': 'Technical Summary', 'value': 'technical'},
                            {'label': 'Financial Analysis', 'value': 'financial'},
                            {'label': 'Full Compliance Report', 'value': 'full'}
                        ],
                        value='technical'
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Scenario Selection"),
                    dcc.Dropdown(
                        id='report-scenarios',
                        options=SCENARIOS,
                        multi=True,
                        placeholder="Select scenarios..."
                    )
                ], md=8)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Report Dates"),
                    dcc.DatePickerRange(
                        id='report-dates',
                        start_date=datetime.now().date(),
                        end_date=datetime.now().date(),
                        display_format='YYYY-MM-DD'
                    )
                ], md=4),
                dbc.Col([
                    dbc.Label("Currency"),
                    dcc.Dropdown(
                        id='report-currency',
                        options=[
                            {'label': 'Euro (€)', 'value': 'EUR'},
                            {'label': 'US Dollar ($)', 'value': 'USD'},
                            {'label': 'British Pound (£)', 'value': 'GBP'}
                        ],
                        value='EUR'
                    )
                ], md=4),
                dbc.Col([
                    dbc.Button("Generate Report", id='generate-report-btn', color="primary", className="w-100")
                ], md=2),
                dbc.Col([
                    dbc.Button("Download PDF", id='download-report-btn', color="success", className="w-100")
                ], md=2)
            ], className="mb-3")
        ])
    ], className="mb-4"),

    dbc.Card([
        dbc.CardHeader("Report Preview"),
        dbc.CardBody(
            html.Div(id='report-preview', className="report-preview")
        )
    ])
], fluid=True)