import geopandas as gpd
import pandas as pd
import plotly.express as px
from shapely.geometry import Point
import streamlit as st


def convert_to_point(point_str):
    """Converts a string representation of a point to a Shapely Point object."""
    lon, lat = map(float, point_str.strip('POINT ()').split())
    return Point(lon, lat)


def calculate_speed(speed_kts, speed_mach):
    """Calculates speed in knots based on input speed in knots or Mach."""
    if speed_kts == 0:
        return speed_mach * 666.738661
    return speed_kts


def load_and_prepare_data(filepath):
    """Loads geospatial data from a file and prepares it for plotting."""
    air = gpd.read_file(filepath)
    df = pd.DataFrame(air)
    df['geometry'] = df['location'].apply(convert_to_point)
    return gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')


def find_airports_within_range(gdf, icao, distance):
    """Finds airports within a specified range of an airport identified by its ICAO code."""
    airport_location = gdf[gdf['icao'] == icao].geometry.iloc[0]
    radius = distance / 60  # Convert distance to degrees (approximation)
    circle = airport_location.buffer(radius)
    return gdf[gdf.intersects(circle)]


def plot_airports(punkte_im_umkreis):
    """Plots airports within range on a map."""
    fig2 = px.scatter_mapbox(punkte_im_umkreis, lat=punkte_im_umkreis.geometry.y, lon=punkte_im_umkreis.geometry.x,
                             hover_name="icao", hover_data=["icao", "name"], zoom=3, width=1024)
    fig2.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig2)


def main():
    st.set_page_config(layout="wide")
    col1, col2 = st.columns(2)

    col1.write('### Airport Ranger')
    col2.write(
        "Idea: __Max__ / Coding: __Gnasher__\n Airport Data: [Alexander Bilz](https://github.com/lxndrblz/Airports)")

    icao = col1.text_input(label='ICAO').upper()
    ftime = col1.number_input(max_value=3680, min_value=1, step=1, label='Time to fly in minutes')
    speed_kts = col1.number_input(max_value=1000, min_value=0, step=1, label='Speed in ktas')
    speed_mach = col1.number_input(max_value=3.0, min_value=0.0, step=0.01, label='Speed in Mach')

    col2.write('Welcome to the Airport Range Calculator, a handy tool for flight simulator enthusiasts to estimate '
               'reachable airports based on flight speed and time. __Please note, this app is designed solely for '
               'virtual flying and not for real-world aviation purposes.__\n'
               'Here\'s how it works: \n'
               '* Input the ICAO code of your departure airport. \n* Enter your planned flying speed (KTAS) and desired '
               'flight duration. Note: Speed input in the KTAS field overrides the Mach value. \n* For mobile users, '
               'access the options by tapping the arrow in the top left corner. \n* Press "Start searching" to generate '
               'a list of potential destination airports within your specified range, considering both speed and time.')

    col2.write('Keep in mind: \n'
               '* The results are approximate and do not factor in current wind or temperature conditions. \n'
               '* The calculated range is based on a straight-line path; actual IFR flight plans may incur additional'
               ' mileage. \n'
               '* For safety, consider choosing airports slightly closer than the maximum range and check the flight '
               'time in a planning tool like simbrief.')
    col2.write(
        'Our goal is to help you find a convenient airport for a leisurely post-work flight. Enjoy your simulation,'
        ' and may you always have a runway for a smooth landing!')

    if col1.button('Start searching...'):
        speed = calculate_speed(speed_kts, speed_mach)
        ftime_hr = ftime / 60
        distance = speed * ftime_hr
        st.write(f"Distance (rounded): {distance}nm")

        gdf = load_and_prepare_data("data/airports2.csv")
        punkte_im_umkreis = find_airports_within_range(gdf, icao, distance)
        plot_airports(punkte_im_umkreis)


if __name__ == "__main__":
    main()
