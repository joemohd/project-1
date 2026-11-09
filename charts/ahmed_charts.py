"""Charts by Ahmed using Affordable Housing Production by Building and SIRTA crash data.

The datasets are integrated at Borough x Year, with construction type retained
for Chart 1. In the current cleaned SIRTA file, 13,310 of 13,751 rows have a
positive recorded injury or fatality count; the other 441 rows have missing
injury/fatality counts, so their injury status is unknown.
"""

from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


HOUSING_PATH = Path(__file__).parents[1] / "Datasets" / "Housing_Cleaned.csv"
TRANSPORT_PATH = Path(__file__).parents[1] / "Datasets" / "Transportation_Cleaned.csv"
CONSTRUCTION_TYPES = ("New Construction", "Preservation")


def _empty_figure(message: str) -> go.Figure:
    """Return a consistent empty state for dynamic Dash filters."""
    figure = go.Figure()
    figure.update_layout(
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
    )
    return figure


def _first_existing_path(paths: Iterable[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    names = ", ".join(str(path) for path in paths)
    raise FileNotFoundError(f"Could not find a cleaned dataset at any of: {names}")


def build_integrated_data(
    housing: pd.DataFrame, transportation: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate both datasets at Borough × Year before merging them.

    Housing year is the project completion year and crash year is the crash
    date year. This avoids a row-level join and restricts the result to years
    present in both datasets.
    """
    required_housing = {
        "borough",
        "project_completion_date",
        "reporting_construction_type",
        "all_counted_units",
    }
    required_transport = {
        "crash_borough",
        "crash_date",
        "collision_id",
        "total_non_severe_injuries",
        "total_severe_injuries",
        "total_fatalities",
    }
    missing_housing = required_housing - set(housing.columns)
    missing_transport = required_transport - set(transportation.columns)
    if missing_housing or missing_transport:
        raise ValueError(
            f"Missing housing columns: {sorted(missing_housing)}; "
            f"missing transportation columns: {sorted(missing_transport)}"
        )

    housing_rows = housing.copy()
    transport_rows = transportation.copy()
    housing_rows["year"] = pd.to_datetime(
        housing_rows["project_completion_date"], errors="coerce"
    ).dt.year
    transport_rows["year"] = pd.to_datetime(
        transport_rows["crash_date"], errors="coerce"
    ).dt.year
    housing_rows["affordable_units"] = pd.to_numeric(
        housing_rows["all_counted_units"], errors="coerce"
    ).fillna(0)
    for column in (
        "total_non_severe_injuries",
        "total_severe_injuries",
        "total_fatalities",
    ):
        transport_rows[column] = pd.to_numeric(
            transport_rows[column], errors="coerce"
        ).fillna(0)
    housing_rows = housing_rows.dropna(
        subset=["borough", "year", "reporting_construction_type"]
    )
    transport_rows = transport_rows.dropna(subset=["crash_borough", "year"])
    housing_rows = housing_rows[
        housing_rows["reporting_construction_type"].isin(CONSTRUCTION_TYPES)
    ]

    # Sum completed units to borough-year-construction-type before integration.
    housing_by_type = (
        housing_rows.groupby(
            ["borough", "year", "reporting_construction_type"], as_index=False
        )["affordable_units"]
        .sum()
        .rename(
            columns={
                "reporting_construction_type": "construction_type",
                "affordable_units": "completed_units",
            }
        )
    )
    housing_total = (
        housing_by_type.groupby(["borough", "year"], as_index=False)[
            "completed_units"
        ]
        .sum()
        .rename(columns={"completed_units": "total_completed_units"})
    )
    # Aggregate transportation records to borough-year before joining them
    # to housing, rather than joining individual crashes to housing records.
    crash_totals = (
        transport_rows.groupby(["crash_borough", "year"], as_index=False)
        .agg(
            crash_count=("collision_id", "count"),
            non_severe_injuries=("total_non_severe_injuries", "sum"),
            severe_injuries=("total_severe_injuries", "sum"),
            fatalities=("total_fatalities", "sum"),
        )
        .rename(columns={"crash_borough": "borough"})
    )

    integrated = housing_by_type.merge(
        housing_total, on=["borough", "year"], how="left"
    ).merge(crash_totals, on=["borough", "year"], how="inner")
    # Divide by all completed units in the borough-year. The rate repeats for
    # both construction types because those points share the same crash data.
    denominator = integrated["total_completed_units"].replace(0, pd.NA)
    integrated["crash_rate_per_1000_units"] = (
        integrated["crash_count"] / denominator * 1000
    )
    return integrated.sort_values(["year", "borough", "construction_type"]).reset_index(
        drop=True
    )


def make_chart_1(df: pd.DataFrame) -> go.Figure:
    """Compare affordable-housing completion volume with borough-year crash rates.

    Research question: "How do crash rates per 1,000 completed affordable
    housing units vary with the volume of completed units, across boroughs,
    years and construction types (new construction vs preservation)?"
    This matters to New Yorkers because it helps planners consider housing
    production alongside transportation safety. A scatter plot fits the
    question because it shows the relationship between unit volume and the
    normalized rate; color distinguishes borough, marker shape distinguishes
    construction type, and marker size shows borough-year completion volume.
    Columns used: borough, year, construction_type, completed_units,
    total_completed_units, and crash_rate_per_1000_units.
    Limitations: the crash rate uses borough-year units and is repeated for
    both construction types, so it is not a type-specific crash rate. Rates
    can be mechanically higher in low-unit borough-years, groups below 100
    construction-type units are omitted, 2026 is partial, and the analysis
    does not control for traffic or population or establish causation.
    """
    required = {
        "borough",
        "year",
        "construction_type",
        "completed_units",
        "total_completed_units",
        "crash_rate_per_1000_units",
    }
    missing = required - set(df.columns)
    if missing:
        return _empty_figure(
            f"Chart 1 cannot be displayed: missing {', '.join(sorted(missing))}."
        )
    chart_data = df.dropna(subset=list(required)).copy()
    chart_data["completed_units"] = pd.to_numeric(
        chart_data["completed_units"], errors="coerce"
    )
    # Omit groups under 100 completed construction-type units to reduce the
    # influence of unstable small totals on the scatter plot.
    chart_data = chart_data[chart_data["completed_units"] >= 100]
    if chart_data.empty:
        return _empty_figure(
            "No borough-year construction groups have at least 100 completed units."
        )

    figure = px.scatter(
        chart_data,
        x="completed_units",
        y="crash_rate_per_1000_units",
        color="borough",
        symbol="construction_type",
        size="total_completed_units",
        hover_name="borough",
        hover_data={
            "year": True,
            "construction_type": True,
            "completed_units": ":,.0f",
            "total_completed_units": ":,.0f",
            "crash_rate_per_1000_units": ":.2f",
        },
        color_discrete_sequence=px.colors.qualitative.Safe,
        size_max=32,
        labels={
            "completed_units": "Completed affordable units (construction type)",
            "crash_rate_per_1000_units": (
                "Crashes per 1,000 completed affordable units (borough-year)"
            ),
            "construction_type": "Construction type",
            "total_completed_units": "Borough-year completed units",
        },
        title="Affordable housing completions and normalized crash rates",
    )
    figure.update_layout(
        template="plotly_white",
        legend_title_text="Borough / construction type",
        hovermode="closest",
        xaxis_type="log",
        annotations=[
            {
                "text": (
                    "Note: the rate is mechanically lower where the same number "
                    "of crashes is divided by more completed units."
                ),
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.08,
                "showarrow": False,
                "align": "left",
            }
        ],
    )
    figure.update_xaxes(
        title_text="Completed affordable units by construction type (log scale)",
        tickvals=[300, 1000, 3000, 10000, 20000],
        ticktext=["300", "1k", "3k", "10k", "20k"],
    )
    return figure


def make_chart_2(df: pd.DataFrame) -> go.Figure:
    """Compare affordable-housing completions with fatalities in crash data.

    Research question: "Do borough-years with more completed affordable
    housing units show higher fatality rates in injury crashes?" This matters
    to New Yorkers because planners can compare housing production with
    transportation safety outcomes across boroughs and years. Two aligned
    heatmaps make fatality rates and completed-unit totals easy to compare for
    the same borough-years. Columns used: borough, year, crash_count,
    fatalities, severe_injuries, non_severe_injuries, and
    total_completed_units.
    Limitations: 441 SIRTA rows have missing injury/fatality counts, so their
    injury status is unknown; borough-year totals are repeated across
    construction types before being collapsed; Staten Island crash counts are
    small; 2026 is partial; the analysis does not control for traffic or
    population and does not establish causation.
    """
    required = {
        "borough",
        "year",
        "crash_count",
        "total_completed_units",
        "non_severe_injuries",
        "severe_injuries",
        "fatalities",
    }
    missing = required - set(df.columns)
    if missing:
        return _empty_figure(
            f"Chart 2 cannot be displayed: missing {', '.join(sorted(missing))}."
        )
    chart_data = df.dropna(subset=list(required)).copy()
    if chart_data.empty:
        return _empty_figure("No overlapping borough-year data matches the filters.")
    chart_data["year"] = pd.to_numeric(chart_data["year"], errors="coerce").astype(int)

    # Construction types share the same borough-year severity exposure, so
    # collapse them before making the heatmap to avoid duplicate cells.
    chart_data = (
        chart_data.groupby(["borough", "year"], as_index=False)
        .agg(
            crash_count=("crash_count", "first"),
            total_completed_units=("total_completed_units", "first"),
            non_severe_injuries=("non_severe_injuries", "first"),
            severe_injuries=("severe_injuries", "first"),
            fatalities=("fatalities", "first"),
        )
        .sort_values(["borough", "year"])
    )
    if chart_data.empty:
        return _empty_figure("No borough-year severity data matches the filters.")
    # Calculate fatalities per 100 recorded crash rows at borough-year level.
    chart_data["fatality_rate_per_100_crashes"] = (
        chart_data["fatalities"] / chart_data["crash_count"] * 100
    )

    pivot = chart_data.pivot(
        index="borough", columns="year", values="fatality_rate_per_100_crashes"
    )
    years = [int(year) for year in pivot.columns]
    boroughs = pivot.index.tolist()
    text_values = pivot.apply(
        lambda column: column.map(
            lambda value: f"{value:.1f}" if pd.notna(value) else ""
        )
    )
    actual_min = float(pivot.min().min())
    actual_max = float(pivot.max().max())
    housing_pivot = (
        chart_data.pivot(
            index="borough", columns="year", values="total_completed_units"
        )
        .reindex(index=pivot.index, columns=pivot.columns)
        .fillna(0)
    )
    housing_text = housing_pivot.apply(
        lambda column: column.map(lambda value: f"{value:,.0f}")
    )
    hover_text = chart_data.assign(
        hover=chart_data.apply(
            lambda row: (
                f"Borough: {row['borough']}<br>Year: {int(row['year'])}"
                f"<br>Crash count: {row['crash_count']:,.0f}"
                f"<br>Non-severe injuries: {row['non_severe_injuries']:,.0f}"
                f"<br>Severe injuries: {row['severe_injuries']:,.0f}"
                f"<br>Fatalities: {row['fatalities']:,.0f}"
                f"<br>Completed units: {row['total_completed_units']:,.0f}"
                f"<br>Fatalities per 100 crashes: "
                f"{row['fatality_rate_per_100_crashes']:.1f}"
            ),
            axis=1,
        )
    ).pivot(index="borough", columns="year", values="hover")
    hover_values = hover_text.reindex(
        index=pivot.index, columns=pivot.columns
    ).values
    figure = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        shared_xaxes=True,
        subplot_titles=(
            "Fatalities per 100 injury/fatal crashes",
            "Completed affordable housing units",
        ),
        horizontal_spacing=0.12,
    )
    figure.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=years,
            y=boroughs,
            text=text_values.values,
            customdata=hover_values,
            texttemplate="%{text}",
            hovertemplate="%{customdata}<extra></extra>",
            colorscale="YlOrRd",
            colorbar={
                "title": "Fatalities per 100 crashes",
                "x": 0.46,
                "thickness": 12,
                "len": 0.8,
                "y": 0.5,
                "yanchor": "middle",
            },
            zmin=actual_min,
            zmax=actual_max,
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Heatmap(
            z=housing_pivot.values,
            x=years,
            y=boroughs,
            text=housing_text.values,
            customdata=hover_values,
            texttemplate="%{text}",
            hovertemplate="%{customdata}<extra></extra>",
            colorscale="Blues",
            colorbar={
                "title": "Completed affordable units",
                "x": 1.02,
                "thickness": 12,
                "len": 0.8,
                "y": 0.5,
                "yanchor": "middle",
            },
        ),
        row=1,
        col=2,
    )
    figure.update_layout(
        template="plotly_white",
        title=(
            "Do boroughs with more completed affordable housing see deadlier "
            "injury crashes?"
            # The latest year in this source snapshot may not cover a full year.
            "<br><sup>2026 is a partial year</sup>"
        ),
        xaxis_title="Year",
        xaxis2_title="Year",
        yaxis_title="Borough",
        margin={"l": 95, "r": 155, "t": 125, "b": 75},
    )
    return figure


def load_integrated_data() -> pd.DataFrame:
    """Load the cleaned files and create the integrated chart input."""
    housing_path = _first_existing_path(
        [HOUSING_PATH, HOUSING_PATH.with_name("housing_cleaned.csv")]
    )
    transport_path = _first_existing_path(
        [
            TRANSPORT_PATH,
            TRANSPORT_PATH.with_name("Transport_cleaned.csv"),
            TRANSPORT_PATH.with_name("transportation_cleaned.csv"),
        ]
    )
    return build_integrated_data(
        pd.read_csv(housing_path), pd.read_csv(transport_path)
    )


if __name__ == "__main__":
    integrated_data = load_integrated_data()
    make_chart_1(integrated_data).show()
    make_chart_2(integrated_data).show()
