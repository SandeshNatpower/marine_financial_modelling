import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from pages import input_module, output_module, power_profiles, reporting, database

###############################################################################
# APP SETUP
###############################################################################
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="NatPower Marine Financial Modelling"
)

# Layout color and sizing constants
PRIMARY_COLOR = "#0A4B8C"       # Deep navy
SECONDARY_COLOR = "#00B0B9"     # Marine cyan
BACKGROUND_COLOR = "#F5F8FA"    # Light sky
TEXT_COLOR = "#212121"
SIDEBAR_BG = "#2c3e50"          # Dark navy
HIGHLIGHT_COLOR = "#FF6B35"     # Safety orange
SIDEBAR_WIDTH = "350px"

###############################################################################
# SIDEBAR LAYOUT
###############################################################################
def get_sidebar():
    sidebar_style = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": SIDEBAR_WIDTH,
        "padding": "2rem 1rem",
        "backgroundColor": SIDEBAR_BG,
        "overflowX": "hidden",
        "overflowY": "auto",
        "boxShadow": "2px 0px 10px rgba(0,0,0,0.1)",
        "transition": "all 0.3s ease"
    }
    link_style = {
        "textDecoration": "none",
        "color": "#ecf0f1",
        "fontSize": "20px",
        "margin": "0.8rem 0",
        "padding": "0.5rem",
        "borderRadius": "4px",
        "transition": "all 0.3s ease",
        "display": "block"
    }
    nav_links = dbc.Nav(
        [
            dbc.NavLink([html.I(className="fas fa-file-import me-2"), "Input"],
                        href="/input", active="exact", style=link_style),
            dbc.NavLink([html.I(className="fas fa-file-export me-2"), "Output"],
                        href="/output", active="exact", style=link_style),
            dbc.NavLink([html.I(className="fas fa-chart-line me-2"), " Dashboard & Scenarios"],
                        href="/power-profiles", active="exact", style=link_style),
            dbc.NavLink([html.I(className="fas fa-chart-bar me-2"), " Reporting"],
                        href="/reporting", active="exact", style=link_style),
            dbc.NavLink([html.I(className="fas fa-database me-2"), " Reference Data Table"],
                        href="/database", active="exact", style=link_style),
        ],
        vertical=True,
        pills=True
    )
    logo_section = html.Div([
        html.Img(src="/assets/Natpower_Marine.png", style={"width": "200px", "marginBottom": "1rem"})
    ])
    help_button = html.Div(
        html.Button("Need Help?", id="help-button", className="btn btn-outline-light btn-sm w-100",
                    style={"marginTop": "1rem"})
    )
    info_note = html.Div(
        [
            html.I(className="fas fa-info-circle me-2"),
            "Use the menu to navigate modules"
        ],
        style={"marginTop": "2rem", "fontSize": "14px", "color": "#bdc3c7", "display": "flex", "alignItems": "center"}
    )
    return html.Div(
        [logo_section, html.Hr(style={"backgroundColor": "rgba(255,255,255,0.2)", "margin": "1rem 0"}),
         nav_links, html.Hr(style={"backgroundColor": "rgba(255,255,255,0.2)", "margin": "1rem 0"}),
         info_note, help_button],
        style=sidebar_style
    )

###############################################################################
# CONTENT LAYOUT
###############################################################################
def get_content():
    content_style = {
        "marginLeft": SIDEBAR_WIDTH,
        "padding": "2rem",
        "backgroundColor": BACKGROUND_COLOR,
        "minHeight": "100vh",
        "transition": "all 0.3s"
    }
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-header", style={"marginBottom": "1rem"}),
            dbc.Breadcrumb(
                id="breadcrumb",
                items=[{"label": "Home", "href": "/", "external_link": False}],
                style={"backgroundColor": "transparent", "padding": "0", "marginBottom": "1rem"}
            ),
            html.Div(id="page-content", style={
                "backgroundColor": "white",
                "padding": "2rem",
                "borderRadius": "8px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.1)"
            })
        ],
        style=content_style
    )

###############################################################################
# MAIN LAYOUT
###############################################################################
app.layout = html.Div([
    dcc.Store(id="vessel-data-store"),
    dcc.Store(id="future-data-store"),
    dcc.Store(id="api-data-store", storage_type="session"),
    dcc.Store(id="dashboard-scenarios-store", storage_type="session"),  # Store for dashboard scenarios
    dcc.Store(id="financial-data-store", storage_type="session"),
    dcc.Store(id="tab-switch"),
    # Replace the debug store with a Pre element for displaying debug text
    html.Pre(id="debug-dashboard-data", style={"backgroundColor": "#f8f9fa", "padding": "10px", "maxHeight": "200px", "overflowY": "scroll"}),
    html.Link(rel="stylesheet", href="https://use.fontawesome.com/releases/v5.15.4/css/all.css"),
    get_sidebar(),
    get_content(),
    dbc.Modal(
        [
            dbc.ModalHeader("Help & Support"),
            dbc.ModalBody("Here you can find documentation, FAQs, and contact details for support."),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-help", className="ml-auto", n_clicks=0)
            )
        ],
        id="help-modal",
        is_open=False,
        centered=True,
    )
])

###############################################################################
# BREADCRUMB CALLBACK
###############################################################################
@app.callback(
    Output("breadcrumb", "items"),
    Input("url", "pathname")
)
def update_breadcrumb(pathname):
    base_items = [{"label": "Natpower Marine Financial Modelling", "href": "/", "external_link": False}]
    if pathname == "/input":
        return base_items + [{"label": "Input", "href": "/input", "external_link": False}]
    elif pathname == "/output":
        return base_items + [{"label": "Output", "href": "/output", "external_link": False}]
    elif pathname == "/power-profiles":
        return base_items + [{"label": "Dashboard & Scenarios", "href": "/power-profiles", "external_link": False}]
    elif pathname == "/reporting":
        return base_items + [{"label": "Reporting", "href": "/reporting", "external_link": False}]
    elif pathname == "/database":
        return base_items + [{"label": "Database", "href": "/database", "external_link": False}]
    else:
        return base_items

###############################################################################
# PAGE ROUTER CALLBACK
###############################################################################
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/input":
        return input_module.layout()
    elif pathname == "/output":
        return output_module.layout()
    elif pathname == "/power-profiles":
        return power_profiles.layout()
    elif pathname == "/reporting":
        return reporting.layout()
    elif pathname == "/database":
        return database.layout()
    else:
        return input_module.layout()

###############################################################################
# HELP MODAL CALLBACK
###############################################################################
@app.callback(
    Output("help-modal", "is_open"),
    [Input("help-button", "n_clicks"), Input("close-help", "n_clicks")],
    [State("help-modal", "is_open")]
)
def toggle_help_modal(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

###############################################################################
# AUTOMATIC TAB SWITCHING CALLBACK
###############################################################################
@app.callback(
    Output("url", "pathname"),
    Input("tab-switch", "data"),
    prevent_initial_call=True
)
def switch_tab(tab_data):
    if tab_data:
        return "/" + tab_data
    return no_update

###############################################################################
# REGISTER CALLBACKS FROM callbacks.py
###############################################################################
from callbacks import register_callbacks
register_callbacks(app)

###############################################################################
# RUN SERVER
###############################################################################
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050, use_reloader=False)
