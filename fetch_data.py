
import dash_mantine_components as dmc
import requests
from datetime import datetime
import re


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
        # # Remove airport code
        # metar = metar[:6] + metar[10:]
        # taf = taf[:4] + taf[9:]
        taf = taf.replace(" FM", "  \n      FM")
        raw_wx= metar + "  \n" + taf

        # Remove state and country  from name
        name = item.get("name", "")
        # get the state
        state = name[-6:-4]
        name = name[:-8]

        processed_data.append({
            "state": state,
            "icaoId": item.get("icaoId", ""),
            "name": name,
            "wdir": str(item.get("wdir", "")),
            "wspd": str(item.get("wspd", "")) + "KT",
            "wgst": item.get("wgst", ""),
            "visib": item.get("visib", ""),
            "cover": item.get("cover", ""),
            "clouds": clouds_str,
            "rawOb": raw_wx,
            "rawTaf": item.get("rawTaf", "")
        })
    return processed_data


def fetch_data(airport_codes):
    """
    :param airport_codes: str  entered by users
    :return: rowData for table, message
    """

    # clean codes and put in a list
    airport_codes = airport_codes.upper()
    codes = re.findall(r'\w+', airport_codes)

    # allows user to enter 3 char airport codes and 2 char states.
    # ie converts bfi to KBFI and wa to @WA
    codes_fixed = []
    for c in codes:
        if len(c) == 2:
            c= "@"+ c
        if len(c) == 3 and not c.startswith("@"):
            c= "K" + c
        codes_fixed.append(c)

    # TODO verify codes are valid

    ids_param = ",".join(codes_fixed)

    # Fetch data from Aviation Weather API
    url = "https://aviationweather.gov/api/data/metar"
    params = {
        "ids": ids_param,
        "format": "json",
        "taf" : "true"
    }
    headers = {
        "User-Agent": "DashWeatherApp/1.0"    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 204:
            return [], dmc.Alert("No data available for the specified airport(s)", color="yellow"), False

        response.raise_for_status()
        data = response.json()
     #   data = response.text
        if not data:
            return [], dmc.Alert("No weather data found", color="yellow"), False


        row_data = process_data(data)

        success_msg = dmc.Alert(
            f"Successfully fetched WX for {len(row_data)} station(s). Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            color="green"
        )

        return row_data, success_msg

    except requests.exceptions.RequestException as e:
        error_msg = dmc.Alert(f"Error fetching data: {str(e)}", color="red")
        return [], error_msg
