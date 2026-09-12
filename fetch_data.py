import dash_mantine_components as dmc
import requests
from datetime import datetime, timezone
import re, json, gzip
from collections import defaultdict

# create a list of airports by state when app starts
def get_state_airports():
    headers = {"User-Agent": "DashWeatherApp/2.0"}
    response = requests.get(
    "https://aviationweather.gov/data/cache/stations.cache.json.gz",
        headers=headers,
        timeout=30,
    )

    stations = json.loads(
        gzip.decompress(response.content)
    )

    stations = [station for station in stations if station.get("country") == "US" and station.get("icaoId") and station.get("siteType") != []]

    stations_icaoId = [s["icaoId"] for s in stations]

    st_airports = defaultdict(list)

    for station in stations:
        state = station.get("state")
        icao = station.get("icaoId")

        if state and icao:
            st_airports[state].append(icao)

    return  dict(st_airports), stations, stations_icaoId

state_airports, us_stations_data, stations_id = get_state_airports()



def validate_stations(codes):
    invalid_codes = [c for c in codes if c not in stations_id ]
    return  invalid_codes


def process_data(data):

    # Process the fetched weather data
    processed_data = []

    for item in data:
        # convert cloud object to string
        clouds = item.get("clouds", [])
        cloud_layers = []
        for cloud in clouds:
            cover = cloud.get("cover")
            base = cloud.get("base")

            if cover and base is not None:
                # Convert base (feet) → hundreds of feet, padded to 3 digits
                if isinstance(base, (int)):
                    hundreds = int(base / 100)
                    base_str = f"{hundreds:03d}"
                else:
                    base_str = str(base)

                cloud_layers.append(f"{cover}{base_str}")

            elif cover:
                cloud_layers.append(cover)

        clouds_str = " ".join(cloud_layers) if cloud_layers else ""

        metar = item.get("rawOb", "")
        taf = item.get("rawTaf", "")
        taf = taf.replace(" FM", "  \n      FM")
        raw_wx = metar + "  \n" + taf

        # Remove state and country  from name
        name = item.get("name", "")
        # get the state
        state = name[-6:-4]
        name = name[:-8]

        processed_data.append(
            {
                "state": state,
                "icaoId": item.get("icaoId", ""),
                "name": name,
                "wdir": str(item.get("wdir", "")),
                "wspd": item.get("wspd"),
                "wgst": item.get("wgst"),
                "visib": item.get("visib", ""),
                "cover": item.get("cover", ""),
                "clouds": clouds_str,
                "rawOb": raw_wx,
                "rawTaf": item.get("rawTaf", ""),
                "fltCat": item.get("fltCat", ""),
                "lat": item.get("lat", ""),
                "lon": item.get("lon", ""),
            }
        )
    return processed_data


def fetch_data(airport_codes):
    """
    :param airport_codes: str  entered by users
    :return: rowData for table, message
    """

    # clean codes and put in a list
    airport_codes = airport_codes.upper()
    codes = re.findall(r"\w+", airport_codes)

    # allows user to enter 3 char airport codes and 2 char states.
    # ie converts bfi to KBFI
    codes_fixed = []
    for c in codes:
        if len(c) == 2:
            s = state_airports.get(c,"")
            codes_fixed.extend(s)
        if len(c) == 3:
            c = "K" + c
            codes_fixed.append(c)
        if len(c) >= 4:
            codes_fixed.append(c)

    invalid_codes = validate_stations(codes_fixed)
    if invalid_codes:
        return (
            [],
            dmc.Alert(
                f"Invalid weather station: {invalid_codes}", color="yellow"
            )
        )



    ids_param = ",".join(codes_fixed)

    # Fetch data from Aviation Weather API
    url = "https://aviationweather.gov/api/data/metar"

    params = {"ids": ids_param, "format": "json", "taf": "true"}
    headers = {"User-Agent": "DashWeatherApp/2.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 204:
            return (
                [],
                dmc.Alert(
                    "No data available", color="yellow"
                )
            )

        response.raise_for_status()
        data = response.json()
        if not data:
            return [], dmc.Alert("No weather data found", color="yellow")

        row_data = process_data(data)

        success_msg = dmc.Alert(
             f"WX for {len(row_data)} station(s). Last updated: {datetime.now():%Y-%m-%d %H:%M} local / {datetime.now(timezone.utc):%d%H%MZ}",
            color="green",
        )

        return row_data, success_msg

    except requests.exceptions.RequestException as e:
        error_msg = dmc.Alert([f"Error fetching data: {str(e)}", dmc.Text("Check for invalid codes")], color="red")
        return [], error_msg
