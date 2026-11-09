"""Interactive NYC affordable housing and transportation safety dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update

ROOT = Path(__file__).resolve().parent


def load_data():
    housing = pd.read_csv(ROOT / "datasets" / "Housing_Cleaned.csv", low_memory=False)
    transport = pd.read_csv(ROOT / "datasets" / "Transportation_Cleaned.csv", low_memory=False)
    housing["year"] = pd.to_datetime(housing["project_completion_date"], errors="coerce").dt.year
    transport["year"] = pd.to_datetime(transport["crash_date"], errors="coerce").dt.year
    housing["units"] = pd.to_numeric(housing["all_counted_units"], errors="coerce").fillna(0)
    for col in ("total_non_severe_injuries", "total_severe_injuries", "total_fatalities"):
        transport[col] = pd.to_numeric(transport[col], errors="coerce").fillna(0)
    h = housing.dropna(subset=["borough", "year", "reporting_construction_type"])
    h = h.groupby(["borough", "year", "reporting_construction_type"], as_index=False).agg(
        units=("units", "sum"), projects=("project_id", "nunique"))
    t = transport.dropna(subset=["crash_borough", "year"]).copy()
    t["borough"] = t["crash_borough"].astype(str).str.upper().str.strip()
    t = t.groupby(["borough", "year"], as_index=False).agg(
        crashes=("collision_id", "nunique"), fatalities=("total_fatalities", "sum"),
        severe_injuries=("total_severe_injuries", "sum"), injuries=("total_non_severe_injuries", "sum"))
    return h.merge(t, on=["borough", "year"], how="inner")


DATA = load_data()
BOROUGHS = sorted(DATA.borough.dropna().astype(str).unique())
YEARS = sorted(DATA.year.dropna().astype(int).unique())
TYPES = sorted(DATA.reporting_construction_type.dropna().astype(str).unique())
app = Dash(__name__, title="NYC | Homes & Safe Streets", update_title="Updating report…")
COLORS = {"ink": "#142c2a", "muted": "#70817c", "green": "#126b55", "lime": "#d8efb1", "paper": "#f5f6f1", "line": "#e4e9e2"}


def dropdown(label, ident, options, value):
    return html.Div([html.Label(label, className="filter-label"), dcc.Dropdown(
        id=ident, options=[{"label": str(x), "value": x} for x in options],
        value=value, multi=True, clearable=True, searchable=True, className="filter-select")], className="filter-item")


app.layout = html.Div(
    [
        html.Header(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("NYC / FIELD NOTES", className="eyebrow"),
                                html.H1("Homes & safe streets", className="brand-title"),
                            ]
                        ),
                        html.Div(
                            [
                                html.Span("DATA STORY", className="header-tag"),
                                html.Span("01 / 04", className="header-index"),
                            ],
                            className="header-right",
                        ),
                    ],
                    className="topbar wrap",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("THE QUESTION", className="eyebrow"),
                                html.H2("As affordable homes take shape, what does street safety look like across the five boroughs?"),
                                html.P("An interactive look at completed affordable housing and reported crash outcomes, borough by borough.", className="hero-deck"),
                            ],
                            className="hero-copy",
                        ),
                        html.Div(
                            [
                                html.Span("A SHARED CITY, TWO SIGNALS", className="eyebrow"),
                                html.Div(
                                    [
                                        html.Div([html.B("5"), html.Span("boroughs")], className="hero-stat"),
                                        html.Div([html.B("2"), html.Span("city systems")], className="hero-stat"),
                                        html.Div([html.B("01"), html.Span("exploration")], className="hero-stat"),
                                    ],
                                    className="hero-stats",
                                ),
                            ],
                            className="hero-note",
                        ),
                    ],
                    className="hero wrap",
                ),
            ]
        ),
        html.Main(
            [
                html.Section(
                    [
                        html.Div(
                            [
                                html.Div([html.Span("REPORT BUILDER", className="eyebrow"), html.H2("Find your view", className="section-title")]),
                                html.Button([html.Span("Generate report"), html.Span("↗", className="button-icon")], id="generate", n_clicks=0, className="generate-button"),
                            ],
                            className="section-heading",
                        ),
                        html.Div(
                            [
                                dropdown("Borough", "borough", BOROUGHS, BOROUGHS),
                                dropdown("Year", "year", YEARS, YEARS),
                                dropdown("Housing · delivery type", "construction", TYPES, TYPES),
                                dropdown("Transport · outcome", "outcome", ["Crashes", "Fatalities", "Severe injuries", "Non-severe injuries"], ["Crashes"]),
                            ],
                            className="filter-grid",
                        ),
                        html.Div(
                            [
                                html.Label("SEARCH THE STORY", htmlFor="search", className="filter-label"),
                                dcc.Input(id="search", type="search", placeholder="Try ‘Brooklyn 2022 New Construction’", className="search-input"),
                                html.Span("Search applies borough, year and housing type when mentioned.", className="search-hint"),
                            ],
                            className="search-row",
                        ),
                        html.Div(id="report-status", className="report-status"),
                    ],
                    className="report-builder content-wrap",
                ),
                html.Section(
                    [
                        html.Div(
                            [
                                html.Div([html.Span("01 — THE LANDSCAPE", className="eyebrow"), html.H2("One city. Different rhythms.", className="section-title")]),
                                html.P("Choose filters above, then generate a report to compare borough-years.", className="section-aside"),
                            ],
                            className="section-heading landscape-heading",
                        ),
                        html.Div(
                            [
                                html.Div([html.Div([html.Span("AFFORDABLE HOMES", className="eyebrow"), html.H3("Completions over time")], className="chart-head"), dcc.Graph(id="housing-chart", config={"responsive": True}, className="chart")], className="chart-card wide"),
                                html.Div([html.Div([html.Span("SAFETY OUTCOMES", className="eyebrow"), html.H3("Reported outcomes over time")], className="chart-head"), dcc.Graph(id="transport-chart", config={"responsive": True}, className="chart")], className="chart-card"),
                            ],
                            className="chart-grid report-content",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div([html.Span("02 — THE CONNECTION", className="eyebrow"), html.H2("A borough-year lens", className="section-title")]),
                                        html.P("Each point combines housing delivery and crash records for the same borough and year. Descriptive, not causal.", className="section-aside"),
                                    ],
                                    className="section-heading",
                                ),
                                html.Div([dcc.Graph(id="relationship-chart", config={"responsive": True}, className="chart")], className="chart-card relationship-card"),
                            ],
                            className="story-section report-content",
                        ),
                    ],
                ),
                html.Section(
                    [
                        html.Div(
                            [
                                html.Div([html.Span("03 — READ WITH CARE", className="eyebrow"), html.H2("What the data can tell us", className="section-title")]),
                                html.P("A starting point for better questions, not a verdict on a neighborhood.", className="section-aside"),
                            ],
                            className="section-heading",
                        ),
                        html.Div(
                            [
                                html.Article([html.Span("01 / SIGNAL", className="eyebrow"), html.H3("Scale changes the picture"), html.P("Crash counts reflect many factors, including traffic exposure. A per-unit ratio can rise simply when the housing denominator is small; it is not a neighborhood safety score.")], className="story-card"),
                                html.Article([html.Span("02 / CAVEAT", className="eyebrow"), html.H3("Coverage has edges"), html.P("2026 is a partial year. Some crash records have missing injury fields; annual counts vary, and these comparisons do not control for traffic, population or street design.")], className="story-card"),
                                html.Article([html.Span("03 / CITY BENEFIT", className="eyebrow"), html.H3("A prompt for joined-up planning"), html.P("Pairing housing and safety signals can help NYC teams spot borough-years to investigate, then bring in exposure, street design and community context before acting.")], className="story-card"),
                            ],
                            className="story-grid",
                        ),
                    ],
                    className="story-section closing-section report-content",
                ),
                html.Footer(
                    [
                        html.Div([html.Span("NYC / FIELD NOTES", className="eyebrow"), html.Span("Housing × Transportation · Borough-year comparison")]),
                        html.Span("Explore with context.", className="footer-note"),
                    ],
                    className="footer content-wrap",
                ),
            ],
            className="page-content",
        ),
    ],
    className="site-shell",
)


def empty(message):
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref="paper", yref="paper", showarrow=False, font={"color": COLORS["muted"], "size": 14})
    fig.update_layout(template="plotly_white", xaxis={"visible": False}, yaxis={"visible": False}, margin={"l": 20, "r": 20, "t": 20, "b": 20}, paper_bgcolor="white")
    return fig


def polish(fig, height=440):
    fig.update_layout(template="plotly_white", height=height, margin={"l": 25, "r": 20, "t": 25, "b": 50}, paper_bgcolor="white", plot_bgcolor="white", font={"family": "Inter, Arial, sans-serif", "color": COLORS["ink"], "size": 11}, legend={"orientation": "h", "y": -.25, "title": None}, hoverlabel={"bgcolor": COLORS["ink"], "font_color": "white"}, xaxis={"showgrid": False, "linecolor": COLORS["line"], "zeroline": False}, yaxis={"gridcolor": "#edf0eb", "zeroline": False})
    return fig


@app.callback(Output("borough", "value"), Output("year", "value"), Output("construction", "value"), Input("search", "value"), State("borough", "value"), State("year", "value"), State("construction", "value"))
def parse_search(query, boroughs, years, types):
    if not query:
        return no_update, no_update, no_update
    text = query.casefold()
    borough = next((b for b in BOROUGHS if b.casefold() in text), None)
    year = next((y for y in YEARS if str(y) in text), None)
    kind = next((t for t in TYPES if t.casefold() in text), None)
    return ([borough] if borough else no_update, [year] if year else no_update, [kind] if kind else no_update)


@app.callback(Output("housing-chart", "figure"), Output("transport-chart", "figure"), Output("relationship-chart", "figure"), Output("report-status", "children"), Input("generate", "n_clicks"), State("borough", "value"), State("year", "value"), State("construction", "value"), State("outcome", "value"))
def generate_report(clicks, boroughs, years, types, outcomes):
    d = DATA.copy()
    if boroughs:
        d = d[d.borough.isin(boroughs)]
    if years:
        d = d[d.year.isin(years)]
    if types:
        d = d[d.reporting_construction_type.isin(types)]
    if outcomes:
        # The outcome filter selects the safety measure drawn in the time chart.
        outcome = outcomes[0]
    else:
        outcome = "Crashes"
    metric = {"Crashes": "crashes", "Fatalities": "fatalities", "Severe injuries": "severe_injuries", "Non-severe injuries": "injuries"}.get(outcome, "crashes")
    if d.empty:
        msg = "No overlapping borough-year records match these filters."
        return empty(msg), empty(msg), empty(msg), msg
    # Keep the housing series at construction-type grain; safety is a borough-year
    # measure, so collapse any selected housing types before drawing it.
    homes = d.groupby(["year", "reporting_construction_type"], as_index=False).units.sum()
    f1 = px.bar(homes, x="year", y="units", color="reporting_construction_type", barmode="group", labels={"year": "Completion year", "units": "Affordable units", "reporting_construction_type": "Delivery type"}, color_discrete_sequence=["#126b55", "#c4d99a", "#75a79b"])
    borough_year = d.groupby(["borough", "year"], as_index=False).agg(
        units=("units", "sum"), crashes=("crashes", "first"),
        fatalities=("fatalities", "first"), severe_injuries=("severe_injuries", "first"),
        injuries=("injuries", "first"))
    safety = borough_year.groupby(["year", "borough"], as_index=False).agg(value=(metric, "first"))
    f2 = px.line(safety, x="year", y="value", color="borough", markers=True, labels={"year": "Crash year", "value": outcome}, color_discrete_sequence=px.colors.qualitative.Safe)
    points = borough_year
    rel = px.scatter(points, x="units", y=metric, color="borough", size="crashes", hover_name="borough", hover_data={"year": True, "units": ":,.0f", "crashes": ":,.0f", "fatalities": ":,.0f", "severe_injuries": ":,.0f", "injuries": ":,.0f"}, labels={"units": "Completed affordable units", metric: outcome, "crashes": "Crash count"}, color_discrete_sequence=px.colors.qualitative.Safe)
    polish(f1, 440); polish(f2, 440); polish(rel, 510)
    return f1, f2, rel, f"{borough_year.borough.nunique()} boroughs · {borough_year.year.nunique()} years · {int(borough_year.units.sum()):,} completed affordable units · {int(borough_year.crashes.sum()):,} recorded crashes"


if __name__ == "__main__":
    app.run(debug=True)
