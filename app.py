import dash
from dash import html, dcc, Input, Output, State, callback, ALL, ctx
import dash_mantine_components as dmc
import dash_ag_grid as dag

from fetch_data import fetch_data, us_stations_data

app = dash.Dash()
app.title = "Jim's Aviation Weather Data"

def make_favorite(n):
    return dmc.Group(
        [
            dmc.TextInput(
                id={"type": "favorite-name", "index": n},
                w=100,
                persistence=True,
                label="Name",
            ),
            dmc.Textarea(
                id={"type": "favorite-codes", "index": n},
                label="Airport or State Code(s)",
                placeholder="e.g., wa avq KTUS",
                style={"flex": 1},
                persistence=True,
                autosize=True,
            ),
            dmc.Button("Select", id={"type": "favorite-fetch", "index": n}, mt=25),
        ],
        align="flex-start",
        mb=20,
    )

def make_seach():
    return dmc.Box([
        dmc.Select(
            id="search-value",
            searchable=True,
            data=[{"value": s["icaoId"], "label": f"{s['icaoId']} {s['state']} {s['site']}"} for s in us_stations_data],
        ),
        dmc.Box(id="search-results")
    ])


app.layout = dmc.MantineProvider(
    forceColorScheme="light",
    children=dmc.Container(
        [
            dmc.BackgroundImage(
                [
                    dmc.Title("Jim's Aviation Weather Data", order=1, mb=20),
                    dmc.Text("Your go-to METAR and TAF checker", mt="md"),
                ],
                src="/assets/dot.jpg",
                h=150,
                p="lg",
                c="white",
                mb="lg",
            ),
            dmc.Group(
                [
                    dmc.TextInput(
                        id="airport-input",
                        label="Airport or State Code(s)",
                        placeholder="e.g., wa avq KTUS",
                        debounce=True,
                        style={"flex": 1},
                     #   autosize=True,
                        persistence=True,
                    ),
                    dmc.Button("Favorites", id="btn-modal-favorites", size="sm", mt=25),
                    dmc.Button("Search", id="btn-search", size="sm", mt=25),
                ],
                align="flex-start",
                mb=20,
            ),

            dmc.Modal(
                title="Favorite Groups",
                id="modal-favorites",
                children=[make_favorite(i) for i in range(6)],
                size="75%",
            ),
            dmc.Modal(
                title="Search",
                id="modal-search",
                children=make_seach(),
                size="75%",
            ),

            dmc.Box(
                [
                    dmc.Group([
                        dmc.Box(id="status-message", flex=1),
                        dmc.NumberInput(
                            label="Auto update time",
                            id="auto-update-time",
                            suffix=" minutes",
                            value=5,
                            min=0.5,
                            w=180,
                            mt=0,
                            persistence=True
                        ),
                    ], mb="md" ),
                    dag.AgGrid(
                        id="weather-grid",
                        columnDefs=[
                            {
                                "field": "state",
                                "headerName": "St",
                                "width": 75,
                            },
                            {
                                "field": "icaoId",
                                "headerName": "Airport",
                                "width": 120,
                                "sort": "asc",
                            },
                            {"field": "fltCat", "headerName": "VFR", "width": 75, "cellRenderer": "ColorCellRenderer"},
                            {"field": "name", "headerName": "Name", "width": 200},
                            {
                                "field": "rawOb",
                                "headerName": "METAR & TAF",
                                "width": 700,
                                "autoHeight": True,
                                "sortable": False,
                                "cellStyle": {
                                    "whiteSpace": "pre",
                                    "lineHeight": "1.5",
                                    "paddingTop": 10,
                                },
                            },
                            {
                                "field": "wdir", "headerName": "Dir", "width": 80,

                            },
                            {
                                "field": "wspd", "headerName": "Speed", "width": 95,
                                "valueFormatter": {"function": " (params.value ? params.value + 'KT' :'')"},
                            },
                            {
                                "field": "wgst", "headerName": "Gusts", "width": 95,
                                "valueFormatter": {"function": " (params.value ? params.value + 'KT' :'')"},
                            },
                            {"field": "visib", "headerName": "Vis", "width": 80},
                            {"field": "clouds", "headerName": "Clouds", "width": 200},
                            {"field": "lat", "headerName": "Lat", "width": 95},
                            {"field": "lon", "headerName": "lon", "width": 95},




                        ],
                        defaultColDef={"filter": True},
                        rowData=[],
                        style={"height": 800},
                        persistence=True,
                        persisted_props=["columnState"],
                    ),
                ],
            ),
            dcc.Interval(id="interval", disabled=True),
        ],
        fluid=True,
    ),
)

@callback(
    Output("interval", "disabled"),
    Output("interval", "n_intervals"),
    Output("interval", "interval"),
    Input("auto-update-time", "value"),
)
def update_autoupdate_time(autoupdate_time):
    if autoupdate_time:
        interval = autoupdate_time * 60 * 1000
        return False, 0, interval
    return dash.no_update, dash.no_update, dash.no_update



@callback(
    Output("weather-grid", "rowData"),
    Output("status-message", "children"),
    Input("interval", "n_intervals"),
    Input("airport-input", "value"),
)
def fetch_weather_data(_, airport_codes):
    if not airport_codes:
        return [], dmc.Alert(
            "Please enter at least one airport code or state", color="yellow"
        )

    return fetch_data(airport_codes)


@callback(
    Output("modal-favorites", "opened"),
    Input("btn-modal-favorites", "n_clicks"),
    Input({"type": "favorite-fetch", "index": ALL}, "n_clicks"),
    State("modal-favorites", "opened"),
    prevent_initial_call=True,
)
def modal_demo(nc1, nc2, opened):
    return not opened

@callback(
    Output("modal-search", "opened"),
    Input("btn-search", "n_clicks"),
    State("modal-search", "opened"),
    prevent_initial_call=True,

)
def modal_search(_, opened):
    return not opened

@callback(
    Output("search-results", "children"),
    Input("search-value", "value"),
    prevent_initial_call=True,
    optional=True
)
def get_search_results(value):
    if value:
        wx_data, msg = fetch_data(value)
        return dmc.Box([dmc.Textarea(wx_data[0].get('rawOb', ""), autosize=True, mb="md"), msg])
    return []

@callback(
    Output("airport-input", "value"),
    Input({"type": "favorite-fetch", "index": ALL}, "n_clicks"),
    State({"type": "favorite-codes", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def fetch_from_favorites(n, values):
    if ctx.triggered_id:
        index = ctx.triggered_id["index"]
        if values:
            return values[index]
    return dash.no_update


if __name__ == "__main__":
    app.run(debug=True, port=8050)
