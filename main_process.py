"""
WellVisualizerMain.py
Author: Colton Goodrich
Date: 11/10/2024
Python Version: 3.12
This module is a PyQt5 application that provides a graphical user interface (GUI) for
visualizing and analyzing well data, board matters, and related information from the
State of Utah, Division of Oil, Gas, and Mining.

The application features various functionalities, including:

- Interactive visualization of well trajectories in both 2D and 3D views, including
  planned, currently drilling, and completed wells
- Real-time well path visualization with different line styles for different well states
  (planned: dashed, drilling: solid, completed: solid)
- Advanced filtering system for wells based on type (oil, gas, water disposal, dry hole,
  injection) and status (shut-in, PA, producing, drilling)
- Mineral ownership visualization with section-level detail and agency tracking
- Dynamic operator filtering system with color-coded checkboxes and scrollable interfaces
- Production data visualization with cumulative and time-series analysis
- Field boundary and plat code visualization with centroid labeling
- Interactive well selection system with detailed data display
- Customizable visualization features including zoom, pan, and scale adjustment

Classes:
- MultiBoldRowDelegate: A custom delegate for applying bold formatting to specific rows
  in Qt views, particularly useful for emphasizing important wells
- BoldDelegate: A custom delegate for applying bold formatting to specific values in
  Qt views
- wellVisualizationProcess: The main application class that inherits from QMainWindow
  and BoardMattersVisualizer, handling all core functionality

Key Components:
- Data Management: Utilizes Pandas, GeoPandas, and SQLite for efficient data handling
- Visualization: Combines Matplotlib with PyQt5 for interactive plotting
- Geospatial Processing: Integrates UTM and Shapely for coordinate transformations
  and geometric operations
- User Interface: Custom-designed PyQt5 interface with scrollable areas and
  dynamic updates

The module serves as a comprehensive tool for analyzing and visualizing well data,
providing detailed insights into well operations, ownership, and regulatory matters
for the State of Utah's Division of Oil, Gas, and Mining operations.

Dependencies:
- Core Scientific: numpy, pandas, geopandas
- GUI Framework: PyQt5
- Visualization: matplotlib
- Geospatial: shapely, utm
- Database: sqlite3, sqlalchemy
- Utility: regex

Note: This application requires specific data structures and database connectivity
to function properly. See accompanying documentation for setup requirements.
"""

# Python standard library imports
import itertools
import os
import sqlite3
from datetime import datetime
from typing import Callable, Dict, List, Literal, NoReturn, Optional, Set, Tuple, Union

# Third-party imports - Core Data/Scientific
import numpy as np
from numpy import array, std
import pandas as pd
from pandas import DataFrame, concat, options, read_sql, set_option, to_datetime, to_numeric
import geopandas as gpd
import utm
from sqlalchemy import create_engine

# Third-party imports - PyQt5
import PyQt5
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt5.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QGraphicsDropShadowEffect, QHeaderView,
    QHBoxLayout, QLabel, QLayout, QMainWindow, QScrollArea,
    QStyledItemDelegate, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget
)

# Third-party imports - Matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import LineCollection, PatchCollection, PolyCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Polygon
from matplotlib.text import Text
from matplotlib.textpath import TextPath
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from mpl_toolkits.mplot3d.art3d import Line3DCollection

# Third-party imports - Geospatial
from shapely import wkt
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

# Third-party imports - Other
import regex as re

# Local application imports
from WellVisualizerBoardMatters import BoardMattersVisualizer
from WellVisualizationUI import Ui_Dialog
from main_process_year import Year

class wellVisualizationProcess(QMainWindow):
    def __init__(self, flag=True):
        super().__init__()
        set_option('display.max_columns', None)
        options.mode.chained_assignment = None
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        path = r"C:\Work\databases"
        apd_data_dir = os.path.join(path, 'Board_DB.db')
        self.conn_db = sqlite3.connect(apd_data_dir)
        self.cursor_db = self.conn_db.cursor()
        # Create SQLAlchemy engine
        self.engine = create_engine(f'sqlite:///{apd_data_dir}')
        self.df_field, self.df_owner = None, None
        self.df_adjacent_fields = None
        self.df_plat = None
        self.df_adjacent_plats = None
        self.well_data_unique_df = None
        self.well_df = None
        self.dx_df = None
        self.df_shl = None
        self.used_dockets = None
        self.used_years = None
        self.df_board_data = None
        self.df_board_data_links = None
        """Setup the tables so that they are prepped and ready to go."""
        self.setup_tables()
        """Load the data to be used, process it, alter it, etc for usage"""
        self.load_data()
        self.populate_year_combo_box()
        self.ui.year_lst_combobox.activated.connect(lambda: self.do_this_when_year_combo_box_pressed(self.well_df))

    def populate_year_combo_box(self):
        self.ui.year_lst_combobox.clear()
        self.ui.month_lst_combobox.clear()
        self.ui.board_matter_lst_combobox.clear()
        self.ui.well_lst_combobox.clear()
        model: QStandardItemModel = QStandardItemModel()
        for year in self.used_years:
            item: QStandardItem = QStandardItem(str(year))
            model.appendRow(item)
        self.ui.year_lst_combobox.setModel(model)

    def do_this_when_year_combo_box_pressed(self, well_df):
        selected_year: str = self.ui.year_lst_combobox.currentText()
        df_year = well_df[well_df['Board_Year'] == selected_year]
        year_obj = Year(ui=self.ui, year=selected_year, df_year=df_year, df_dx = self.dx_df)


    def load_data(self):
        # Load field and ownership base data
        df_field = read_sql('select * from Field', self.conn_db)
        df_owner = read_sql('select * from Owner', self.conn_db)
        df_adjacent_fields = self.load_df_fields(df_field)  # Process field information
        df_board_data, df_board_data_links = self.load_board_data()
        df_plat, df_adjacent_plats = self.load_plat_data()
        well_data_unique_df, well_df = self.load_well_df_data()
        dx_df, df_shl = self.load_well_data(well_data_unique_df)
        used_dockets = well_df['Board_Docket'].unique()
        used_years = well_df['Board_Year'].unique()
        df_prod = read_sql('select * from Production', self.conn_db)
        df_prod.drop_duplicates(keep='first', inplace=True)

        self.df_adjacent_fields = df_adjacent_fields
        self.df_plat = df_plat
        self.df_adjacent_plats = df_adjacent_plats
        self.well_data_unique_df = well_data_unique_df #dx_data_unique
        self.well_df = well_df #dx_data
        self.dx_df = dx_df
        self.df_shl = df_shl
        self.used_dockets = used_dockets
        self.used_years = used_years
        self.df_board_data = df_board_data
        self.df_board_data_links = df_board_data_links
        self.df_field = df_field
        self.df_owner = df_owner



    def load_df_fields(self, df_field):
        # Initialize storage for adjacent field relationships
        adjacent_fields: List[Dict[str, str]] = []

        # Create point geometries for field locations
        df_field['geometry'] = df_field.apply(
            lambda row: Point(row['Easting'], row['Northing']),
            axis=1
        )

        # Extract relevant fields for polygon creation
        used_fields = df_field[['Field_Name', 'Easting', 'Northing']]

        # Generate field polygons from coordinate groups
        polygons = used_fields.groupby('Field_Name').apply(
            lambda x: Polygon(zip(x['Easting'], x['Northing'])),
            include_groups=False
        ).reset_index()
        polygons.columns = ['Field_Name', 'geometry']

        # Create GeoDataFrame with buffer zones
        gdf = gpd.GeoDataFrame(polygons, geometry='geometry')
        gdf['buffer'] = gdf['geometry'].buffer(10)

        # Identify adjacent fields using spatial analysis
        for _, row in gdf.iterrows():
            # Find neighboring fields using buffer intersection
            neighbors = gdf[gdf['buffer'].intersects(row['geometry'])]['Field_Name'].tolist()
            neighbors.remove(row['Field_Name'])  # Remove self-reference

            # Create adjacency relationships
            adjacent_fields.extend([
                {'Field_Name': row['Field_Name'], 'adjacent_Field_Name': neighbor}
                for neighbor in neighbors
            ])
        columns = [k for k,v in adjacent_fields[0].items()]
        return pd.DataFrame(data = adjacent_fields, columns=columns)

    def load_board_data(self):
        def translateNumberToDirection(variable, val):
            translations = {
                'rng': {'2': 'W', '1': 'E'},
                'township': {'2': 'S', '1': 'N'},
                'baseline': {'2': 'U', '1': 'S'},
                'alignment': {'1': 'SE', '2': 'NE', '3': 'SW', '4': 'NW'}
            }
            return translations.get(variable, {}).get(val, val)
        def conc_code_maker(i):
            conc_code_merged = i[:6]
            conc_code_merged.iloc[2] = translateNumberToDirection('township',
                                                                       str(conc_code_merged.iloc[2])).upper()
            conc_code_merged.iloc[4] = translateNumberToDirection('rng', str(conc_code_merged.iloc[4])).upper()
            conc_code_merged.iloc[5] = translateNumberToDirection('baseline',
                                                                       str(conc_code_merged.iloc[5])).upper()
            conc_code_merged.iloc[0] = str(int(float(conc_code_merged.iloc[0]))).zfill(2)
            conc_code_merged.iloc[1] = str(int(float(conc_code_merged.iloc[1]))).zfill(2)
            conc_code_merged.iloc[3] = str(int(float(conc_code_merged.iloc[3]))).zfill(2)
            conc_code = "".join([str(q) for q in conc_code_merged])
            return conc_code

        # Load board meeting records and associated links
        df_board_data = read_sql('select * from BoardData', self.conn_db)
        df_board_data_links = read_sql('select * from BoardDataLinks', self.conn_db)

        # Generate concatenated location codes using ModuleAgnostic translator
        df_board_data['Conc'] = df_board_data[[
            'Sec', 'Township', 'TownshipDir',
            'Range', 'RangeDir', 'PM'
        ]].apply(lambda x: conc_code_maker(x), axis=1)
        return df_board_data, df_board_data_links

    def load_plat_data(self):
        # Load raw plat data from database
        df_plat = read_sql('select * from PlatData', self.conn_db)
        df_adjacent_plats = read_sql('select * from Adjacent', self.conn_db)

        # Clean plat data by removing duplicates and invalid coordinates
        df_plat.drop_duplicates(keep='first', inplace=True)
        df_plat = df_plat.dropna(subset=['Lat', 'Lon'])

        # Convert geographic coordinates (Lat/Lon) to UTM projection (Easting/Northing)
        df_plat['Easting'], df_plat['Northing'] = zip(
            *df_plat.apply(lambda row: utm.from_latlon(row['Lat'], row['Lon'])[:2], axis=1))

        # Create Shapely Point geometries for spatial analysis
        df_plat['geometry'] = df_plat.apply(
            lambda row: Point(row['Easting'], row['Northing']),
            axis=1)
        return df_plat, df_adjacent_plats
    
    def load_well_df_data(self):
        """
        Loads and processes directional well data from database, performing data cleanup
        and standardization.

        Loads well information, removes plugged wells, standardizes field names, and calculates
        well ages. Processes dates and creates display names for wells.

        Args:
            None

        Returns:
            DataFrame: Processed well data with unique WellIDs containing columns:
                - WellID: str - Unique identifier for well
                - WellName: str - Name of the well
                - DisplayName: str - Combined WellID and WellName for UI display
                - Operator: str - Well operator name
                - WorkType: str - Type of well work being performed
                - DrySpud: str - Formatted spud date (YYYY-MM-DD)
                - WellAge: int - Age of well in months
                - CurrentWellStatus: str - Current status of well
                - FieldName: str - Standardized field name
                - Board_Year: int - Year of board approval
                - Docket_Month: str - Month of board approval

        Side Effects:
            - Creates/Updates self.well_df with processed well information

        Notes:
            - Filters out plugged wells (WorkType = 'PLUG')
            - Removes duplicate entries
            - Standardizes field names using translation dictionary
            - Calculates well age in months from spud date
            - Sets well age to 0 for approved permits without spud dates
        """
        # Define field name translations for standardization
        translated_fields: Dict[str, str] = {'AAGARD RANCH': 'AAGARD RANCH FIELD', 'ANDERSON JUNCTION': 'ANDERSON JUNCTION FIELD', 'ANSCHUTZ RANCH WEBER': 'ANSCHUTZ RANCH (WEBER) FIELD', 'BAR X': 'BAR X FIELD', 'BIG FLAT': 'BIG FLAT FIELD', 'BIG FLAT WEST': 'BIG FLAT WEST FIELD', 'BIG INDIAN SOUTH': 'BIG INDIAN (SOUTH) FIELD', 'BONANZA': 'BONANZA FIELD', 'BOUNDARY BUTTE': 'BOUNDARY BUTTE FIELD', 'BRADFORD CYN': 'BRADFORD CANYON FIELD', 'BUZZARD BENCH': 'BUZZARD BENCH FIELD', 'CABALLO': 'CABALLO FIELD',
                             'CACTUS PARK': 'CACTUS PARK FIELD', 'CHOKECHERRY CYN': 'CHOKECHERRY CANYON FIELD', 'CLAY HILL': 'CLAY HILL FIELD', 'CLEAR CREEK': 'CLEAR CREEK FIELD', 'DARK CANYON': 'DARK CANYON FIELD', 'DESERT CREEK': 'DESERT CREEK FIELD', 'ELKHORN': 'ELKHORN FIELD', 'FARNHAM DOME': 'FARNHAM DOME FIELD', 'FENCE CANYON': 'FENCE CANYON FIELD', 'GREATER CISCO': 'GREATER CISCO FIELD', 'HALFWAY HOLLOW': 'HALFWAY HOLLOW FIELD', 'HATCH POINT': 'HATCH POINT FIELD', 'HOGAN': 'HOGAN FIELD',
                             'HOGBACK RIDGE': 'HOGBACK RIDGE FIELD', 'HORSEHEAD POINT': 'HORSEHEAD POINT FIELD', 'HORSESHOE BEND': 'HORSESHOE BEND FIELD', 'ICE CANYON (DK-MR)': 'ICE CANYON FIELD', 'LAKE CANYON': 'LAKE CANYON FIELD', 'LAST CHANCE': 'LAST CHANCE FIELD', 'LODGEPOLE': 'LODGEPOLE FIELD', 'MAIN CANYON': 'MAIN CANYON FIELD', 'MANCOS FLAT': 'MANCOS FLAT FIELD', 'MCELMO MESA': 'MCELMO MESA FIELD', 'NAVAJO CANYON': 'NAVAJO CANYON FIELD', 'NORTH MYTON BENCH': 'NORTH MYTON BENCH',
                             'PARIETTE BENCH': 'PARIETTE BENCH FIELD', 'PARK ROAD': 'PARK ROAD FIELD', 'PETERS POINT': 'PETERS POINT FIELD', 'PETES WASH': 'PETES WASH FIELD', 'RABBIT EARS': 'RABBIT EARS FIELD', 'RANDLETT': 'RANDLETT FIELD', 'ROBIDOUX': 'ROBIDOUX FIELD', 'ROCK HOUSE': 'ROCK HOUSE FIELD', 'RUNWAY': 'RUNWAY FIELD', 'SEGUNDO CANYON': 'SEGUNDO CANYON FIELD', 'SOUTH PINE RIDGE': 'SOUTH PINE RIDGE FIELD', 'STRAWBERRY': 'STRAWBERRY FIELD', 'SWEET WATER RIDGE': 'SWEETWATER RIDGE FIELD',
                             'TOHONADLA': 'TOHONADLA FIELD', 'UCOLO': 'UCOLO FIELD', 'UTELAND BUTTE': 'UTELAND BUTTE FIELD', 'WHITE MESA': 'WHITE MESA FIELD', 'WILD STALLION': 'WILD STALLION FIELD', 'WINDY RIDGE': 'WINDY RIDGE FIELD', 'WONSITS VALLEY': 'WONSITS VALLEY FIELD', 'WOODSIDE': 'WOODSIDE FIELD', '8 MILE FLAT NORTH': 'EIGHT MILE FLAT NORTH FIELD', 'AGENCY DRAW': 'AGENCY DRAW FIELD', 'ALKALI CANYON': 'ALKALI CANYON FIELD', 'ALTAMONT': 'ALTAMONT FIELD', 'ANETH': 'ANETH FIELD',
                             'ANTELOPE CREEK': 'ANTELOPE CREEK FIELD', 'BIG VALLEY': 'BIG VALLEY FIELD', 'BLUEBELL': 'BLUEBELL FIELD', 'BLUFF': 'BLUFF FIELD', 'BLUFF BENCH': 'BLUFF BENCH FIELD', 'BRIDGELAND': 'BRIDGELAND FIELD', 'BRIDGER LAKE': 'BRIDGER LAKE FIELD', 'BRUNDAGE CANYON': 'BRUNDAGE CANYON FIELD', 'BUCK CANYON': 'BUCK CANYON FIELD', 'BUSHY': 'BUSHY FIELD', 'CEDAR CAMP': 'CEDAR CAMP FIELD', 'CHEROKEE': 'CHEROKEE FIELD', 'CHINLE WASH': 'CHINLE WASH FIELD',
                             'CISCO DOME': 'CISCO DOME FIELD', 'CLAY BASIN': 'CLAY BASIN FIELD', 'CLEFT': 'CLEFT FIELD', 'CONE ROCK': 'CONE ROCK FIELD', 'COVENANT': 'COVENANT FIELD', 'COWBOY': 'COWBOY FIELD', 'DAVIS CANYON': 'DAVIS CANYON FIELD', 'DEAD MAN CANYON': 'DEADMAN CANYON FIELD', 'DEADMAN-ISMY': 'DEADMAN (ISMAY) FIELD', 'DELTA SALT CAVERN STORAGE': 'DELTA SALT CAVERN STORAGE FIELD', 'DEVILS PLAYGROUND': "DEVIL'S PLAYGROUND FIELD", 'DRY BURN': 'DRY BURN FIELD',
                             'EAST CANYON': 'EAST CANYON FIELD', 'EVACUATION CREEK': 'EVACUATION CREEK FIELD', 'FARMINGTON': 'FARMINGTON FIELD', 'GRASSY TRAIL': 'GRASSY TRAIL FIELD', 'GRAYSON': 'GRAYSON FIELD', 'GUSHER': 'GUSHER FIELD', 'HATCH': 'HATCH FIELD', "HELL'S HOLE": "HELL'S HOLE FIELD", 'HELPER': 'HELPER FIELD', 'HORSE CANYON': 'HORSE CANYON FIELD', 'INDEPENDENCE': 'INDEPENDENCE FIELD', 'KACHINA': 'KACHINA FIELD', 'KICKER': 'KICKER FIELD', 'LIGHTNING DRAW': 'LIGHTNING DRAW FIELD',
                             'LION MESA': 'LION MESA FIELD', 'LISBON': 'LISBON FIELD', 'MC CRACKEN SPRING': 'MCCRACKEN SPRING FIELD', 'MOAB GAS STORAGE': 'MOAB GAS STORAGE', 'MONUMENT': 'MONUMENT FIELD', 'MONUMENT BUTTE': 'MONUMENT BUTTE FIELD', 'MUSTANG FLAT': 'MUSTANG FLAT FIELD', 'NATURAL BUTTES': 'NATURAL BUTTES FIELD', 'NINE MILE CANYON': 'NINE MILE CANYON FIELD', 'NORTH BONANZA': 'NORTH BONANZA FIELD', 'PAIUTE KNOLL': 'PAIUTE KNOLL FIELD', 'PEAR PARK': 'PEAR PARK FIELD',
                             'POWDER SPRINGS': 'POWDER SPRINGS FIELD', 'RAT HOLE CANYON': 'RAT HOLE CANYON FIELD', 'RECAPTURE CREEK': 'RECAPTURE CREEK FIELD', 'ROCKWELL FLAT': 'ROCKWELL FLAT FIELD', 'SAN ARROYO': 'SAN ARROYO FIELD', 'SEEP RIDGE': 'SEEP RIDGE FIELD', 'SHUMWAY POINT': 'SHUMWAY POINT FIELD', 'SODA SPRING': 'SODA SPRING FIELD', 'SOLDIER CREEK': 'SOLDIER CREEK FIELD', 'SOUTH ISMAY': 'SOUTH ISMAY FIELD', 'SOWERS CANYON': 'SOWER CANYON FIELD', 'STONE CABIN': 'STONE CABIN FIELD',
                             'SWEETWATER CYN': 'SWEETWATER CANYON FIELD', 'TIN CUP MESA': 'TIN CUP MESA FIELD', 'TOWER': 'TOWER FIELD', 'TURNER BLUFF': 'TURNER BLUFF FIELD', 'VIRGIN': 'VIRGIN FIELD', 'WHITE RIVER': 'WHITE RIVER FIELD', 'WINTER CAMP': 'WINTER CAMP FIELD', 'ALGER PASS': 'ALGER PASS FIELD', 'ALKALI POINT': 'ALKALI POINT FIELD', 'ANIDO CREEK': 'ANIDO CREEK FIELD', 'ASPHALT WASH': 'ASPHALT WASH FIELD', 'ATCHEE RIDGE': 'ATCHEE RIDGE FIELD', 'BANNOCK': 'BANNOCK FIELD',
                             'BIG SPRING': 'BIG SPRING FIELD', 'BITTER CREEK': 'BITTER CREEK FIELD', 'BLACK BULL': 'BLACK BULL FIELD', 'BLACK HORSE CYN': 'BLACK HORSE CANYON FIELD', 'BOOK CLIFFS': 'BOOK CLIFFS FIELD', 'BRENNAN BOTTOM': 'BRENNAN BOTTOM FIELD', 'BROKEN HILLS': 'BROKEN HILLS FIELD', 'BRONCO': 'BRONCO FIELD', 'BRYSON CANYON': 'BRYSON CANYON FIELD', 'CAJON LAKE': 'CAJON LAKE FIELD', 'CANE CREEK': 'KANE CREEK FIELD', 'CASA MESA': 'CASA MESA FIELD',
                             'CHALK CREEK GAS STORAGE': 'CHALK CREEK GAS STORAGE', 'COTTONWOOD WASH': 'COTTONWOOD WASH FIELD', 'CROOKED CANYON': 'CROOKED CANYON FIELD', 'DUCHESNE': 'DUCHESNE FIELD', 'FLAT CANYON': 'FLAT CANYON FIELD', 'GATE CANYON': 'GATE CANYON FIELD', 'GORDON CREEK': 'GORDON CREEK FIELD', 'GOTHIC MESA': 'GOTHIC MESA FIELD', 'GYPSUM HILLS': 'GYPSUM HILLS FIELD', 'HELL ROARING': 'HELL ROARING FIELD', 'HERON': 'HERON FIELD', 'HILL CREEK': 'HILL CREEK FIELD',
                             'HORSE POINT': 'HORSE POINT FIELD', "JOE'S VALLEY": "JOE'S VALLEY FIELD", 'KENNEDY WASH': 'KENNEDY WASH FIELD', 'LIGHTNING DRAW SE': 'LIGHTNING DRAW FIELD', 'LITTLE NANCY': 'LITTLE NANCY FIELD', 'LITTLE VALLEY': 'LITTLE VALLEY FIELD', 'LONE SPRING': 'LONE SPRING FIELD', 'LONG CANYON': 'LONG CANYON FIELD', 'MIDDLE BENCH': 'MIDDLE BENCH FIELD', 'MOON RIDGE': 'MOON RIDGE FIELD', 'NAVAL RESERVE': 'NAVAL RESERVE FIELD', 'PETERSON SPRING': 'PETERSON SPRINGS FIELD',
                             'PLEASANT VALLEY': 'PLEASANT VALLEY FIELD', 'RED WASH': 'RED WASH FIELD', 'SALT WASH': 'SALT WASH FIELD', 'SCOFIELD': 'UCOLO FIELD', 'SHAFER CANYON': 'SHAFER CANYON FIELD', 'SOUTH CANYON': 'SOUTH CANYON FIELD', 'SOUTH MYTON BENCH': 'NORTH MYTON BENCH', 'SQUAW POINT': 'SQUAW POINT FIELD', 'WALKER HOLLOW': 'WALKER HOLLOW FIELD', 'WESTWATER': 'WESTWATER FIELD', 'WHITEBELLY WASH': 'WHITEBELLY WASH FIELD', 'YELLOW ROCK': 'YELLOW ROCK FIELD',
                             'AGENCY DRAW WEST': 'AGENCY DRAW WEST FIELD', 'ANSCHUTZ RANCH': 'ANSCHUTZ RANCH FIELD', 'ANSCHUTZ RANCH EAST': 'ANSCHUTZ RANCH EAST FIELD', 'ASHLEY VALLEY': 'ASHLEY VALLEY FIELD', 'BIG INDIAN NORTH': 'BIG INDIAN (NORTH) FIELD', 'BLAZE CANYON': 'BLAZE CANYON FIELD', 'CAJON MESA': 'CAJON MESA FIELD', 'CASTLEGATE': 'CASTLEGATE FIELD', 'CAVE CANYON': 'CAVE CANYON FIELD', 'CAVE CREEK': 'CAVE CREEK FIELD', 'CEDAR RIM': 'CEDAR RIM FIELD',
                             'COALVILLE GAS STORAGE': 'COALVILLE GAS STORAGE', 'COYOTE BASIN': 'COYOTE BASIN FIELD', 'DIAMOND RIDGE': 'DIAMOND RIDGE FIELD', 'DRUNKARDS WASH': 'DRUNKARDS WASH FIELD', 'EIGHT MILE FLAT': 'EIGHT MILE FLAT FIELD', 'FERRON': 'FERRON FIELD', 'FIRTH': 'FIRTH FIELD', 'FLAT ROCK': 'FLAT ROCK FIELD', 'GREATER ANETH': 'GREATER ANETH FIELD', 'GREENTOWN': 'GREENTOWN FIELD', 'INDIAN CANYON': 'INDIAN CANYON FIELD', 'ISMAY': 'ISMAY FIELD',
                             'LEFT HAND CYN': 'LEFT HAND CANYON FIELD', 'LELAND BENCH': 'LELAND BENCH FIELD', 'MATHEWS': 'MATHEWS FIELD', 'MEXICAN HAT': 'MEXICAN HAT FIELD', 'MIDDLE CANYON (DKTA)': 'MIDDLE CANYON FIELD', 'MILLER CREEK': 'MILLER CREEK FIELD', 'MOFFAT CANAL': 'MOFFAT CANAL FIELD', 'NORTH PINEVIEW': 'NORTH PINEVIEW FIELD', 'OIL SPRINGS': 'OIL SPRINGS FIELD', 'PATTERSON CANYON': 'PATTERSON CANYON FIELD', 'PINE SPRINGS': 'PINE SPRINGS FIELD', 'PINEVIEW': 'PINEVIEW FIELD',
                             'PROVIDENCE': 'PROVIDENCE FIELD', 'RECAPTURE POCKET': 'RECAPTURE POCKET FIELD', 'RIVER BANK': 'RIVER BANK FIELD', 'ROAD CANYON': 'ROAD CANYON FIELD', 'ROZEL POINT': 'ROZEL POINT FIELD', 'SEEP RIDGE B (DKTA)': 'SEEP RIDGE B FIELD', 'SQUAW CANYON': 'SQUAW CANYON FIELD', 'STARR FLAT': 'STARR FLAT FIELD', 'STATELINE': 'STATE LINE FIELD', 'TEN MILE': 'TEN MILE FIELD', 'THREE RIVERS': 'THREE RIVERS FIELD', 'UPPER VALLEY': 'UPPER VALLEY FIELD',
                             'WEST WILLOW CREEK': 'WEST WILLOW CREEK FIELD', 'WHISKEY CREEK': 'WHISKEY CREEK FIELD', 'WILSON CANYON': 'WILSON CANYON FIELD', 'WOLF POINT': 'WOLF POINT FIELD', 'TABYAGO': 'TABYAGO CANYON FIELD', 'KIVA': 'KIVA FIELD', 'AKAH': 'AKAH FIELD', 'BUG': 'BUG FIELD', 'LOVE': 'LOVE FIELD', '12 MILE WASH': 'TWELVE MILE WASH FIELD'}

        # Define month name to number mapping
        month_dict: Dict[str, int] = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

        # Load and initial processing of well data
        well_df = read_sql('select * from WellInfo', self.conn_db)
        well_df = well_df.rename(columns={'entityname': 'Operator'})

        # Remove plugged wells and duplicates
        well_df = well_df[well_df['WorkType'] != 'PLUG']
        well_df.drop_duplicates(keep='first', inplace=True)

        # Create display names for wells
        well_df['DisplayName'] = well_df['WellID'].astype(str) + ' - ' + well_df['WellName'].astype(str)
        # Process dates and calculate well age
        well_df['DrySpud'] = to_datetime(well_df['DrySpud'])
        well_df['WellAge'] = (datetime.now().year - well_df['DrySpud'].dt.year) * 12 + datetime.now().month - \
                                  well_df['DrySpud'].dt.month
        well_df['DrySpud'] = well_df['DrySpud'].dt.strftime('%Y-%m-%d')

        # Set well age to 0 for approved permits without spud dates
        condition = pd.isna(well_df['WellAge']) & (well_df['CurrentWellStatus'] == 'Approved Permit')
        well_df.loc[condition, 'WellAge'] = 0

        # Sort by month and year
        well_df['month_order'] = well_df['Docket_Month'].map(month_dict)
        df_sorted = well_df.sort_values(by=['Board_Year', 'month_order'])
        well_df = df_sorted.drop('month_order', axis=1)

        # Standardize field names
        well_df['FieldName'] = well_df['FieldName'].map(translated_fields)

        # Return unique wells only
        well_data_unique_df = well_df.drop_duplicates(subset=['WellID'])
        return well_data_unique_df, well_df

    def load_well_data(self, well_data_unique_df: DataFrame):
        """Loads and processes well directional survey data, merging it with unique well information
        and performing necessary coordinate and elevation calculations.

        This method queries the DX table, merges it with well-specific data, and performs various
        data transformations including elevation calculations and coordinate conversions.

        Args:
            well_data_unique_df (DataFrame): DataFrame containing unique well records with columns:
                - WellID: Well identifier
                - Elevation: Surface elevation of well
                - FieldName: Name of the oil/gas field
                - Mineral Lease: Associated mineral lease information
                - ConcCode: Concentration code

        Notes:
            - Updates several class attributes including self.dx_df and self.df_shl
            - Performs coordinate conversions from meters to state plane (feet)
            - Adjusts vertical well coordinates slightly to enable linestring creation
            - All depth and elevation calculations are in consistent units (feet)

        Side Effects:
            - Modifies self.dx_df: Main directional survey DataFrame
            - Creates self.df_shl: Surface hole location DataFrame
        """
        # Load directional survey data and remove duplicates
        dx_df = read_sql('select * from DX', self.conn_db)
        dx_df.drop_duplicates(keep='first', inplace=True)
        # Merge directional survey data with well-specific information
        dx_df = pd.merge(
            dx_df,
            well_data_unique_df[['WellID', 'Elevation', 'FieldName', 'Mineral Lease', 'ConcCode']],
            how='left',
            left_on='APINumber',
            right_on='WellID'
        )

        # Convert coordinate columns to float type
        dx_df['X'] = dx_df['X'].astype(float)
        dx_df['Y'] = dx_df['Y'].astype(float)

        # Calculate true elevation relative to well head elevation
        dx_df['TrueElevation'] = dx_df['Elevation'] - to_numeric(dx_df['TrueVerticalDepth'],
                                                                           errors='coerce')
        dx_df['MeasuredDepth'] = to_numeric(dx_df['MeasuredDepth'], errors='coerce')

        # Standardize citing type to lowercase
        dx_df['CitingType'] = dx_df['CitingType'].str.lower()

        # Adjust Y coordinates for vertical wells to create valid linestrings
        # Adds small incremental offset (0.001) to Y coordinate for each point
        dx_df.loc[dx_df['CitingType'] == 'vertical', 'Y'] += dx_df.groupby(['X', 'Y']).cumcount() * 1e-3

        # Convert coordinates to state plane (meters to feet)
        dx_df['SPX'] = dx_df['X'].astype(float) / 0.3048  # Convert meters to feet
        dx_df['SPY'] = dx_df['Y'].astype(float) / 0.3048  # Convert meters to feet

        # Sort data by well ID and measured depth
        dx_df = dx_df.sort_values(by=['WellID', 'MeasuredDepth'])

        # Create surface hole location DataFrame from first point of each well
        df_shl = dx_df.groupby('WellID').first().reset_index()
        return dx_df, df_shl

    def setup_tables(self) -> None:
        """Initializes UI tables with empty QTableWidgetItems for data display.

        Creates and sets up the initial state of three well data tables and one
        board data table in the user interface. Each table is populated with empty
        QTableWidgetItem instances to prepare for later data insertion.

        Table Structure:
            - Well Data Tables (3):
                - 1 row x 12 columns each
                - All cells initialized as empty
            - Board Data Table:
                - 3 rows x 1 column
                - All cells initialized as empty

        Side Effects:
            Modifies the following UI components:
            - self.ui.well_data_table_1
            - self.ui.well_data_table_2
            - self.ui.well_data_table_3
            - self.ui.board_data_table

        Note:
            This method should be called once during UI initialization before
            any data population occurs.

        Raises:
            AttributeError: If any of the required UI table widgets are not properly initialized.
        """
        # Initialize list of well data tables for batch processing
        well_tables: List[QTableWidget] = [
            self.ui.well_data_table_1,
            self.ui.well_data_table_2,
            self.ui.well_data_table_3
        ]

        # Initialize all well data tables (12 columns x 1 row each)
        for table in well_tables:  # type: QTableWidget
            for column in range(12):  # Create empty cells across all columns
                empty_item = QTableWidgetItem()  # Create empty cell
                table.setItem(0, column, empty_item)  # Set cell in first row

        # Initialize board data table (1 column x 3 rows)
        for row in range(3):  # Create empty cells down first column
            empty_item = QTableWidgetItem()  # Create empty cell
            self.ui.board_data_table.setItem(row, 0, empty_item)  # Set cell in first column

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = wellVisualizationProcess()
    w.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())