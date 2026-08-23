import dash
from dash import html, Input, Output, State, callback, ALL, ctx
import dash_mantine_components as dmc
import dash_ag_grid as dag

from fetch_data import fetch_data


app = dash.Dash()


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
                    dmc.Textarea(
                        id="airport-input",
                        label="Airport or State Code(s)",
                        placeholder="e.g., wa avq KTUS",

                        style={"flex": 1},
                        autosize=True,
                        persistence=True,
                    ),
                    dmc.Button("Fetch WX Data", id="fetch-button", mt=25, size="sm"),
                    dmc.Button("Favorites", id="btn-modal-favorites", size="sm", mt=25),
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
            dmc.Box(
                [
                    html.Div(id="status-message", style={"marginBottom": "10px"}),
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
                            {"field": "name", "headerName": "Name", "width": 200},
                            {
                                "field": "rawOb",
                                "headerName": "METAR & TAF",
                                "width": 600,
                                "autoHeight": True,
                                "cellStyle": {
                                    "whiteSpace": "pre",
                                    "lineHeight": "1.5",
                                    "paddingTop": 10,
                                },
                            },
                            {"field": "wdir", "headerName": "Dir", "width": 80},
                            {"field": "wspd", "headerName": "Speed", "width": 95},
                            {"field": "wgst", "headerName": "Gusts", "width": 95},
                            {"field": "visib", "headerName": "Vis", "width": 80},
                            {"field": "clouds", "headerName": "clouds", "width": 200},
                        ],
                        defaultColDef={"filter": True},
                        rowData=[],
                        style={"height": 800},
                    ),
                ],
            ),
        ],
        fluid=True,
    ),
)


@callback(
    Output("weather-grid", "rowData"),
    Output("status-message", "children"),
    Input("fetch-button", "n_clicks"),
    State("airport-input", "value"),
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
    Output("airport-input", "value"),
    Input({"type": "favorite-fetch", "index": ALL}, "n_clicks"),
    State({"type": "favorite-codes", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def fetch_from_favorites(n, values):
    if ctx.triggered_id:
        index = ctx.triggered_id["index"]
        print(index)
        print(values)
        if values:
            return values[index]
    return dash.no_update


if __name__ == "__main__":
    app.run(debug=True, port=8050)
