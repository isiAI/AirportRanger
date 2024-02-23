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
    # clean up data we don't need or want
    df.dropna()
    df.drop(df[df['type'] == 'heliport'].index, inplace=True)
    df.drop(df[df['type'] == 'closed'].index, inplace=True)
    df.drop(df[df['type'] == 'seaplane_base'].index, inplace=True)
    df.drop(df[df['type'] == 'balloonport'].index, inplace=True)
    df.drop(['municipality', 'wikipedia_link', 'keywords'], axis=1, inplace=True)

    # clean up possible binary data in name
    df['name'] = df['name'].astype(str)
    # add color
    # df['color'] = 'red'

    # debug stuff
    # print("------\n")
    # print(df.head())
    #
    # for col in df.select_dtypes(include=['object']).columns:
    #     # Check if any row in the column contains data of type `bytes`
    #     if any(isinstance(x, bytes) for x in df[col]):
    #         print(f"Column '{col}' contains binary data.")

    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude_deg'], df['latitude_deg']), crs='EPSG:4326')


def find_airports_within_range(gdf, icao, distance):
    """Finds airports within a specified range of an airport identified by its ICAO code."""
    airport_location = gdf[gdf['ident'] == icao].geometry.iloc[0]
    radius = distance / 60  # Convert distance to degrees (approximation)
    circle = airport_location.buffer(radius)
    return gdf[gdf.intersects(circle)]


def plot_airports(punkte_im_umkreis):
    """Plots airports within range on a map."""
    fig2 = px.scatter_mapbox(punkte_im_umkreis,
                             lat=punkte_im_umkreis.geometry.y,
                             lon=punkte_im_umkreis.geometry.x,
                             hover_name="ident",
                             hover_data={"name": True,
                                         "ident": False,
                                         "type": False},
                             labels={"name": "Name",
                                     "ident": "ICAO",
                                     "type": "Airport size"},
                             zoom=3,
                             width=1024,
                             color="type",
                             color_discrete_sequence=['#00cc96', '#DC3912', '#316395'],
                             category_orders={"type": ["small_airport", "medium_airport", "large_airport"]},
                             )
    fig2.update_layout(mapbox_style="open-street-map",
                       margin={"r": 0, "t": 20, "l": 0, "b": 0},
                       title="Airports in range",
                       legend_title="Airport size / click to turn on/off",
                       )

    st.plotly_chart(fig2)


def main():
    st.set_page_config(layout="wide", page_title="Airport Ranger - find your next destination")
    col1, col2 = st.columns([1, 2], gap="large")
    col1.write('# Airport Ranger')

    icao = col1.text_input(label='ICAO').upper()
    ftime = col1.number_input(max_value=3680, min_value=1, step=1, label='Time to fly in minutes')
    speed_kts = col1.number_input(max_value=1000, min_value=0, step=1, label='Speed in ktas')
    speed_mach = col1.number_input(max_value=3.0, min_value=0.0, step=0.01, label='Speed in Mach')

    col2.write('Welcome to the Airport Range Calculator, a handy tool for flight simulator enthusiasts to estimate '
               'reachable airports based on flight speed and time.\n\n__Please note, this app is designed solely for '
               'virtual flying and not for real-world aviation purposes.__\n\n'
               'Here\'s how it works: \n'
               '* Enter the ICAO code of your starting airport. \n'
               '* Set your duration in time to fly field that you wish to fly\n'
               '* Input your planned flying speed in KTAS (Knots True Airspeed) and the duration of your flight. '
               '__Note: Entering a speed in KTAS will override any Mach number input.__ \n'
               '* Press "Start searching" to generate a list of potential destination airports within your specified '
               'range, considering both speed and time.\n'
               '* Click the airport size labels on the right side of the map to show/hide airports for better overview.')

    col2.write('Keep in mind: \n'
               '* The results are approximate and do not factor in current wind or temperature conditions. \n'
               '* The calculated range is based on a straight-line path; actual IFR flight plans may incur additional'
               ' mileage. \n'
               '* For safety, consider choosing airports slightly closer than the maximum range and check the flight '
               'time in a planning tool like simbrief.')
    col2.write(
        'Our goal is to help you find a convenient airport for a leisurely flight. Enjoy your simulation,'
        ' and may you always have a runway for a smooth landing!')
    col2.write(
        "Idea: __Max__ / Coding: __Bjoern__")

    if col1.button('Start searching...'):
        speed = calculate_speed(speed_kts, speed_mach)
        ftime_hr = ftime / 60
        distance = speed * ftime_hr
        st.write(f"Distance (rounded): {distance:.2f} nm")

        with st.spinner("Searching"):
            gdf = load_and_prepare_data("data/airports.csv")
            punkte_im_umkreis = find_airports_within_range(gdf, icao, distance)
            st.write(f'Found: {len(punkte_im_umkreis)} airports')
            plot_airports(punkte_im_umkreis)


if __name__ == "__main__":
    main()
