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
from main_process_well import Well
from main_process_drawer import Drawer


class BoldDelegate(QStyledItemDelegate):
    """
    A custom delegate class that applies bold formatting to specific values in a Qt view.

    This delegate allows you to specify certain values that should be displayed in bold.
    It's particularly useful when you want to emphasize specific items based on their
    content in a QTableView or QListView.

    Attributes:
        bold_values (list or set): A collection of values that should be displayed in bold.

    Args:
        bold_values (list or set): The values that should be displayed in bold.
        parent (QObject, optional): The parent object. Defaults to None.
    """

    def __init__(self, bold_values, parent=None):
        """
        Initialize the BoldDelegate.

        Args:
            bold_values (list or set): The values that should be displayed in bold.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        # Step 1: Initialize the parent class
        super().__init__(parent)

        # Step 2: Store the bold_values for later use
        self.bold_values = bold_values

    def initStyleOption(self, option, index):
        """
        Initialize the style options for the delegate.

        This method is called by the view when it needs to paint an item. It sets
        the font to bold if the item's data matches any value in bold_values.

        Args:
            option (QStyleOptionViewItem): The style options for the item.
            index (QModelIndex): The model index of the item.
        """
        # Step 1: Call the parent class's initStyleOption method
        super().initStyleOption(option, index)

        # Step 2: Check if the current item's data should be bold
        if index.data() in self.bold_values:
            # Step 3: If it should be bold, get the current font
            font = option.font

            # Step 4: Set the font to bold
            font.setBold(True)

            # Step 5: Apply the modified font to the option
            option.font = font


class BoardMatter:
    def __init__(self, ui, board_matter, df_board_matters, df_dx):
        super().__init__()
        self.ui = ui
        self.df_dx = df_dx
        well_lst = self.create_well_lst(df_board_matters)
        self.populate_wells_combo_box(well_lst)
        self.make_wells_bold_in_combobox(df_board_matters)
        used_df_dx = df_dx[df_dx['APINumber'].isin(df_board_matters['WellID'].unique())]
        self.Drawer = Drawer(self.ui, used_df_dx, df_board_matters)
        self.ui.well_lst_combobox.activated.connect(lambda: self.do_this_when_wells_combo_box_pressed(df_board_matters))


    def make_wells_bold_in_combobox(self, df):
        masters_apds: List[str] = sorted(df[df['MainWell'] == 1]['DisplayName'].unique())
        delegate: QStyledItemDelegate = BoldDelegate(masters_apds)
        self.ui.well_lst_combobox.setItemDelegate(delegate)

    def create_well_lst(self, df):
        unique_count: List[str] = sorted(df['DisplayName'].unique())
        master_data: pd.DataFrame = df[df['MainWell'] == 1]
        masters_apds: List[str] = sorted(master_data['DisplayName'].unique())
        sorted_list: List[str] = sorted([x for x in unique_count if x not in masters_apds])
        well_lst: List[str] = masters_apds + sorted_list
        return well_lst

    def populate_wells_combo_box(self, well_lst):
        self.ui.well_lst_combobox.clear()
        model: QStandardItemModel = QStandardItemModel()
        for item_text in well_lst:
            item = QStandardItem(item_text)
            model.appendRow(item)
        self.ui.well_lst_combobox.setModel(model)

    def do_this_when_wells_combo_box_pressed(self, df):
        well_name: str = self.ui.well_lst_combobox.currentText()
        well_obj = Well(ui=self.ui, well_name=well_name, df=df, df_dx = self.df_dx)

