import pandas as pd
import numpy as np
import panel as pn
import panel.widgets as pnw
import plotly.express as px

pn.extension("tabulator")

games = pd.read_csv("Video_Games_Sales_as_at_22_Dec_2016.csv")

PLATFORM_COL = "Platform"
YEAR_COL = "Year_of_Release"
SALES_COL = "Global_Sales"
NAME_COL = "Name"
GENRE_COL = "Genre"

games[YEAR_COL] = pd.to_numeric(games[YEAR_COL], errors="coerce")
games[SALES_COL] = pd.to_numeric(games[SALES_COL], errors="coerce")
games = games.dropna(subset=[PLATFORM_COL, SALES_COL]).copy()

platform_options = sorted(games[PLATFORM_COL].dropna().unique().tolist())

platform_multi = pnw.MultiChoice(
    name="Platforms",
    value=platform_options[:5],
    options=platform_options
)

year_slider = pnw.IntRangeSlider(
    name="Release Year Range",
    start=int(games[YEAR_COL].min(skipna=True)),
    end=int(games[YEAR_COL].max(skipna=True)),
    value=(
        int(games[YEAR_COL].min(skipna=True)),
        int(games[YEAR_COL].max(skipna=True))
    )
)

cap_outliers = pnw.Checkbox(
    name="Cap extreme outliers",
    value=False
)

cap_quantile = pnw.FloatSlider(
    name="Outlier cap quantile",
    start=0.90,
    end=0.99,
    step=0.01,
    value=0.99
)

def filtered_data(platforms, year_range, cap_flag, q):
    temp = games.copy()

    if platforms:
        temp = temp[temp[PLATFORM_COL].isin(platforms)]

    temp = temp[
        (temp[YEAR_COL] >= year_range[0]) &
        (temp[YEAR_COL] <= year_range[1])
    ].copy()

    if cap_flag:
        cap_value = temp[SALES_COL].quantile(q)
        temp["Capped_Sales"] = np.minimum(temp[SALES_COL], cap_value)
        temp["Log_Sales"] = np.log1p(temp["Capped_Sales"])
    else:
        temp["Log_Sales"] = np.log1p(temp[SALES_COL])

    return temp

def dashboard_plot(platforms, year_range, cap_flag, q):
    temp = filtered_data(platforms, year_range, cap_flag, q)

    if temp.empty:
        return pn.pane.Markdown("No data matches the selected filters.")

    plot = px.box(
        temp,
        x=PLATFORM_COL,
        y="Log_Sales",
        points="outliers",
        hover_name=NAME_COL,
        hover_data={
            GENRE_COL: True,
            YEAR_COL: True,
            SALES_COL: ":.2f",
            "Log_Sales": ":.2f",
            PLATFORM_COL: False
        },
        title="Distribution of Global Video Game Sales by Platform (Log Scale)",
        labels={
            "Log_Sales": "log(1 + Global Sales)",
            PLATFORM_COL: "Platform"
        }
    )

    return pn.pane.Plotly(plot, config={"responsive": True})

def dashboard_table(platforms, year_range, cap_flag, q):
    temp = filtered_data(platforms, year_range, cap_flag, q)

    if temp.empty:
        return pd.DataFrame(columns=[NAME_COL, PLATFORM_COL, GENRE_COL, YEAR_COL, "Log_Sales"])

    return temp[[NAME_COL, PLATFORM_COL, GENRE_COL, YEAR_COL, "Log_Sales"]] \
        .sort_values("Log_Sales", ascending=False) \
        .head(15) \
        .reset_index(drop=True)

def summary_stats(platforms, year_range, cap_flag, q):
    temp = filtered_data(platforms, year_range, cap_flag, q)

    if temp.empty:
        return pn.pane.Markdown("### Summary\nNo data available.")

    text = f"""
### Summary
- **Games shown:** {len(temp)}
- **Platforms shown:** {temp[PLATFORM_COL].nunique()}
- **Median sales:** {temp[SALES_COL].median():.2f} M
- **Mean sales:** {temp[SALES_COL].mean():.2f} M
"""
    return pn.pane.Markdown(text)

bound_plot = pn.bind(
    dashboard_plot,
    platforms=platform_multi,
    year_range=year_slider,
    cap_flag=cap_outliers,
    q=cap_quantile
)

bound_table = pn.bind(
    dashboard_table,
    platforms=platform_multi,
    year_range=year_slider,
    cap_flag=cap_outliers,
    q=cap_quantile
)

bound_summary = pn.bind(
    summary_stats,
    platforms=platform_multi,
    year_range=year_slider,
    cap_flag=cap_outliers,
    q=cap_quantile
)

dashboard = pn.Column(
    "# Interactive Plot: Sales Distribution by Platform",
    "Question: How does the distribution of global video game sales differ across platforms?",
    pn.Row(platform_multi, year_slider),
    pn.Row(cap_outliers, cap_quantile),
    pn.Row(
        bound_plot,
        pn.Column(
            bound_summary,
            pn.widgets.Tabulator(
                bound_table,
                show_index=False,
                width=500,
                height=400
            )
        )
    )
)

dashboard.servable()