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
from PyQt5.QtWidgets import QMainWindow, QApplication, QStyledItemDelegate, QHeaderView, QAbstractItemView, QWidget, QApplication, QMainWindow, QVBoxLayout, QWidget, QSizePolicy

class MultiBoldRowDelegate(QStyledItemDelegate):
    """
    A custom delegate class that applies bold formatting to specific rows in a Qt view.

    This delegate allows you to specify certain rows that should be displayed in bold.
    It's particularly useful when you want to emphasize specific rows in a QTableView
    or QListView.

    Attributes:
        bold_rows (set): A set containing the row indices that should be bold.

    Args:
        bold_rows (list or set): The row indices that should be displayed in bold.
        parent (QObject, optional): The parent object. Defaults to None.
    """

    def __init__(self, bold_rows, parent=None):
        """
        Initialize the MultiBoldRowDelegate.

        Args:
            bold_rows (list or set): The row indices that should be displayed in bold.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        # Step 1: Initialize the parent class
        super().__init__(parent)

        # Step 2: Convert bold_rows to a set for faster lookup and store it
        self.bold_rows = set(bold_rows)

    def initStyleOption(self, option, index):
        """
        Initialize the style options for the delegate.

        This method is called by the view when it needs to paint an item. It sets
        the font to bold if the current row is in the bold_rows set.

        Args:
            option (QStyleOptionViewItem): The style options for the item.
            index (QModelIndex): The model index of the item.
        """
        # Step 1: Call the parent class's initStyleOption method
        super().initStyleOption(option, index)

        # Step 2: Check if the current row should be bold
        if index.row() in self.bold_rows:
            # Step 3: If it should be bold, set the font to bold
            option.font.setBold(True)


class Well:
    def __init__(self, ui, well_name, df, df_dx):
        super().__init__()
        self.ui = ui
        well_df = df[df['display_name']==well_name]
        self.df_dx = df_dx
        self.specific_well_data_model = QStandardItemModel()
        self.ui.well_data_table_view.setModel(self.specific_well_data_model)
        self.ui.well_data_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.update_data_on_well_change(well_df)

    def update_data_on_well_change(self, df):
        # Handle multiple records by selecting most recent
        if len(df) > 1:
            current_data_row = df.sort_values(by='apdapproved_date', ascending=False).head(1)

        # Define data fields for each table
        row_1_data: List[str] = ['well_id', 'well_name', 'side_track', 'current_well_status', 'current_well_type',
                                 'apdreceived_date', 'apdreturn_date', 'apdapproved_date', 'apdext_date',
                                 'apdrescind_date', 'dry_spud', 'rotary_spud']

        row_2_data: List[str] = ['well_status_report', 'well_type_report', 'first_prod_date', 'wcrcompletion_date',
                                 'test_date', 'production_method', 'oil_rate', 'gas_rate', 'water_rate', 'dst',
                                 'dir_survey_run', 'completion_type']

        row_3_data: List[str] = ['gas_volume', 'oil_volume', 'well_age', 'last_production_if_shut_in',
                                 'months_shut_in', 'operator', 'md', 'tvd', 'perforation_md',
                                 'perforation_tvd', 'work_type', 'slant']
        # Setup table structure
        self.setup_table_data([row_1_data, row_2_data, row_3_data], df)

        # Populate each table with corresponding data
        for i, value in enumerate(row_1_data):
            print(df[value])
            self.ui.well_data_table_1.item(0, i).setText(str(df[value].item()))

        for i, value in enumerate(row_2_data):
            self.ui.well_data_table_2.item(0, i).setText(str(df[value].iloc[0]))

        for i, value in enumerate(row_3_data):
            self.ui.well_data_table_3.item(0, i).setText(str(df[value].iloc[0]))


    def setup_table_data(self, row_data: List[List[str]], df: pd.DataFrame):
        self.specific_well_data_model.setRowCount(0)  # Clear existing rows efficiently
        self.ui.well_data_table_view.setModel(self.specific_well_data_model)
        self.ui.well_data_table_view.setUpdatesEnabled(False)

        # Clear existing table data
        # Define modified headers for the third row
        row_3_data_edited: List[str] = ['gas_volume', 'oil_volume', 'well_age', 'last_production_if_shut_in',
            'months_shut_in', 'operator', 'md', 'tvd',
            'perforation_md', 'perforation_tvd', 'work_type', 'slant']

        # Initialize data structure for table population
        data_used_lst: List[List[str]] = [row_data[0], [], row_data[1], [], row_3_data_edited, []]
        # Populate data rows from DataFrame
        for i, value in enumerate(row_data[0]):
            data_used_lst[1].append(str(df[value].values[0]))
        for i, value in enumerate(row_data[1]):
            data_used_lst[3].append(str(df[value].values[0]))
        for i, value in enumerate(row_data[2]):
            data_used_lst[5].append(str(df[value].values[0]))

        # Create and append items to model
        for row in data_used_lst:
            items = [QStandardItem(str(item)) for item in row]
            self.specific_well_data_model.appendRow(items)

        self.ui.well_data_table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.well_data_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.well_data_table_view.verticalHeader().setVisible(False)
        self.ui.well_data_table_view.setShowGrid(True)
        self.ui.well_data_table_view.setUpdatesEnabled(True)
        self.ui.well_data_table_view.show()

        bold_rows: List[int] = [0, 2, 4]
        delegate = MultiBoldRowDelegate(bold_rows)
        self.ui.well_data_table_view.setItemDelegate(delegate)