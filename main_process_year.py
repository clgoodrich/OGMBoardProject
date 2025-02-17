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
from main_process_month import Month

class Year:
    def __init__(self, ui, year, df_year, df_dx):
        super().__init__()
        self.ui = ui
        self.df_dx = df_dx
        # df_year = df[df['Board_Year'] == year]
        self.populate_month_combo_box(df_year, year)
        self.ui.month_lst_combobox.activated.connect(lambda: self.do_this_when_month_combo_box_pressed(df_year))

    def populate_month_combo_box(self, well_data, selected_year):
        self.ui.month_lst_combobox.clear()
        self.ui.board_matter_lst_combobox.clear()
        self.ui.well_lst_combobox.clear()
        used_months: List[str] = well_data[
                well_data['Board_Year'] == selected_year
                ]['Docket_Month'].unique()
            # Create and populate model for month combo box
        model: QStandardItemModel = QStandardItemModel()
        for month in used_months:
            item: QStandardItem = QStandardItem(month)
            model.appendRow(item)
        # Update month combo box with new model
        self.ui.month_lst_combobox.setModel(model)


    def do_this_when_month_combo_box_pressed(self, df_year):
        selected_month: str = self.ui.month_lst_combobox.currentText()
        df_month = df_year[df_year['Docket_Month'] == selected_month]
        month_obj = Month(ui=self.ui, month_name=selected_month, df_month=df_month, df_dx = self.df_dx)


    # def when_year_combo_box_pressed_do_this(self, well_data):
    #     selected_year: str = self.ui.year_lst_combobox.currentText()
    #     # Filter and update class data members
    #     used_months: List[str] = well_data[
    #         well_data['Board_Year'] == selected_year
    #         ]['Docket_Month'].unique()
    #     df_year = well_data[well_data['Board_Year'] == selected_year]
    #     # Create and populate model for month combo box
    #     model: QStandardItemModel = QStandardItemModel()
    #     for month in used_months:
    #         print(month)
    #         item: QStandardItem = QStandardItem(month)
    #         model.appendRow(item)
    #         self.months_dict[month] = Month(ui = self.ui, month_name = month, df = df_year)
    #     # Update month combo box with new model
    #     self.ui.month_lst_combobox.setModel(model)
    #
    # #