"""
WellVisualizerV2
Author: Colton Goodrich
Date: 8/31/2024

This module is a PyQt5 application that provides a graphical user interface (GUI) for
visualizing and analyzing well data, board matters, and related information from the
State of Utah, Division of Oil, Gas, and Mining.

The application features various functionalities, including:

- Displaying well data, such as location, status, production, and directional surveys,
  on 2D and 3D plots.
- Visualizing board matters, including sections, townships, and ranges, with the ability
  to highlight specific areas and view associated information.
- Rendering oil and gas field boundaries, along with field names.
- Generating production charts for selected wells, showing potential profit and
  cumulative production over time.
- Filtering and displaying wells based on various criteria, such as age, well type,
  status, and board docket information.
- Providing a tabular view of well data and allowing selection of individual wells
  for detailed analysis.

The module utilizes PyQt5 for the graphical user interface, along with libraries like
Matplotlib for plotting, Pandas for data manipulation, and various other dependencies
for geospatial data processing, database connectivity, and utility functions.

Classes:
- wellVisualizationProcess: The main class that inherits from QMainWindow and
  BoardMattersVisualizer. It handles the application's setup, data loading, GUI
  interactions, and visualization functionalities.
- ZoomPan: A utility class for enabling zoom and pan functionality on the plots.
- MultiBoldRowDelegate and BoldDelegate: Custom delegates for rendering bold text
  in specific rows or cells of the GUI tables.

Functions:
The module contains numerous functions for various tasks, such as data loading, processing,
filtering, plotting, and event handling. Some notable functions include:

- setupTables(): Sets up the tables in the GUI.
- zoom(): Handles zooming functionality on the 3D plot.
- comboBoxSetupYear(): Initializes the year combo box in the GUI.
- comboBoxSetupMonthWhenYearChanges(): Updates the month combo box based on the selected year.
- comboBoxSetupBoardWhenMonthChanges(): Updates the board matter combo box based on the
  selected month.
- comboBoxSetupWellsWhenDocketChanges(): Updates the well combo box based on the selected
  board docket.
- comboUpdateWhenWellChanges(): Updates the GUI with well-specific information based on
  the selected well.
- drawTSRPlat(): Renders the township, section, and range (TSR) plat on the 2D plot.
- manipulateTheDfDocketDataDependingOnCheckboxes(): Filters and updates the well data
  based on the selected checkboxes (e.g., well type, status).
- drawProductionGraphic(): Generates the production chart for the selected well.
- load_data2(): Loads and processes the initial data from the database.

The module serves as the main entry point for the well visualization application, providing
a comprehensive interface for exploring and analyzing well data, board matters, and
related information from the State of Utah, Division of Oil, Gas, and Mining.
"""
from typing import List
from PyQt5.QtWidgets import QLabel, QLayout
from PyQt5.QtCore import QAbstractItemModel
import pandas as pd
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath
from matplotlib.lines import Line2D
from typing import NoReturn
from pandas import concat
from typing import List, Union, Optional
from typing import Dict, Literal
from typing import List, Optional, Dict
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QComboBox
from typing import Tuple
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent
from typing import List
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QScrollArea, QLabel
from shapely.ops import unary_union
from sqlalchemy import create_engine
from matplotlib.patches import Polygon
from shapely.geometry import Point
from matplotlib.collections import PatchCollection
import itertools
import regex as re
import matplotlib.dates as mdates
from PyQt5.QtCore import QModelIndex, Qt
from matplotlib.textpath import TextPath
from matplotlib.patches import PathPatch
from WellVisualizerBoardMatters import BoardMattersVisualizer
import pandas as pd
import numpy as np
import geopandas as gpd
import time
from shapely.geometry import Polygon
import PyQt5
from matplotlib.ticker import ScalarFormatter, FuncFormatter
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.collections import LineCollection, PolyCollection
import matplotlib.pyplot as plt
from numpy import array, std
from pandas import to_numeric, read_sql, set_option, concat, to_datetime, options
import utm
import sqlite3
from PyQt5.QtWidgets import QMainWindow, QApplication, QStyledItemDelegate, QHeaderView
from datetime import datetime
import ModuleAgnostic as ma
from WellVisualizationV2 import Ui_Dialog
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from shapely import wkt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
"""Function and class designed for creating bold values in the self.ui.well_lst_combobox, specifically bolding wells of importance."""


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

# class MultiBoldRowDelegate(QStyledItemDelegate):
#     def __init__(self, bold_rows, parent=None):
#         super().__init__(parent)
#         self.bold_rows = set(bold_rows)  # Convert to set for faster lookup
#
#     def initStyleOption(self, option, index):
#         super().initStyleOption(option, index)
#         if index.row() in self.bold_rows:
#             option.font.setBold(True)
#
#
# class BoldDelegate(QStyledItemDelegate):
#     def __init__(self, bold_values, parent=None):
#         super().__init__(parent)
#         self.bold_values = bold_values
#
#     def initStyleOption(self, option, index):
#         super().initStyleOption(option, index)
#         if index.data() in self.bold_values:
#             font = option.font
#             font.setBold(True)
#             option.font = font
#

class wellVisualizationProcess(QMainWindow, BoardMattersVisualizer):
    checkbox_state_changed = PyQt5.QtCore.pyqtSignal(int, str, bool, PyQt5.QtGui.QColor)
    def __init__(self, flag=True):
        super().__init__()
        self.combo_box_data = None
        self.docket_ownership_data = None
        self.used_plat_codes = None
        self.df_adjacent_plats = None
        self.df_adjacent_fields = None
        set_option('display.max_columns', None)
        options.mode.chained_assignment = None
        self.field_labels = None
        self.field_centroids_lst = None
        self.df_shl = None
        self.all_wells_model = None
        self.df_all_wells_table = None
        self.df_BoardData = None
        self.df_BoardDataLinks = None
        self.currently_drilling_segments_3d = None
        self.currently_drilling_segments = None
        self.planned_segments_3d = None
        self.planned_segments = None
        self.drilled_df = None
        self.planned_df = None
        self.currently_drilling_df = None
        self.drilled_segments = None
        self.drilled_segments_3d = None
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.wellsLoc = []
        self.df = None
        self.df_year, self.df_month, self.df_docket, self.wellsUsedInBoardOrder, self.df_docket_data, self.df_prod, self.df_tsr = None, None, None, None, None, None, None
        self.used_sections, self.centroids_lst = None, None
        self.currently_used_lines = None
        self.drilled, self.planned, self.currently_drilling = (), (), ()
        self.drilled_xy, self.planned_xy, self.currently_drilling_xy = {}, {}, {}
        self.dx_df_asDrilled, self.dx_df_planned, self.dx_df, self.dx_data, self.df_plat = [], [], [], [], []
        self.planned_xy_2d, self.planned_xy_3d, self.drilled_xy_2d, self.drilled_xy_3d, self.currently_drilling_xy_2d, self.currently_drilling_xy_3d = [], [], [], [], [], []
        self.colors = ["#000000", "#004949", "#009292", "#ff6db6", "#ffb6db",
                       "#490092", "#006ddb", "#b66dff", "#6db6ff", "#b6dbff",
                       "#920000", "#924900", "#db6d00", "#24ff24", "#ffff6d",
                       "#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442"]
        self.type_checks = [self.ui.oil_well_check, self.ui.gas_well_check, self.ui.water_disposal_check, self.ui.dry_hole_check, self.ui.injection_check, self.ui.other_well_status_check]
        self.status_checks = [self.ui.shut_in_check, self.ui.pa_check, self.ui.producing_check, self.ui.drilling_status_check, self.ui.producing_check]

        self.ui.oil_well_check.setStyleSheet(f"""QCheckBox {{color: {'#c34c00'};}}""")
        self.ui.gas_well_check.setStyleSheet(f"""QCheckBox {{color: {'#f1aa00'};}}""")
        self.ui.water_disposal_check.setStyleSheet(f"""QCheckBox {{color: {'#0032b0'};}}""")
        self.ui.dry_hole_check.setStyleSheet(f"""QCheckBox {{color: {'#4f494b'};}}""")
        self.ui.injection_check.setStyleSheet(f"""QCheckBox {{color: {'#93ebff'};}}""")
        self.ui.other_well_status_check.setStyleSheet(f"""QCheckBox {{color: {'#985bee'};}}""")
        self.ui.producing_check.setStyleSheet(f"""QCheckBox {{color: {'#a2e361'};}}""")
        self.ui.shut_in_check.setStyleSheet(f"""QCheckBox {{color: {'#D2B48C'};}}""")
        self.ui.pa_check.setStyleSheet(f"""QCheckBox {{color: {'#4c2d77'};}}""")
        self.ui.drilling_status_check.setStyleSheet(f"""QCheckBox {{color: {'#001958'};}}""")
        self.ui.misc_well_type_check.setStyleSheet(f"""QCheckBox {{color: {'#4a7583'};}}""")

        self.specific_well_data_model = QStandardItemModel()
        self.operators_model = QStandardItemModel()
        self.owner_model = QStandardItemModel()
        self.agency_model = QStandardItemModel()

        # Create a scroll area for checkboxes
        self.checkbox_scroll_area = QScrollArea()
        self.checkbox_scroll_area.setWidgetResizable(True)
        self.checkbox_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.checkbox_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create a widget to hold the checkboxes
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_layout.setAlignment(Qt.AlignTop)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox_layout.setSpacing(2)

        # Set the checkbox container as the widget for the scroll area
        self.checkbox_scroll_area.setWidget(self.checkbox_container)

        # Create a horizontal layout to hold the checkbox scroll area and the existing layout
        new_layout = QHBoxLayout()
        new_layout.addWidget(self.checkbox_scroll_area)

        # Move the existing layout into the new horizontal layout
        existing_content = QWidget()
        existing_content.setLayout(self.ui.operators_layout)
        new_layout.addWidget(existing_content)
        self.owner_scroll_area = QScrollArea()
        self.owner_scroll_area.setWidgetResizable(True)
        self.owner_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.owner_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.owner_label_container = QWidget()
        self.owner_layout = QVBoxLayout(self.owner_label_container)
        self.owner_layout.setAlignment(Qt.AlignTop)
        self.owner_layout.setContentsMargins(0, 0, 0, 0)
        self.owner_layout.setSpacing(2)
        self.owner_scroll_area.setWidget(self.owner_label_container)
        new_layout_labels = QHBoxLayout()
        new_layout_labels.addWidget(self.owner_scroll_area)
        existing_content_owners = QWidget()
        existing_content_owners.setLayout(self.ui.owner_layout)
        new_layout_labels.addWidget(existing_content_owners)

        # Set the new layout for the operator_model_widget
        self.ui.operator_model_widget.setLayout(new_layout)
        self.ui.owner_model_widget.setLayout(new_layout_labels)

        self.checkbox_dict = {}  # Dictionary to store checkboxes
        self.operator_checkbox_list = []  # List to store checkboxes in order
        self.owner_label_list = []
        self.agency_label_list = []
        self.color_palette = self.generate_color_palette()
        self.line_style = '-'
        self.used_dockets, self.used_years, self.used_months = [], [], []
        self.figure_plat = plt.figure()
        self.canvas_plat = FigureCanvas(self.figure_plat)
        self.ax_plat = self.figure_plat.subplots()
        self.targeted_well_elevation = 0
        self.selected_well_2d_path = []
        self.selected_well_3d_path = []
        self.targeted_well = "00000000000"
        self.scale_factor = 1
        self.line_prod_1, self.line_prod_2, self.line_prod_1_cum, self.line_prod_2_cum = None, None, None, None
        """2d graphic"""
        """Generate the graphic, the canvas, etc"""
        self.figure2d = plt.figure()
        self.canvas2d = FigureCanvas(self.figure2d)
        self.ax2d = self.figure2d.subplots()
        self.ui.well_graphic_mp_2d_model.addWidget(self.canvas2d)

        """This button press event is triggered when you click on a visible well. It will highlight the well, load information to the well, etc"""
        self.canvas2d.mpl_connect('button_press_event', self.onClick2d)

        """Zoom function designed for zooming and panning. I stole this code from someone else and repurposed it."""
        self.zp = ZoomPan()
        self.zoom_fac = self.zp.zoom_factory(self.ax2d, 1.1)
        figPan = self.zp.pan_factory(self.ax2d)

        """These are specific empty plots and collections specifically for toggling visual data on and off. The idea is that as data selection changes and check boxes are activated or deactivated, 
        the code will dynamically update without having to fully redrawn the graphic."""
        self.spec_well_2d, = self.ax2d.plot([], [], c='purple', linewidth=3, linestyle=self.line_style, zorder=5)  ### graphing the selected well
        self.spec_vertical_wells_2d = self.ax2d.scatter([], [], c='purple', s=25, zorder=5, alpha=0.5)  ### graphic for specific vertical wells. I'm pretty sure this is deprecated.
        self.outlined_board_sections = PolyCollection([], zorder=3, alpha=0.2)  ### graphic for board matters. Will highlight specific sections.
        self.ownership_sections = PolyCollection([], zorder=1, alpha=0.2)  ### graphic for showing mineral ownership. Currently disabled while I troubleshoot the data
        self.ownership_sections_owner = PolyCollection([], zorder=1, alpha=0.8)  ### graphic for showing mineral ownership. Currently disabled while I troubleshoot the data
        self.ownership_sections_agency = PolyCollection([], zorder=1, alpha=0.8)  ### graphic for showing mineral ownership. Currently disabled while I troubleshoot the data
        self.field_sections = PolyCollection([], zorder=2, alpha=0.2)  ### graphic for showing oil fields.
        self.all_vertical_wells_2d = self.ax2d.scatter([], [], c='black', s=15, zorder=5)  ### graphic for all vertical wells. I'm pretty sure this is deprecated.
        self.all_wells_2d = LineCollection([], color='black', linewidth=0.5, linestyle=self.line_style, zorder=5)  ### graphic for all wells. I'm pretty sure this is deprecated.
        self.all_wells_2d_planned = LineCollection([], color='black', linewidth=0.5, linestyle="--", zorder=5)  ### graphic for all nonvertical wells that are currently planned but not being drilled.
        self.all_wells_2d_asdrilled = LineCollection([], color='black', linewidth=0.5, linestyle="-", zorder=5)  ### graphic for all nonvertical wells that are currently drilled
        self.all_wells_2d_current = LineCollection([], color='blue', linewidth=0.5, linestyle="dotted", zorder=5)  ### graphic for all nonvertical wells that are currently *being* drilled
        self.all_wells_plat_labels, self.all_wells_plat_labels_for_editing = [], []  ### empty lists for labels
        self.all_wells_2d_vertical_planned = self.ax2d.scatter([], [], c='black', s=5, zorder=5)  ### graphic for all vertical wells that are currently planned but not being drilled.
        self.all_wells_2d_vertical_asdrilled = self.ax2d.scatter([], [], c='black', s=5, zorder=5)  ### graphic for all vertical wells that are currently drilled
        self.all_wells_2d_vertical_current = self.ax2d.scatter([], [], c='blue', s=5, zorder=5)  ### graphic for all vertical wells that are currently *being* drilled
        self.plats_2d = LineCollection([], color='black', linewidth=2, linestyle=self.line_style, zorder=4, alpha=0.5)  ### graphic for mapping township and range section data
        self.plats_2d_main = LineCollection([], color='black', linewidth=4, linestyle=self.line_style, zorder=4)  ### graphic for mapping township and range section data
        self.plats_2d_1adjacent = LineCollection([], color='black', linewidth=2, linestyle=self.line_style, zorder=4, alpha=0.75)  ### graphic for mapping township and range section data
        self.plats_2d_2adjacent = LineCollection([], color='black', linewidth=2, linestyle=self.line_style, zorder=4, alpha=0.75)  ### graphic for mapping township and range section data
        self.all_wells_2d_operators = []
        self.all_wells_2d_operators_vertical = []
        self.labels_plats_2d_main = PatchCollection([
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red", zorder=1)
            for coord, text in zip([], [])], facecolors="black")  ### graphic for mapping township and range labels

        self.labels_plats_2d_1adjacent = PatchCollection([
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red", zorder=1)
            for coord, text in zip([], [])], facecolors="black")  ### graphic for mapping township and range labels

        self.labels_plats_2d_2adjacent = PatchCollection([
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red", zorder=1)
            for coord, text in zip([], [])], facecolors="black")  ### graphic for mapping township and range labels

        self.labels_plats_2d = PatchCollection([
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red", zorder=1)
            for coord, text in zip([], [])], facecolors="black")  ### graphic for mapping township and range labels

        self.labels_field = PatchCollection([
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red", zorder=1)
            for coord, text in zip([], [])], facecolors="black")  ### graphic for mapping oil and gas field labels
        self.ui.board_matter_files.setOpenExternalLinks(True)

        """Add collections to the axes for each display item"""
        self.ax2d.add_collection(self.outlined_board_sections)
        self.ax2d.add_collection(self.ownership_sections_owner)
        self.ax2d.add_collection(self.field_sections)
        self.ax2d.add_collection(self.ownership_sections_agency)
        self.ax2d.add_collection(self.all_wells_2d)
        self.ax2d.add_collection(self.all_wells_2d_planned)
        self.ax2d.add_collection(self.all_wells_2d_asdrilled)
        self.ax2d.add_collection(self.all_wells_2d_current)
        self.ax2d.add_collection(self.labels_plats_2d)
        self.ax2d.add_collection(self.labels_field)
        self.ax2d.add_collection(self.plats_2d)
        self.ax2d.add_collection(self.plats_2d_main)
        self.ax2d.add_collection(self.plats_2d_1adjacent)
        self.ax2d.add_collection(self.plats_2d_2adjacent)
        self.ax2d.add_collection(self.labels_plats_2d_main)
        self.ax2d.add_collection(self.labels_plats_2d_1adjacent)
        self.ax2d.add_collection(self.labels_plats_2d_2adjacent)
        self.ax2d.axis('equal')

        """3d Graphic"""
        """Generate the graphic, the canvas, etc"""
        self.all_wells_3d_data = []  # This should be filled with (x, y, z) tuples for each line
        self.fig3d, self.ax3d = plt.subplots(subplot_kw={'projection': '3d'})
        self.canvas3d = FigureCanvas(self.fig3d)
        self.ui.well_graphic_mp_3d_model.addWidget(self.canvas3d)
        self.ax3d.set_xlabel('Northing')
        self.ax3d.set_ylabel('Easting')
        self.ax3d.set_zlabel('TVD')
        self.ax3d.view_init(elev=20., azim=0, roll=0)
        self.centroid = [0, 0, 0]
        self.fig3d.canvas.mpl_connect('scroll_event', lambda event: self.zoom(event, self.ax3d, self.centroid, self.fig3d))

        """These are specific empty plots and collections specifically for toggling visual data on and off. The idea is that as data selection changes and check boxes are activated or deactivated, 
        the code will dynamically update without having to fully redrawn the graphic."""
        self.spec_well_3d, = self.ax3d.plot([], [], [], c='purple', linewidth=3, linestyle=self.line_style, zorder=5)  ### graph the selected well in 3d
        self.all_wells_3d = Line3DCollection([], colors='black', linewidth=0.5, linestyle='-', zorder=5)  ### graph all wells in 3d. Deprecated
        self.all_wells_3d_planned = Line3DCollection([], colors='black', linewidth=0.5, linestyle='dashed', zorder=5)  ### graph all planned wells in 3d
        self.all_wells_3d_asdrilled = Line3DCollection([], colors='black', linewidth=0.5, linestyle='solid', zorder=5)  ### graph all drilled wells in 3d
        self.all_wells_3d_current = Line3DCollection([], colors='blue', linewidth=0.5, linestyle='dotted', zorder=5)  ### graph all currently drilling wells in 3d

        """Add collections to the axes for each display item"""
        self.ax3d.add_collection(self.all_wells_3d)
        self.ax3d.add_collection(self.all_wells_3d_planned)
        self.ax3d.add_collection(self.all_wells_3d_asdrilled)
        self.ax3d.add_collection(self.all_wells_3d_current)

        """3d Graphic solo"""
        """Generate the graphic, the canvas, etc"""
        self.fig3d_solo, self.ax3d_solo = plt.subplots(subplot_kw={'projection': '3d'})
        self.canvas3d_solo = FigureCanvas(self.fig3d_solo)
        self.ui.well_graphic_mp_3d_model_2.addWidget(self.canvas3d_solo)
        self.ax3d_solo.set_xlabel('Northing')
        self.ax3d_solo.set_ylabel('Easting')
        self.ax3d_solo.set_zlabel('TVD')
        self.ax3d_solo.view_init(elev=20., azim=0, roll=0)
        self.spec_well_3d_solo, = self.ax3d_solo.plot([], [], [], c='purple', linewidth=3, linestyle=self.line_style, zorder=5)  ### graph the selected well in 3d
        self.fig3d_solo.canvas.mpl_connect('scroll_event', lambda event: self.zoom(event, self.ax3d_solo, self.centroid, self.fig3d_solo))

        """Prod Chart"""
        fig_width = 2.6  # Adjust as needed (361 pixels / 80 dpi ≈ 4.5 inches)
        fig_height = 1.4

        """Generate the two production figures on their seperate tabs. #1 examines potential profit, #2 examines production values"""
        self.fig_prod_1 = plt.figure(figsize=(fig_width, fig_height), constrained_layout=True)
        self.canvas_prod_1 = FigureCanvas(self.fig_prod_1)
        self.ax_prod_1 = self.fig_prod_1.add_subplot(111)
        self.ui.well_graphic_production_1.addWidget(self.canvas_prod_1)

        self.fig_prod_2 = plt.figure(figsize=(fig_width, fig_height), constrained_layout=True)
        self.canvas_prod_2 = FigureCanvas(self.fig_prod_2)
        self.ax_prod_2 = self.fig_prod_2.add_subplot(111)
        self.ui.well_graphic_production_2.addWidget(self.canvas_prod_2)
        self.ax_prod_1.set_xticks(self.ax_prod_1.get_xticks())
        self.ax_prod_1.set_xticklabels(self.ax_prod_1.get_xticklabels(), rotation=45, ha='right')
        self.ax_prod_2.set_xticks(self.ax_prod_2.get_xticks())
        self.ax_prod_2.set_xticklabels(self.ax_prod_2.get_xticklabels(), rotation=45, ha='right')
        # self.profit_line, = self.ax_prod_1.plot([], [], color='red', linewidth=2, zorder=1)  ## create the line graphic for profit
        # self.profit_line_cum, = self.ax_prod_1.plot([], [], color='black', linewidth=2, zorder=1)  ## create the line graphic for cumulative profit
        # self.prod_line, = self.ax_prod_2.plot([], [], color='blue', linewidth=2, zorder=1)  ## create the line graphic for production
        # self.prod_line_cum, = self.ax_prod_2.plot([], [], color='black', linewidth=2, zorder=1)  ## create the line graphic for cumulative production
        self.current_prod = 'oil'  ### create an initial default for oil. fig 1 can switch between gas and oil

        self.profit_line, = self.ax_prod_1.plot([], [], color='red', linewidth=2, zorder=1, label='Monthly Profit')
        self.profit_line_cum, = self.ax_prod_1.plot([], [], color='black', linewidth=2, zorder=1,
                                                    label='Cumulative Profit')
        self.prod_line, = self.ax_prod_2.plot([], [], color='blue', linewidth=2, zorder=1, label='Monthly Production')
        self.prod_line_cum, = self.ax_prod_2.plot([], [], color='black', linewidth=2, zorder=1,
                                                  label='Cumulative Production')


        """Board Data"""
        self.board_table_model = QStandardItemModel()
        self.all_wells_model = QStandardItemModel()
        self.used_plat_codes_for_boards = None
        """Assemble, organize, and produce the actual data from the .db item,"""
        self.table_model = QStandardItemModel()
        apd_data_dir = os.path.join(os.getcwd(), 'Board_DB.db')
        print(apd_data_dir)
        self.conn_db = sqlite3.connect(apd_data_dir)
        self.cursor_db = self.conn_db.cursor()

        # Create SQLAlchemy engine
        self.engine = create_engine(f'sqlite:///{apd_data_dir}')

        """Setup the tables so that they are prepped and ready to go."""
        self.setupTables()

        """Load the data to be used, process it, alter it, etc for usage"""
        self.load_data2()

        """Setup the initial data for the year. Presently only uses 2024"""
        self.comboBoxSetupYear()
        """Setting up the radio buttons. Specifically their ID because QT Designer won't #@$@#$ing do it. This is for ease of reference when clicking different radio buttons"""


        """This is for the radio buttons that correspond to the years currently being displayed. IE, when was the well drilled? Last 10 years, 5 years, 1 year, any time"""
        self.ui.drilling_within_button_group.setId(self.ui.radioButton_5, 0)
        self.ui.drilling_within_button_group.setId(self.ui.radioButton_6, 1)
        self.ui.drilling_within_button_group.setId(self.ui.radioButton_7, 2)
        self.ui.drilling_within_button_group.setId(self.ui.radioButton_8, 3)

        """This alters the board data display page. This will allow you to either search by the board orders themselves, or to search by board orders affecting the section"""
        self.ui.board_order_button_group.setId(self.ui.search_section_radio, 1)
        self.ui.board_order_button_group.setId(self.ui.search_board_radio, 2)

        """UI Elements connections. Run these when events happen. Go figure."""

        """Switch between gas and oil toggle"""
        self.ui.prod_button_group.buttonClicked.connect(self.drawProductionGraphic)

        """Switch between applicable years toggle"""
        self.ui.drilling_within_button_group.buttonClicked.connect(self.returnWellDataDependingOnParametersTest)

        """Toggle between displaying asDrilled wells"""
        self.ui.asdrilled_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying planned wells"""
        self.ui.planned_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying currently drilling wells"""
        self.ui.currently_drilling_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying oil wells"""
        self.ui.oil_well_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying gas wells"""
        self.ui.gas_well_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying water disposal wells"""
        self.ui.water_disposal_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying injection wells"""
        self.ui.injection_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying all other wells"""
        self.ui.other_well_status_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying shut-in wells"""
        self.ui.dry_hole_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying producing wells"""
        self.ui.producing_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying shut in wells"""
        self.ui.shut_in_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying plugged and abandoned wells"""
        self.ui.pa_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying drilling wells"""
        self.ui.drilling_status_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying all other status wells"""
        self.ui.misc_well_type_check.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying field names"""
        self.ui.field_names_checkbox.stateChanged.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

        """Toggle between displaying township and range sections"""
        self.ui.section_label_checkbox.stateChanged.connect(self.drawTSRPlat)

        """Do these when the combobox is changed via the user"""

        """Setup the month combo box when the user changes the relevant year"""
        self.ui.year_lst_combobox.activated.connect(self.comboBoxSetupMonthWhenYearChanges)

        """Setup the docket combo box when the user changes the relevant month"""
        self.ui.month_lst_combobox.activated.connect(self.comboBoxSetupBoardWhenMonthChanges)

        """Setup the wells combo box when the user changes the relevant docket data"""
        self.ui.board_matter_lst_combobox.activated.connect(self.comboBoxSetupWellsWhenDocketChanges)

        """Setup the displays and information when a well is selected"""
        self.ui.well_lst_combobox.activated.connect(self.comboUpdateWhenWellChanges)

        """Setup the Sections Combo Box for board orders (list sections)"""
        self.ui.sectionsBoardComboBox.activated.connect(self.setupBoardMattersGraphic)

        """Setup the board orders combo box dependent on what was used in the previous sections box"""
        self.ui.mattersBoardComboBox.activated.connect(self.updateBoardMatterDetails)

        """Setup the board orders box that just lists all board orders."""
        self.ui.board_matters_visible_combo.activated.connect(self.updateBoardMatterDetails)

        """Run this process when the radio button for searching for board orders is clicked or changed"""
        self.ui.board_order_button_group.buttonClicked.connect(self.prodButtonsActivate)

        """Run this when the table in All Wells is clicked. It should then highlight the appropriate wells. Note, nothing will happen if no wells are displayed"""
        self.ui.all_wells_qtableview.clicked.connect(self.on_row_clicked)

        self.ui.ownership_button_group.buttonClicked.connect(self.ownershipSelection)

        # self.ui.ownership_checkbox.stateChanged.connect(self.ownershipSelection)
        self.ui.ownership_checkbox.setEnabled(False)
        self.ui.section_ownership_radio_complex.setEnabled(False)
        self.ui.section_ownership_radio_simplified.setEnabled(False)
        self.ui.well_type_or_status_button_group.buttonClicked.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

    # def setupTables(self):
    #     """
    #     Initialize the tables in the user interface with empty QTableWidgetItems.
    #
    #     This function sets up three well data tables and one board data table
    #     by populating them with empty QTableWidgetItems. This prepares the tables
    #     for later data insertion.
    #     """
    #     # Set up the three well data tables
    #     for table in [self.ui.well_data_table_1, self.ui.well_data_table_2, self.ui.well_data_table_3]:
    #         # For each table, populate the first row with 12 empty items
    #         for column in range(12):
    #             # Create a new empty QTableWidgetItem
    #             empty_item = PyQt5.QtWidgets.QTableWidgetItem()
    #             # Set the empty item in the first row (row 0) and current column
    #             table.setItem(0, column, empty_item)
    #
    #     # Set up the board data table
    #     # Populate the first column of the board data table with 3 empty items
    #     for row in range(3):
    #         # Create a new empty QTableWidgetItem
    #         empty_item = PyQt5.QtWidgets.QTableWidgetItem()
    #         # Set the empty item in the current row and first column (column 0)
    #         self.ui.board_data_table.setItem(row, 0, empty_item)

    def setupTables(self) -> None:
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
        # Initialize the three well data tables with empty items
        well_tables: List[QTableWidget] = [
            self.ui.well_data_table_1,
            self.ui.well_data_table_2,
            self.ui.well_data_table_3
        ]

        # Populate well data tables
        for table in well_tables:
            for column in range(12):
                empty_item = QTableWidgetItem()
                table.setItem(0, column, empty_item)

        # Populate board data table's first column
        for row in range(3):
            empty_item = QTableWidgetItem()
            self.ui.board_data_table.setItem(row, 0, empty_item)

    def zoom(self, event: MouseEvent, ax: plt.Axes, centroid: Tuple[float, float, float],fig: Figure,) -> None:
        """
        Performs zooming operations on a 3D plot using mouse scroll events with a fixed centroid as anchor point.

        The zoom operation maintains the plot's center at the centroid while scaling the view
        based on mouse scroll direction. Scrolling up zooms in, while scrolling down zooms out.

        Args:
            event (MouseEvent): The matplotlib scroll event containing scroll direction
                information. The event.button will be either 'up' or 'down'.
            ax (plt.Axes): The 3D matplotlib axes object to be zoomed. Must be a 3D axes
                created with projection='3d'.
            centroid (Tuple[float, float, float]): The (x, y, z) coordinates representing
                the center point around which to zoom. This point remains fixed during zooming.
            fig (Figure): The matplotlib figure object containing the axes. Used for
                refreshing the display after zoom.

        Notes:
            - The zoom factor is fixed at 1.1 for zoom in and 0.9 for zoom out
            - The zoom is applied equally to all three axes to maintain aspect ratio
            - The centroid remains stationary during zoom operations
            - The method directly modifies the axes limits without returning any values

        Example:
            ```python
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            centroid = (0.0, 0.0, 0.0)

            def on_scroll(event):
                zoom(self, event, ax, centroid, fig)

            fig.canvas.mpl_connect('scroll_event', on_scroll)
            ```

        Warning:
            This method assumes the input axes is a 3D axes object. Using with 2D axes
            will result in AttributeError when accessing 3D-specific methods.
        """
        # Calculate the current zoom level by getting the range of the x-axis
        current_zoom: float = ax.get_xlim3d()[1] - ax.get_xlim3d()[0]

        # Determine zoom direction: zoom in (factor > 1) if scrolling up, else zoom out
        zoom_factor: float = 1.1 if event.button == 'up' else 0.9

        # Calculate the amount to zoom based on current zoom and zoom factor
        zoom_amount: float = (current_zoom * zoom_factor) / 2

        # Calculate new axis limits centered on the centroid
        new_xlim: list[float] = [centroid[0] - zoom_amount, centroid[0] + zoom_amount]
        new_ylim: list[float] = [centroid[1] - zoom_amount, centroid[1] + zoom_amount]
        new_zlim: list[float] = [centroid[2] - zoom_amount, centroid[2] + zoom_amount]

        # Apply the new limits to all three axes
        ax.set_xlim3d(new_xlim)
        ax.set_ylim3d(new_ylim)
        ax.set_zlim3d(new_zlim)

        # Redraw the plot to reflect the changes
        fig.canvas.draw_idle()

    # def zoom(self, event, ax, centroid, fig):
    #     """
    #     Perform zooming on a 3D plot based on a scroll event, using the centroid as an anchor.
    #
    #     Args:
    #     event (Event): The scroll event triggering the zoom.
    #     ax (Axes3D): The 3D axes object to be zoomed.
    #     centroid (tuple): The (x, y, z) coordinates of the centroid of the plot.
    #     fig (Figure): The figure containing the plot.
    #     """
    #     # Calculate the current zoom level by getting the range of the x-axis
    #     current_zoom = ax.get_xlim3d()[1] - ax.get_xlim3d()[0]
    #
    #     # Determine zoom direction: zoom in (factor > 1) if scrolling up, else zoom out
    #     zoom_factor = 1.1 if event.button == 'up' else 0.9
    #
    #     # Calculate the amount to zoom based on current zoom and zoom factor
    #     zoom_amount = (current_zoom * zoom_factor) / 2
    #
    #     # Calculate new axis limits centered on the centroid
    #     new_xlim = [centroid[0] - zoom_amount, centroid[0] + zoom_amount]
    #     new_ylim = [centroid[1] - zoom_amount, centroid[1] + zoom_amount]
    #     new_zlim = [centroid[2] - zoom_amount, centroid[2] + zoom_amount]
    #
    #     # Apply the new limits to all three axes
    #     ax.set_xlim3d(new_xlim)
    #     ax.set_ylim3d(new_ylim)
    #     ax.set_zlim3d(new_zlim)
    #
    #     # Redraw the plot to reflect the changes
    #     fig.canvas.draw_idle()
    def comboBoxSetupYear(self) -> None:
        """
        Sets up and populates the year combo box with available years.

        This method manages the year selection combo box by creating a new model and
        populating it with years from self.used_years. The function follows a clear,
        create, populate, and set pattern for managing the combo box contents.

        Args:
            self: Instance of the containing class, which must have:
                - self.used_years (List[str]): List of years to populate the combo box
                - self.ui.year_lst_combobox (QComboBox): The combo box widget to populate

        Returns:
            None

        Example:
            >>> self.used_years = ['2021', '2022', '2023']
            >>> self.comboBoxSetupYear()
            # Results in combo box populated with these three years

        Note:
            - Assumes self.used_years contains string representations of years
            - Clears existing items before populating new ones
            - Creates a fresh model instance for each setup
            - Does not maintain previous selection state

        Warning:
            Make sure self.used_years is initialized before calling this method,
            otherwise the combo box will be cleared but not populated.
        """
        # Clear any existing items from the year combo box
        self.ui.year_lst_combobox.clear()

        # Create a new QStandardItemModel to hold the year items
        model: QStandardItemModel = QStandardItemModel()

        # Iterate through each year in the self.used_years list
        for year in self.used_years:
            # Create a new QStandardItem for the current year
            item: QStandardItem = QStandardItem(str(year))
            # Add the year item to the model
            model.appendRow(item)

        # Set the created model as the model for the year combo box
        self.ui.year_lst_combobox.setModel(model)


    # def comboBoxSetupYear(self):
    #     """
    #     Set up the year combo box with available years.
    #
    #     This function populates the year combo box with the years stored in self.used_years.
    #     It creates a new model for the combo box and adds each year as an item.
    #     """
    #     # Clear any existing items from the year combo box
    #     self.ui.year_lst_combobox.clear()
    #
    #     # Create a new QStandardItemModel to hold the year items
    #     model = QStandardItemModel()
    #
    #     # Iterate through each year in the self.used_years list
    #     for year in self.used_years:
    #         # Create a new QStandardItem for the current year
    #         item = QStandardItem(year)
    #         # Add the year item to the model
    #         model.appendRow(item)
    #
    #     # Set the created model as the model for the year combo box
    #     self.ui.year_lst_combobox.setModel(model)
    def comboBoxSetupMonthWhenYearChanges(self) -> None:
        """
        Updates the month combo box when the selected year changes in the year combo box.
        This method is triggered when a new year is selected and handles the cascading updates
        of dependent combo boxes.

        The function performs the following operations:
        1. Clears related combo boxes (wells, board matters, months)
        2. Filters data for the selected year
        3. Populates the month combo box with available months for the selected year

        Args:
            self: The class instance containing UI elements and data

        Returns:
            None

        Side Effects:
            - Clears well_lst_combobox
            - Clears board_matter_lst_combobox
            - Clears month_lst_combobox
            - Updates self.used_months with filtered month values
            - Updates self.df_year with filtered year data
            - Populates month_lst_combobox with new values

        Example:
            # This method is typically connected to the year combo box's activated signal
            self.ui.year_lst_combobox.activated.connect(self.comboBoxSetupMonthWhenYearChanges)

        Notes:
            - This function is part of a cascading update system where changing the year
              triggers updates to months, board matters, and wells
            - The function relies on self.dx_data containing 'Board_Year' and 'Docket_Month' columns
            - Any existing visualization data is cleared when this function is called
        """
        # Clear dependent combo boxes to prevent stale data
        self.ui.well_lst_combobox.clear()
        self.ui.board_matter_lst_combobox.clear()
        self.ui.month_lst_combobox.clear()

        # Get selected year from combo box
        selected_year: str = self.ui.year_lst_combobox.currentText()

        # Filter and update class data members
        self.used_months: List[str] = self.dx_data[
            self.dx_data['Board_Year'] == selected_year
            ]['Docket_Month'].unique()

        self.df_year = self.dx_data[self.dx_data['Board_Year'] == selected_year]

        # Create and populate model for month combo box
        model: QStandardItemModel = QStandardItemModel()
        for month in self.used_months:
            item: QStandardItem = QStandardItem(month)
            model.appendRow(item)

        # Update month combo box with new model
        self.ui.month_lst_combobox.setModel(model)



    # def comboBoxSetupMonthWhenYearChanges(self):
    #     """
    #     Update the month combo box when the selected year changes.
    #     """
    #     # Clear the wells list combo box
    #     self.ui.well_lst_combobox.clear()
    #
    #     # Clear the board matters list combo box
    #     self.ui.board_matter_lst_combobox.clear()
    #
    #     # Clear the month list combo box
    #     self.ui.month_lst_combobox.clear()
    #
    #     # Get the currently selected year from the year combo box
    #     selected_year = self.ui.year_lst_combobox.currentText()
    #
    #     # Filter dx_data for the selected year and extract unique Docket_Month values
    #     self.used_months = self.dx_data[self.dx_data['Board_Year'] == selected_year]['Docket_Month'].unique()
    #
    #     # Create a new dataframe (df_year) containing only data for the selected year
    #     self.df_year = self.dx_data[self.dx_data['Board_Year'] == selected_year]
    #
    #     # Create a new QStandardItemModel to hold the month items
    #     model = QStandardItemModel()
    #
    #     # Iterate through each month in the used_months list
    #     for month in self.used_months:
    #         # Create a new QStandardItem for the current month
    #         item = QStandardItem(month)
    #         # Add the month item to the model
    #         model.appendRow(item)
    #
    #     # Set the created model as the model for the month combo box
    #     self.ui.month_lst_combobox.setModel(model)

    """Run this to setup the board matters tab when the month tab is changed. Ran when month_lst_combobox is used"""

    def comboBoxSetupBoardWhenMonthChanges(self) -> None:
        """
        Updates the board matters combo box when a new month is selected. This method manages
        the cascading update of UI elements and visualization data when the month selection changes.

        The function performs the following operations:
        1. Clears dependent UI elements (wells list and board matters)
        2. Clears visualization data from 2D and 3D displays
        3. Filters data based on selected year and month
        4. Populates board matters combo box with relevant dockets

        Args:
            self: The class instance containing UI elements and data members

        Returns:
            None

        Side Effects:
            - Clears well_lst_combobox
            - Clears board_matter_lst_combobox
            - Calls clearDataFrom2dAnd3d() to reset visualization
            - Updates self.df_month with filtered monthly data
            - Populates board_matter_lst_combobox with new values

        Example:
            # This method is typically connected to the month combo box's activated signal
            self.ui.month_lst_combobox.activated.connect(self.comboBoxSetupBoardWhenMonthChanges)

        Notes:
            - Part of a hierarchical combo box update system (Year -> Month -> Board Matter -> Wells)
            - Depends on self.dx_data containing 'Board_Year', 'Docket_Month', and 'Board_Docket' columns
            - Visualization data is cleared to prevent displaying outdated information
            - Maintains data consistency by clearing dependent selections
        """
        # Clear dependent UI elements and visualization data
        self.ui.well_lst_combobox.clear()
        self.ui.board_matter_lst_combobox.clear()
        self.clearDataFrom2dAnd3d()

        # Retrieve current selections from UI
        selected_year: str = self.ui.year_lst_combobox.currentText()
        selected_month: str = self.ui.month_lst_combobox.currentText()

        # Filter data for selected year and month
        df_month: pd.DataFrame = self.dx_data[
            (self.dx_data['Board_Year'] == selected_year) &
            (self.dx_data['Docket_Month'] == selected_month)
            ]

        # Update class member with filtered monthly data
        self.df_month = self.df_year[self.df_year['Docket_Month'] == selected_month]

        # Extract unique board matters and populate combo box
        board_matters: List[str] = df_month['Board_Docket'].unique()
        model: QStandardItemModel = QStandardItemModel()

        # Populate model with board matters
        for board_matter in board_matters:
            item: QStandardItem = QStandardItem(board_matter)
            model.appendRow(item)

        # Update board matters combo box with new model
        self.ui.board_matter_lst_combobox.setModel(model)


    # def comboBoxSetupBoardWhenMonthChanges(self):
    #     """
    #     Update the board matters combo box when the selected month changes.
    #     """
    #     # Clear the wells list combo box
    #     self.ui.well_lst_combobox.clear()
    #
    #     # Clear the board matters list combo box
    #     self.ui.board_matter_lst_combobox.clear()
    #
    #     # Clear 2D and 3D visualization data
    #     self.clearDataFrom2dAnd3d()
    #
    #     # Get the currently selected year and month from their respective combo boxes
    #     selected_year = self.ui.year_lst_combobox.currentText()
    #     selected_month = self.ui.month_lst_combobox.currentText()
    #
    #     # Filter dx_data for the selected year and month
    #     df_month = self.dx_data[
    #         (self.dx_data['Board_Year'] == selected_year) &
    #         (self.dx_data['Docket_Month'] == selected_month)
    #         ]
    #
    #     # Update df_month to contain only data for the selected month from df_year
    #     self.df_month = self.df_year[self.df_year['Docket_Month'] == selected_month]
    #
    #     # Extract unique Board_Docket values for the filtered data
    #     board_matters = df_month['Board_Docket'].unique()
    #
    #     # Create a new QStandardItemModel to hold the board matter items
    #     model = QStandardItemModel()
    #
    #     # Iterate through each board matter in the board_matters list
    #     for board_matter in board_matters:
    #         # Create a new QStandardItem for the current board matter
    #         item = QStandardItem(board_matter)
    #         # Add the board matter item to the model
    #         model.appendRow(item)
    #
    #     # Set the created model as the model for the board matters combo box
    #     self.ui.board_matter_lst_combobox.setModel(model)


    """Run this to setup the list of wells tab when the board matter tab is changed. It is run when the combobox board_matter_lst_combobox is used"""

    # def comboBoxSetupWellsWhenDocketChanges2(self):
    #     """
    #     Updates the well list and related data when a new board docket is selected.
    #     """
    #     # Clear all previous 2D and 3D data visualizations
    #     self.clearDataFrom2dAnd3d()
    #
    #     # Filter the main data (dx_data) for the selected board docket
    #     self.df_docket = self.dx_data[
    #         (self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText()) &
    #         (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText()) &
    #         (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())
    #         ]
    #
    #     # Get unique operators and update the operators model
    #     operators = sorted(self.df_docket['Operator'].unique())
    #     self.operators_model.clear()
    #     for row in operators:
    #         self.operators_model.appendRow(QStandardItem(row))
    #
    #     # Get unique well IDs and display names
    #     apis = self.df_docket['WellID'].unique()
    #     unique_count = sorted(self.df_docket['DisplayName'].unique())
    #
    #     # Filter directional survey data (dx_df) for wells in the current docket
    #     test_df = (self.dx_df[self.dx_df['APINumber'].isin(apis)]
    #                .drop_duplicates(keep='first')
    #                .sort_values(by=['APINumber', 'MeasuredDepth']))
    #
    #     # Update df_docket to include only wells with directional survey data
    #     unique_apis_with_data = test_df['APINumber'].unique()
    #     self.df_docket = self.df_docket[self.df_docket['WellID'].isin(unique_apis_with_data)]
    #
    #     # Identify main wells (MainWell == 1) and create a final sorted list of wells
    #     master_data = self.df_docket[self.df_docket['MainWell'] == 1]
    #     masters_apds = sorted(master_data['DisplayName'].unique())
    #     sorted_list = sorted([x for x in unique_count if x not in masters_apds])
    #     final_list = masters_apds + sorted_list
    #
    #     # Update the "All Wells" table with the final list of wells
    #     self.fillInAllWellsTable(final_list)
    #
    #     # Update the well list combo box
    #     self.ui.well_lst_combobox.clear()
    #     model = QStandardItemModel()
    #     for item_text in final_list:
    #         item = QStandardItem(item_text)
    #         model.appendRow(item)
    #     self.ui.well_lst_combobox.setModel(model)
    #
    #     # Make main wells bold in the combo box
    #     delegate = BoldDelegate(masters_apds)
    #     self.ui.well_lst_combobox.setItemDelegate(delegate)
    #
    #     # Update 2D data (relative elevation, targeted data, etc.)
    #     self.update2dWhenDocketChanges()
    #
    #     # Create a new dataframe with well parameters for the current docket
    #     self.df_docket_data = self.returnWellsWithParameters()
    #
    #     # Set the axes limits for the plots based on the current data
    #     self.setAxesLimits()
    #
    #     # Prepare the data for filtering based on well age parameters
    #     self.setupDataForBoardDrillingInformation()
    #
    #     # Update 3D view if data is available
    #     if self.drilled_segments_3d:
    #         self.centroid, std_vals = self.calculate_centroid_np(self.drilled_segments_3d)
    #         new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
    #         new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
    #         new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]
    #         self.ax3d.set_xlim3d(new_xlim)
    #         self.ax3d.set_ylim3d(new_ylim)
    #         self.ax3d.set_zlim3d(new_zlim)
    #
    #     # Generate section data for the 2D model
    #     self.used_sections, self.all_wells_plat_labels = self.draw2dModelSections()
    #
    #     # Color in the oil and gas fields on the plot
    #     self.colorInFields()
    #
    #     # Update the checkboxes for well types and statuses
    #     self.update_checkboxes()
    #
    #     # Calculate centroids for each section (used for labeling)
    #     self.centroids_lst = []
    #     for i, val in enumerate(self.used_sections):
    #         self.used_sections[i].append(self.used_sections[i][0])
    #         centroid = Polygon(self.used_sections[i]).centroid
    #         self.centroids_lst.append(centroid)
    #
    #     # Update the well data based on the current parameter settings
    #     self.returnWellDataDependingOnParametersTest()
    #
    #     # Draw the Township, Section, and Range (TSR) plat on the 2D plot
    #     self.drawTSRPlat()
    #
    #     # Process and display ownership data
    #     self.colorInOwnership()
    #     self.ownershipSelection()
    #
    #     # Update the owner and agency models with the current data
    #     owners = sorted(self.docket_ownership_data['owner'].unique())
    #     agencies = sorted(self.docket_ownership_data['state_legend'].unique())
    #     self.owner_model.clear()
    #     self.agency_model.clear()
    #     for row in owners:
    #         self.owner_model.appendRow(QStandardItem(row))
    #     for row in agencies:
    #         self.agency_model.appendRow(QStandardItem(row))
    #
    #     # Update the ownership checkboxes in the UI
    #     self.updateOwnershipCheckboxes()
    #
    #     # Redraw the 2D canvas to reflect all changes
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()
    #
    #     # Update the combo_box_data attribute with the first 10 characters of each well name
    #     self.combo_box_data = [self.ui.well_lst_combobox.itemText(i)[:10] for i in
    #                            range(self.ui.well_lst_combobox.count())]
    #
    #     # Activate the production buttons in the UI
    #     self.prodButtonsActivate()
    #
    #     # Define the main well statuses and types for counting
    #     main_statuses = ['Plugged & Abandoned', 'Producing', 'Shut-in', 'Drilling']
    #     other_statuses = [
    #         'Location Abandoned - APD rescinded', 'Returned APD (Unapproved)',
    #         'Approved Permit', 'Active', 'Drilling Operations Suspended',
    #         'New Permit', 'Inactive', 'Temporarily-abandoned', 'Test Well or Monitor Well'
    #     ]
    #     main_types = ['Unknown', 'Oil Well', 'Dry Hole', 'Gas Well', 'Test Well', 'Water Source Well']
    #     merged_types = {
    #         'Injection Well': ['Water Injection Well', 'Gas Injection Well'],
    #         'Disposal Well': ['Water Disposal Well', 'Oil Well/Water Disposal Well'],
    #         'Other': ['Test Well', 'Water Source Well', 'Unknown']
    #     }
    #
    #     # Update the counters for well statuses and types in the UI
    #     self.getCountersForStatus(main_statuses, other_statuses)
    #     self.getCountersForType(main_types, merged_types)
    #
    # def comboBoxSetupWellsWhenDocketChanges3(self):
    #     """
    #     Updates the well list and related data when a new board docket is selected.
    #     """
    #     self.clearDataFrom2dAnd3d()
    #     self.filterMainDataForDocket()
    #     self.updateOperatorsModel()
    #     self.updateWellIDsAndDisplayNames()
    #     self.filterDirectionalSurveyData()
    #     self.filterDocketForDirectionalSurveyData()
    #     self.createFinalSortedListOfWells()
    #     # self.updateAllWellsTable()
    #     self.fillInAllWellsTable(self.final_list)
    #     self.updateWellListComboBox()
    #     self.makeMainWellsBoldInComboBox()
    #     self.update2dWhenDocketChanges()
    #     # self.createDocketDataFrameWithParameters()
    #     self.df_docket_data = self.returnWellsWithParameters()
    #     self.setAxesLimits()
    #     # self.prepareDataForBoardDrillingInfo()
    #     self.setupDataForBoardDrillingInformation()
    #     self.update3dViewIfAvailable()
    #     # self.generateSectionDataFor2DModel()
    #     self.used_sections, self.all_wells_plat_labels = self.draw2dModelSections()
    #     self.colorInFields()
    #     # self.updateWellTypeAndStatusCheckboxes()
    #     self.update_checkboxes()
    #     self.calculateCentroidsForSections()
    #     # self.updateWellDataBasedOnParameters()
    #     self.returnWellDataDependingOnParametersTest()
    #     self.drawTSRPlat()
    #     # self.processAndDisplayOwnershipData()
    #     self.colorInOwnership()
    #     self.ownershipSelection()
    #     self.updateOwnerAndAgencyModels()
    #     self.updateOwnershipCheckboxes()
    #     # self.redraw2DCanvas()
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()
    #     self.updateComboBoxData()
    #     self.combo_box_data = [self.ui.well_lst_combobox.itemText(i)[:10] for i in
    #                            range(self.ui.well_lst_combobox.count())]
    #     # self.activateProductionButtons()
    #     self.prodButtonsActivate()
    #
    #     self.updateCountersForStatusAndType()

    def comboBoxSetupWellsWhenDocketChanges(self) -> None:
        """
        Updates the well list and related data when a new board docket is selected.
        This is a comprehensive update function that handles all aspects of well data
        display and management when the user selects a different docket.

        The function performs the following major operations:
        1. Clears existing data
        2. Updates well information and displays
        3. Processes directional survey data
        4. Updates UI elements and visualizations
        5. Handles ownership and agency information
        6. Updates status and type counters

        Note:
            This is a complex operation that triggers multiple UI updates and data
            recalculations. May cause temporary UI freezing for large datasets.

        Raises:
            ValueError: If required docket data is missing or malformed
            AttributeError: If UI components are not properly initialized
        """
        # Clear and filter data
        self.clearDataFrom2dAnd3d()
        self.filterMainDataForDocket()

        # Update models and displays
        self.updateOperatorsModel()
        self.updateWellIDsAndDisplayNames()

        # Process directional survey data
        self.filterDirectionalSurveyData()
        self.filterDocketForDirectionalSurveyData()

        # Update well lists and displays
        self.createFinalSortedListOfWells()
        # self.updateAllWellsTable()
        self.fillInAllWellsTable(self.final_list)
        self.updateWellListComboBox()
        self.makeMainWellsBoldInComboBox()

        # Update visualizations
        self.update2dWhenDocketChanges()
        # self.createDocketDataFrameWithParameters()
        self.df_docket_data = self.returnWellsWithParameters()
        self.setAxesLimits()

        # Process and update additional data
        # self.prepareDataForBoardDrillingInfo()
        self.setupDataForBoardDrillingInformation()
        self.update3dViewIfAvailable()
        # self.generateSectionDataFor2DModel()
        self.used_sections, self.all_wells_plat_labels = self.draw2dModelSections()
        self.colorInFields()

        # Update UI elements and ownership data
        # self.updateWellTypeAndStatusCheckboxes()
        self.update_checkboxes()
        self.calculateCentroidsForSections()
        # self.updateWellDataBasedOnParameters()
        self.returnWellDataDependingOnParametersTest()
        self.drawTSRPlat()
        # self.processAndDisplayOwnershipData()
        self.colorInOwnership()
        self.ownershipSelection()
        self.updateOwnerAndAgencyModels()
        self.updateOwnershipCheckboxes()

        # Finalize updates
        # self.redraw2DCanvas()
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()
        self.updateComboBoxData()
        # self.activateProductionButtons()
        self.prodButtonsActivate()

        self.updateCountersForStatusAndType()
    # Helper functions below

    # def filterMainDataForDocket2(self):
    #     self.df_docket = self.dx_data[
    #         (self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText()) &
    #         (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText()) &
    #         (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())
    #         ]
    def filterMainDataForDocket(self) -> None:
        """
        Filters the main data frame to only include records matching the currently
        selected year, month, and board docket.

        The filtered data is stored in self.df_docket for further processing.
        """
        self.df_docket = self.dx_data[
            (self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText()) &
            (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText()) &
            (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())
        ]

    # def updateOperatorsModel2(self):
    #     operators = sorted(self.df_docket['Operator'].unique())
    #     self.operators_model.clear()
    #     for row in operators:
    #         self.operators_model.appendRow(QStandardItem(row))

    def updateOperatorsModel(self) -> None:
        """
        Updates the operators model with sorted unique operator names from the current docket.

        This function performs the following operations:
        1. Extracts unique operator names from the current docket DataFrame
        2. Sorts them alphabetically
        3. Clears the existing operators model
        4. Populates the model with new operator items

        The operators model is used to populate UI elements like combo boxes and checkbox lists
        that display operator information.

        Attributes:
            self.df_docket (pd.DataFrame): DataFrame containing the current docket information
            self.operators_model (QStandardItemModel): Model storing operator information

        Note:
            - This function should be called whenever the docket selection changes
            - The operators_model must be properly initialized before calling this function
            - Operators are displayed in alphabetical order for easier navigation

        Raises:
            AttributeError: If self.df_docket or self.operators_model is not initialized
            KeyError: If 'Operator' column is missing from df_docket
        """
        # Extract and sort unique operators from the current docket
        operators: List[str] = sorted(self.df_docket['Operator'].unique())

        # Clear existing items from the operators model
        self.operators_model.clear()

        # Add each operator as a new item in the model
        for row in operators:
            # Create a new standard item for each operator
            item = QStandardItem(row)
            # Append the item to the model
            self.operators_model.appendRow(item)


    # def updateWellIDsAndDisplayNames2(self):
    #     self.apis = self.df_docket['WellID'].unique()
    #     self.unique_count = sorted(self.df_docket['DisplayName'].unique())



    def updateWellIDsAndDisplayNames(self) -> None:
        """
        Updates the well identifiers and display names from the current docket data.

        Extracts and stores unique well IDs and display names from the current docket.
        Well IDs are stored as-is while display names are sorted alphabetically.

        Attributes:
            self.apis (Set[str]): Set of unique well API numbers from the docket
            self.unique_count (List[str]): Sorted list of unique well display names
            self.df_docket (pd.DataFrame): DataFrame containing current docket data

        Note:
            - The APIs are used for matching wells across different data sources
            - Display names are sorted for consistent presentation in the UI
            - This method should be called whenever the docket selection changes

        Side Effects:
            - Updates self.apis with unique WellID values
            - Updates self.unique_count with sorted DisplayName values

        Raises:
            KeyError: If 'WellID' or 'DisplayName' columns are missing from df_docket
            AttributeError: If self.df_docket is not properly initialized
        """
        # Extract unique well IDs (API numbers)
        self.apis: Set[str] = self.df_docket['WellID'].unique()

        # Extract and sort unique display names
        self.unique_count: List[str] = sorted(self.df_docket['DisplayName'].unique())


    # def filterDirectionalSurveyData(self):
    #     self.test_df = (self.dx_df[self.dx_df['APINumber'].isin(self.apis)]
    #                     .drop_duplicates(keep='first')
    #                     .sort_values(by=['APINumber', 'MeasuredDepth']))

    def filterDirectionalSurveyData(self) -> None:
        """
        Filters and processes directional survey data for wells in the current docket.

        This function filters the directional survey DataFrame (dx_df) to include only
        wells that match the API numbers from the current docket. The resulting data is
        cleaned by removing duplicates and sorted by API number and measured depth.

        Attributes:
            self.dx_df (pd.DataFrame): Source DataFrame containing directional survey data
            self.apis (Set[str]): Set of API numbers from the current docket
            self.test_df (pd.DataFrame): Filtered and processed directional survey data

        Operations performed:
        1. Filters dx_df to include only rows matching current API numbers
        2. Removes duplicate entries, keeping first occurrence
        3. Sorts data by API number and measured depth

        Note:
            - This function is called during docket changes to update well trajectory data
            - The filtered data is used for well path visualization in 2D and 3D views
            - Measured depth sorting is crucial for proper well trajectory display

        Side Effects:
            Updates self.test_df with filtered and sorted directional survey data

        Raises:
            KeyError: If required columns ('APINumber', 'MeasuredDepth') are missing
            AttributeError: If self.dx_df or self.apis are not properly initialized
        """
        self.test_df: pd.DataFrame = (
            # Filter for wells in current docket
            self.dx_df[self.dx_df['APINumber'].isin(self.apis)]
            # Remove duplicate entries
            .drop_duplicates(keep='first')
            # Sort by API number and depth for proper trajectory ordering
            .sort_values(by=['APINumber', 'MeasuredDepth'])
        )
    def filterDocketForDirectionalSurveyData2(self):
        unique_apis_with_data = self.test_df['APINumber'].unique()
        self.df_docket = self.df_docket[self.df_docket['WellID'].isin(unique_apis_with_data)]


    def filterDocketForDirectionalSurveyData(self) -> None:
        """
        Filters the docket DataFrame to include only wells that have directional survey data.

        This function identifies wells with existing directional survey data in test_df and
        updates the docket DataFrame to include only those wells. This ensures consistency
        between the directional survey data and the docket information for visualization
        and analysis purposes.

        Attributes:
            self.test_df (pd.DataFrame): DataFrame containing processed directional survey data
            self.df_docket (pd.DataFrame): DataFrame containing well docket information

        Operations:
        1. Extracts unique API numbers from wells with directional survey data
        2. Filters docket DataFrame to retain only wells with survey data

        Note:
            - This function should be called after filterDirectionalSurveyData()
            - Maintains data consistency for well visualization and analysis
            - Wells without directional survey data are excluded from the docket

        Side Effects:
            - Modifies self.df_docket to contain only wells with directional survey data

        Raises:
            AttributeError: If self.test_df or self.df_docket is not initialized
            KeyError: If 'APINumber' column is missing from test_df or 'WellID' from df_docket
        """
        # Get unique API numbers from wells with directional survey data
        unique_apis_with_data: Set[str] = self.test_df['APINumber'].unique()

        # Filter docket to include only wells that have directional survey data
        self.df_docket = self.df_docket[self.df_docket['WellID'].isin(unique_apis_with_data)]


    # def createFinalSortedListOfWells2(self):
    #     master_data = self.df_docket[self.df_docket['MainWell'] == 1]
    #     masters_apds = sorted(master_data['DisplayName'].unique())
    #     sorted_list = sorted([x for x in self.unique_count if x not in masters_apds])
    #     self.final_list = masters_apds + sorted_list

    def createFinalSortedListOfWells(self) -> None:
        """
        Creates a sorted list of wells with master wells prioritized at the beginning.

        This function performs the following operations:
        1. Identifies master wells from the docket
        2. Creates a sorted list of master well display names
        3. Creates a sorted list of non-master wells
        4. Combines both lists maintaining master wells at the start

        Attributes:
            self.df_docket (pd.DataFrame): DataFrame containing well information
            self.unique_count (List[str]): List of all unique well display names
            self.final_list (List[str]): Resulting sorted list with master wells first

        Note:
            - Master wells are identified by 'MainWell' column value of 1
            - Display names are used for well identification in UI components
            - Order is preserved for consistent UI presentation

        Side Effects:
            - Updates self.final_list with the combined sorted well list

        Raises:
            KeyError: If 'MainWell' or 'DisplayName' columns are missing from df_docket
            AttributeError: If self.df_docket or self.unique_count is not initialized
        """
        # Filter and extract master wells from the docket
        master_data: pd.DataFrame = self.df_docket[self.df_docket['MainWell'] == 1]

        # Create sorted list of master well display names
        masters_apds: List[str] = sorted(master_data['DisplayName'].unique())

        # Create sorted list of non-master wells
        sorted_list: List[str] = sorted([x for x in self.unique_count if x not in masters_apds])

        # Combine master wells and other wells into final sorted list
        self.final_list: List[str] = masters_apds + sorted_list


    # def updateAllWellsTable(self):
    #     self.fillInAllWellsTable(self.final_list)

    # def updateWellListComboBox2(self):
    #     self.ui.well_lst_combobox.clear()
    #     model = QStandardItemModel()
    #     for item_text in self.final_list:
    #         item = QStandardItem(item_text)
    #         model.appendRow(item)
    #     self.ui.well_lst_combobox.setModel(model)

    def updateWellListComboBox(self) -> None:
        """
        Updates the well list combo box with the current final list of wells.

        This function refreshes the well selection combo box in the UI by:
        1. Clearing existing items
        2. Creating a new item model
        3. Populating the model with well names from final_list
        4. Setting the updated model to the combo box

        Attributes:
            self.ui.well_lst_combobox (QComboBox): UI combo box for well selection
            self.final_list (List[str]): Sorted list of well names to display

        Note:
            - This function should be called after final_list is updated
            - Wells are displayed in the order specified in final_list
            - The combo box allows user selection of wells for detailed view
            - This update affects the well selection UI component only

        Side Effects:
            - Clears all existing items in the well list combo box
            - Updates the combo box with new well names
            - Maintains any existing delegate settings (e.g., bold formatting)

        Raises:
            AttributeError: If self.final_list or self.ui.well_lst_combobox is not initialized
        """
        # Clear existing items from the combo box
        self.ui.well_lst_combobox.clear()

        # Create new model for the combo box
        model: QStandardItemModel = QStandardItemModel()

        # Add each well from final_list to the model
        for item_text in self.final_list:
            item = QStandardItem(item_text)
            model.appendRow(item)

        # Set the updated model to the combo box
        self.ui.well_lst_combobox.setModel(model)

    def makeMainWellsBoldInComboBox(self) -> None:
        """
        Applies bold formatting to main wells in the well list combo box.

        This function identifies main wells from the docket and applies bold styling
        to make them visually distinct in the well selection combo box. Main wells
        are those with MainWell=1 in the docket data.

        Attributes:
            self.df_docket (pd.DataFrame): DataFrame containing well information
            self.ui.well_lst_combobox (QComboBox): UI combo box for well selection

        Operations:
        1. Extracts and sorts display names of main wells
        2. Creates a custom delegate for bold formatting
        3. Applies the delegate to the combo box

        Note:
            - Main wells are identified by 'MainWell' column value of 1
            - Bold formatting helps users quickly identify primary wells
            - The delegate preserves other combo box functionality
            - This styling persists until a new delegate is set

        Side Effects:
            - Updates the item delegate of the well list combo box
            - Changes the visual appearance of main well entries

        Raises:
            KeyError: If 'MainWell' or 'DisplayName' columns are missing from df_docket
            AttributeError: If self.df_docket or self.ui.well_lst_combobox is not initialized
        """
        # Extract and sort display names of main wells
        masters_apds: List[str] = sorted(
            self.df_docket[self.df_docket['MainWell'] == 1]['DisplayName'].unique()
        )

        # Create delegate for bold formatting of main wells
        delegate: QStyledItemDelegate = BoldDelegate(masters_apds)

        # Apply the delegate to the combo box
        self.ui.well_lst_combobox.setItemDelegate(delegate)

    # def makeMainWellsBoldInComboBox2(self):
    #     masters_apds = sorted(self.df_docket[self.df_docket['MainWell'] == 1]['DisplayName'].unique())
    #     delegate = BoldDelegate(masters_apds)
    #     self.ui.well_lst_combobox.setItemDelegate(delegate)

    # def createDocketDataFrameWithParameters(self):
    #     self.df_docket_data = self.returnWellsWithParameters()

    # def prepareDataForBoardDrillingInfo(self):
    #     self.setupDataForBoardDrillingInformation()
    def update3dViewIfAvailable(self) -> None:
        """
        Updates the 3D view boundaries based on the centroid of drilled segments.

        If 3D segment data is available, this function:
        1. Calculates the centroid of all drilled segments
        2. Sets new view boundaries extending 10,000 units in each direction
        3. Updates the 3D axis limits to center on the well segments

        Attributes:
            self.drilled_segments_3d (np.ndarray): Array of 3D coordinates for well segments
            self.ax3d (Axes3D): The 3D matplotlib axes object for well visualization
            self.centroid (np.ndarray): Calculated center point of all well segments

        Note:
            - Function only executes if drilled_segments_3d contains data
            - View boundaries are set symmetrically around the centroid
            - The ±10,000 unit range provides consistent zoom level across wells
            - Visualization updates immediately when called

        Side Effects:
            - Updates self.centroid with new calculated center point
            - Modifies 3D axis limits of the visualization
            - Changes the visible range of the 3D well plot

        Raises:
            AttributeError: If self.ax3d or self.drilled_segments_3d is not initialized
            ValueError: If drilled_segments_3d contains invalid coordinate data
        """
        # Only update if 3D segment data exists
        if self.drilled_segments_3d:
            # Calculate centroid and standard deviation of well segments
            self.centroid: np.ndarray
            std_vals: np.ndarray
            self.centroid, std_vals = self.calculate_centroid_np(self.drilled_segments_3d)

            # Define new view boundaries centered on centroid
            new_xlim: List[float] = [self.centroid[0] - 10000, self.centroid[0] + 10000]
            new_ylim: List[float] = [self.centroid[1] - 10000, self.centroid[1] + 10000]
            new_zlim: List[float] = [self.centroid[2] - 10000, self.centroid[2] + 10000]

            # Update 3D axis limits with new boundaries
            self.ax3d.set_xlim3d(new_xlim)
            self.ax3d.set_ylim3d(new_ylim)
            self.ax3d.set_zlim3d(new_zlim)

    # def update3dViewIfAvailable2(self):
    #     if self.drilled_segments_3d:
    #         self.centroid, std_vals = self.calculate_centroid_np(self.drilled_segments_3d)
    #         new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
    #         new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
    #         new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]
    #         self.ax3d.set_xlim3d(new_xlim)
    #         self.ax3d.set_ylim3d(new_ylim)
    #         self.ax3d.set_zlim3d(new_zlim)

    # def generateSectionDataFor2DModel(self):
    #     self.used_sections, self.all_wells_plat_labels = self.draw2dModelSections()

    # def updateWellTypeAndStatusCheckboxes(self):
    #     self.update_checkboxes()


    def calculateCentroidsForSections(self) -> None:
        """
        Calculates centroids for each well section polygon.

        Processes each section in the used_sections list by:
        1. Closing each polygon by appending first point to end
        2. Computing the geometric centroid of each section
        3. Storing centroids for later use in visualization

        Attributes:
            self.used_sections (List[List[Tuple[float, float]]]): List of section coordinates
            self.centroids_lst (List[Point]): List to store computed centroids

        Note:
            - Sections must be valid polygons for centroid calculation
            - Centroids are used for section labeling and visualization
            - Each section is automatically closed by connecting last point to first

        Side Effects:
            - Modifies self.used_sections by closing each polygon
            - Populates self.centroids_lst with computed centroids

        Raises:
            ValueError: If any section contains invalid polygon coordinates
            AttributeError: If self.used_sections is not properly initialized
        """
        # Initialize empty list to store centroids
        self.centroids_lst: List[Point] = []

        # Process each section in used_sections
        for i, val in enumerate(self.used_sections):
            # Close the polygon by appending first point to end
            self.used_sections[i].append(self.used_sections[i][0])

            # Calculate and store centroid for the section
            centroid: Point = Polygon(self.used_sections[i]).centroid
            self.centroids_lst.append(centroid)

    # def calculateCentroidsForSections2(self):
    #     self.centroids_lst = []
    #     for i, val in enumerate(self.used_sections):
    #         self.used_sections[i].append(self.used_sections[i][0])
    #         centroid = Polygon(self.used_sections[i]).centroid
    #         self.centroids_lst.append(centroid)

    # def updateWellDataBasedOnParameters(self):
    #     self.returnWellDataDependingOnParametersTest()

    # def processAndDisplayOwnershipData(self):
    #     self.colorInOwnership()
    #     self.ownershipSelection()
    def updateOwnerAndAgencyModels(self) -> None:
        """
        Updates the owner and agency list models with unique values from docket ownership data.

        This function refreshes two separate list models by:
        1. Extracting and sorting unique owners from docket data
        2. Extracting and sorting unique state agencies from docket data
        3. Clearing existing models
        4. Populating models with new sorted data

        Attributes:
            self.docket_ownership_data (pd.DataFrame): DataFrame containing ownership information
                with 'owner' and 'state_legend' columns
            self.owner_model (QStandardItemModel): Model for owner list view
            self.agency_model (QStandardItemModel): Model for agency list view

        Note:
            - Models are completely refreshed each time this is called
            - Items are sorted alphabetically for consistent display
            - Empty models are created if no data is available
            - Used for populating filter/selection UI components

        Side Effects:
            - Clears all existing items in both models
            - Updates models with new sorted lists of owners and agencies

        Raises:
            KeyError: If 'owner' or 'state_legend' columns are missing from docket_ownership_data
            AttributeError: If models or docket_ownership_data are not initialized
        """
        # Extract and sort unique owners and agencies
        owners: List[str] = sorted(self.docket_ownership_data['owner'].unique())
        agencies: List[str] = sorted(self.docket_ownership_data['state_legend'].unique())

        # Clear existing data from both models
        self.owner_model.clear()
        self.agency_model.clear()

        # Populate owner model with sorted owner names
        for row in owners:
            self.owner_model.appendRow(QStandardItem(row))

        # Populate agency model with sorted agency names
        for row in agencies:
            self.agency_model.appendRow(QStandardItem(row))

    # def updateOwnerAndAgencyModels2(self):
    #     owners = sorted(self.docket_ownership_data['owner'].unique())
    #     agencies = sorted(self.docket_ownership_data['state_legend'].unique())
    #     self.owner_model.clear()
    #     self.agency_model.clear()
    #     for row in owners:
    #         self.owner_model.appendRow(QStandardItem(row))
    #     for row in agencies:
    #         self.agency_model.appendRow(QStandardItem(row))

    # def redraw2DCanvas(self):
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()

    def updateComboBoxData(self) -> None:
        """
        Updates the internal combo box data list with truncated well names.

        Processes the well list combo box by:
        1. Iterating through all combo box items
        2. Extracting the first 10 characters of each well name
        3. Storing truncated names in combo_box_data list

        Attributes:
            self.ui.well_lst_combobox (QComboBox): Combo box containing well names
            self.combo_box_data (List[str]): List to store truncated well identifiers

        Note:
            - Well names are truncated to 10 characters for consistent sizing
            - Used for internal data processing and matching
            - Should be called after any changes to well list combo box
            - Maintains synchronization between UI and internal data

        Side Effects:
            - Updates self.combo_box_data with new truncated well names

        Raises:
            AttributeError: If self.ui.well_lst_combobox is not initialized
        """
        # Create list of truncated well names from combo box
        self.combo_box_data: List[str] = [
            self.ui.well_lst_combobox.itemText(i)[:10]
            for i in range(self.ui.well_lst_combobox.count())
        ]



    # def updateComboBoxData(self):
    #     self.combo_box_data = [self.ui.well_lst_combobox.itemText(i)[:10] for i in
    #                            range(self.ui.well_lst_combobox.count())]

    # def activateProductionButtons(self):
    #     self.prodButtonsActivate()
    # def getCountersForStatus(self, main_status, other_status):
    #     # Initialize a dictionary to store the counts
    #     status_counts = {status: 0 for status in main_status}
    #     status_counts['Other'] = 0
    #
    #     # Count occurrences
    #     for status in main_status:
    #         status_counts[status] = self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)
    #
    #     # Count and sum up 'Other' category
    #     for status in other_status:
    #         status_counts['Other'] += self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)
    #
    #     self.ui.producing_check.setText(f"""Producing ({str(status_counts['Producing'])})""")
    #     self.ui.shut_in_check.setText(f"""Shut In ({str(status_counts['Shut-in'])})""")
    #     self.ui.pa_check.setText(f"""Plugged and Abandoned ({str(status_counts['Plugged & Abandoned'])})""")
    #     self.ui.drilling_status_check.setText(f"""Drilling ({str(status_counts['Drilling'])})""")
    #     self.ui.misc_well_type_check.setText(f"""Misc ({str(status_counts['Other'])})""")

    # def updateCountersForStatusAndType2(self):
    #     main_statuses = ['Plugged & Abandoned', 'Producing', 'Shut-in', 'Drilling']
    #     other_statuses = [
    #         'Location Abandoned - APD rescinded', 'Returned APD (Unapproved)',
    #         'Approved Permit', 'Active', 'Drilling Operations Suspended',
    #         'New Permit', 'Inactive', 'Temporarily-abandoned', 'Test Well or Monitor Well'
    #     ]
    #     main_types = ['Unknown', 'Oil Well', 'Dry Hole', 'Gas Well', 'Test Well', 'Water Source Well']
    #     merged_types = {
    #         'Injection Well': ['Water Injection Well', 'Gas Injection Well'],
    #         'Disposal Well': ['Water Disposal Well', 'Oil Well/Water Disposal Well'],
    #         'Other': ['Test Well', 'Water Source Well', 'Unknown']
    #     }
    #     self.getCountersForStatus(main_statuses, other_statuses)
    #     self.getCountersForType(main_types, merged_types)
    #
    #
    #
    #
    # def getCountersForStatus2(self, main_status, other_status):
    #     """
    #     Counts the occurrences of different well statuses and updates the UI accordingly.
    #
    #     This method categorizes well statuses into main statuses and 'Other' statuses,
    #     counts their occurrences in the current docket data, and updates the UI elements
    #     to display these counts.
    #
    #     Parameters:
    #     main_status (list): A list of strings representing the main well status categories to be counted individually.
    #     other_status (list): A list of strings representing well status categories to be grouped under 'Other'.
    #
    #     The method performs the following steps:
    #     1. Initializes a counter dictionary for main statuses and 'Other'.
    #     2. Counts occurrences of main statuses.
    #     3. Counts and sums up 'Other' statuses.
    #     4. Updates UI elements with the counted values.
    #
    #     Note: This method assumes the existence of self.df_docket DataFrame and specific UI elements.
    #     """
    #
    #     # Step 1: Initialize a dictionary to store the counts
    #     status_counts = {status: 0 for status in main_status}
    #     status_counts['Other'] = 0
    #     # This creates a dictionary with keys for each main status and 'Other', all initialized to 0.
    #
    #     # Step 2: Count occurrences of main statuses
    #     for status in main_status:
    #         status_counts[status] = self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)
    #     # For each main status, this counts its occurrences in the 'CurrentWellStatus' column of df_docket.
    #     # The .get(status, 0) ensures that if a status is not found, it returns 0 instead of raising an error.
    #
    #     # Step 3: Count and sum up 'Other' category
    #     for status in other_status:
    #         status_counts['Other'] += self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)
    #     # This sums up the counts of all statuses in the other_status list and adds them to the 'Other' category.
    #
    #     # Step 4: Update UI elements with the counted values
    #     # Each line below updates a specific UI checkbox with the count for its corresponding status
    #     self.ui.producing_check.setText(f"""Producing ({str(status_counts['Producing'])})""")
    #     self.ui.shut_in_check.setText(f"""Shut In ({str(status_counts['Shut-in'])})""")
    #     self.ui.pa_check.setText(f"""Plugged and Abandoned ({str(status_counts['Plugged & Abandoned'])})""")
    #     self.ui.drilling_status_check.setText(f"""Drilling ({str(status_counts['Drilling'])})""")
    #     self.ui.misc_well_type_check.setText(f"""Misc ({str(status_counts['Other'])})""")
    #     # These UI updates assume the existence of specific checkbox elements in the UI,
    #     # each corresponding to a particular well status or the 'Other' category.
    #
    #
    # def getCountersForType2(self, main_types, merged_types):
    #     type_counts = {well_type: 0 for well_type in main_types}
    #     type_counts.update({merged: 0 for merged in merged_types})
    #     # Count occurrences
    #     for well_type in main_types:
    #         type_counts[well_type] = self.df_docket['CurrentWellType'].value_counts().get(well_type, 0)
    #
    #     # Count and sum up merged categories
    #     for merged, subtypes in merged_types.items():
    #         for subtype in subtypes:
    #             type_counts[merged] += self.df_docket['CurrentWellType'].value_counts().get(subtype, 0)
    #
    #     self.ui.oil_well_check.setText(f"""Oil Well ({str(type_counts['Oil Well'])})""")
    #     self.ui.gas_well_check.setText(f"""Gas Well ({str(type_counts['Gas Well'])})""")
    #     self.ui.water_disposal_check.setText(f"""Water Disposal ({str(type_counts['Disposal Well'])})""")
    #     self.ui.dry_hole_check.setText(f"""Dry Hole ({str(type_counts['Dry Hole'])})""")
    #     self.ui.injection_check.setText(f"""Injection Well ({str(type_counts['Injection Well'])})""")
    #     self.ui.other_well_status_check.setText(f"""Other ({str(type_counts['Other'])})""")


    def updateCountersForStatusAndType(self) -> None:
        """
        Updates UI counters for well statuses and types by processing docket data.

        Coordinates the counting and UI updates for both well statuses and types by:
        1. Defining classification categories for statuses and types
        2. Delegating counting to specialized methods
        3. Maintaining consistent categorization across the application

        Attributes:
            self.df_docket (pd.DataFrame): DataFrame containing well information with
                'CurrentWellStatus' and 'CurrentWellType' columns

        Note:
            - Main statuses represent primary operational states
            - Other statuses are grouped for simplified visualization
            - Well types are organized with some types merged into broader categories
            - UI elements are automatically updated with count information

        Side Effects:
            - Updates multiple UI checkbox labels with count information
            - Triggers recalculation of all well status and type counts

        Raises:
            AttributeError: If df_docket or UI elements are not properly initialized
            KeyError: If required DataFrame columns are missing
        """
        # Define primary operational status categories
        main_statuses: List[str] = [
            'Plugged & Abandoned',
            'Producing',
            'Shut-in',
            'Drilling'
        ]

        # Define secondary status categories for 'Other' grouping
        other_statuses: List[str] = [
            'Location Abandoned - APD rescinded',
            'Returned APD (Unapproved)',
            'Approved Permit',
            'Active',
            'Drilling Operations Suspended',
            'New Permit',
            'Inactive',
            'Temporarily-abandoned',
            'Test Well or Monitor Well'
        ]

        # Define primary well type categories
        main_types: List[str] = [
            'Unknown',
            'Oil Well',
            'Dry Hole',
            'Gas Well',
            'Test Well',
            'Water Source Well'
        ]

        # Define merged categories for related well types
        merged_types: Dict[str, List[str]] = {
            'Injection Well': ['Water Injection Well', 'Gas Injection Well'],
            'Disposal Well': ['Water Disposal Well', 'Oil Well/Water Disposal Well'],
            'Other': ['Test Well', 'Water Source Well', 'Unknown']
        }

        # Process and update counters for both classifications
        self.getCountersForStatus(main_statuses, other_statuses)
        self.getCountersForType(main_types, merged_types)

    def getCountersForType(self, main_types: List[str], merged_types: Dict[str, List[str]]) -> None:
        """
        Calculates and updates UI elements with well type counts from docket data.

        Processes well types by:
        1. Counting occurrences of main well types
        2. Aggregating counts for merged type categories
        3. Updating UI checkboxes with count information

        Args:
            main_types: List of primary well type categories to count individually
            merged_types: Dictionary mapping merged category names to lists of subtypes

        Note:
            - Main types are counted directly from CurrentWellType column
            - Merged types aggregate counts from multiple related subtypes
            - UI updates use f-strings for count display

        Side Effects:
            - Updates multiple UI checkbox labels with count information

        Raises:
            AttributeError: If df_docket or UI elements are not initialized
        """
        # Initialize count dictionary for all well types
        type_counts: Dict[str, int] = {well_type: 0 for well_type in main_types}
        type_counts.update({merged: 0 for merged in merged_types})

        # Count occurrences of main well types
        for well_type in main_types:
            type_counts[well_type] = self.df_docket['CurrentWellType'].value_counts().get(well_type, 0)

        # Aggregate counts for merged type categories
        for merged, subtypes in merged_types.items():
            for subtype in subtypes:
                type_counts[merged] += self.df_docket['CurrentWellType'].value_counts().get(subtype, 0)

        # Update UI elements with calculated counts
        self.ui.oil_well_check.setText(f"""Oil Well ({str(type_counts['Oil Well'])})""")
        self.ui.gas_well_check.setText(f"""Gas Well ({str(type_counts['Gas Well'])})""")
        self.ui.water_disposal_check.setText(f"""Water Disposal ({str(type_counts['Disposal Well'])})""")
        self.ui.dry_hole_check.setText(f"""Dry Hole ({str(type_counts['Dry Hole'])})""")
        self.ui.injection_check.setText(f"""Injection Well ({str(type_counts['Injection Well'])})""")
        self.ui.other_well_status_check.setText(f"""Other ({str(type_counts['Other'])})""")

    def getCountersForStatus(self, main_status: List[str], other_status: List[str]) -> None:
        """
        Counts the occurrences of different well statuses and updates the UI accordingly.

        This method categorizes well statuses into main statuses and 'Other' statuses,
        counts their occurrences in the current docket data, and updates the UI elements
        to display these counts.

        Args:
            main_status: List of strings representing primary well status categories
                to be counted individually. Expected values include 'Producing',
                'Shut-in', 'Plugged & Abandoned', and 'Drilling'.
            other_status: List of strings representing secondary well status categories
                to be grouped under 'Other'. Includes statuses like 'Approved Permit',
                'Inactive', etc.

        Attributes:
            self.df_docket (pd.DataFrame): DataFrame containing well information with
                a 'CurrentWellStatus' column
            self.ui: PyQt5 UI object containing checkbox elements for status display

        Note:
            - Uses pandas value_counts() for efficient counting
            - Handles missing statuses gracefully by defaulting to 0
            - Updates UI checkboxes with formatted count strings
            - Thread-safe for UI updates when used with PyQt5

        Side Effects:
            - Updates text of multiple UI checkbox elements:
                - producing_check
                - shut_in_check
                - pa_check
                - drilling_status_check
                - misc_well_type_check

        Raises:
            AttributeError: If df_docket or UI elements are not properly initialized
            KeyError: If 'CurrentWellStatus' column is missing from df_docket
        """
        # Initialize counter dictionary with main statuses and 'Other' category
        status_counts: Dict[str, int] = {status: 0 for status in main_status}
        status_counts['Other'] = 0

        # Count occurrences of main well statuses from docket data
        for status in main_status:
            status_counts[status] = self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)

        # Aggregate counts for 'Other' category from secondary statuses
        for status in other_status:
            status_counts['Other'] += self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)

        # Update UI checkbox labels with formatted count information
        self.ui.producing_check.setText(f"""Producing ({str(status_counts['Producing'])})""")
        self.ui.shut_in_check.setText(f"""Shut In ({str(status_counts['Shut-in'])})""")
        self.ui.pa_check.setText(f"""Plugged and Abandoned ({str(status_counts['Plugged & Abandoned'])})""")
        self.ui.drilling_status_check.setText(f"""Drilling ({str(status_counts['Drilling'])})""")
        self.ui.misc_well_type_check.setText(f"""Misc ({str(status_counts['Other'])})""")

    def colorInFields(self) -> None:
        """Processes and visualizes field sections with distinct colors on the map.

        This method handles the coloring and visualization of field polygons based on
        field data from multiple DataFrames. It processes field boundaries, creates
        polygon visualizations, and sets up field labels with centroids.

        Instance Attributes Modified:
            field_sections: Updates colors, paths, and visibility
            field_centroids_lst: Stores centroid points for field labels
            field_labels: Stores unique field names

        Note:
            - Requires pre-populated DataFrames: df_docket, df_adjacent_fields, and df_field
            - Uses a colorblind-friendly color palette
            - Initially sets field sections as invisible

        Raises:
            AttributeError: If required instance DataFrames are not initialized
        """
        # Color list definition (truncated for brevity)
        color_lst = [
            '#000000', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600']

        polygons_lst: List[np.ndarray] = []

        # Extract unique fields from docket data
        all_used_fields = self.df_docket['FieldName'].unique()

        # Process adjacent fields
        used_fields = self.df_adjacent_fields[
            self.df_adjacent_fields['Field_Name'].isin(all_used_fields)]

        # Combine original and adjacent field names
        used_fields_names = list(set(
            used_fields['adjacent_Field_Name'].values.tolist() +
            all_used_fields.tolist()
        ))

        # Filter fields DataFrame for relevant fields
        used_fields = self.df_field[self.df_field['Field_Name'].isin(used_fields_names)]

        # Process line segments and create field groups
        used_fields['LineSegmentOrder'] = used_fields.groupby('Field_Name').cumcount() + 1
        used_fields = used_fields.drop_duplicates(keep='first')
        grouped_rows = used_fields.groupby('Field_Name')

        # Create polygon coordinates for each field
        for _, group in grouped_rows:
            coordinates = group[['Easting', 'Northing']].values.tolist()
            polygons_lst.append(np.array(coordinates))

        # Update field section properties
        self.field_sections.set_color(color_lst)
        self.field_sections.set_paths(polygons_lst)
        self.field_sections.set_visible(False)

        # Calculate and store field centroids and labels
        self.field_centroids_lst = [Polygon(i).centroid for i in polygons_lst]
        self.field_labels = used_fields['Field_Name'].unique()

    def fillInAllWellsTable(self, lst: List[str]) -> None:
        """Populates the wells table with filtered well data.

        Args:
            lst: List of DisplayNames to filter the wells data

        This method filters the docket DataFrame based on provided display names,
        sorts the data, and populates a QTableView with the results.

        Instance Attributes Modified:
            df_all_wells_table: Updates filtered wells data
            all_wells_model: Updates table model with new data

        Note:
            - Maintains display name ordering based on input list
            - Automatically resizes table columns and rows
            - Hides vertical headers in the table view

        Raises:
            AttributeError: If required DataFrame or UI components are not initialized
        """
        # Filter and sort wells data
        self.df_all_wells_table = self.df_docket[self.df_docket['DisplayName'].isin(lst)]
        self.df_all_wells_table['DisplayName'] = pd.Categorical(
            self.df_all_wells_table['DisplayName'],
            categories=lst,
            ordered=True
        )
        self.df_all_wells_table.sort_values('DisplayName', inplace=True)
        self.df_all_wells_table.reset_index(drop=True, inplace=True)

        # Prepare table data
        data = self.df_all_wells_table.values.tolist()
        self.all_wells_model.removeRows(0, self.all_wells_model.rowCount())

        # Set up table headers and populate data
        self.all_wells_model.setHorizontalHeaderLabels(self.df_all_wells_table.columns)
        for row in data:
            items = [QStandardItem(str(item)) for item in row]
            self.all_wells_model.appendRow(items)

        # Configure table view properties
        self.ui.all_wells_qtableview.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.ui.all_wells_qtableview.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.ui.all_wells_qtableview.verticalHeader().setVisible(False)

        # Set the model to the view
        self.ui.all_wells_qtableview.setModel(self.all_wells_model)

    def colorInOwnership(self) -> None:
        """Processes and visualizes land ownership data with color-coded polygons for both owners and agencies.

        This method handles the visualization of land ownership by:
        1. Loading and preprocessing ownership data
        2. Applying color schemes for both owners and agencies
        3. Converting geometries to proper coordinate systems
        4. Creating polygon collections for visualization

        Color schemes are predefined for different types of ownership and agencies.

        Returns:
            None

        Side Effects:
            - Updates self.docket_ownership_data
            - Modifies ownership_sections_agency and ownership_sections_owner properties
            - Creates ownership labels through createOwnershipLabels()

        Requires:
            - self.df_owner: DataFrame containing ownership data
            - self.used_plat_codes_for_boards: List of valid plat codes
            - self.ownership_sections_agency: PatchCollection for agency visualization
            - self.ownership_sections_owner: PatchCollection for owner visualization
        """
        # Initialize empty lists for polygon coordinates
        polygons_lst_owner: List[np.ndarray] = []
        polygons_lst_agency: List[np.ndarray] = []

        # Define color mappings for different types of ownership
        colors_owner: Dict[str, str] = {
            'Private': '#D2B48C',
            'Tribal': '#800000',
            'State': '#0000FF',
            'Federal': '#008000'
        }

        # Define color mappings for different agencies
        colors_agency: Dict[str, str] = {
            'None': 'white',
            'Bureau of Land Management': '#2f4b7c',
            'Bureau of Reclamation': '#003f5c',
            'Department of Defense': '#ffa600',
            'Department of Energy': '#ff7c43',
            'National Park Service': '#ff7c43',
            'Private': '#D2B48C',
            'Utah State Forestry Service': '#f95d6a',
            'United States Fish and Wildlife Service': '#d45087',
            'Department of Natural Resources': '#a05195',
            'Other State': '#665191',
            'State Trust Lands': '#2f4b7c',
            'Utah Department of Transportation': '#003f5c',
            'Tribal': '#800000'
        }

        # Process ownership data and convert to GeoDataFrame
        docket_ownership_data = self.df_owner[self.df_owner['conc'].isin(self.used_plat_codes_for_boards)]
        docket_ownership_data['geometry'] = docket_ownership_data['geometry'].apply(wkt.loads)
        docket_ownership_data = gpd.GeoDataFrame(docket_ownership_data, geometry='geometry', crs='EPSG:4326')

        # Transform coordinate system to UTM Zone 12N (EPSG:26912)
        docket_ownership_data = docket_ownership_data.to_crs(epsg=26912)

        # Map colors to ownership and agency data
        docket_ownership_data['owner_color'] = docket_ownership_data['owner'].map(colors_owner)
        docket_ownership_data['agency_color'] = docket_ownership_data['state_legend'].map(colors_agency)

        # Create order columns for potential use in visualization
        docket_ownership_data['owner_order'] = docket_ownership_data.groupby('owner').cumcount() + 1
        docket_ownership_data['agency_order'] = docket_ownership_data.groupby('state_legend').cumcount() + 1

        # Remove duplicates and store processed data
        docket_ownership_data = docket_ownership_data.drop_duplicates(keep='first')
        self.docket_ownership_data = docket_ownership_data

        # Process geometries and colors for both owner and agency visualizations
        colors_owner_used: List[str] = []
        colors_agency_used: List[str] = []

        # Create polygon collections for owners
        for conc, group in docket_ownership_data.groupby('owner'):
            for idx, row in group.iterrows():
                coordinates = list(row['geometry'].exterior.coords)
                polygons_lst_owner.append(np.array(coordinates))
                colors_owner_used.append(row['owner_color'])

        # Create polygon collections for agencies
        for conc, group in docket_ownership_data.groupby('state_legend'):
            for idx, row in group.iterrows():
                coordinates = list(row['geometry'].exterior.coords)
                polygons_lst_agency.append(np.array(coordinates))
                colors_agency_used.append(row['agency_color'])

        # Update visualization properties for both agency and owner layers
        self.ownership_sections_agency.set_color(colors_agency_used)
        self.ownership_sections_agency.set_paths(polygons_lst_agency)
        self.ownership_sections_agency.set_visible(False)
        self.ownership_sections_owner.set_color(colors_owner_used)
        self.ownership_sections_owner.set_paths(polygons_lst_owner)
        self.ownership_sections_owner.set_visible(False)

        # Generate labels for ownership visualization
        self.createOwnershipLabels()


    # def colorInOwnership2(self):
    #     polygons_lst_owner, polygons_lst_agency = [], []
    #     colors_owner = {'Private': '#D2B48C',
    #                     'Tribal': '#800000',
    #                     'State': '#0000FF',
    #                     'Federal': '#008000'}
    #     colors_agency = {'None': 'white',
    #                      'Bureau of Land Management': '#2f4b7c',
    #                      'Bureau of Reclamation': '#003f5c',
    #                      'Department of Defense': '#ffa600',
    #                      'Department of Energy': '#ff7c43',
    #                      'National Park Service': '#ff7c43',
    #                      'Private': '#D2B48C',
    #                      'Utah State Forestry Service': '#f95d6a',
    #                      'United States Fish and Wildlife Service': '#d45087',
    #                      'Department of Natural Resources': '#a05195',
    #                      'Other State': '#665191',
    #                      'State Trust Lands': '#2f4b7c',
    #                      'Utah Department of Transportation': '#003f5c',
    #                      'Tribal': '#800000'}
    #
    #     docket_ownership_data = self.df_owner[self.df_owner['conc'].isin(self.used_plat_codes_for_boards)]
    #     docket_ownership_data['geometry'] = docket_ownership_data['geometry'].apply(wkt.loads)
    #     docket_ownership_data = gpd.GeoDataFrame(docket_ownership_data, geometry='geometry', crs='EPSG:4326')
    #     docket_ownership_data = docket_ownership_data.to_crs(epsg=26912)
    #     docket_ownership_data['owner_color'] = docket_ownership_data['owner'].map(colors_owner)
    #     docket_ownership_data['agency_color'] = docket_ownership_data['state_legend'].map(colors_agency)
    #
    #     docket_ownership_data['owner_order'] = docket_ownership_data.groupby('owner').cumcount() + 1
    #     docket_ownership_data['agency_order'] = docket_ownership_data.groupby('state_legend').cumcount() + 1
    #
    #     docket_ownership_data = docket_ownership_data.drop_duplicates(keep='first')
    #     self.docket_ownership_data = docket_ownership_data
    #     grouped_rows_owner = docket_ownership_data.groupby('owner')
    #     grouped_rows_agency = docket_ownership_data.groupby('state_legend')
    #     colors_owner_used, colors_agency_used = [], []
    #     for conc, group in grouped_rows_owner:
    #         for idx, row in group.iterrows():
    #             coordinates = list(row['geometry'].exterior.coords)
    #             polygons_lst_owner.append(np.array(coordinates))
    #             colors_owner_used.append(row['owner_color'])
    #
    #     for conc, group in grouped_rows_agency:
    #         for idx, row in group.iterrows():
    #             coordinates = list(row['geometry'].exterior.coords)
    #             polygons_lst_agency.append(np.array(coordinates))
    #             colors_agency_used.append(row['agency_color'])
    #
    #     self.ownership_sections_agency.set_color(colors_agency_used)
    #     self.ownership_sections_agency.set_paths(polygons_lst_agency)
    #     self.ownership_sections_agency.set_visible(False)
    #     self.ownership_sections_owner.set_color(colors_owner_used)
    #     self.ownership_sections_owner.set_paths(polygons_lst_owner)
    #     self.ownership_sections_owner.set_visible(False)
    #     self.createOwnershipLabels()

    def colorInFields2(self):
        # Here's a big list of distinctive colors,hopefully colorblind friendly.
        color_lst = [
            '#000000', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c',
            '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191',
            '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
            '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600']
        polygons_lst = []
        # Get a list of all fields out there that are used in these welkls
        all_used_fields = self.df_docket['FieldName'].unique()

        # Get a list of adjacent fields to the fields that are being used
        used_fields = self.df_adjacent_fields[self.df_adjacent_fields['Field_Name'].isin(all_used_fields)]

        # get the names of all the adjacent fields and merge them with the original fields
        used_fields_names = list(set(used_fields['adjacent_Field_Name'].values.tolist() + all_used_fields.tolist()))

        # search df_fields for those fields specifically and generate a dataframe
        used_fields = self.df_field[self.df_field['Field_Name'].isin(used_fields_names)]

        # group the fields linesegments, drop dupes, group by name
        used_fields['LineSegmentOrder'] = used_fields.groupby('Field_Name').cumcount() + 1
        used_fields = used_fields.drop_duplicates(keep='first')
        grouped_rows = used_fields.groupby('Field_Name')
        # Create a dictionary to store the polygons for each Conc and iterate them. There's probably a better way to do this

        for conc, group in grouped_rows:
            # Extract the coordinates from the group
            coordinates = group[['Easting', 'Northing']].values.tolist()
            polygons_lst.append(np.array(coordinates))

        # set the colors, paths, and visibility. Initially it won't be visible.
        self.field_sections.set_color(color_lst)
        self.field_sections.set_paths(polygons_lst)
        self.field_sections.set_visible(False)

        # get the centroids. These will be where the field name labels will be anchored.
        self.field_centroids_lst = [Polygon(i).centroid for i in polygons_lst]
        self.field_labels = used_fields['Field_Name'].unique()

    def fillInAllWellsTable2(self, lst):
        self.df_all_wells_table = self.df_docket[self.df_docket['DisplayName'].isin(lst)]
        self.df_all_wells_table['DisplayName'] = pd.Categorical(self.df_all_wells_table['DisplayName'], categories=lst, ordered=True)
        self.df_all_wells_table.sort_values('DisplayName', inplace=True)
        self.df_all_wells_table.reset_index(drop=True, inplace=True)
        data = self.df_all_wells_table.values.tolist()
        self.all_wells_model.removeRows(0, self.all_wells_model.rowCount())

        self.all_wells_model.setHorizontalHeaderLabels(self.df_all_wells_table.columns)
        for row in data:
            items = [QStandardItem(str(item)) for item in row]
            self.all_wells_model.appendRow(items)

        # Set the model to the QTableView
        self.ui.all_wells_qtableview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.all_wells_qtableview.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.all_wells_qtableview.verticalHeader().setVisible(False)

        self.ui.all_wells_qtableview.setModel(self.all_wells_model)

    def on_row_clicked(self, index: QModelIndex) -> None:
        """
        Handles the event when a row is clicked in the all wells table view.
        Updates well information displays, tables, and visualizations based on the selected well.

        This method performs several key operations:
        1. Extracts row data from the selected well
        2. Filters well data based on API Number
        3. Updates 2D and 3D visualization paths
        4. Updates the well selection combo box
        5. Populates well data tables with detailed information

        Args:
            index (QModelIndex): The index of the clicked row in the table view

        Returns:
            None

        Side Effects:
            - Updates self.selected_well_2d_path and self.selected_well_3d_path
            - Updates self.targeted_well
            - Modifies well_lst_combobox selection
            - Updates well data tables (well_data_table_1, well_data_table_2, well_data_table_3)
            - Triggers 2D visualization update

        Requires:
            - self.all_wells_model: QStandardItemModel containing well data
            - self.currently_used_lines: DataFrame with well coordinates and information
            - self.combo_box_data: List of well identifiers
            - self.ui: UI component container
        """
        # Extract row data from the model
        row: int = index.row()
        row_data: List[Any] = [
            self.all_wells_model.data(self.all_wells_model.index(row, column))
            for column in range(self.all_wells_model.columnCount())
        ]

        # Filter well data based on API Number and extract coordinates
        filtered_df: pd.DataFrame = self.currently_used_lines[
            self.currently_used_lines['APINumber'] == row_data[0]
            ]
        data_select_2d: np.ndarray = filtered_df[['X', 'Y']].to_numpy().astype(float)
        data_select_3d: np.ndarray = filtered_df[
            ['SPX', 'SPY', 'Targeted Elevation']
        ].to_numpy().astype(float)

        # Update well path data
        self.selected_well_2d_path: List[List[float]] = data_select_2d.tolist()
        self.selected_well_3d_path: List[List[float]] = data_select_3d.tolist()

        # Update selected well and combo box selection
        self.targeted_well: str = row_data[0]
        target_index: int = self.combo_box_data.index(self.targeted_well)
        self.ui.well_lst_combobox.setCurrentIndex(target_index)

        # Define data categories for table population
        row_1_data: List[str] = [
            'WellID', 'WellName', 'SideTrack', 'WorkType', 'Slant',
            'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate',
            'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud'
        ]
        row_2_data: List[str] = [
            'WCRCompletionDate', 'WellStatusReport', 'WellTypeReport',
            'FirstProdDate', 'TestDate', 'ProductionMethod', 'OilRate',
            'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType'
        ]
        row_3_data: List[str] = [
            'MD', 'TVD', 'Perforation MD', 'Perforation TVD',
            'CurrentWellStatus', 'CurrentWellType', 'Total Gas Prod',
            'Total Oil Prod', 'WellAge', 'Last Production (if Shut In)',
            'Months Shut In'
        ]

        # Create dictionary and DataFrame for data organization
        all_columns: List[str] = row_1_data + row_2_data + row_3_data
        result_dict: Dict[str, Any] = {
            col: value for col, value in zip(all_columns, row_data)
        }
        test_df: pd.DataFrame = pd.DataFrame([result_dict])

        # Populate the three data tables with well information
        for i, value in enumerate(row_1_data):
            self.ui.well_data_table_1.item(0, i).setText(str(test_df[value].item()))
        for i, value in enumerate(row_2_data):
            self.ui.well_data_table_2.item(0, i).setText(str(test_df[value].iloc[0]))
        for i, value in enumerate(row_3_data):
            self.ui.well_data_table_3.item(0, i).setText(str(test_df[value].iloc[0]))

        # Update 2D visualization
        self.update2dSelectedWhenWellChanges()
    # def on_row_clicked2(self, index: QModelIndex):
    #     row = index.row()
    #     row_data = [self.all_wells_model.data(self.all_wells_model.index(row, column)) for column in range(self.all_wells_model.columnCount())]
    #     """Filter based on API Number"""
    #     filtered_df = self.currently_used_lines[self.currently_used_lines['APINumber'] == row_data[0]]
    #     data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
    #     data_select_3d = filtered_df[['SPX', 'SPY', 'Targeted Elevation']].to_numpy().astype(float)
    #
    #     """Add wells to list"""
    #     self.selected_well_2d_path = data_select_2d.tolist()
    #     self.selected_well_3d_path = data_select_3d.tolist()
    #
    #     """Set the selected well, and change the combo box to match"""
    #     self.targeted_well = row_data[0]
    #     target_index = self.combo_box_data.index(self.targeted_well)
    #     self.ui.well_lst_combobox.setCurrentIndex(target_index)
    #
    #     """Fill in the data rows"""
    #     row_1_data = ['WellID', 'WellName', 'SideTrack', 'WorkType', 'Slant', 'APDReceivedDate', 'APDReturnDate',
    #                   'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud']
    #     row_2_data = ['WCRCompletionDate', 'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'TestDate',
    #                   'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType']
    #     row_3_data = ['MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'CurrentWellStatus', 'CurrentWellType',
    #                   'Total Gas Prod', 'Total Oil Prod', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In']
    #     all_columns = row_1_data + row_2_data + row_3_data
    #     result_dict = {col: value for col, value in zip(all_columns, row_data)}
    #     test_df = pd.DataFrame([result_dict])
    #     # Parse and fill out the data rows
    #     for i, value in enumerate(row_1_data):
    #         self.ui.well_data_table_1.item(0, i).setText(str(test_df[value].item()))
    #     for i, value in enumerate(row_2_data):
    #         self.ui.well_data_table_2.item(0, i).setText(str(test_df[value].iloc[0]))
    #     for i, value in enumerate(row_3_data):
    #         self.ui.well_data_table_3.item(0, i).setText(str(test_df[value].iloc[0]))
    #     self.update2dSelectedWhenWellChanges()
    #
    #     # self.comboUpdateWhenSelectedFromAllWellsTable(row_data)

    """This just clears all the data."""

    def clearDataFrom2dAnd3d(self) -> None:
        """
        Clears all data and resets visualization components in both 2D and 3D views.

        This method performs a comprehensive cleanup of the application state, including:
        1. Clearing UI components and data structures
        2. Resetting well visualizations in 2D and 3D
        3. Clearing plat and section visualizations
        4. Resetting production data displays
        5. Clearing well data tables
        6. Resetting checkbox labels

        Side Effects:
            - Clears multiple UI components (ComboBoxes, text areas, tables)
            - Resets all visualization parameters and collections
            - Clears all stored well data and paths
            - Updates multiple canvas elements
            - Resets checkbox labels to default states

        Returns:
            None

        Note:
            This method should be called when a complete reset of the application
            state is needed, such as when switching between different datasets
            or clearing the current visualization.
        """
        # Clear UI components and basic data structures
        self.used_plat_codes: List[str] = []
        self.ui.sectionsBoardComboBox.clear()  # Clear combo box selections
        self.ui.board_matter_files.clear()
        self.ui.board_brief_text.clear()

        # Reset 2D and 3D well visualizations
        for model_type in ['current', 'planned', 'asdrilled']:
            # Update 2D models
            self.drawModelBasedOnParameters2d(
                getattr(self, f'all_wells_2d_{model_type}'),
                [], [], [], self.ax2d,
                getattr(self, f'all_wells_2d_vertical_{model_type}')
            )
            # Update 3D models
            self.drawModelBasedOnParameters(
                getattr(self, f'all_wells_3d_{model_type}'),
                [], [], [], self.ax3d
            )

        # Clear operator-specific well visualizations
        for i in range(len(self.all_wells_2d_operators)):
            self.drawModelBasedOnParameters2d(
                self.all_wells_2d_operators[i],
                [], [], [],
                self.ax2d,
                self.all_wells_2d_operators_vertical[i]
            )

        # Reset 3D specific well properties
        for well_obj in [self.spec_well_3d, self.spec_well_3d_solo]:
            well_obj.set_data([], [])
            well_obj.set_3d_properties([])

        # Clear 2D visualization components
        self.all_vertical_wells_2d.set_offsets([None, None])
        self.spec_vertical_wells_2d.set_offsets([None, None])
        self.spec_well_2d.set_data([], [])

        # Reset plat visualizations
        for plat_collection in [
            self.plats_2d, self.plats_2d_main,
            self.plats_2d_1adjacent, self.plats_2d_2adjacent
        ]:
            plat_collection.set_segments([])

        # Clear section and ownership visualizations
        for section_collection in [
            self.ownership_sections_agency,
            self.ownership_sections_owner,
            self.field_sections,
            self.outlined_board_sections
        ]:
            section_collection.set_paths([])

        # Reset production data visualizations
        for line in [
            self.profit_line, self.profit_line_cum,
            self.prod_line, self.prod_line_cum
        ]:
            line.set_data([], [])

        # Clear well data tables
        self.specific_well_data_model.removeRows(
            0, self.specific_well_data_model.rowCount()
        )
        for i in range(11):
            for table in [
                self.ui.well_data_table_1,
                self.ui.well_data_table_2,
                self.ui.well_data_table_3
            ]:
                table.item(0, i).setText('')

        # Clear zoom/pan text objects
        for text in self.zp.text_objects:
            text.remove()
        self.zp.text_objects = []

        # Update all canvases
        for canvas in [
            self.canvas_prod_1, self.canvas_prod_2,
            self.canvas3d_solo, self.canvas2d,
            self.canvas3d
        ]:
            canvas.draw()

        # Special handling for 2D canvas
        self.ax2d.draw_artist(self.all_vertical_wells_2d)
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas3d.blit(self.ax3d.bbox)

        # Reset well table and operators
        self.ui.all_wells_qtableview.setModel(None)
        self.all_wells_2d_operators = []
        self.all_wells_2d_operators_vertical = []

        # Reset checkbox labels
        checkbox_labels = {
            'producing_check': 'Producing',
            'shut_in_check': 'Shut In',
            'pa_check': 'Plugged and Abandoned',
            'drilling_status_check': 'Drilling',
            'misc_well_type_check': 'Misc',
            'oil_well_check': 'Oil Well',
            'gas_well_check': 'Gas Well',
            'water_disposal_check': 'Water Disposal',
            'dry_hole_check': 'Dry Hole',
            'injection_check': 'Injection Well',
            'other_well_status_check': 'Other'
        }

        for check_name, label in checkbox_labels.items():
            getattr(self.ui, check_name).setText(f"{label}")

    # def clearDataFrom2dAnd3d2(self):
    #     self.used_plat_codes = []
    #     self.ui.sectionsBoardComboBox.clear()
    #     self.ui.board_matter_files.clear()
    #     self.ui.board_brief_text.clear()
    #     self.ui.board_brief_text.clear()
    #
    #     self.drawModelBasedOnParameters2d(self.all_wells_2d_current, [], [], [], self.ax2d, self.all_wells_2d_vertical_asdrilled)
    #     self.drawModelBasedOnParameters(self.all_wells_3d_current, [], [], [], self.ax3d)
    #
    #     self.drawModelBasedOnParameters2d(self.all_wells_2d_planned, [], [], [], self.ax2d, self.all_wells_2d_vertical_planned)
    #     self.drawModelBasedOnParameters(self.all_wells_3d_planned, [], [], [], self.ax3d)
    #
    #     self.drawModelBasedOnParameters2d(self.all_wells_2d_asdrilled, [], [], [], self.ax2d, self.all_wells_2d_vertical_current)
    #     self.drawModelBasedOnParameters(self.all_wells_3d_asdrilled, [], [], [], self.ax3d)
    #
    #     for i in range(len(self.all_wells_2d_operators)):
    #         self.drawModelBasedOnParameters2d(self.all_wells_2d_operators[i], [], [], [], self.ax2d, self.all_wells_2d_operators_vertical[i])
    #
    #     self.spec_well_3d.set_data([], [])
    #     self.spec_well_3d.set_3d_properties([])
    #
    #     self.spec_well_3d_solo.set_data([], [])
    #     self.spec_well_3d_solo.set_3d_properties([])
    #     self.spec_well_3d.set_data([], [])
    #     self.spec_well_3d.set_3d_properties([])
    #     self.all_vertical_wells_2d.set_offsets([None, None])
    #     self.spec_vertical_wells_2d.set_offsets([None, None])
    #     self.spec_well_2d.set_data([], [])
    #     self.plats_2d.set_segments([])
    #     self.plats_2d_main.set_segments([])
    #     self.plats_2d_1adjacent.set_segments([])
    #     self.plats_2d_2adjacent.set_segments([])
    #
    #     self.ownership_sections_agency.set_paths([])
    #     self.ownership_sections_owner.set_paths([])
    #     self.field_sections.set_paths([])
    #     self.profit_line.set_data([], [])
    #     self.profit_line_cum.set_data([], [])
    #     self.prod_line.set_data([], [])
    #     self.prod_line_cum.set_data([], [])
    #     self.outlined_board_sections.set_paths([])
    #     self.specific_well_data_model.removeRows(0, self.specific_well_data_model.rowCount())
    #
    #     for i in range(11):
    #         self.ui.well_data_table_1.item(0, i).setText('')
    #         self.ui.well_data_table_2.item(0, i).setText('')
    #         self.ui.well_data_table_3.item(0, i).setText('')
    #
    #     for text in self.zp.text_objects:
    #         text.remove()
    #     self.zp.text_objects = []
    #     self.canvas_prod_1.draw()
    #     self.canvas_prod_2.draw()
    #     self.ax2d.draw_artist(self.all_vertical_wells_2d)
    #     self.canvas3d_solo.draw()
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()
    #     self.canvas3d.blit(self.ax3d.bbox)
    #     self.canvas3d.draw()
    #     self.ui.all_wells_qtableview.setModel(None)
    #     self.all_wells_2d_operators = []
    #     self.all_wells_2d_operators_vertical = []
    #     self.ui.producing_check.setText(f"""Producing)""")
    #     self.ui.shut_in_check.setText(f"""Shut In""")
    #     self.ui.pa_check.setText(f"""Plugged and Abandoned""")
    #     self.ui.drilling_status_check.setText(f"""Drilling""")
    #     self.ui.misc_well_type_check.setText(f"""Misc""")
    #     self.ui.oil_well_check.setText(f"""Oil Well""")
    #     self.ui.gas_well_check.setText(f"""Gas Well""")
    #     self.ui.water_disposal_check.setText(f"""Water Disposal""")
    #     self.ui.dry_hole_check.setText(f"""Dry Hole""")
    #     self.ui.injection_check.setText(f"""Injection Well""")
    #     self.ui.other_well_status_check.setText(f"""Other""")

    """Set the axes limits for the 2d image based on the data that is found."""
    def setAxesLimits(self) -> None:
        """
        Sets the axes limits for the 2D visualization based on the data points' distribution.

        This method processes the docket data to determine appropriate axis limits that will
        properly display all data points with sufficient padding. The process involves:
        1. Generating line segments from docket data
        2. Extracting unique coordinate points
        3. Calculating boundaries with padding
        4. Setting axis limits with a 16000-unit buffer

        Args:
            self: The class instance containing required attributes:
                - df_docket_data (pd.DataFrame): DataFrame containing docket information
                - ax2d (Axes): The 2D matplotlib axes object to be adjusted

        Returns:
            None

        Side Effects:
            - Modifies the x and y limits of self.ax2d

        Notes:
            - Adds a 16000-unit buffer on all sides to ensure visibility of edge points
            - Uses numpy operations for efficient array processing
            - Assumes all coordinate data is valid and numerical

        Example:
            >>> self.setAxesLimits()  # Adjusts axes based on current docket data
        """
        # Generate all line segments from docket data
        segments: List[List[Tuple[float, float]]] = self.returnSegmentsFromDF(self.df_docket_data)

        # Convert segments to unique coordinate points
        flattened_list: List[Tuple[float, float]] = [
            tuple(point) for sublist in segments for point in sublist
        ]
        unique_points: np.ndarray = np.array(list(set(flattened_list)))

        # Calculate boundary values from coordinate points
        min_x: float = np.min(unique_points[:, 0])  # Minimum x coordinate
        max_x: float = np.max(unique_points[:, 0])  # Maximum x coordinate
        min_y: float = np.min(unique_points[:, 1])  # Minimum y coordinate
        max_y: float = np.max(unique_points[:, 1])  # Maximum y coordinate

        # Set axis limits with padding
        self.ax2d.set_xlim([min_x - 16000, max_x + 16000])  # Add x-axis buffer
        self.ax2d.set_ylim([min_y - 16000, max_y + 16000])  # Add y-axis buffer


    # def setAxesLimits2(self):
    #     # Generate all line segments
    #     segments = self.returnSegmentsFromDF(self.df_docket_data)
    #     # flatten the whole thing into one list and then convert it into a numpy array
    #     flattened_list = [tuple(point) for sublist in segments for point in sublist]
    #     unique_points = np.array(list(set(flattened_list)))
    #     # get mins and maxes and adjust the 2d axes accordingly.
    #     min_x = np.min(unique_points[:, 0])
    #     max_x = np.max(unique_points[:, 0])
    #     min_y = np.min(unique_points[:, 1])
    #     max_y = np.max(unique_points[:, 1])
    #     self.ax2d.set_xlim([min_x - 16000, max_x + 16000])
    #     self.ax2d.set_ylim([min_y - 16000, max_y + 16000])

    def onClick2d(self, event: MouseEvent) -> None:
        """
        Handles mouse click events in the 2D well visualization to select and display well information.

        This method processes click events by:
        1. Calculating the distance between the click location and all visible wells
        2. Identifying the closest well within a dynamic threshold
        3. Loading and displaying the selected well's data
        4. Updating the UI components to reflect the selection

        Args:
            event (MouseEvent): Matplotlib mouse event containing click coordinates
                and axes information

        Side Effects:
            - Updates self.selected_well_2d_path with new well coordinates
            - Updates self.selected_well_3d_path with new well 3D coordinates
            - Updates self.targeted_well with selected well's API number
            - Changes well_lst_combobox selection
            - Triggers well information update via comboUpdateWhenWellChanges

        Notes:
            - Selection threshold is dynamically calculated based on current view dimensions
            - Only processes clicks within the plot axes
            - Requires valid well data in self.currently_used_lines DataFrame

        Example:
            # Event handler automatically called on mouse click
            >>> self.canvas2d.mpl_connect('button_press_event', self.onClick2d)
        """
        if event.inaxes is not None:
            # Extract click coordinates
            x_selected: float = event.xdata
            y_selected: float = event.ydata

            # Calculate dynamic selection threshold based on current view
            limit: float = (np.diff(self.ax2d.get_xlim())[0] + np.diff(self.ax2d.get_ylim())[0]) / 80

            # Calculate distances to all visible wells
            self.currently_used_lines['distance'] = np.sqrt(
                (self.currently_used_lines['X'].astype(float) - x_selected) ** 2 +
                (self.currently_used_lines['Y'].astype(float) - y_selected) ** 2
            )

            # Filter wells within selection threshold
            closest_points: pd.DataFrame = self.currently_used_lines[
                self.currently_used_lines['distance'] < limit
                ]

            if not closest_points.empty:
                # Identify closest well
                closest_point: pd.Series = closest_points.loc[
                    closest_points['distance'].idxmin()
                ]

                # Get API number of selected well
                selected_well_api: str = closest_point['APINumber']

                # Filter full well data
                filtered_df: pd.DataFrame = self.currently_used_lines[
                    self.currently_used_lines['APINumber'] == selected_well_api
                    ]

                # Extract 2D and 3D coordinate data
                data_select_2d: np.ndarray = filtered_df[['X', 'Y']].to_numpy().astype(float)
                data_select_3d: np.ndarray = filtered_df[
                    ['SPX', 'SPY', 'Targeted Elevation']
                ].to_numpy().astype(float)

                # Update instance variables with selected well data
                self.selected_well_2d_path: List[List[float]] = data_select_2d.tolist()
                self.selected_well_3d_path: List[List[float]] = data_select_3d.tolist()
                self.targeted_well: str = selected_well_api

                # Update combo box selection
                target_index: int = self.combo_box_data.index(self.targeted_well)
                self.ui.well_lst_combobox.setCurrentIndex(target_index)

                # Update well information display
                self.comboUpdateWhenWellChanges()

    # def onClick2d(self, event):
    #     if event.inaxes is not None:
    #         x_selected, y_selected = event.xdata, event.ydata
    #         # When you click to select wells, there needs to be a threshold established for how close you have to click before it is registered as selected
    #
    #         # Find that rough selection distance
    #         limit = (np.diff(self.ax2d.get_xlim())[0] + np.diff(self.ax2d.get_ylim())[0]) / 80
    #
    #         # Find the distance from the point that was selected to all other wells that are currently displayed
    #         self.currently_used_lines['distance'] = np.sqrt((self.currently_used_lines['X'].astype(float) - x_selected) ** 2 + (self.currently_used_lines['Y'].astype(float) - y_selected) ** 2)
    #
    #         # Create a dataframe of points that are within the limit distance of the actively found points
    #         closest_points = self.currently_used_lines[self.currently_used_lines['distance'] < limit]
    #
    #         # do this assuming there *are* points within that distance
    #         if not closest_points.empty:
    #             # Find the closest point
    #             closest_point = closest_points.loc[closest_points['distance'].idxmin()]
    #
    #             # get the api identification for that closest point
    #             selected_well_api = closest_point['APINumber']
    #
    #             # generate a dataframe that is the full data for the well with that API Number
    #             filtered_df = self.currently_used_lines[self.currently_used_lines['APINumber'] == selected_well_api]
    #
    #             # convert data types (partly routine)
    #             data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
    #             data_select_3d = filtered_df[['SPX', 'SPY', 'Targeted Elevation']].to_numpy().astype(float)
    #
    #             # Add the data to the self. elements
    #             self.selected_well_2d_path = data_select_2d.tolist()
    #             self.selected_well_3d_path = data_select_3d.tolist()
    #             self.targeted_well = selected_well_api
    #
    #             # Search the combo box and find the index where this occurs
    #             target_index = self.combo_box_data.index(self.targeted_well)
    #
    #             # Update the combobox with the found index
    #             self.ui.well_lst_combobox.setCurrentIndex(target_index)
    #
    #             # Run all the appropriate processes that should be run when the selected well is instantiated(?)
    #             self.comboUpdateWhenWellChanges()

    """# This will update the 2d data. Relative Elevation, targeted data, etc"""

    def update2dWhenDocketChanges(self) -> None:
        """
        Updates the 2D visualization data when the selected docket or well changes.

        This method processes the currently selected well from the combo box to:
        1. Extract and format coordinate data for 2D/3D visualization
        2. Calculate relative elevation values
        3. Update instance variables with new well data

        Args:
            self: The class instance containing:
                - ui.well_lst_combobox (QComboBox): Combo box with well selections
                - dx_df (pd.DataFrame): DataFrame containing well data
                - dx_data (pd.DataFrame): DataFrame with elevation data

        Side Effects:
            - Updates self.selected_well_2d_path with new 2D coordinates
            - Updates self.selected_well_3d_path with new 3D coordinates
            - Updates self.targeted_well with current API number
            - Updates self.targeted_well_elevation
            - Modifies dx_df and dx_data with new relative elevation calculations

        Notes:
            - API numbers are truncated to first 10 characters for filtering
            - Elevation calculations are based on the first entry in dx_data
            - Coordinates are converted to float type for numerical operations

        Example:
            >>> self.update2dWhenDocketChanges()  # Updates visualization after well selection
        """
        # Extract current well selection from combo box
        current_text: str = self.ui.well_lst_combobox.currentText()
        api_number: str = current_text[:10]  # First 10 chars represent API number

        # Filter well data based on API number
        filtered_df: pd.DataFrame = self.dx_df[
            self.dx_df['APINumber'] == api_number]

        # Extract and convert coordinate data
        data_select_2d: np.ndarray = filtered_df[['X', 'Y']].to_numpy().astype(float)
        data_select_3d: np.ndarray = filtered_df[
            ['X', 'Y', 'TrueVerticalDepth']
        ].to_numpy().astype(float)

        # Update instance variables with new coordinate data
        self.selected_well_2d_path: List[List[float]] = data_select_2d.tolist()
        self.selected_well_3d_path: List[List[float]] = data_select_3d.tolist()
        self.targeted_well: str = api_number

        # Calculate relative elevation values
        self.targeted_well_elevation: float = self.dx_data['Elevation'].iloc[0]

        # Update DataFrames with relative elevation calculations
        self.dx_df['Targeted Elevation'] = (self.dx_df['TrueElevation'] - self.targeted_well_elevation)
        self.dx_data['Relative Elevation'] = (self.dx_data['Elevation'] - self.targeted_well_elevation)

    # def update2dWhenDocketChanges(self):
    #     # get the current text
    #     current_text = self.ui.well_lst_combobox.currentText()
    #
    #     # filter down the api numbers at 10 values
    #     filtered_df = self.dx_df[self.dx_df['APINumber'] == current_text[:10]]
    #
    #     # set to appropriate data types
    #     data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
    #     data_select_3d = filtered_df[['X', 'Y', 'TrueVerticalDepth']].to_numpy().astype(float)
    #     # add to lists
    #     self.selected_well_2d_path = data_select_2d.tolist()
    #     self.selected_well_3d_path = data_select_3d.tolist()
    #     # set the targeted well to the current text (again, 10 data values)
    #     self.targeted_well = current_text[:10]
    #
    #     # This is for creating a relative elevation for a deprecated function. the idea was that if the targeted well was at elevation 0, what would the other well elevations be relative to it?
    #     self.targeted_well_elevation = self.dx_data['Elevation'].iloc[0]
    #     self.dx_df['Targeted Elevation'] = self.dx_df['TrueElevation'] - self.targeted_well_elevation
    #     self.dx_data['Relative Elevation'] = self.dx_data['Elevation'] - self.targeted_well_elevation

    def comboUpdateWhenWellChanges(self) -> None:
        """
        Updates the UI tables and visualization when a well selection changes in the combo box.

        This method filters the well data based on current selections and populates three data
        tables with detailed well information. The process includes:
        1. Filtering data based on year, month, and board matter
        2. Identifying the currently selected well
        3. Populating three UI tables with well-specific data
        4. Triggering 2D visualization updates

        Args:
            self: The class instance containing:
                - dx_data (pd.DataFrame): Main well data
                - ui: UI components including combo boxes and tables

        Side Effects:
            - Updates well_data_table_1, well_data_table_2, and well_data_table_3
            - Triggers update2dSelectedWhenWellChanges

        Notes:
            - Handles multiple records for same well by selecting most recent APD approval
            - Data is organized into three distinct tables for different well attributes
            - All values are converted to strings for display

        Example:
            >>> self.comboUpdateWhenWellChanges()  # Updates UI after well selection change
        """
        # Filter data frame based on current UI selections
        df_month: pd.DataFrame = self.dx_data[
            (self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText()) &
            (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText()) &
            (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())
            ]

        # Get current well selection
        current_text: str = self.ui.well_lst_combobox.currentText()

        # Filter to current well's data
        current_data_row: pd.DataFrame = df_month[df_month['DisplayName'] == current_text]

        # Handle multiple records by selecting most recent
        if len(current_data_row) > 1:
            current_data_row = current_data_row.sort_values(
                by='APDApprovedDate',
                ascending=False
            ).head(1)

        # Define data fields for each table
        row_1_data: List[str] = [
            'WellID', 'WellName', 'SideTrack', 'CurrentWellStatus', 'CurrentWellType',
            'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate',
            'APDRescindDate', 'DrySpud', 'RotarySpud'
        ]

        row_2_data: List[str] = [
            'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'WCRCompletionDate',
            'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST',
            'DirSurveyRun', 'CompletionType'
        ]

        row_3_data: List[str] = [
            'GasVolume', 'OilVolume', 'WellAge', 'Last Production (if Shut In)',
            'Months Shut In', 'Operator', 'MD', 'TVD', 'Perforation MD',
            'Perforation TVD', 'WorkType', 'Slant'
        ]

        # Setup table structure
        self.setupTableData([row_1_data, row_2_data, row_3_data], current_data_row)

        # Populate each table with corresponding data
        for i, value in enumerate(row_1_data):
            self.ui.well_data_table_1.item(0, i).setText(str(current_data_row[value].item()))

        for i, value in enumerate(row_2_data):
            self.ui.well_data_table_2.item(0, i).setText(str(current_data_row[value].iloc[0]))

        for i, value in enumerate(row_3_data):
            self.ui.well_data_table_3.item(0, i).setText(str(current_data_row[value].iloc[0]))

        # Update 2D visualization
        self.update2dSelectedWhenWellChanges()

    # def comboUpdateWhenWellChanges(self):
    #     # filter and restrict the data frame down to the relevant docket and well data
    #
    #     df_month = self.dx_data[(self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText())
    #                             & (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText())
    #                             & (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())]
    #
    #     # get the current text in the combo box so that we know what we're looking at.
    #     current_text = self.ui.well_lst_combobox.currentText()
    #
    #     # restrict down to the current data row.
    #     current_data_row = df_month[df_month['DisplayName'] == current_text]
    #     if len(current_data_row) > 1:
    #         current_data_row = current_data_row.sort_values(by='APDApprovedDate', ascending=False).head(1)
    #     # I'm sure there's a better way to do this, but this is for filling out data in the table with the appropriate value in case for some reason the data order is scrambled.
    #     row_1_data = ['WellID', 'WellName', 'SideTrack', 'CurrentWellStatus', 'CurrentWellType', 'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud']
    #     row_2_data = ['WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'WCRCompletionDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType']
    #
    #     row_3_data = ['GasVolume', 'OilVolume', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In', 'Operator', 'MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'WorkType', 'Slant', ]
    #
    #     self.setupTableData([row_1_data, row_2_data, row_3_data], current_data_row)
    #     for i, value in enumerate(row_1_data):
    #         self.ui.well_data_table_1.item(0, i).setText(str(current_data_row[value].item()))
    #     for i, value in enumerate(row_2_data):
    #         self.ui.well_data_table_2.item(0, i).setText(str(current_data_row[value].iloc[0]))
    #     for i, value in enumerate(row_3_data):
    #         self.ui.well_data_table_3.item(0, i).setText(str(current_data_row[value].iloc[0]))
    #     self.update2dSelectedWhenWellChanges()
    def setupTableData(self, row_data: List[List[str]], df: pd.DataFrame) -> None:
        """
        Sets up and populates a table view with well data using a custom model and delegate.

        This method organizes well data into a structured table format with alternating
        header and data rows. It handles the formatting and display of well attributes
        including production, physical characteristics, and operational data.

        Args:
            row_data: List of three lists containing column headers for each data section:
                - row_data[0]: Basic well information and dates
                - row_data[1]: Well status and production metrics
                - row_data[2]: Physical characteristics and operations
            df: DataFrame containing the well data to populate the table

        Side Effects:
            - Clears and updates self.specific_well_data_model
            - Modifies table view formatting and visibility settings
            - Sets custom delegate for bold row styling

        Notes:
            - Headers (bold rows) are at indices 0, 2, and 4
            - Data rows follow their respective headers
            - Table adjusts column and row sizes automatically
            - Headers are hidden for custom formatting

        Example:
            >>> row_data = [['WellID', 'WellName'], ['Status', 'Type'], ['MD', 'TVD']]
            >>> setupTableData(row_data, well_df)  # Populates table with well data
        """
        # Clear existing table data
        self.specific_well_data_model.removeRows(0, self.specific_well_data_model.rowCount())

        # Define modified headers for the third row
        row_3_data_edited: List[str] = [
            'GasVolume', 'OilVolume', 'WellAge', 'Recorded Last Production',
            'Months Shut In (if applicable)', 'Operator', 'MD', 'TVD',
            'Perforation MD', 'Perforation TVD', 'WorkType', 'Slant'
        ]

        # Initialize data structure for table population
        data_used_lst: List[List[str]] = [
            row_data[0], [], row_data[1], [], row_3_data_edited, []
        ]

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

        # Configure table view display settings
        self.ui.well_data_table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.ui.well_data_table_view.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.ui.well_data_table_view.horizontalHeader().setVisible(False)
        self.ui.well_data_table_view.verticalHeader().setVisible(False)
        self.ui.well_data_table_view.setModel(self.specific_well_data_model)

        # Apply custom formatting for bold rows
        bold_rows: List[int] = [0, 2, 4]
        delegate = MultiBoldRowDelegate(bold_rows)
        self.ui.well_data_table_view.setItemDelegate(delegate)

    # def setupTableData(self, row_data, df):
    #     self.specific_well_data_model.removeRows(0, self.specific_well_data_model.rowCount())
    #     row_3_data_edited = ['GasVolume', 'OilVolume', 'WellAge', 'Recorded Last Production', 'Months Shut In (if applicable)', 'Operator', 'MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'WorkType', 'Slant', ]
    #
    #     data_used_lst = [row_data[0], [], row_data[1], [], row_3_data_edited, []]
    #     for i, value in enumerate(row_data[0]):
    #         data_used_lst[1].append(str(df[value].values[0]))
    #     for i, value in enumerate(row_data[1]):
    #         data_used_lst[3].append(str(df[value].values[0]))
    #     for i, value in enumerate(row_data[2]):
    #         data_used_lst[5].append(str(df[value].values[0]))
    #
    #     for row in data_used_lst:
    #         items = [QStandardItem(str(item)) for item in row]
    #         self.specific_well_data_model.appendRow(items)
    #
    #     self.ui.well_data_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    #     self.ui.well_data_table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    #     self.ui.well_data_table_view.horizontalHeader().setVisible(False)
    #     self.ui.well_data_table_view.verticalHeader().setVisible(False)
    #     self.ui.well_data_table_view.setModel(self.specific_well_data_model)
    #
    #     bold_rows = [0, 2, 4]  # The row you want to bold (0-indexed)
    #     delegate = MultiBoldRowDelegate(bold_rows)
    #     self.ui.well_data_table_view.setItemDelegate(delegate)

    def update2dSelectedWhenWellChanges(self) -> None:
        """
        Updates the 2D visualization when a well selection changes, handling both data
        and visual model updates.

        This method acts as a coordinator between data updates and visual rendering by:
        1. Triggering updates to well data, relative elevations, and targeting data
        2. Redrawing the 2D visualization model for the selected well

        Args:
            self: The class instance containing:
                - update2dWhenDocketChanges method for data updates
                - draw2dModelSelectedWell method for visualization updates

        Side Effects:
            - Updates well data through update2dWhenDocketChanges
            - Refreshes 2D visualization through draw2dModelSelectedWell
            - Modifies scatter plots and line collections in the 2D view

        Notes:
            - Called when a well is selected either through combo box or table click
            - Part of the visualization update chain triggered by well selection changes
            - Coordinates both data and visual updates in the correct sequence

        Example:
            >>> self.update2dSelectedWhenWellChanges()  # Updates view after well selection
        """
        # Update well data and calculations
        self.update2dWhenDocketChanges()

        # Refresh the 2D visualization model
        self.draw2dModelSelectedWell()


    # def update2dSelectedWhenWellChanges(self):
    #     self.update2dWhenDocketChanges()
    #     self.draw2dModelSelectedWell()


    # def comboUpdateWhenSelectedFromAllWellsTable(self, data):
    #     """Filter based on API Number"""
    #     filtered_df = self.currently_used_lines[self.currently_used_lines['APINumber'] == data[0]]
    #     data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
    #     data_select_3d = filtered_df[['SPX', 'SPY', 'Targeted Elevation']].to_numpy().astype(float)
    #
    #     """Add wells to list"""
    #     self.selected_well_2d_path = data_select_2d.tolist()
    #     self.selected_well_3d_path = data_select_3d.tolist()
    #
    #     """Set the selected well, and change the combo box to match"""
    #     self.targeted_well = data[0]
    #     target_index = self.combo_box_data.index(self.targeted_well)
    #     self.ui.well_lst_combobox.setCurrentIndex(target_index)
    #
    #     """Fill in the data rows"""
    #     row_1_data = ['WellID', 'WellName', 'SideTrack', 'WorkType', 'Slant', 'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud']
    #     row_2_data = ['WCRCompletionDate', 'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType']
    #     row_3_data = ['MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'CurrentWellStatus', 'CurrentWellType', 'Total Gas Prod', 'Total Oil Prod', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In']
    #     all_columns = row_1_data + row_2_data + row_3_data
    #     result_dict = {col: value for col, value in zip(all_columns, data)}
    #     test_df = pd.DataFrame([result_dict])
    #     # Parse and fill out the data rows
    #     for i, value in enumerate(row_1_data):
    #         self.ui.well_data_table_1.item(0, i).setText(str(test_df[value].item()))
    #     for i, value in enumerate(row_2_data):
    #         self.ui.well_data_table_2.item(0, i).setText(str(test_df[value].iloc[0]))
    #     for i, value in enumerate(row_3_data):
    #         self.ui.well_data_table_3.item(0, i).setText(str(test_df[value].iloc[0]))
    #     self.update2dSelectedWhenWellChanges()

    def draw2dModelSelectedWell(self) -> None:
        """
        Draws and updates the 2D and 3D visualizations for the currently selected well.

        This method processes well data and updates multiple visualization components:
        - 2D well path visualization
        - 3D well trajectory
        - Production graphics
        - Vertical well representations

        The method handles different citing types (as-drilled, planned, vertical) and
        ensures visualization even with partial data availability.

        Args:
            self: The class instance containing:
                - df_docket (pd.DataFrame): Docket-specific well data
                - dx_data (pd.DataFrame): Display-formatted well data
                - dx_df (pd.DataFrame): Directional survey data
                - Various matplotlib plot elements and canvases

        Side Effects:
            - Updates spec_vertical_wells_2d scatter plot
            - Updates spec_well_2d line plot
            - Updates spec_well_3d and spec_well_3d_solo 3D plots
            - Modifies plot limits and redraws canvases
            - Triggers production graphic updates

        Notes:
            - Prioritizes data display in order: as-drilled > planned > vertical
            - Converts coordinates to float for plotting
            - Centers view on well's centroid with 8000-unit buffer
            - Handles both vertical and directional wells differently

        Example:
            >>> self.draw2dModelSelectedWell()  # Updates visualizations for selected well
        """
        # Get well parameter data from current selection
        df_well_data: pd.DataFrame = self.df_docket.loc[
            self.dx_data['DisplayName'] == self.ui.well_lst_combobox.currentText()
            ]

        # Filter directional survey data for selected well
        df_well: pd.DataFrame = self.dx_df[
            self.dx_df['APINumber'] == df_well_data['WellID'].iloc[0]
            ]

        # Separate data by citing type
        drilled_df: pd.DataFrame = df_well[df_well['CitingType'].isin(['asdrilled'])]
        planned_df: pd.DataFrame = df_well[df_well['CitingType'].isin(['planned'])]
        vert_df: pd.DataFrame = df_well[df_well['CitingType'].isin(['vertical'])]

        # Get best available data based on priority
        df_well = self.findPopulatedDataframeForSelection(drilled_df, planned_df, vert_df)
        df_well.drop_duplicates(keep='first', inplace=True)
        df_well['X'] = df_well['X'].astype(float)
        df_well['Y'] = df_well['Y'].astype(float)

        # Extract coordinate data
        xy_data = df_well[['X', 'Y']].values

        # Update appropriate plot based on well type
        if df_well['CitingType'].iloc[0] == 'vertical':
            self.spec_vertical_wells_2d.set_offsets(xy_data)
            self.spec_well_2d.set_data([], [])
        else:
            self.spec_vertical_wells_2d.set_offsets([None, None])
            self.spec_well_2d.set_data(xy_data[:, 0], xy_data[:, 1])

        # Process 3D coordinates
        x = to_numeric(df_well['SPX'], errors='coerce')
        y = to_numeric(df_well['SPY'], errors='coerce')
        z = to_numeric(df_well['Targeted Elevation'], errors='coerce')
        self.centroid = (x.mean(), y.mean(), z.mean())

        # Update 3D visualizations
        self.spec_well_3d.set_data(x, y)
        self.spec_well_3d.set_3d_properties(z)
        self.spec_well_3d_solo.set_data(x, y)
        self.spec_well_3d_solo.set_3d_properties(z)

        # Refresh canvases
        self.canvas2d.draw()
        self.canvas3d.draw()

        # Set new view limits centered on well
        new_xlim = [self.centroid[0] - 8000, self.centroid[0] + 8000]
        new_ylim = [self.centroid[1] - 8000, self.centroid[1] + 8000]
        new_zlim = [self.centroid[2] - 8000, self.centroid[2] + 8000]

        # Update 3D solo view limits
        self.ax3d_solo.set_xlim3d(new_xlim)
        self.ax3d_solo.set_ylim3d(new_ylim)
        self.ax3d_solo.set_zlim3d(new_zlim)

        # Refresh solo canvas and production graphic
        self.canvas3d_solo.draw()
        self.drawProductionGraphic()

    # def draw2dModelSelectedWell(self):
    #     """Get the well's parameter data"""
    #     df_well_data = self.df_docket.loc[self.dx_data['DisplayName'] == self.ui.well_lst_combobox.currentText()]
    #
    #     """Restrict down to the dx data for the specific well"""
    #     df_well = self.dx_df[self.dx_df['APINumber'] == df_well_data['WellID'].iloc[0]]
    #     """Differentiate between the citing types (generate seperate data frames)"""
    #     drilled_df = df_well[df_well['CitingType'].isin(['asdrilled'])]
    #     planned_df = df_well[df_well['CitingType'].isin(['planned'])]
    #     vert_df = df_well[df_well['CitingType'].isin(['vertical'])]
    #
    #     """This will prioritize the data, making sure that *something* gets plotted, even if you're just trying to look at asDrilled data and this well doesn't have anything."""
    #     df_well = self.findPopulatedDataframeForSelection(drilled_df, planned_df, vert_df)
    #     df_well.drop_duplicates(keep='first', inplace=True)
    #     df_well['X'] = df_well['X'].astype(float)
    #     df_well['Y'] = df_well['Y'].astype(float)
    #
    #     """Isolate out the xy data into a list."""
    #     xy_data = df_well[['X', 'Y']].values
    #
    #     """Setup the data for the vertical well data"""
    #     if df_well['CitingType'].iloc[0] == 'vertical':
    #         self.spec_vertical_wells_2d.set_offsets(xy_data)
    #         self.spec_well_2d.set_data([], [])
    #     else:
    #         self.spec_vertical_wells_2d.set_offsets([None, None])
    #         self.spec_well_2d.set_data(xy_data[:, 0], xy_data[:, 1])
    #     x = to_numeric(df_well['SPX'], errors='coerce')
    #     y = to_numeric(df_well['SPY'], errors='coerce')
    #     z = to_numeric(df_well['Targeted Elevation'], errors='coerce')
    #     self.centroid = (x.mean(), y.mean(), z.mean())
    #     self.spec_well_3d.set_data(x, y)
    #     self.spec_well_3d.set_3d_properties(z)
    #
    #     self.spec_well_3d_solo.set_data(x, y)
    #     self.spec_well_3d_solo.set_3d_properties(z)
    #
    #     self.canvas2d.draw()
    #     self.canvas3d.draw()
    #
    #     new_xlim = [self.centroid[0] - 8000, self.centroid[0] + 8000]
    #     new_ylim = [self.centroid[1] - 8000, self.centroid[1] + 8000]
    #     new_zlim = [self.centroid[2] - 8000, self.centroid[2] + 8000]
    #
    #     self.ax3d_solo.set_xlim3d(new_xlim)
    #     self.ax3d_solo.set_ylim3d(new_ylim)
    #     self.ax3d_solo.set_zlim3d(new_zlim)
    #
    #     self.canvas3d_solo.draw()
    #     self.drawProductionGraphic()

    def findPopulatedDataframeForSelection(
            self,
            drilled_df: pd.DataFrame,
            planned_df: pd.DataFrame,
            vert_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Prioritizes and returns the first non-empty DataFrame from the provided well data sources.

        This method implements a prioritized selection of well data, checking in order:
        1. As-drilled data (highest priority)
        2. Planned well data
        3. Vertical well data (fallback option)

        Args:
            drilled_df: DataFrame containing as-drilled well survey data
            planned_df: DataFrame containing planned well survey data
            vert_df: DataFrame containing vertical well survey data

        Returns:
            pd.DataFrame: The first non-empty DataFrame based on priority order.
            Will return vert_df even if empty if no other data is available.

        Notes:
            - Used to ensure visualization data is available even with partial surveys
            - Prioritizes actual drilled data over planned trajectories
            - Serves as a data selection failsafe for visualization methods

        Example:
            >>> selected_df = findPopulatedDataframeForSelection(
            ...     drilled_df=empty_df,
            ...     planned_df=populated_df,
            ...     vert_df=empty_df
            ... )
            >>> # Returns populated_df since drilled_df is empty
        """
        if not drilled_df.empty:
            return drilled_df
        elif not planned_df.empty:
            return planned_df
        else:
            return vert_df


    # def findPopulatedDataframeForSelection(self, drilled_df, planned_df, vert_df):
    #     if not drilled_df.empty:
    #         return drilled_df
    #         # If the first is empty, check the second DataFrame
    #     elif not planned_df.empty:
    #         return planned_df
    #         # If the first two are empty, default to the third DataFrame
    #     else:
    #         return vert_df

    def drawTSRPlat(self) -> None:
        """
        Renders a Township, Section, and Range (TSR) plat visualization with adjacent territories.

        This method creates a 2D visualization of plat data showing main and adjacent territories,
        complete with labels and boundaries. It processes three levels of adjacency:
        - Main plat areas (Order 0)
        - First-level adjacent plats (Order 1)
        - Second-level adjacent plats (Order 2)

        The visualization includes:
        1. Plat boundaries for all three adjacency levels
        2. Centered labels for each plat
        3. Automatic viewport centering on the main plat area
        4. Optional section labels based on checkbox state

        Args:
            self: Parent class instance containing required attributes:
                - ui: User interface elements
                - df_adjacent_plats: DataFrame with adjacency information
                - df_plat: DataFrame with plat geometry data
                - ax2d: Matplotlib axes for 2D plotting
                - canvas2d: Matplotlib canvas for rendering

        Attributes Modified:
            - used_plat_codes: List of unique plat codes in main area
            - used_plat_codes_for_boards: List of all unique plat codes
            - Various matplotlib artists (plats_2d_main, labels_plats_2d_main, etc.)

        Notes:
            - Requires fieldsTester1() helper function for geometry processing
            - Handles visibility toggling based on UI checkbox state
            - Updates the plot limits based on centroid calculation
            - Attempts to update dependent data via manipulateTheDfDocketDataDependingOnCheckboxes()
        """

        def fieldsTester1(df_field: pd.DataFrame) -> pd.DataFrame:
            """
            Processes field data to create geometric representations and labeling for visualization.

            Transforms raw field data into a geometric dataset by:
            1. Converting coordinate pairs to Point geometries
            2. Grouping points by concentration to form polygons
            3. Calculating centroids for each polygon
            4. Adding transformed labels

            Args:
                df_field (pd.DataFrame): Input DataFrame containing at minimum:
                    - Easting (float): X coordinates
                    - Northing (float): Y coordinates
                    - Conc (Any): Concentration or field identifier

            Returns:
                pd.DataFrame: Processed DataFrame containing:
                    - Conc: Original field identifier
                    - geometry: Polygon geometries formed from point groups
                    - centroid: Centroid point for each polygon
                    - label: Transformed string label

            Notes:
                - Assumes transform_string() helper function exists for label creation
                - Creates both point and polygon geometries for visualization
                - Handles merging and cleanup of intermediate geometric data
                - Uses Shapely geometry objects for spatial operations

            Example:
                >>> field_data = pd.DataFrame({
                ...     'Easting': [1.0, 2.0, 3.0],
                ...     'Northing': [1.0, 2.0, 3.0],
                ...     'Conc': ['A', 'A', 'B']
                ... })
                >>> result = fieldsTester1(field_data)
            """
            # Create point geometries from coordinates
            df_field['geometry'] = df_field.apply(
                lambda row: Point(row['Easting'], row['Northing']),
                axis=1
            )

            # Extract and process relevant fields
            used_fields = df_field[['Conc', 'Easting', 'Northing', 'geometry']]
            used_fields['geometry'] = used_fields.apply(
                lambda row: Point(row['Easting'], row['Northing']),
                axis=1
            )

            # Helper function to create polygons from coordinate groups
            def create_polygon(group: pd.DataFrame) -> Polygon:
                return Polygon(zip(group['Easting'], group['Northing']))

            # Create polygons grouped by concentration
            polygons = used_fields.groupby(
                'Conc',
                group_keys=False
            ).apply(create_polygon, include_groups=False).reset_index()

            # Rename geometry column
            polygons = polygons.rename(columns={0: 'geometry'})

            # Merge point and polygon data
            merged_data = used_fields.merge(polygons, on='Conc')
            merged_data = merged_data.drop('geometry_y', axis=1).rename(
                columns={'geometry_x': 'geometry'}
            )

            # Create final polygon dataset
            df_new = merged_data.groupby('Conc').apply(
                lambda x: Polygon(zip(x['Easting'], x['Northing'])),
                include_groups=False
            ).reset_index()

            # Set column names and add derived fields
            df_new.columns = ['Conc', 'geometry']
            df_new['centroid'] = df_new.apply(lambda x: x['geometry'].centroid, axis=1)
            df_new['label'] = df_new.apply(lambda x: transform_string(x['Conc']), axis=1)

            return df_new
        # def fieldsTester1(df_field):
        #     df_field['geometry'] = df_field.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)
        #     used_fields = df_field[['Conc', 'Easting', 'Northing', 'geometry']]
        #     used_fields['geometry'] = used_fields.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)
        #     def create_polygon(group):
        #         return Polygon(zip(group['Easting'], group['Northing']))
        #     # Use include_groups=False to exclude the grouping columns from the operation
        #     polygons = used_fields.groupby('Conc', group_keys=False).apply(create_polygon, include_groups=False).reset_index()
        #     # Rename the column containing the polygons
        #     polygons = polygons.rename(columns={0: 'geometry'})
        #     merged_data = used_fields.merge(polygons, on='Conc')
        #     merged_data = merged_data.drop('geometry_y', axis=1).rename(columns={'geometry_x': 'geometry'})
        #     df_new = merged_data.groupby('Conc').apply(lambda x: Polygon(zip(x['Easting'], x['Northing'])), include_groups=False).reset_index()
        #     df_new.columns = ['Conc', 'geometry']
        #     df_new['centroid'] = df_new.apply(lambda x: x['geometry'].centroid, axis=1)
        #     df_new['label'] = df_new.apply(lambda x: transform_string(x['Conc']), axis=1)
        #     return df_new
        def transform_string(s: str) -> str:
            """
            Transforms a well location string from compact format to readable format.

            Converts strings like "0102S03WA" to "1 2S 3W A" by:
            1. Extracting numeric and directional components
            2. Removing leading zeros
            3. Adding proper spacing

            Args:
                s (str): Input string in format "TTRRSDDDW[A-Z]" where:
                    - TT: Township number (2 digits)
                    - RRS: Range number with S direction (3 chars)
                    - DDDW: Distance number with W direction (3 chars)
                    - [A-Z]: Single letter designation

            Returns:
                str: Transformed string with removed leading zeros and added spaces.
                     Returns original string if pattern doesn't match.

            Notes:
                - Uses regex pattern matching to identify string components
                - Maintains directional indicators (S/W) in output
                - Preserves single letter designation without modification

            Example:
                >>> transform_string("0102S03WA")
                "1 2S 3W A"
                >>> transform_string("invalid")
                "invalid"
            """
            # Pattern matching for well location format
            parts = re.match(r'(\d{2})(\d{2}S)(\d{2}W)([A-Z])', s)

            # Return original string if pattern doesn't match
            if not parts:
                return s

            # Extract and transform components
            part1 = str(int(parts.group(1)))  # Township number without leading zeros
            part2 = str(int(parts.group(2)[:-1])) + parts.group(2)[-1]  # Range with S
            part3 = str(int(parts.group(3)[:-1])) + parts.group(3)[-1]  # Distance with W
            part4 = parts.group(4)  # Letter designation

            # Format with spaces between components
            return f"{part1} {part2} {part3} {part4}"
        # def transform_string(s):
        #     # Split the string into parts using regular expressions
        #     parts = re.match(r'(\d{2})(\d{2}S)(\d{2}W)([A-Z])', s)
        #     if not parts:
        #         return s  # If the string doesn't match the pattern, return it as is
        #
        #     # Remove leading zeros from each part
        #     part1 = str(int(parts.group(1)))
        #     part2 = str(int(parts.group(2)[:-1])) + parts.group(2)[-1]
        #     part3 = str(int(parts.group(3)[:-1])) + parts.group(3)[-1]
        #     part4 = parts.group(4)
        #
        #     return f"{part1} {part2} {part3} {part4}"
        # Initialize plat codes list
        self.used_plat_codes = []

        # Get current board data and filter adjacent plats
        board_data = self.ui.board_matter_lst_combobox.currentText()
        adjacent_all = self.df_adjacent_plats[
            self.df_adjacent_plats['Board_Docket'] == board_data
            ]
        df_plat_docket = self.df_plat[
            self.df_plat['Board_Docket'] == board_data
            ]

        # Filter adjacency orders
        adjacent_main = adjacent_all[adjacent_all['Order'] == 0]
        adjacent_1 = adjacent_all[adjacent_all['Order'] == 1]
        adjacent_2 = adjacent_all[adjacent_all['Order'] == 2]

        # Get plat data for each adjacency level
        adjacent_main_plats = df_plat_docket[
            df_plat_docket['Conc'].isin(adjacent_main['src_FullCo'].unique())
        ]
        adjacent_1_plats = df_plat_docket[
            df_plat_docket['Conc'].isin(adjacent_1['src_FullCo'].unique())
        ]
        adjacent_2_plats = df_plat_docket[
            df_plat_docket['Conc'].isin(adjacent_2['src_FullCo'].unique())
        ]

        # Process geometry data
        plat_data_main = fieldsTester1(adjacent_main_plats)
        plat_data_adjacent_1 = fieldsTester1(adjacent_1_plats)
        plat_data_adjacent_2 = fieldsTester1(adjacent_2_plats)

        # Create text labels with paths
        paths_main = [
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
            for coord, text in zip(plat_data_main['centroid'], plat_data_main['label'])
        ]
        paths_adjacent_1 = [
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
            for coord, text in zip(plat_data_adjacent_1['centroid'], plat_data_adjacent_1['label'])
        ]
        paths_adjacent_2 = [
            PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
            for coord, text in zip(plat_data_adjacent_2['centroid'], plat_data_adjacent_2['label'])
        ]

        # Set label paths
        self.labels_plats_2d_main.set_paths(paths_main)
        self.labels_plats_2d_1adjacent.set_paths(paths_adjacent_1)
        self.labels_plats_2d_2adjacent.set_paths(paths_adjacent_2)

        # Set geometry segments
        self.plats_2d_main.set_segments(
            plat_data_main['geometry'].apply(lambda x: x.exterior.coords)
        )
        self.plats_2d_1adjacent.set_segments(
            plat_data_adjacent_1['geometry'].apply(lambda x: x.exterior.coords)
        )
        self.plats_2d_2adjacent.set_segments(
            plat_data_adjacent_2['geometry'].apply(lambda x: x.exterior.coords)
        )

        # Calculate and set plot limits based on centroid
        all_polygons = unary_union(plat_data_main['geometry'].tolist())
        overall_centroid = all_polygons.centroid
        self.ax2d.set_xlim(overall_centroid.x - 10000, overall_centroid.x + 10000)
        self.ax2d.set_ylim(overall_centroid.y - 10000, overall_centroid.y + 10000)

        # Update plat codes and visibility
        self.used_plat_codes = plat_data_main['Conc'].unique().tolist()
        self.plats_2d_main.set_visible(True)
        self.plats_2d_1adjacent.set_visible(True)
        self.plats_2d_2adjacent.set_visible(True)

        # Handle label visibility based on checkbox
        label_visibility = self.ui.section_label_checkbox.isChecked()
        for labels in [self.labels_plats_2d_main,
                       self.labels_plats_2d_1adjacent,
                       self.labels_plats_2d_2adjacent]:
            labels.set_visible(True)  # Always visible per original logic

        # Compile all unique plat codes
        self.used_plat_codes_for_boards = list(set(
            plat_data_main['Conc'].unique().tolist() +
            plat_data_adjacent_1['Conc'].unique().tolist() +
            plat_data_adjacent_2['Conc'].unique().tolist()
        ))

        # Update canvas
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()

        # Try to update dependent data
        try:
            self.manipulateTheDfDocketDataDependingOnCheckboxes()
        except AttributeError:
            pass

        # board_data = self.ui.board_matter_lst_combobox.currentText()
        # adjacent_all = self.df_adjacent_plats[self.df_adjacent_plats['Board_Docket'] == board_data]
        # df_plat_docket = self.df_plat[self.df_plat['Board_Docket'] == board_data]
        #
        # """Isolate out each adjacent list by adjacency order"""
        # adjacent_main = adjacent_all[adjacent_all['Order'] == 0]
        # adjacent_1 = adjacent_all[adjacent_all['Order'] == 1]
        # adjacent_2 = adjacent_all[adjacent_all['Order'] == 2]
        #
        # """Get the plat data values for each adjacency list"""
        # adjacent_main_plats = df_plat_docket[df_plat_docket['Conc'].isin(adjacent_main['src_FullCo'].unique())]
        # adjacent_1_plats = df_plat_docket[df_plat_docket['Conc'].isin(adjacent_1['src_FullCo'].unique())]
        # adjacent_2_plats = df_plat_docket[df_plat_docket['Conc'].isin(adjacent_2['src_FullCo'].unique())]
        #
        # plat_data_main = fieldsTester1(adjacent_main_plats)
        # plat_data_adjacent_1 = fieldsTester1(adjacent_1_plats)
        # plat_data_adjacent_2 = fieldsTester1(adjacent_2_plats)
        #
        # """Set labels"""
        # paths_main = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red") for coord, text in zip(plat_data_main['centroid'], plat_data_main['label'])]
        # paths_adjacent_1 = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red") for coord, text in zip(plat_data_adjacent_1['centroid'], plat_data_adjacent_1['label'])]
        # paths_adjacent_2 = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red") for coord, text in zip(plat_data_adjacent_2['centroid'], plat_data_adjacent_2['label'])]
        # self.labels_plats_2d_main.set_paths(paths_main)
        # self.labels_plats_2d_1adjacent.set_paths(paths_adjacent_1)
        # self.labels_plats_2d_2adjacent.set_paths(paths_adjacent_2)
        #
        # """Set Paths"""
        # self.plats_2d_main.set_segments(plat_data_main['geometry'].apply(lambda x: x.exterior.coords))
        # self.plats_2d_1adjacent.set_segments(plat_data_adjacent_1['geometry'].apply(lambda x: x.exterior.coords))
        # self.plats_2d_2adjacent.set_segments(plat_data_adjacent_2['geometry'].apply(lambda x: x.exterior.coords))
        #
        # all_polygons = unary_union(plat_data_main['geometry'].tolist())
        # overall_centroid = all_polygons.centroid
        # centroid_x = overall_centroid.x
        # centroid_y = overall_centroid.y
        #
        # #
        # self.ax2d.set_xlim(centroid_x - 10000, centroid_x + 10000)
        # self.ax2d.set_ylim(centroid_y - 10000, centroid_y + 10000)
        #
        # self.used_plat_codes = plat_data_main['Conc'].unique().tolist()
        # self.plats_2d_main.set_visible(True)
        # self.plats_2d_1adjacent.set_visible(True)
        # self.plats_2d_2adjacent.set_visible(True)
        # if self.ui.section_label_checkbox.isChecked():
        #     self.labels_plats_2d_main.set_visible(True)
        #     self.labels_plats_2d_1adjacent.set_visible(True)
        #     self.labels_plats_2d_2adjacent.set_visible(True)
        # else:
        #     self.labels_plats_2d_main.set_visible(True)
        #     self.labels_plats_2d_1adjacent.set_visible(True)
        #     self.labels_plats_2d_2adjacent.set_visible(True)
        #
        # self.used_plat_codes_for_boards = plat_data_main['Conc'].unique().tolist() + plat_data_adjacent_1['Conc'].unique().tolist() + plat_data_adjacent_2['Conc'].unique().tolist()
        # self.used_plat_codes_for_boards = list(set(self.used_plat_codes_for_boards))
        # self.canvas2d.blit(self.ax2d.bbox)
        # self.canvas2d.draw()
        #
        # try:
        #     self.manipulateTheDfDocketDataDependingOnCheckboxes()
        # except AttributeError as e:
        #     pass
        # pass

    """This is going to manipulate and organize the data into new dataframes based on when the wells were drilled. This is used when the radio buttons are changed """

    def setupDataForBoardDrillingInformation(self):
        # Clear and prep the data
        self.df_docket_data = self.preprocessData(self.df_docket_data)

        # Initialize data containers
        self.planned_xy_2d, self.planned_xy_3d, self.drilled_xy_2d, self.drilled_xy_3d, self.currently_drilling_xy_2d, self.currently_drilling_xy_3d = [], [], [], [], [], []

        # Generate masks for data filtering
        mask_drilled, mask_planned, mask_drilling = self.generateMasks()

        # Generate age-based masks
        age_masks = self.createAgeMasks()

        # Clean data
        self.df_docket_data = self.cleanData(self.df_docket_data)

        # Generate dataframes based on conditions

        # For drilled
        drilled_dfs = self.generate_dataframes('drilled', mask_drilled, age_masks)
        # For planned
        planned_dfs = self.generate_dataframes('planned', mask_planned, age_masks)
        # For currently drilling
        currently_drilling_dfs = self.generate_dataframes('currently_drilling', mask_drilling, age_masks)


        drilled_dataframes = [drilled_dfs['drilled_year'], drilled_dfs['drilled_5years'], drilled_dfs['drilled_10years'], drilled_dfs['drilled_all']]
        planned_dataframes = [planned_dfs['planned_year'], planned_dfs['planned_5years'], planned_dfs['planned_10years'], planned_dfs['planned_all']]
        currently_drilling_dataframes = [currently_drilling_dfs['currently_drilling_year'], currently_drilling_dfs['currently_drilling_5years'], currently_drilling_dfs['currently_drilling_10years'], currently_drilling_dfs['currently_drilling_all']]


        # print(drilled_dataframes)
        # print(planned_dataframes)
        # Filter out planned data based on drilled data
        planned_dataframes = self.filterPlannedData(drilled_dataframes, planned_dataframes)

        # Prepare final data structures
        self.prepareFinalData(drilled_dataframes, planned_dataframes, currently_drilling_dataframes)

    def preprocessData(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocesses well data by removing duplicates, sorting, and handling missing ages.

        Performs the following operations in sequence:
        1. Removes duplicate rows keeping first occurrence
        2. Sorts data by API number
        3. Resets DataFrame index
        4. Fills missing well ages with 0

        Args:
            self: Parent class instance
            df (pd.DataFrame): Input DataFrame containing well data.
                Required columns:
                - APINumber: Well identification number
                - WellAge: Age of the well (can contain NaN values)

        Returns:
            pd.DataFrame: Processed DataFrame with:
                - No duplicates
                - Sorted by APINumber
                - Reset index
                - WellAge filled with 0 for missing values

        Notes:
            - Preserves all original columns except duplicates
            - Assumes APINumber is a valid sorting key
            - Treatment of NaN well ages as 0 typically indicates planned/permitted wells
            - Original index is dropped during reset

        Example:
            >>> df = pd.DataFrame({
            ...     'APINumber': [2, 1, 2, 3],
            ...     'WellAge': [5.0, None, 5.0, 3.0]
            ... })
            >>> processed_df = preprocessData(self, df)
            >>> processed_df['APINumber'].tolist()
            [1, 2, 3]
        """
        # Remove duplicates and sort
        df = df.drop_duplicates(keep='first')
        df = df.sort_values(by='APINumber')

        # Reset index and handle missing ages
        df = df.reset_index(drop=True)
        df['WellAge'] = df['WellAge'].fillna(0)

        return df

    # def preprocessData(self, df):
    #     df = df.drop_duplicates(keep='first').sort_values(by='APINumber').reset_index(drop=True)
    #     df['WellAge'] = df['WellAge'].fillna(0)
    #     return df
    def generateMasks(self) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Generates boolean masks for filtering well data based on drilling status and type.

        Creates three separate boolean masks for categorizing wells:
        1. Drilled wells (completed or vertical)
        2. Planned wells (permitted or planned vertical)
        3. Currently drilling wells

        Args:
            self: Parent class instance containing:
                - df_docket_data (pd.DataFrame): DataFrame with well information
                    Required columns:
                    - CitingType: Type of well citation
                    - CurrentWellStatus: Current status of the well

        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: Three boolean masks:
                - mask_drilled: True for already drilled/completed wells
                - mask_planned: True for planned/permitted wells
                - mask_drilling: True for currently drilling wells

        Notes:
            - CitingType values considered as drilled: ['asdrilled', 'vertical']
            - CitingType values considered as planned: ['planned', 'vertical']
            - CurrentWellStatus value for drilling: ['Drilling']
            - Masks can be used directly for DataFrame filtering

        Example:
            >>> drilled, planned, drilling = self.generateMasks()
            >>> drilled_wells = self.df_docket_data[drilled]
            >>> planned_wells = self.df_docket_data[planned]
            >>> drilling_wells = self.df_docket_data[drilling]
        """
        # Generate mask for drilled/completed wells
        mask_drilled = self.df_docket_data['CitingType'].isin(['asdrilled', 'vertical'])

        # Generate mask for planned/permitted wells
        mask_planned = self.df_docket_data['CitingType'].isin(['planned', 'vertical'])

        # Generate mask for currently drilling wells
        mask_drilling = self.df_docket_data['CurrentWellStatus'].isin(['Drilling'])

        return mask_drilled, mask_planned, mask_drilling

    # def generateMasks(self):
    #     mask_drilled = (self.df_docket_data['CitingType'].isin(['asdrilled', 'vertical']))
    #     mask_planned = (self.df_docket_data['CitingType'].isin(['planned', 'vertical']))
    #     mask_drilling = (self.df_docket_data['CurrentWellStatus'].isin(['Drilling']))
    #     return mask_drilled, mask_planned, mask_drilling
    def createAgeMasks(self) -> List[pd.Series]:
        """
        Creates boolean masks for filtering wells based on age thresholds.

        Generates four boolean masks representing different well age ranges:
        1. Wells up to 1 year old (≤12 months)
        2. Wells up to 5 years old (≤60 months)
        3. Wells up to 10 years old (≤120 months)
        4. All wells regardless of age (≤9999 months)

        Args:
            self: Parent class instance containing:
                - df_docket_data (pd.DataFrame): DataFrame with well information
                    Required columns:
                    - WellAge: Age of wells in months

        Returns:
            List[pd.Series]: List of four boolean masks where True indicates
            wells within the respective age thresholds:
            - mask[0]: Age ≤ 12 months
            - mask[1]: Age ≤ 60 months
            - mask[2]: Age ≤ 120 months
            - mask[3]: Age ≤ 9999 months (effectively all wells)

        Notes:
            - WellAge is expected to be in months
            - Missing/NaN ages should be handled before calling this function
            - Masks can be used directly for DataFrame filtering
            - The 9999 threshold effectively includes all wells

        Example:
            >>> age_masks = self.createAgeMasks()
            >>> new_wells = self.df_docket_data[age_masks[0]]  # Wells ≤ 1 year
            >>> mature_wells = self.df_docket_data[age_masks[2]]  # Wells ≤ 10 years
        """
        # Create list of boolean masks for different age thresholds
        return [
            (self.df_docket_data['WellAge'] <= 12),  # 1 year threshold
            (self.df_docket_data['WellAge'] <= 60),  # 5 year threshold
            (self.df_docket_data['WellAge'] <= 120),  # 10 year threshold
            (self.df_docket_data['WellAge'] <= 9999)  # All wells threshold
        ]

    # def createAgeMasks(self):
    #     return [
    #         (self.df_docket_data['WellAge'] <= 12),
    #         (self.df_docket_data['WellAge'] <= 60),
    #         (self.df_docket_data['WellAge'] <= 120),
    #         (self.df_docket_data['WellAge'] <= 9999)
    #     ]
    def cleanData(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the input DataFrame by removing rows with missing targeted elevation values.

        Performs basic data cleaning by dropping any rows where the 'Targeted Elevation'
        column contains null/NaN values. This ensures downstream calculations have valid
        elevation data to work with.

        Args:
            self: Parent class instance
            df (pd.DataFrame): Input DataFrame containing well data.
                Required columns:
                - Targeted Elevation: Well target elevation values (can contain NaN)

        Returns:
            pd.DataFrame: Cleaned DataFrame with:
                - All rows containing null targeted elevations removed
                - Original column structure preserved
                - Original index structure preserved

        Notes:
            - Rows with NaN values in other columns are preserved
            - No modifications are made to non-null values
            - Does not reset the index after dropping rows
            - Operation is not performed in-place; returns new DataFrame

        Example:
            >>> df = pd.DataFrame({
            ...     'Targeted Elevation': [100.0, None, 200.0],
            ...     'Other Data': [1, 2, 3]
            ... })
            >>> cleaned_df = cleanData(self, df)
            >>> len(cleaned_df)
            2
        """
        # Remove rows with missing targeted elevation values
        return df.dropna(subset=['Targeted Elevation'])

    # def generateDrilledDataframes(self, mask_drilled, age_masks):
    #     drilled_df_year = self.df_docket_data.loc[mask_drilled & age_masks[0]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     drilled_df_5years = self.df_docket_data.loc[mask_drilled & age_masks[1]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     drilled_df_10years = self.df_docket_data.loc[mask_drilled & age_masks[2]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     drilled_df_all = self.df_docket_data.loc[mask_drilled & age_masks[3]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     return drilled_df_year, drilled_df_5years, drilled_df_10years, drilled_df_all
    #
    # def generatePlannedDataframes(self, mask_planned, age_masks):
    #     planned_year = self.df_docket_data.loc[mask_planned & age_masks[0]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     planned_5years = self.df_docket_data.loc[mask_planned & age_masks[1]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     planned_10years = self.df_docket_data.loc[mask_planned & age_masks[2]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     planned_all = self.df_docket_data.loc[mask_planned & age_masks[3]].reset_index(drop=True).sort_values(
    #         by=['APINumber', 'MeasuredDepth'])
    #     return planned_year, planned_5years, planned_10years, planned_all
    #
    # def generateCurrentlyDrillingDataframes(self, mask_drilling, age_masks):
    #     currently_drilling_year = self.df_docket_data.loc[mask_drilling & age_masks[0]].reset_index(
    #         drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     currently_drilling_5years = self.df_docket_data.loc[mask_drilling & age_masks[1]].reset_index(
    #         drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     currently_drilling_10years = self.df_docket_data.loc[mask_drilling & age_masks[2]].reset_index(
    #         drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     currently_drilling_all = self.df_docket_data.loc[mask_drilling & age_masks[3]].reset_index(
    #         drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     return currently_drilling_year, currently_drilling_5years, currently_drilling_10years, currently_drilling_all
    def generate_dataframes(
            self,
            mask_type: Literal['drilled', 'planned', 'drilling'],
            mask: pd.Series,
            age_masks: list[pd.Series]
    ) -> Dict[str, pd.DataFrame]:
        """
        Generates filtered DataFrames based on well type and age ranges.

        Creates a dictionary of DataFrames filtered by the specified mask type
        (drilled/planned/drilling) and four different age ranges. Each DataFrame
        is sorted and index-reset for consistency.

        Args:
            self: Parent class instance containing:
                - df_docket_data (pd.DataFrame): Source DataFrame with well information
                    Required columns:
                    - APINumber: Well identification number
                    - MeasuredDepth: Well depth measurement
            mask_type (Literal['drilled', 'planned', 'drilling']): Type of wells to filter
            mask (pd.Series): Boolean mask identifying well type
            age_masks (list[pd.Series]): List of 4 boolean masks for age filtering:
                - age_masks[0]: ≤ 12 months
                - age_masks[1]: ≤ 60 months
                - age_masks[2]: ≤ 120 months
                - age_masks[3]: All wells

        Returns:
            Dict[str, pd.DataFrame]: Dictionary containing filtered DataFrames:
                - {mask_type}_year: Wells within 1 year
                - {mask_type}_5years: Wells within 5 years
                - {mask_type}_10years: Wells within 10 years
                - {mask_type}_all: All wells of specified type

        Notes:
            - All DataFrames are sorted by APINumber and MeasuredDepth
            - Indexes are reset for all DataFrames
            - Empty DataFrames may be returned if no wells match criteria
            - Original data is not modified

        Example:
            >>> drilled_dfs = generate_dataframes(self, 'drilled', mask_drilled, age_masks)
            >>> print(f"New drilled wells: {len(drilled_dfs['drilled_year'])}")
            >>> print(f"All drilled wells: {len(drilled_dfs['drilled_all'])}")
        """
        # Initialize dictionary for storing filtered DataFrames
        dataframes = {}

        # Generate DataFrames for each age range
        for i, age_range in enumerate(['year', '5years', '10years', 'all']):
            # Create dictionary key combining mask type and age range
            key = f"{mask_type}_{age_range}"

            # Filter data using combined masks and sort
            dataframes[key] = self.df_docket_data.loc[mask & age_masks[i]]
            dataframes[key] = dataframes[key].reset_index(drop=True).sort_values(
                by=['APINumber', 'MeasuredDepth']
            )

        return dataframes

    # def generate_dataframes(self, mask_type, mask, age_masks):
    #     # Initialize dictionary for each type of age range (year, 5years, etc.)
    #     dataframes = {}
    #     for i, age_range in enumerate(['year', '5years', '10years', 'all']):
    #         key = f"{mask_type}_{age_range}"
    #         dataframes[key] = self.df_docket_data.loc[mask & age_masks[i]].reset_index(drop=True).sort_values(
    #             by=['APINumber', 'MeasuredDepth']
    #         )
    #     return dataframes
    def filterPlannedData(
            self,
            drilled_dataframes: List[pd.DataFrame],
            planned_dataframes: List[pd.DataFrame]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Filters planned well data by comparing against drilled wells for different time periods.

        For each time period (1 year, 5 years, 10 years, and all time), removes planned wells
        that have already been drilled from the planned wells dataset.

        Args:
            self: Parent class instance containing filterPlannedDataForYear method
            drilled_dataframes (List[pd.DataFrame]): List of 4 DataFrames containing drilled well data:
                - drilled_dataframes[0]: Wells drilled within 1 year
                - drilled_dataframes[1]: Wells drilled within 5 years
                - drilled_dataframes[2]: Wells drilled within 10 years
                - drilled_dataframes[3]: All drilled wells
            planned_dataframes (List[pd.DataFrame]): List of 4 DataFrames containing planned well data:
                - planned_dataframes[0]: Wells planned within 1 year
                - planned_dataframes[1]: Wells planned within 5 years
                - planned_dataframes[2]: Wells planned within 10 years
                - planned_dataframes[3]: All planned wells

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
                - planned_year: Filtered planned wells for 1 year
                - planned_5years: Filtered planned wells for 5 years
                - planned_10years: Filtered planned wells for 10 years
                - planned_all: Filtered planned wells for all time

        Notes:
            - Uses filterPlannedDataForYear helper method for each time period
            - Maintains original DataFrame structure and column organization
            - Does not modify input DataFrames
            - Returns empty DataFrames if all planned wells have been drilled

        Example:
            >>> filtered_planned = filterPlannedData(self, drilled_dfs, planned_dfs)
            >>> print(f"Remaining planned wells (1yr): {len(filtered_planned[0])}")
        """
        # Filter planned wells for each time period using helper method
        planned_year = self.filterPlannedDataForYear(
            drilled_dataframes[0], planned_dataframes[0])  # 1 year filter

        planned_5years = self.filterPlannedDataForYear(
            drilled_dataframes[1], planned_dataframes[1])  # 5 year filter

        planned_10years = self.filterPlannedDataForYear(
            drilled_dataframes[2], planned_dataframes[2])  # 10 year filter

        planned_all = self.filterPlannedDataForYear(
            drilled_dataframes[3], planned_dataframes[3])  # All time filter

        return planned_year, planned_5years, planned_10years, planned_all

    # def filterPlannedData(self, drilled_dataframes, planned_dataframes):
    #     planned_year = self.filterPlannedDataForYear(drilled_dataframes[0], planned_dataframes[0])
    #     planned_5years = self.filterPlannedDataForYear(drilled_dataframes[1], planned_dataframes[1])
    #     planned_10years = self.filterPlannedDataForYear(drilled_dataframes[2], planned_dataframes[2])
    #     planned_all = self.filterPlannedDataForYear(drilled_dataframes[3], planned_dataframes[3])
    #     return planned_year, planned_5years, planned_10years, planned_all
    def filterPlannedDataForYear(
            self,
            drilled_df: pd.DataFrame,
            planned_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filters planned wells by removing those that have been drilled or are currently drilling.

        Takes a DataFrame of planned wells and removes any wells that:
        1. Already exist in the drilled wells dataset (based on APINumber)
        2. Have a current status of "Drilling"

        Args:
            self: Parent class instance
            drilled_df (pd.DataFrame): DataFrame containing drilled well data
                Required columns:
                - APINumber: Unique well identifier
            planned_df (pd.DataFrame): DataFrame containing planned well data
                Required columns:
                - APINumber: Unique well identifier
                - CurrentWellStatus: Current status of the well

        Returns:
            pd.DataFrame: Filtered planned wells DataFrame with:
                - Wells that exist in drilled_df removed
                - Wells with 'Drilling' status removed
                - All other columns and data preserved
                - Original index structure maintained

        Notes:
            - Uses APINumber for well identification and matching
            - Case-sensitive matching for 'Drilling' status
            - Does not modify input DataFrames
            - Returns empty DataFrame if all planned wells are filtered out

        Example:
            >>> filtered_planned = filterPlannedDataForYear(
            ...     drilled_df=drilled_wells,
            ...     planned_df=planned_wells
            ... )
            >>> print(f"Remaining planned wells: {len(filtered_planned)}")
        """
        # Filter out wells that are either drilled or currently drilling
        planned_year = planned_df[
            ~planned_df['APINumber'].isin(drilled_df['APINumber']) &
            (planned_df['CurrentWellStatus'] != 'Drilling')
            ]

        return planned_year

    # def filterPlannedDataForYear(self, drilled_df, planned_df):
    #     planned_year = planned_df[
    #         ~planned_df['APINumber'].isin(drilled_df['APINumber']) & (planned_df['CurrentWellStatus'] != 'Drilling')]
    #     return planned_year
    def prepareFinalData(
            self,
            drilled_dataframes: Dict[str, pd.DataFrame],
            planned_dataframes: Dict[str, pd.DataFrame],
            currently_drilling_dataframes: Dict[str, pd.DataFrame]
    ) -> None:
        """
        Prepares and processes the final well data for all well categories.

        Stores well data by category (drilled, planned, currently drilling) and processes
        spatial (XY) coordinates for each category. Updates instance attributes with
        processed data.

        Args:
            drilled_dataframes (Dict[str, pd.DataFrame]): Dictionary of drilled well DataFrames
                Keys: 'drilled_year', 'drilled_5years', 'drilled_10years', 'drilled_all'
            planned_dataframes (Dict[str, pd.DataFrame]): Dictionary of planned well DataFrames
                Keys: 'planned_year', 'planned_5years', 'planned_10years', 'planned_all'
            currently_drilling_dataframes (Dict[str, pd.DataFrame]): Dictionary of currently drilling well DataFrames
                Keys: 'drilling_year', 'drilling_5years', 'drilling_10years', 'drilling_all'

        Notes:
            - Updates instance attributes:
                self.drilled: Stores drilled well data
                self.planned: Stores planned well data
                self.currently_drilling: Stores currently drilling well data
            - Processes XY coordinates for each well category using processXYData method
            - Original DataFrames are not modified
            - Empty DataFrames are handled gracefully

        Side Effects:
            - Modifies instance attributes (self.drilled, self.planned, self.currently_drilling)
            - Calls processXYData which may modify additional instance attributes
        """
        # Store DataFrames as instance attributes
        self.drilled = drilled_dataframes
        self.planned = planned_dataframes
        self.currently_drilling = currently_drilling_dataframes

        # Process spatial coordinates for each well category
        self.processXYData(drilled_dataframes, 'drilled')  # Process drilled wells XY data
        self.processXYData(planned_dataframes, 'planned')  # Process planned wells XY data
        self.processXYData(currently_drilling_dataframes, 'currently_drilling')  # Process drilling wells XY data

    # def prepareFinalData(self, drilled_dataframes, planned_dataframes, currently_drilling_dataframes):
    #     self.drilled = drilled_dataframes
    #     self.planned = planned_dataframes
    #     self.currently_drilling = currently_drilling_dataframes
    #
    #     # Process XY data for each category
    #     self.processXYData(drilled_dataframes, 'drilled')
    #     self.processXYData(planned_dataframes, 'planned')
    #     self.processXYData(currently_drilling_dataframes, 'currently_drilling')
    def processXYData(            self,            dataframes: Dict[str, pd.DataFrame],            data_type: Literal['drilled', 'planned', 'currently_drilling']    ) -> None:
        """
        Processes spatial (XY) coordinate data for each well dataframe in a category.

        Iterates through dataframes of a specific well type and processes their spatial
        coordinates using the processSingleDataframe helper method. Handles different
        time periods (1 year, 5 years, 10 years, all) for each well category.

        Args:
            self: Parent class instance containing:
                - processSingleDataframe method for individual DataFrame processing
            dataframes (Dict[str, pd.DataFrame]): Dictionary of well DataFrames
                Keys expected in format: f"{data_type}_{time_period}"
                where time_period is one of: year, 5years, 10years, all
            data_type (Literal['drilled', 'planned', 'currently_drilling']):
                Category of wells being processed

        Notes:
            - Processes spatial coordinates for visualization purposes
            - Each DataFrame is processed sequentially
            - Order of processing matches time period sequence:
                1. year (≤12 months)
                2. 5years (≤60 months)
                3. 10years (≤120 months)
                4. all
            - Relies on processSingleDataframe method for actual coordinate processing

        Side Effects:
            - Calls processSingleDataframe which may modify visualization attributes
            - May update plot data or other visualization components

        Example:
            >>> processXYData(self, drilled_dataframes, 'drilled')
        """
        # Process each DataFrame in the dictionary
        for i, df in enumerate(dataframes):
        # Call helper method to process individual DataFrame
            self.processSingleDataframe(df, data_type, i)

    # def processXYData(self, dataframes, data_type):
    def processSingleDataframe(
            self,
            df: pd.DataFrame,
            data_type: Literal['drilled', 'planned', 'currently_drilling'],
            index: int
    ) -> None:
        """
        Processes a single well DataFrame to extract and store 2D and 3D spatial coordinates.

        Extracts XY coordinates and organizes them for both 2D and 3D visualization purposes.
        The processed data is stored in instance attributes for later plotting.

        Args:
            self: Parent class instance containing:
                - createXYPointsDict method for coordinate extraction
                - {data_type}_xy_2d attribute lists for 2D plotting
                - {data_type}_xy_3d attribute lists for 3D plotting
            df (pd.DataFrame): Well data DataFrame containing:
                Required columns:
                - APINumber: Unique well identifier
                - X: X coordinate in state plane
                - Y: Y coordinate in state plane
            data_type (Literal['drilled', 'planned', 'currently_drilling']):
                Category of wells being processed
            index (int): Index for the time period being processed (0=1yr, 1=5yr, 2=10yr, 3=all)

        Notes:
            - Creates separate point collections for 2D and 3D visualization
            - Points are organized by API number for consistent well identification
            - Handles missing or invalid coordinates gracefully
            - Data is appended to existing visualization lists

        Side Effects:
            - Modifies instance attributes:
                - self.{data_type}_xy_2d: List of 2D coordinate sets
                - self.{data_type}_xy_3d: List of 3D coordinate sets

        Example:
            >>> processSingleDataframe(df_wells, 'drilled', 0)
            # Updates self.drilled_xy_2d[0] and self.drilled_xy_3d[0] with new coordinates
        """
        # Generate dictionary of XY points for each well
        xy_points_dict = self.createXYPointsDict(df)

        # Get unique API numbers from the DataFrame
        apinums: Set[str] = set(df['APINumber'])

        # Create attribute keys for storing coordinates
        xy_2d_key = f"{data_type}_xy_2d"
        xy_3d_key = f"{data_type}_xy_3d"

        # Extract 2D coordinates (X,Y) for visualization
        xy_2d_data = [[r[:2] for r in v] for k, v in xy_points_dict.items()
                      if k in apinums]

        # Extract 3D coordinates (Z coordinates) for visualization
        xy_3d_data = [[r[2:] for r in v] for k, v in xy_points_dict.items()
                      if k in apinums]

        # Store processed coordinate data in instance attributes
        getattr(self, xy_2d_key).append(xy_2d_data)
        getattr(self, xy_3d_key).append(xy_3d_data)

    # def processSingleDataframe(self, df, data_type, index):
    #     xy_points_dict = self.createXYPointsDict(df)
    #     apinums = set(df['APINumber'])
    #
    #     xy_2d_key = f"{data_type}_xy_2d"
    #     xy_3d_key = f"{data_type}_xy_3d"
    #
    #     xy_2d_data = [[r[:2] for r in v] for k, v in xy_points_dict.items() if k in apinums]
    #     xy_3d_data = [[r[2:] for r in v] for k, v in xy_points_dict.items() if k in apinums]
    #
    #     getattr(self, xy_2d_key).append(xy_2d_data)
    #     getattr(self, xy_3d_key).append(xy_3d_data)
    def createXYPointsDict(
            self,
            df: pd.DataFrame
    ) -> Dict[str, List[List[float]]]:
        """
        Creates a dictionary mapping API numbers to their coordinate points and elevation data.

        Groups well data by API number and creates coordinate lists containing surface
        coordinates (X,Y), state plane coordinates (SPX,SPY) and targeted elevation for
        each well.

        Args:
            self: Parent class instance
            df (pd.DataFrame): Well data DataFrame containing:
                Required columns:
                - APINumber: Unique well identifier
                - X: Surface X coordinate
                - Y: Surface Y coordinate
                - SPX: State plane X coordinate
                - SPY: State plane Y coordinate
                - Targeted Elevation: Well's target elevation

        Returns:
            Dict[str, List[List[float]]]: Dictionary where:
                - Keys: API numbers (str)
                - Values: List of coordinate lists, each containing:
                    [x, y, spx, spy, z] where:
                    - x,y: Surface coordinates
                    - spx,spy: State plane coordinates
                    - z: Targeted elevation

        Notes:
            - All coordinate values are converted to float type
            - Handles missing values by converting to float (may result in NaN)
            - Groups data by APINumber to maintain well identity
            - Coordinates are organized for both 2D and 3D visualization use

        Example:
            >>> xy_dict = createXYPointsDict(well_df)
            >>> first_well = next(iter(xy_dict.values()))
            >>> print(f"First well coordinates: {first_well[0]}")
            First well coordinates: [1234.5, 5678.9, 1000.0, 2000.0, 3500.0]
        """
        return {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in
                zip(g['X'].astype(float),
                    g['Y'].astype(float),
                    g['SPX'].astype(float),
                    g['SPY'].astype(float),
                    g['Targeted Elevation'].astype(float))]
            for k, g in df.groupby('APINumber')}
    # def createXYPointsDict(self, df):
    #     return {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in
    #                 zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float),
    #                     g['Targeted Elevation'].astype(float))] for k, g in df.groupby('APINumber')}


    # def setupDataForBoardDrillingInformation(self):
    #     def filterPlannedData(df1, df2):
    #         planned_year = df2[~df2['APINumber'].isin(df1['APINumber']) & (df2['CurrentWellStatus'] != 'Drilling')]
    #         return planned_year
    #
    #     # Clear and prep the data
    #     self.df_docket_data = self.df_docket_data.drop_duplicates(keep='first').sort_values(by='APINumber').reset_index(drop=True)
    #     self.df_docket_data['WellAge'] = self.df_docket_data['WellAge'].fillna(0)
    #
    #     self.planned_xy_2d, self.planned_xy_3d, self.drilled_xy_2d, self.drilled_xy_3d, self.currently_drilling_xy_2d, self.currently_drilling_xy_3d = [], [], [], [], [], []
    #
    #     # generate masks that will be used for filtering the data (based on drilled, planned, drilling, etc. Honestly, vertical isn't necessary
    #
    #     mask_drilled = (self.df_docket_data['CitingType'].isin(['asdrilled', 'vertical']))
    #     mask_planned = (self.df_docket_data['CitingType'].isin(['planned', 'vertical']))
    #     mask_drilling = (self.df_docket_data['CurrentWellStatus'].isin(['Drilling']))
    #
    #     # Generate masks on df_docket_data (which is docket data but also has directional surveys) based on the age in months
    #     age_masks = [(self.df_docket_data['WellAge'] <= 12),
    #                  (self.df_docket_data['WellAge'] <= 60),
    #                  (self.df_docket_data['WellAge'] <= 120),
    #                  (self.df_docket_data['WellAge'] <= 9999)]
    #
    #     # Remove any null data in targeted elevation
    #     self.df_docket_data = self.df_docket_data.dropna(subset=['Targeted Elevation'])
    #
    #     # Using the two massks, generate 4x dataframes for each parameter that can then be referred back to.
    #     drilled_df_year = self.df_docket_data.loc[mask_drilled & age_masks[0]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     drilled_df_5years = self.df_docket_data.loc[mask_drilled & age_masks[1]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     drilled_df_10years = self.df_docket_data.loc[mask_drilled & age_masks[2]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     drilled_df_all = self.df_docket_data.loc[mask_drilled & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #
    #     planned_year = self.df_docket_data.loc[mask_planned & age_masks[0]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     planned_5years = self.df_docket_data.loc[mask_planned & age_masks[1]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     planned_10years = self.df_docket_data.loc[mask_planned & age_masks[2]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     planned_all = self.df_docket_data.loc[mask_planned & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #
    #     # filter out data is currently being drilled.
    #     planned_year = filterPlannedData(drilled_df_year, planned_year)
    #     planned_5years = filterPlannedData(drilled_df_5years, planned_5years)
    #     planned_10years = filterPlannedData(drilled_df_10years, planned_10years)
    #     planned_all = filterPlannedData(drilled_df_all, planned_all)
    #
    #     currently_drilling_year = self.df_docket_data.loc[mask_drilling & age_masks[0]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     currently_drilling_5years = self.df_docket_data.loc[mask_drilling & age_masks[1]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     currently_drilling_10years = self.df_docket_data.loc[mask_drilling & age_masks[2]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #     currently_drilling_all = self.df_docket_data.loc[mask_drilling & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
    #
    #     # turn into tuples
    #     self.drilled = (drilled_df_year, drilled_df_5years, drilled_df_10years, drilled_df_all)
    #     self.planned = (planned_year, planned_5years, planned_10years, planned_all)
    #     self.currently_drilling = (currently_drilling_year, currently_drilling_5years, currently_drilling_10years, currently_drilling_all)
    #     out1 = drilled_df_all['APINumber'].unique().tolist()
    #     out2 = planned_all['APINumber'].unique().tolist()
    #     out3 = currently_drilling_all['APINumber'].unique().tolist()
    #     full = out1 + out2 + out3
    #
    #     # just get rid of those vertical things
    #     for i in range(4):
    #         self.drilled[i]['CitingType'] = 'asdrilled'
    #         self.planned[i]['CitingType'] = 'planned'
    #
    #     # create dictionaries of the data for further manipulationg
    #     xy_points_dict_drilled = {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float), g['Targeted Elevation'].astype(float))] for k, g in drilled_df_all.groupby('APINumber')}
    #     xy_points_dict_planned = {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float), g['Targeted Elevation'].astype(float))] for k, g in planned_all.groupby('APINumber')}
    #     xy_points_dict_drilling = {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float), g['Targeted Elevation'].astype(float))] for k, g in currently_drilling_all.groupby('APINumber')}
    #
    #     # Get the api numbers for each column
    #     drilled_apinums_year = set(self.drilled[0]['APINumber'])
    #     drilled_apinums_5years = set(self.drilled[1]['APINumber'])
    #     drilled_apinums_10years = set(self.drilled[2]['APINumber'])
    #     drilled_apinums_all = set(self.drilled[3]['APINumber'])
    #
    #     planned_apinums_year = set(self.planned[0]['APINumber'])
    #     planned_apinums_5years = set(self.planned[1]['APINumber'])
    #     planned_apinums_10years = set(self.planned[2]['APINumber'])
    #     planned_apinums_all = set(self.planned[3]['APINumber'])
    #
    #     drilling_apinums_year = set(self.currently_drilling[3]['APINumber'])
    #     drilling_apinums_5years = set(self.currently_drilling[3]['APINumber'])
    #     drilling_apinums_10years = set(self.currently_drilling[3]['APINumber'])
    #     drilling_apinums_all = set(self.currently_drilling[3]['APINumber'])
    #
    #     # Assemble these into lists that are easier to call later (so when the radio button is clicked, it immediately knows what data to call)
    #     self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_year])
    #     self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_year])
    #
    #     self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_5years])
    #     self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_5years])
    #
    #     self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_10years])
    #     self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_10years])
    #
    #     self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_all])
    #     self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_all])
    #
    #     self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_year])
    #     self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_year])
    #
    #     self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_5years])
    #     self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_5years])
    #
    #     self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_10years])
    #     self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_10years])
    #
    #     self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_all])
    #     self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_all])
    #
    #     self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_year])
    #     self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_year])
    #
    #     self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_5years])
    #     self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_5years])
    #
    #     self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_10years])
    #     self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_10years])
    #
    #     self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_all])
    #     self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_all])

    def returnWellDataDependingOnParametersTest(self) -> None:
        """
        Updates instance attributes with well data based on selected time period radio button.

        Retrieves the currently selected time period from the UI radio button group and
        updates relevant instance attributes with corresponding well data and spatial
        coordinates for visualization.

        Args:
            self: Parent class instance containing:
                Required UI elements:
                - ui.drilling_within_button_group: QButtonGroup for time period selection
                Required data attributes:
                - drilled, planned, currently_drilling: DataFrames by time period
                - *_xy_2d, *_xy_3d: Spatial coordinate lists by time period

        Side Effects:
            Updates the following instance attributes based on selected time period:
            DataFrames:
            - self.drilled_df: Drilled wells data
            - self.planned_df: Planned wells data
            - self.currently_drilling_df: Currently drilling wells data

            2D Visualization Data:
            - self.drilled_segments: Drilled wells 2D coordinates
            - self.planned_segments: Planned wells 2D coordinates
            - self.currently_drilling_segments: Drilling wells 2D coordinates

            3D Visualization Data:
            - self.drilled_segments_3d: Drilled wells 3D coordinates
            - self.planned_segments_3d: Planned wells 3D coordinates
            - self.currently_drilling_segments_3d: Drilling wells 3D coordinates

        Notes:
            - Time period index (id_1) corresponds to:
              0: 1 year
              1: 5 years
              2: 10 years
              3: All time
            - All data structures must be pre-populated with corresponding time period data
            - No validation is performed on the button group checked state
        """
        # Get selected time period from UI radio button group
        id_1 = self.ui.drilling_within_button_group.checkedId()

        # Update DataFrame attributes for each well category
        self.drilled_df = self.drilled[id_1]
        self.planned_df = self.planned[id_1]
        self.currently_drilling_df = self.currently_drilling[id_1]

        # Update 2D visualization coordinates
        self.drilled_segments = self.drilled_xy_2d[id_1]
        self.planned_segments = self.planned_xy_2d[id_1]
        self.currently_drilling_segments = self.currently_drilling_xy_2d[id_1]

        # Update 3D visualization coordinates
        self.drilled_segments_3d = self.drilled_xy_3d[id_1]
        self.planned_segments_3d = self.planned_xy_3d[id_1]
        self.currently_drilling_segments_3d = self.currently_drilling_xy_3d[id_1]
    # def returnWellDataDependingOnParametersTest(self):
    #     id_1 = self.ui.drilling_within_button_group.checkedId()
    #     self.drilled_df = self.drilled[id_1]
    #     self.planned_df = self.planned[id_1]
    #     self.currently_drilling_df = self.currently_drilling[id_1]
    #     self.drilled_segments = self.drilled_xy_2d[id_1]
    #     self.drilled_segments_3d = self.drilled_xy_3d[id_1]
    #     self.planned_segments = self.planned_xy_2d[id_1]
    #     self.planned_segments_3d = self.planned_xy_3d[id_1]
    #     self.currently_drilling_segments = self.currently_drilling_xy_2d[id_1]
    #     self.currently_drilling_segments_3d = self.currently_drilling_xy_3d[id_1]
    #     # self.manipulateTheDfDocketDataDependingOnCheckboxes()

    """This is the main function that serves the biggest purpose. It looks at what check boxes are currently activated and manipulates the data accordingly."""


    # def manipulateTheDfDocketDataDependingOnCheckboxes(self):
    #     drilled_segments, planned_segments, currently_drilling_segments = (
    #         self.drilled_segments,
    #         self.planned_segments,
    #         self.currently_drilling_segments,
    #     )
    #     drilled_segments_3d, planned_segments_3d, currently_drilling_segments_3d = (
    #         self.drilled_segments_3d,
    #         self.planned_segments_3d,
    #         self.currently_drilling_segments_3d,
    #     )
    #     drilled_df, planned_df, currently_drilling_df = (
    #         self.drilled_df,
    #         self.planned_df,
    #         self.currently_drilling_df,
    #     )
    #
    #     # 1. Process API Numbers and filter segments
    #     def platBounded(df, segments, segments_3d):
    #         df = df.sort_values(by=['APINumber', 'MeasuredDepth'])
    #         api = df[['APINumber']].drop_duplicates().reset_index(drop=True)
    #         api['index'] = api.index
    #         merged = pd.merge(api, df, on='APINumber')
    #         segments = [segments[i] for i in merged['index'].unique()]
    #         segments_3d = [segments_3d[i] for i in merged['index'].unique()]
    #         return df, segments, segments_3d
    #
    #     drilled_df, drilled_segments, drilled_segments_3d = platBounded(
    #         drilled_df, drilled_segments, drilled_segments_3d
    #     )
    #     planned_df, planned_segments, planned_segments_3d = platBounded(
    #         planned_df, planned_segments, planned_segments_3d
    #     )
    #     currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d = platBounded(
    #         currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d
    #     )
    #
    #     # 2. Helper to restrict data by APINumber
    #     def restrict_by_api(df):
    #         return df.groupby('APINumber').first().reset_index()
    #
    #     drilled_df_restricted = restrict_by_api(drilled_df)
    #     planned_df_restricted = restrict_by_api(planned_df)
    #     currently_drilling_df_restricted = restrict_by_api(currently_drilling_df)
    #
    #     # 3. Update color and width based on masks
    #     def update_color_and_width(mask, df, param_df, color_col, width=1.5):
    #         param_df.loc[mask, 'color'] = df.loc[mask, color_col]
    #         param_df.loc[mask, 'width'] = width
    #
    #     # 4. Apply well types and update visuals
    #     def wellChecked(type, column, df, param_df, color_col):
    #         mask = df[column] == type
    #         update_color_and_width(mask, df, param_df, color_col)
    #
    #     def wellCheckedMultiple(types, column, df, param_df, color_col):
    #         mask = df[column].isin(types)
    #         update_color_and_width(mask, df, param_df, color_col)
    #
    #     # 5. Handle checkboxes for different well types
    #     def apply_checkboxes_for_well_types():
    #         if self.ui.oil_well_check.isChecked():
    #             wellChecked('Oil Well', 'CurrentWellType', drilled_df_restricted, df_drilled_parameters,
    #                         'WellTypeColor')
    #         if self.ui.gas_well_check.isChecked():
    #             wellChecked('Gas Well', 'CurrentWellType', planned_df_restricted, df_planned_parameters,
    #                         'WellTypeColor')
    #         if self.ui.water_disposal_check.isChecked():
    #             wellCheckedMultiple(['Water Disposal Well', 'Oil Well/Water Disposal Well'], 'CurrentWellType',
    #                                 currently_drilling_df_restricted, df_drilling_parameters, 'WellTypeColor')
    #         # Add further checks similarly...
    #
    #     # 6. Set visibility of wells and draw models based on parameters
    #     def set_visibility_and_draw(well_check, segments, colors, widths, is_visible):
    #         if well_check.isChecked():
    #             self.drawModelBasedOnParameters2d(self.all_wells_2d_asdrilled, segments, colors, widths, self.ax2d,
    #                                               self.all_wells_2d_vertical_asdrilled)
    #             self.drawModelBasedOnParameters(self.all_wells_3d_asdrilled, segments, colors, widths, self.ax3d)
    #             self.all_wells_2d_asdrilled.set_visible(is_visible)
    #             self.all_wells_3d_asdrilled.set_visible(is_visible)
    #             self.all_wells_2d_vertical_asdrilled.set_visible(is_visible)
    #         else:
    #             self.all_wells_2d_asdrilled.set_visible(False)
    #             self.all_wells_3d_asdrilled.set_visible(False)
    #             self.all_wells_2d_vertical_asdrilled.set_visible(False)
    #
    #     # 7. Process each checkbox type and handle visibility
    #     set_visibility_and_draw(self.ui.asdrilled_check, drilled_segments, drilled_colors_init, drilled_line_width,
    #                             True)
    #     set_visibility_and_draw(self.ui.planned_check, planned_segments, planned_colors_init, planned_line_width, True)
    #     set_visibility_and_draw(self.ui.currently_drilling_check, currently_drilling_segments,
    #                             currently_drilling_colors_init, currently_drilling_width, True)
    #
    #     # Update and redraw
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()
    #     self.canvas3d.blit(self.ax3d.bbox)
    #     self.canvas3d.draw()


    def manipulateTheDfDocketDataDependingOnCheckboxes(self):
        """
           Main function for managing well visualization based on UI checkbox states.

           Controls the display of different well types (drilled, planned, currently drilling)
           and their properties in both 2D and 3D views. Handles well filtering, visibility,
           styling, and related UI elements like field names.

           Attributes Modified:
               currently_used_lines (DataFrame): Tracks which well lines are currently displayed
               field_sections (Artist): Visual elements for field sections
               labels_field (Artist): Text labels for fields
               Various matplotlib artists for well visualization

           Side Effects:
               - Updates 2D and 3D matplotlib canvases
               - Modifies well line visibility and styling
               - Updates field name labels
               - Adjusts 3D view limits based on well positions
               - Triggers well type/status filtering

           Processing Steps:
               1. Initializes local data references
               2. Sets up data parameters for each well category
               3. Applies type/status filtering
               4. Handles field name visibility
               5. Processes well display parameters
               6. Toggles visibility for different well categories
               7. Adjusts 3D view boundaries
               8. Updates visualization canvases

           Notes:
               - Central function for well visualization control
               - Connected to multiple UI checkbox events
               - Manages both 2D and 3D visualizations
               - Handles three main well categories:
                   * As-drilled wells
                   * Planned wells
                   * Currently drilling wells
               - Maintains visualization consistency across views
               - Uses helper functions for data setup and display

           Dependencies:
               - setupData(): Prepares well data parameters
               - statusAndTypesEnabler(): Manages well filtering
               - toggle_well_display(): Controls well visibility
               - calculate_centroid_np(): Computes 3D view center
           """
        def platBounded(
                df: pd.DataFrame,
                segments: List[List[List[float]]],
                segments_3d: List[List[List[float]]]
        ) -> Tuple[pd.DataFrame, List[List[List[float]]], List[List[List[float]]]]:
            """
            Filters and reorders well data and segments based on API numbers and measured depth.

            Sorts well data by API number and measured depth, then filters the 2D and 3D
            segment data to match only the wells present in the DataFrame. Maintains data
            consistency across different representations of the same wells.

            Args:
                df (pd.DataFrame): Well data containing:
                    Required columns:
                    - APINumber: Unique well identifier
                    - MeasuredDepth: Depth measurement along wellbore
                segments (List[List[List[float]]]): 2D coordinate segments for visualization
                    Format: [well][segment][x,y coordinates]
                segments_3d (List[List[List[float]]]): 3D coordinate segments for visualization
                    Format: [well][segment][z coordinates]

            Returns:
                Tuple containing:
                - pd.DataFrame: Sorted and filtered well data
                - List[List[List[float]]]: Filtered 2D segments matching DataFrame wells
                - List[List[List[float]]]: Filtered 3D segments matching DataFrame wells

            Notes:
                - Maintains data consistency by filtering segments to match DataFrame wells
                - Preserves original data structure and relationships
                - Handles potential mismatches between DataFrame and segment data
                - Returns empty lists for segments if no matches found

            Example:
                >>> df_filtered, seg_2d, seg_3d = platBounded(well_df, segments_2d, segments_3d)
                >>> print(f"Filtered to {len(seg_2d)} wells")
            """
            # Sort DataFrame by API number and measured depth
            df = df.sort_values(by=['APINumber', 'MeasuredDepth'])

            # Create index mapping for API numbers
            api = df[['APINumber']].drop_duplicates().reset_index(drop=True)
            api['index'] = api.index

            # Merge to maintain relationships
            merged = pd.merge(api, df, left_on='APINumber', right_on='APINumber')

            # Filter segments to match DataFrame wells
            segments = [segments[i] for i in range(len(segments)) if i in merged['index'].unique()]
            segments_3d = [segments_3d[i] for i in range(len(segments_3d)) if i in merged['index'].unique()]

            return df, segments, segments_3d
        # def platBounded(df, segments, segments_3d):
        #     df = df.sort_values(by=['APINumber', 'MeasuredDepth'])
        #     api = df[['APINumber']].drop_duplicates().reset_index(drop=True)
        #     api['index'] = api.index
        #     merged = pd.merge(api, df, left_on='APINumber', right_on='APINumber')
        #     segments = [segments[i] for i in range(len(segments)) if i in merged['index'].unique()]
        #     segments_3d = [segments_3d[i] for i in range(len(segments_3d)) if i in merged['index'].unique()]
        #     return df, segments, segments_3d
        def setupData(
                df: pd.DataFrame,
                segments: List[List[List[float]]],
                segments_3d: List[List[List[float]]]
        ) -> Tuple[pd.DataFrame, List[List[List[float]]], List[List[List[float]]], Dict, pd.DataFrame]:
            """
            Prepares well data and visualization parameters by filtering data and setting up default styling.

            Processes well data through platBounded filter and creates default visualization
            parameters for well segments including color and width attributes.

            Args:
                df (pd.DataFrame): Well data containing:
                    Required columns:
                    - APINumber: Unique well identifier
                    - MeasuredDepth: Depth measurement along wellbore
                segments (List[List[List[float]]]): 2D coordinate segments for visualization
                    Format: [well][segment][x,y coordinates]
                segments_3d (List[List[List[float]]]): 3D coordinate segments for visualization
                    Format: [well][segment][z coordinates]

            Returns:
                Tuple containing:
                - pd.DataFrame: Filtered and sorted well data
                - List[List[List[float]]]: Filtered 2D segments
                - List[List[List[float]]]: Filtered 3D segments
                - Dict: Default styling parameters dictionary with:
                    - color: List of colors (default 'black')
                    - width: List of line widths (default 0.5)
                - pd.DataFrame: Styling parameters as DataFrame

            Notes:
                - Uses platBounded to filter and align data
                - Creates consistent default styling for all well segments
                - Styling can be modified later by other functions
                - Returns both dict and DataFrame versions of styling parameters
                - All segments receive identical initial styling

            Example:
                >>> df, segs_2d, segs_3d, style_dict, style_df = setupData(wells_df, segments_2d, segments_3d)
                >>> print(f"Styled {len(style_df)} well segments")
            """
            # Filter and align data using platBounded
            df, segments, segments_3d = platBounded(df, segments, segments_3d)

            # Create default styling parameters
            data = {'color': ['black'] * len(segments), 'width': [0.5] * len(segments)}

            # Convert styling parameters to DataFrame
            df_parameters = pd.DataFrame(data)

            return df, segments, segments_3d, data, df_parameters
        # def setupData(df, segments, segments_3d):
        #     df, segments, segments_3d = platBounded(df, segments, segments_3d)
        #     data = {'color': ['black'] * len(segments), 'width': [0.5] * len(segments)}
        #     df_parameters = pd.DataFrame(data)
        #     return df, segments, segments_3d, data, df_parameters

        def wellChecked(
                type: str,
                column: Literal['CurrentWellType', 'CurrentWellStatus']
        ) -> None:
            """
            Updates well visualization parameters based on specified well type or status filter.

            Modifies the styling (color and line width) of well segments in the visualization
            based on either well type (e.g., Oil, Gas) or well status (e.g., Producing,
            Shut-in). Wells matching the filter criteria are highlighted with specific colors
            and increased line width.

            Args:
                type (str): Well type or status to filter by. Valid values depend on column:
                    For CurrentWellType:
                        - 'Oil Well'
                        - 'Gas Well'
                        - 'Water Disposal Well'
                        - 'Water Injection Well'
                        - 'Gas Injection Well'
                        - 'Dry Hole'
                        - 'Test Well'
                        - 'Water Source Well'
                        - 'Unknown'
                    For CurrentWellStatus:
                        - Status values from well database
                column (Literal['CurrentWellType', 'CurrentWellStatus']):
                    Column to filter on, determines color mapping used

            Side Effects:
                Updates these visualization parameter DataFrames:
                - df_drilled_parameters
                - df_planned_parameters
                - df_drilling_parameters

                Modifies:
                - 'color': Changed from default black to type-specific color
                - 'width': Increased from 0.5 to 1.5 for matching wells

            Notes:
                - Only processes first row per API number since color/type is constant per well
                - Handles three well categories: drilled, planned, and currently drilling
                - Uses predefined color mappings stored in WellTypeColor or WellStatusColor
                - Non-matching wells retain default black color and 0.5 width
                - Changes are reflected immediately in visualization

            Example:
                >>> wellChecked('Oil Well', 'CurrentWellType')
                # Updates visualization to highlight all oil wells in red
            """
            # Determine color mapping column based on filter type
            colors_lst = 'WellTypeColor' if column == 'CurrentWellType' else 'WellStatusColor'

            # Get first row for each API number to determine well properties
            drilled_df_restricted = drilled_df.groupby('APINumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('APINumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('APINumber').first().reset_index()

            # Create masks for wells matching specified type/status
            drilled_well_mask = drilled_df_restricted[column] == type
            planned_well_mask = planned_df_restricted[column] == type
            currently_drilling_well_mask = currently_drilling_df_restricted[column] == type

            # Update styling for drilled wells
            df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[
                drilled_well_mask, colors_lst]
            df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5

            # Update styling for planned wells
            df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[
                planned_well_mask, colors_lst]
            df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5

            # Update styling for currently drilling wells
            df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[
                currently_drilling_well_mask, colors_lst]
            df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5


        # def wellChecked(type, column):
        #     if column == 'CurrentWellType':
        #         colors_lst = 'WellTypeColor'
        #     else:
        #         colors_lst = 'WellStatusColor'
        #     # restrict the data to the first rows of each api number (since we only need one row to define the color)
        #     drilled_df_restricted = drilled_df.groupby('APINumber').first().reset_index()
        #     planned_df_restricted = planned_df.groupby('APINumber').first().reset_index()
        #     currently_drilling_df_restricted = currently_drilling_df.groupby('APINumber').first().reset_index()
        #
        #     # Filter the data to only the specific type of well (oil, gas, etc)
        #     drilled_well_mask = drilled_df_restricted[column] == type
        #     planned_well_mask = planned_df_restricted[column] == type
        #     currently_drilling_well_mask = currently_drilling_df_restricted[column] == type
        #
        #     # Here, we change the colors and size of the well. So that if we're looking at all oil wells, they'll be changed from the default black to the relevant color, and the size of the line is increased.
        #     df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[drilled_well_mask, colors_lst]
        #     df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5
        #
        #     df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[planned_well_mask, colors_lst]
        #     df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5
        #
        #     df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[currently_drilling_well_mask, colors_lst]
        #     df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5
        def wellCheckedMultiple(
                types: List[str],
                column: Literal['CurrentWellType', 'CurrentWellStatus']
        ) -> None:
            """
            Updates well visualization parameters for multiple well types or statuses simultaneously.

            Similar to wellChecked() but handles multiple types/statuses at once. Modifies the styling
            (color and line width) of well segments in the visualization based on a list of well
            types or statuses. Wells matching any of the filter criteria are highlighted.

            Args:
                types (List[str]): List of well types or statuses to filter by. Valid values depend on column:
                    For CurrentWellType:
                        - 'Oil Well'
                        - 'Gas Well'
                        - 'Water Disposal Well'
                        - 'Oil Well/Water Disposal Well'
                        - 'Water Injection Well'
                        - 'Gas Injection Well'
                        - 'Dry Hole'
                        - etc.
                    For CurrentWellStatus:
                        - 'Location Abandoned - APD rescinded'
                        - 'Returned APD (Unapproved)'
                        - 'Approved Permit'
                        - 'Active'
                        - 'Drilling Operations Suspended'
                        - 'New Permit'
                        - 'Inactive'
                        - 'Temporarily-abandoned'
                        - 'Test Well or Monitor Well'
                        - etc.
                column (Literal['CurrentWellType', 'CurrentWellStatus']):
                    Column to filter on, determines color mapping used

            Side Effects:
                Updates these visualization parameter DataFrames:
                - df_drilled_parameters
                - df_planned_parameters
                - df_drilling_parameters

                Modifies:
                - 'color': Changed from default black to type-specific color
                - 'width': Increased from 0.5 to 1.5 for matching wells

            Notes:
                - Only processes first row per API number since color/type is constant per well
                - Handles three well categories: drilled, planned, and currently drilling
                - Uses predefined color mappings stored in WellTypeColor or WellStatusColor
                - Non-matching wells retain default black color and 0.5 width
                - Changes are reflected immediately in visualization
                - Commonly used for grouping related well types (e.g., all injection wells)
                - Used by the GUI checkbox handlers to update multiple well types at once

            Example:
                >>> wellCheckedMultiple(['Water Injection Well', 'Gas Injection Well'], 'CurrentWellType')
                # Updates visualization to highlight all injection wells
            """
            # Determine color mapping column based on filter type
            colors_lst = 'WellTypeColor' if column == 'CurrentWellType' else 'WellStatusColor'

            # Get first row for each API number to determine well properties
            drilled_df_restricted = drilled_df.groupby('APINumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('APINumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('APINumber').first().reset_index()

            # Create masks for wells matching any specified type/status
            drilled_well_mask = drilled_df_restricted[column].isin(types)
            planned_well_mask = planned_df_restricted[column].isin(types)
            currently_drilling_well_mask = currently_drilling_df_restricted[column].isin(types)

            # Update styling for drilled wells
            df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[
                drilled_well_mask, colors_lst]
            df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5

            # Update styling for planned wells
            df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[
                planned_well_mask, colors_lst]
            df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5

            # Update styling for currently drilling wells
            df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[
                currently_drilling_well_mask, colors_lst]
            df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5

        # def wellCheckedMultiple(types, column):
        #     if column == 'CurrentWellType':
        #         colors_lst = 'WellTypeColor'
        #     else:
        #         colors_lst = 'WellStatusColor'
        #     # restrict the data to the first rows of each api number (since we only need one row to define the color)
        #     drilled_df_restricted = drilled_df.groupby('APINumber').first().reset_index()
        #     planned_df_restricted = planned_df.groupby('APINumber').first().reset_index()
        #     currently_drilling_df_restricted = currently_drilling_df.groupby('APINumber').first().reset_index()
        #
        #     # Filter the data to only the specific type of well (oil, gas, etc)
        #     drilled_well_mask = drilled_df_restricted[column].isin(types)
        #     planned_well_mask = planned_df_restricted[column].isin(types)
        #     currently_drilling_well_mask = currently_drilling_df_restricted[column].isin(types)
        #     # Here, we change the colors and size of the well. So that if we're looking at all oil wells, they'll be changed from the default black to the relevant color, and the size of the line is increased.
        #     df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[drilled_well_mask, colors_lst]
        #     df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5
        #
        #     df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[planned_well_mask, colors_lst]
        #     df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5
        #
        #     df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[currently_drilling_well_mask, colors_lst]
        #     df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5
        def toggle_well_display(
                condition: bool,
                data_frame: pd.DataFrame,
                segments_2d: List[List[float]],
                colors_init: Union[str, List[str]],
                line_width: Union[float, List[float]],
                well_2d: Line2D,
                well_3d: Line2D,
                vertical_well: Line2D,
                segments_3d: List[List[float]]
        ) -> None:
            """
            Toggles the visibility and updates data for well visualization elements based on a boolean condition.

            Controls the display state and data updates for 2D, 3D and vertical well representations in the
            visualization. When enabled, updates the data and makes wells visible. When disabled, hides the wells
            without removing the underlying data.

            Args:
                condition (bool): Toggle state - True to show and update wells, False to hide them
                data_frame (pd.DataFrame): Well data to incorporate into currently displayed wells
                    Required columns:
                    - Well identifiers
                    - Coordinate data
                    - Well properties
                segments_2d (List[List[float]]): 2D coordinate segments for well paths
                    Format: [[x1,y1], [x2,y2], ...]
                colors_init (Union[str, List[str]]): Color specification for well lines
                    Either single color string or list of colors per segment
                line_width (Union[float, List[float]]): Width specification for well lines
                    Either single width value or list of widths per segment
                well_2d (Line2D): Matplotlib line object for 2D well representation
                well_3d (Line2D): Matplotlib line object for 3D well representation
                vertical_well (Line2D): Matplotlib line object for vertical well projection
                segments_3d (List[List[float]]): 3D coordinate segments for well paths
                    Format: [[x1,y1,z1], [x2,y2,z2], ...]

            Side Effects:
                - Updates self.currently_used_lines with new well data when enabled
                - Modifies visibility of well_2d, well_3d and vertical_well line objects
                - Triggers redraw of well visualizations when enabled
                - Changes persist until next toggle operation

            Notes:
                - Uses drawModelBasedOnParameters2d() for 2D visualization updates
                - Uses drawModelBasedOnParameters() for 3D visualization updates
                - Maintains data state even when wells are hidden
                - Deduplicates data when adding new wells
                - Preserves existing well properties when toggling visibility

            Example:
                >>> toggle_well_display(True, new_wells_df, segs_2d, 'blue', 1.0,
                                      well2d, well3d, vert_well, segs_3d)
                # Shows wells and updates with new data
                >>> toggle_well_display(False, new_wells_df, segs_2d, 'blue', 1.0,
                                      well2d, well3d, vert_well, segs_3d)
                # Hides wells without removing data
            """
            if condition:
                # Update data and show wells
                self.currently_used_lines = concat([self.currently_used_lines, data_frame]).drop_duplicates(
                    keep='first').reset_index(drop=True)

                # Redraw 2D and 3D visualizations with updated parameters
                self.drawModelBasedOnParameters2d(well_2d, segments_2d, colors_init, line_width, self.ax2d,
                                                  vertical_well)
                self.drawModelBasedOnParameters(well_3d, segments_3d, colors_init, line_width, self.ax3d)

                # Make all well representations visible
                well_2d.set_visible(True)
                well_3d.set_visible(True)
                vertical_well.set_visible(True)
            else:
                # Hide all well representations
                well_2d.set_visible(False)
                well_3d.set_visible(False)
                vertical_well.set_visible(False)

        # def toggle_well_display(condition, data_frame, segments_2d, colors_init, line_width, well_2d, well_3d,
        #                         vertical_well, segments_3d):
        #     """
        #     Toggle the display and data of well elements based on a condition.
        #
        #     Parameters:
        #         condition (bool): The condition to check (i.e., whether the checkbox is checked).
        #         data_frame (DataFrame): Data to add to currently used lines.
        #         segments_2d, colors_init, line_width: Parameters for 2D drawing.
        #         well_2d, well_3d, vertical_well: 2D, 3D, and vertical well elements.
        #         segments_3d: Parameters for 3D drawing.
        #     """
        #     if condition:
        #         self.currently_used_lines = concat([self.currently_used_lines, data_frame]).drop_duplicates(
        #             keep='first').reset_index(drop=True)
        #         self.drawModelBasedOnParameters2d(well_2d, segments_2d, colors_init, line_width, self.ax2d,
        #                                           vertical_well)
        #         self.drawModelBasedOnParameters(well_3d, segments_3d, colors_init, line_width, self.ax3d)
        #         well_2d.set_visible(True)
        #         well_3d.set_visible(True)
        #         vertical_well.set_visible(True)
        #     else:
        #         well_2d.set_visible(False)
        #         well_3d.set_visible(False)
        #         vertical_well.set_visible(False)
        def statusAndTypesEnabler() -> NoReturn:
            """
            Manages well visualization filters and field label visibility based on UI state.

            Coordinates the mutual exclusivity between well type and status filters while
            maintaining independent control of field label visibility. Handles three main
            aspects of visualization:
            1. Well type filtering (for Oil, Gas, Injection, Disposal wells etc.)
            2. Well status filtering (Producing, Shut-in, P&A, Drilling etc.)
            3. Field name label visibility

            Radio Button IDs:
                -2: Well Type filtering mode (Oil, Gas, Injection, etc.)
                -3: Well Status filtering mode (Producing, Shut-in, etc.)

            Field Labels:
                - Displayed as red text at field centroids when enabled
                - Size: 75 units
                - Visibility tied to field_names_checkbox state

            Side Effects:
                - Updates well visibility based on selected filter mode
                - Modifies field label and section visibility
                - Changes currently_used_lines DataFrame content
                - Triggers field label rendering when enabled
                - Maintains field visibility state independent of filter changes

            Notes:
                - Part of the well visualization control system
                - Connected to radio button and checkbox state changes
                - Preserves field label state across filter changes
                - Ensures proper layering of visual elements
                - Manages memory by creating field labels only when visible
                - Coordinates with wellTypesEnable() and wellStatusEnable()

            Example:
                Called when switching between well type/status or toggling field names:
                >>> self.ui.well_type_or_status_button_group.buttonClicked.connect(
                        self.statusAndTypesEnabler)
                >>> self.ui.field_names_checkbox.stateChanged.connect(
                        self.statusAndTypesEnabler)
            """
            # Store field checkbox state to preserve across filter changes
            field_checkbox_state = self.ui.field_names_checkbox.isChecked()

            # Get the ID of currently selected radio button
            active_button_id_type_status = self.ui.well_type_or_status_button_group.checkedId()

            # Enable well type filtering mode
            if active_button_id_type_status == -2:
                wellTypesEnable()
            # Enable well status filtering mode
            elif active_button_id_type_status == -3:
                wellStatusEnable()

            # Handle field label visibility independent of filter state
            if field_checkbox_state:
                self.field_sections.set_visible(True)
                # Create field label paths with consistent styling
                paths = [
                    PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
                    for coord, text in zip(self.field_centroids_lst, self.field_labels)
                ]
                self.labels_field.set_paths(paths)
                self.labels_field.set_visible(True)
            else:
                self.field_sections.set_visible(False)
                self.labels_field.set_visible(False)


        def wellTypesEnable() -> NoReturn:
            """
            Enables well type filtering while temporarily disabling well status filters.

            Updates the visualization based on selected well type checkboxes in the UI.
            Temporarily blocks signals from status checkboxes to prevent interference
            between type and status filters.

            Well Types Handled:
                - Oil Wells
                - Gas Wells
                - Water Disposal Wells (including dual-purpose Oil/Disposal wells)
                - Dry Holes
                - Injection Wells (Water and Gas)
                - Other Wells (Unknown, Test Wells, Water Source Wells)

            Side Effects:
                # - Temporarily blocks signals from status checkboxes
                - Unchecks all status checkboxes
                - Updates well visualization based on checked type filters
                # - Restores signal handling for status checkboxes
                - Modifies well colors and visibility in the visualization
                - Updates currently_used_lines DataFrame

            Notes:
                - Uses wellChecked() for single well types
                - Uses wellCheckedMultiple() for grouped well types
                - Ensures mutual exclusivity between type and status filters
                - Part of the well visualization control system
                - Connected to UI checkbox state changes
                - Maintains separation between well type and status filtering

            Example:
                Called when user interacts with well type checkboxes:
                >>> self.ui.oil_well_check.stateChanged.connect(self.wellTypesEnable)
            """
            # Temporarily disable status checkbox signals
            # for q in self.status_checks:
            #     q.blockSignals(True)
            #     q.setChecked(False)

            # Handle Oil Well selection
            if self.ui.oil_well_check.isChecked():
                wellChecked('Oil Well', 'CurrentWellType')

            # Handle Gas Well selection
            if self.ui.gas_well_check.isChecked():
                wellChecked('Gas Well', 'CurrentWellType')

            # Handle Water Disposal Well selection (including combination wells)
            if self.ui.water_disposal_check.isChecked():
                wellCheckedMultiple(['Water Disposal Well', 'Oil Well/Water Disposal Well'], 'CurrentWellType')

            # Handle Dry Hole selection
            if self.ui.dry_hole_check.isChecked():
                wellChecked('Dry Hole', 'CurrentWellType')

            # Handle Injection Well selection (both water and gas)
            if self.ui.injection_check.isChecked():
                wellCheckedMultiple(['Water Injection Well', 'Gas Injection Well'], 'CurrentWellType')

            # Handle Other Well Types selection
            if self.ui.other_well_status_check.isChecked():
                wellCheckedMultiple(['Unknown', 'Test Well', 'Water Source Well'], 'CurrentWellType')

            # Re-enable status checkbox signals
            # for q in self.status_checks:
                # q.blockSignals(False)

        def wellStatusEnable() -> NoReturn:
            """
            Enables well status filtering while temporarily disabling well type filters.

            Updates the visualization based on selected well status checkboxes in the UI.
            Temporarily blocks signals from type checkboxes to prevent interference
            between status and type filters.

            Well Statuses Handled:
                - Shut-in wells
                - Plugged & Abandoned wells
                - Producing wells
                - Currently drilling wells
                - Miscellaneous statuses:
                    - Location Abandoned (APD rescinded)
                    - Returned APD (Unapproved)
                    - Approved Permit
                    - Active
                    - Drilling Operations Suspended
                    - New Permit
                    - Inactive
                    - Temporarily-abandoned
                    - Test/Monitor Wells

            Side Effects:
                - Temporarily blocks signals from type checkboxes
                - Unchecks all type checkboxes
                - Updates well visualization based on checked status filters
                - Restores signal handling for type checkboxes
                - Modifies well colors and visibility in visualization
                - Updates currently_used_lines DataFrame

            Notes:
                - Uses wellChecked() for single well statuses
                - Uses wellCheckedMultiple() for grouped miscellaneous statuses
                - Ensures mutual exclusivity between status and type filters
                - Part of the well visualization control system
                - Connected to UI checkbox state changes
                - Maintains separation between well status and type filtering

            Example:
                Called when user interacts with well status checkboxes:
                >>> self.ui.shut_in_check.stateChanged.connect(self.wellStatusEnable)
            """
            # Temporarily disable type checkbox signals
            # for q in self.type_checks:
            #     q.blockSignals(True)
            #     q.setChecked(False)

            # Handle Shut-in wells
            if self.ui.shut_in_check.isChecked():
                wellChecked('Shut-in', 'CurrentWellStatus')

            # Handle Plugged & Abandoned wells
            if self.ui.pa_check.isChecked():
                wellChecked('Plugged & Abandoned', 'CurrentWellStatus')

            # Handle Producing wells
            if self.ui.producing_check.isChecked():
                wellChecked('Producing', 'CurrentWellStatus')

            # Handle Currently Drilling wells
            if self.ui.drilling_status_check.isChecked():
                wellChecked('Drilling', 'CurrentWellStatus')

            # Handle Miscellaneous well statuses
            if self.ui.misc_well_type_check.isChecked():
                wellCheckedMultiple(['Location Abandoned - APD rescinded',
                                     'Returned APD (Unapproved)', 'Approved Permit',
                                     'Active', 'Drilling Operations Suspended', 'New Permit', 'Inactive',
                                     'Temporarily-abandoned', 'Test Well or Monitor Well'], 'CurrentWellStatus')

            # Re-enable type checkbox signals
            # for q in self.type_checks:
            #     q.blockSignals(False)

        # Reset current line tracking
        self.currently_used_lines = None

        # Store segment and DataFrame references locally
        drilled_segments = self.drilled_segments
        planned_segments = self.planned_segments
        currently_drilling_segments = self.currently_drilling_segments

        drilled_segments_3d = self.drilled_segments_3d
        planned_segments_3d = self.planned_segments_3d
        currently_drilling_segments_3d = self.currently_drilling_segments_3d

        drilled_df = self.drilled_df
        planned_df = self.planned_df
        currently_drilling_df = self.currently_drilling_df

        # Process each well category data
        drilled_df, drilled_segments, drilled_segments_3d, data_drilled, df_drilled_parameters = setupData(
            drilled_df, drilled_segments, drilled_segments_3d)
        planned_df, planned_segments, planned_segments_3d, data_planned, df_planned_parameters = setupData(
            planned_df, planned_segments, planned_segments_3d)
        currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d, data_drilling, df_drilling_parameters = setupData(
            currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d)

        # Update well type/status filters
        statusAndTypesEnabler()
        print("sfnjsgnjsjl")
        # Handle field name visibility
        if self.ui.field_names_checkbox.isChecked():
            self.field_sections.set_visible(True)
            paths = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
                     for coord, text in zip(self.field_centroids_lst, self.field_labels)]
            self.labels_field.set_paths(paths)
            self.labels_field.set_visible(True)
        else:
            self.field_sections.set_visible(False)
            self.labels_field.set_visible(False)

        # Extract visualization parameters
        drilled_colors_init, drilled_line_width = df_drilled_parameters['color'].tolist(), df_drilled_parameters[
            'width'].tolist()
        planned_colors_init, planned_line_width = df_planned_parameters['color'].tolist(), df_planned_parameters[
            'width'].tolist()
        currently_drilling_colors_init, currently_drilling_width = df_drilling_parameters['color'].tolist(), \
        df_drilling_parameters['width'].tolist()

        # Toggle visibility for each well category
        toggle_well_display(
            self.ui.asdrilled_check.isChecked(), drilled_df,
            drilled_segments, drilled_colors_init, drilled_line_width,
            self.all_wells_2d_asdrilled, self.all_wells_3d_asdrilled,
            self.all_wells_2d_vertical_asdrilled, drilled_segments_3d)

        toggle_well_display(
            self.ui.planned_check.isChecked(), planned_df,
            planned_segments, planned_colors_init, planned_line_width,
            self.all_wells_2d_planned, self.all_wells_3d_planned,
            self.all_wells_2d_vertical_planned, planned_segments_3d)

        toggle_well_display(
            self.ui.currently_drilling_check.isChecked(), currently_drilling_df,
            currently_drilling_segments, currently_drilling_colors_init, currently_drilling_width,
            self.all_wells_2d_current, self.all_wells_3d_current,
            self.all_wells_2d_vertical_current, currently_drilling_segments_3d)

        # Update 3D plot boundaries if drilled segments exist
        if drilled_segments_3d:
            self.centroid, std_vals = self.calculate_centroid_np(drilled_segments_3d)
            new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
            new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
            new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]
            self.ax3d.set_xlim3d(new_xlim)
            self.ax3d.set_ylim3d(new_ylim)
            self.ax3d.set_zlim3d(new_zlim)

        # Refresh all canvases
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()
        self.canvas3d.blit(self.ax3d.bbox)
        self.canvas3d.draw()
        # def wellStatusEnable():
        #     for q in self.type_checks:
        #         q.blockSignals(True)
        #         q.setChecked(False)
        #     if self.ui.shut_in_check.isChecked():
        #         wellChecked('Shut-in', 'CurrentWellStatus')
        #     if self.ui.pa_check.isChecked():
        #         wellChecked('Plugged & Abandoned', 'CurrentWellStatus')
        #     if self.ui.producing_check.isChecked():
        #         wellChecked('Producing', 'CurrentWellStatus')
        #     if self.ui.drilling_status_check.isChecked():
        #         wellChecked('Drilling', 'CurrentWellStatus')
        #     if self.ui.misc_well_type_check.isChecked():
        #         wellCheckedMultiple(['Location Abandoned - APD rescinded',
        #                              'Returned APD (Unapproved)', 'Approved Permit',
        #                              'Active', 'Drilling Operations Suspended', 'New Permit', 'Inactive',
        #                              'Temporarily-abandoned', 'Test Well or Monitor Well'], 'CurrentWellStatus')
        #     for q in self.type_checks:
        #         q.blockSignals(False)
        # self.currently_used_lines = None
        #
        # # store in the data locally.
        # drilled_segments = self.drilled_segments
        # planned_segments = self.planned_segments
        # currently_drilling_segments = self.currently_drilling_segments
        #
        # drilled_segments_3d = self.drilled_segments_3d
        # planned_segments_3d = self.planned_segments_3d
        # currently_drilling_segments_3d = self.currently_drilling_segments_3d
        #
        # drilled_df = self.drilled_df
        # planned_df = self.planned_df
        # currently_drilling_df = self.currently_drilling_df
        #
        # drilled_df, drilled_segments, drilled_segments_3d,data_drilled,df_drilled_parameters = setupData(drilled_df, drilled_segments, drilled_segments_3d)
        # planned_df, planned_segments, planned_segments_3d,data_planned,df_planned_parameters = setupData(planned_df, planned_segments, planned_segments_3d)
        # currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d,data_drilling,df_drilling_parameters = setupData(currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d)
        # statusAndTypesEnabler()
        # if self.ui.field_names_checkbox.isChecked():
        #     self.field_sections.set_visible(True)
        #     paths = [
        #         PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
        #         for coord, text in zip(self.field_centroids_lst, self.field_labels)]
        #     self.labels_field.set_paths(paths)
        #     self.labels_field.set_visible(True)
        # else:
        #     self.field_sections.set_visible(False)
        #     self.labels_field.set_visible(False)
        #
        #
        # # Extract the colors and line widths that have seen been filled in or altered.
        # drilled_colors_init, drilled_line_width = df_drilled_parameters['color'].tolist(), df_drilled_parameters['width'].tolist()
        # planned_colors_init, planned_line_width = df_planned_parameters['color'].tolist(), df_planned_parameters['width'].tolist()
        # currently_drilling_colors_init, currently_drilling_width = df_drilling_parameters['color'].tolist(), df_drilling_parameters['width'].tolist()
        #
        # toggle_well_display(
        #     self.ui.asdrilled_check.isChecked(), drilled_df,
        #     drilled_segments, drilled_colors_init, drilled_line_width,
        #     self.all_wells_2d_asdrilled, self.all_wells_3d_asdrilled,
        #     self.all_wells_2d_vertical_asdrilled, drilled_segments_3d)
        #
        # toggle_well_display(
        #     self.ui.planned_check.isChecked(), planned_df,
        #     planned_segments, planned_colors_init, planned_line_width,
        #     self.all_wells_2d_planned, self.all_wells_3d_planned,
        #     self.all_wells_2d_vertical_planned, planned_segments_3d)
        #
        # toggle_well_display(
        #     self.ui.currently_drilling_check.isChecked(), currently_drilling_df,
        #     currently_drilling_segments, currently_drilling_colors_init, currently_drilling_width,
        #     self.all_wells_2d_current, self.all_wells_3d_current,
        #     self.all_wells_2d_vertical_current, currently_drilling_segments_3d)
        #
        # if drilled_segments_3d:
        #     self.centroid, std_vals = self.calculate_centroid_np(drilled_segments_3d)
        #     new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
        #     new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
        #     new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]
        #     self.ax3d.set_xlim3d(new_xlim)
        #     self.ax3d.set_ylim3d(new_ylim)
        #     self.ax3d.set_zlim3d(new_zlim)
        #
        # # Update, and draw, etc.
        # self.canvas2d.blit(self.ax2d.bbox)
        # self.canvas2d.draw()
        # self.canvas3d.blit(self.ax3d.bbox)
        # self.canvas3d.draw()

    """Generate a group of data based on the grouped xy data into line segments"""

    def returnSegmentsFromDF(self, df: pd.DataFrame) -> List[List[List[float]]]:
        """
        Converts well coordinate data from a DataFrame into nested segment lists.

        Takes a DataFrame containing well coordinates and groups them by API number,
        converting X/Y coordinates into lists of [x,y] float pairs for each well segment.

        Args:
            df: pd.DataFrame containing well coordinate data with columns:
                - APINumber: Well identifier
                - X: X-coordinate values
                - Y: Y-coordinate values

        Returns:
            List[List[List[float]]]: Nested list structure where:
                - Outer list contains all wells
                - Middle list contains segments for each well
                - Inner list contains [x,y] float coordinate pairs

        Note:
            - Assumes coordinates are numeric/string convertible to float
            - Groups data by APINumber to maintain well segment relationships
            - Preserves coordinate order within each well grouping

        Example:
            >>> df = pd.DataFrame({
            ...     'APINumber': [1, 1, 2, 2],
            ...     'X': ['100.5', '101.5', '200.5', '201.5'],
            ...     'Y': ['500.5', '501.5', '600.5', '601.5']
            ... })
            >>> segments = returnSegmentsFromDF(df)
            >>> segments
            [
                [[100.5, 500.5], [101.5, 501.5]],  # Well 1
                [[200.5, 600.5], [201.5, 601.5]]   # Well 2
            ]
        """
        return [[[float(x), float(y)] for x, y in zip(group['X'], group['Y'])]
                for _, group in df.groupby('APINumber')]
    # def returnSegmentsFromDF(self, df):
    #     return [[[float(x), float(y)] for x, y in zip(group['X'], group['Y'])]  # Convert each x, y to float and store as list
    #             for _, group in df.groupby('APINumber')]

    """Draw model based on these parameters
    lst = LineCollection previously defined in init
    segments = segments as defined by the data that is filtered by well age in returnWellDataDependingOnParametersTest 
    colors = colors defined previously
    line_width = line_width defined previously
    ax = ax2d, previously defined
    scat_line = the scatter plots for vertical wells defined in init"""

    def drawModelBasedOnParameters2d(
            self,
            lst: LineCollection,
            segments: List[List[List[float]]],
            colors: List[str],
            line_width: List[float],
            ax: plt.Axes,
            scat_line: plt.scatter
    ) -> None:
        """
        Draws 2D well segments with specialized handling for vertical wells.

        Renders well segments on a 2D matplotlib plot, with different handling for
        vertical vs directional wells. Vertical wells (segments with exactly 2 points)
        are displayed as scatter points, while other wells are shown as line segments.

        Args:
            lst: LineCollection object for drawing well segments
            segments: List of well segments, where each segment is a list of [x,y] coordinates
            colors: List of colors corresponding to each segment
            line_width: List of line widths for each segment
            ax: Matplotlib axes object for drawing
            scat_line: Scatter plot object for vertical well visualization

        Side Effects:
            - Updates scatter plot data for vertical wells
            - Updates LineCollection for directional wells
            - Refreshes plot artists
            - Modifies scatter point colors and positions
            - Updates line segment properties

        Notes:
            - Vertical wells are identified by having exactly 2 points
            - Empty segments result in scatter points being reset
            - Color matching is maintained between segments and scatter points
            - Drawing is optimized to minimize redraw operations
            - Handles both single-point and multi-point segments

        Example Usage:
            >>> self.drawModelBasedOnParameters2d(
                    well_collection,
                    [[x1,y1], [x2,y2]],  # segments
                    ['red', 'blue'],      # colors
                    [1.0, 1.0],          # line widths
                    ax,
                    scatter_points
                )
        """
        colors_scatter = []
        collapsed_points = []

        try:
            # Extract vertical well data (segments with exactly 2 points)
            lst_vertical_indexes, lst_vertical_data = zip(*[
                (i, val) for i, val in enumerate(segments) if len(val) == 2
            ])
            # Convert vertical well coordinates to tuples
            lst_vertical_data = [tuple(i[0]) for i in lst_vertical_data]
            # Match colors to vertical well indices
            data_color = [colors[i] for i in lst_vertical_indexes]
            # Update scatter plot with vertical well data
            scat_line.set_offsets(lst_vertical_data)
            scat_line.set_facecolor(data_color)
        except ValueError:
            scat_line.set_offsets([None, None])

        # Handle empty or populated segments
        if len(segments) == 0:
            scat_line.set_offsets([None, None])
        else:
            # Process segments for visualization
            for i in range(len(segments)):
                if len(segments[i]) <= 2:
                    used_colors = [colors[i]] * len(segments[i])
                    colors_scatter.extend(used_colors)
                    collapsed_points.extend(segments[i])
            if len(collapsed_points) > 0:
                scat_line.set_offsets(collapsed_points)

        # Update visual properties
        scat_line.set_facecolor(colors_scatter)
        lst.set_segments(segments)
        lst.set_colors(colors)
        lst.set_linewidth(line_width)
        ax.draw_artist(lst)
    # def drawModelBasedOnParameters2d(self, lst, segments, colors, line_width, ax, scat_line):
    #     colors_scatter = []
    #     collapsed_points = []
    #     try:
    #         # get the index and the data
    #         lst_vertical_indexes, lst_vertical_data = zip(*[(i, val) for i, val in enumerate(segments) if len(val) == 2])
    #         # transform to a list of tuples
    #         lst_vertical_data = [tuple(i[0]) for i in lst_vertical_data]
    #         # get colors
    #         data_color = [colors[i] for i in lst_vertical_indexes]
    #         # set offsets and face colors
    #         scat_line.set_offsets(lst_vertical_data)
    #         scat_line.set_facecolor(data_color)
    #     except ValueError:
    #         scat_line.set_offsets([None, None])
    #     # write it all to the graphic
    #     if len(segments) == 0:
    #         scat_line.set_offsets([None, None])
    #     else:
    #         for i in range(len(segments)):
    #             if len(segments[i]) <= 2:
    #                 used_colors = [colors[i]] * len(segments[i])
    #                 colors_scatter.extend(used_colors)
    #                 collapsed_points.extend(segments[i])
    #         if len(collapsed_points) > 0:
    #             scat_line.set_offsets(collapsed_points)
    #
    #     scat_line.set_facecolor(colors_scatter)
    #     lst.set_segments(segments)
    #     lst.set_colors(colors)
    #     lst.set_linewidth(line_width)
    #     ax.draw_artist(lst)

    """Draws the model based on the parameters. This is the same as drawModelBasedOnParameters2d, but in 3d."""

    def drawModelBasedOnParameters(
            self,
            lst: LineCollection,
            segments: List[List[List[float]]],
            colors: List[str],
            line_width: List[float],
            ax: plt.Axes
    ) -> None:
        """
        Sets basic visual properties for well segments and renders them on the plot.

        A simplified version of drawModelBasedOnParameters2d that handles only line
        segments without special cases for vertical wells. Used primarily for 3D
        visualization where scatter points are not needed.

        Args:
            lst: LineCollection object containing the well segments to be drawn
            segments: List of well segments where each segment is a list of coordinate pairs
            colors: List of colors corresponding to each well segment
            line_width: List of line widths for each segment
            ax: Matplotlib axes object to draw on

        Side Effects:
            - Updates LineCollection segment data
            - Modifies segment colors and line widths
            - Triggers redraw of plot artist

        Notes:
            - Part of the well visualization pipeline
            - Handles both 2D and 3D plotting contexts
            - No special handling for vertical wells
            - Coordinates must be in the correct format for the plotting dimension
            - Colors should match the number of segments

        Example:
            >>> self.drawModelBasedOnParameters(
                    well_collection,
                    [[[x1,y1,z1], [x2,y2,z2]]],  # 3D segments
                    ['blue'],                      # colors
                    [1.0],                         # line widths
                    ax3d
                )
        """
        lst.set_segments(segments)
        lst.set_colors(colors)
        lst.set_linewidth(line_width)
        ax.draw_artist(lst)
    # def drawModelBasedOnParameters(self, lst, segments, colors, line_width, ax):
    #     """Set the segments, the colors, the line width and then draw the artist."""
    #     lst.set_segments(segments)
    #     lst.set_colors(colors)
    #     lst.set_linewidth(line_width)
    #     ax.draw_artist(lst)

    """When called, this will go into the self.df_docket dataframe, and add in well colors. This potentially could be done in Load_data2"""

    def generate_color_palette(self) -> List[QColor]:
        """
        Generates a color-blind friendly palette of QColor objects.

        Creates a carefully selected palette of colors that are distinguishable
        by colorblind individuals while maintaining aesthetic appeal. The palette
        includes a mix of primary, secondary, and tertiary colors with sufficient
        contrast between adjacent colors.

        Returns:
            List[QColor]: List of QColor objects representing the color palette

        Color Categories:
            - Base Colors (0-7): Primary distinctive colors for main categories
            - Extended Set (8-15): Secondary colors for additional categories
            - Accent Colors (16-23): Tertiary colors for highlighting
            - Supplementary (24-38): Additional colors for large datasets

        Color Properties:
            - All colors are specified in hex format for precision
            - Includes a mix of warm and cool tones
            - Maintains sufficient brightness contrast
            - Avoids problematic color combinations for common types of color blindness

        Usage Notes:
            - Colors are ordered by visual distinctiveness
            - Black is included last as a fallback/default color
            - Suitable for both light and dark backgrounds
            - Verified for deuteranopia and protanopia visibility

        Example:
            >>> palette = self.generate_color_palette()
            >>> first_color = palette[0]  # Returns QColor for blue (#0072B2)
        """
        # Color-blind friendly palette with semantic groupings
        colors = [
            "#0072B2",  # Blue - Primary visual anchor
            "#E69F00",  # Orange - Strong contrast to blue
            "#009E73",  # Green - Natural/environmental
            "#CC79A7",  # Pink - Soft highlight
            "#56B4E9",  # Sky Blue - Light accent
            "#D55E00",  # Vermillion - Warning/alert
            "#660099",  # Purple - Rich accent
            "#994F00",  # Brown - Earth tone
            "#334B5C",  # Dark Slate - Neutral accent
            "#0000FF",  # Pure Blue - Basic reference
            "#FF0000",  # Red - Critical/alert
            "#006600",  # Dark Green - Secondary natural
            "#FF00FF",  # Magenta - High visibility
            "#8B4513",  # Saddle Brown - Natural accent
            "#800000",  # Maroon - Deep accent
            "#808000",  # Olive - Muted natural
            "#FF1493",  # Deep Pink - Vibrant accent
            "#00CED1",  # Dark Turquoise - Cool accent
            "#8B008B",  # Dark Magenta - Rich contrast
            "#556B2F",  # Dark Olive Green - Muted accent
            "#FF8C00",  # Dark Orange - Warm accent
            "#9932CC",  # Dark Orchid - Royal accent
            "#8B0000",  # Dark Red - Deep warning
            "#008080",  # Teal - Professional accent
            "#4B0082",  # Indigo - Deep cool
            "#B8860B",  # Dark Goldenrod - Warm natural
            "#32CD32",  # Lime Green - Bright natural
            "#800080",  # Purple - Deep rich
            "#A0522D",  # Sienna - Earth accent
            "#FF4500",  # Orange Red - High alert
            "#00FF00",  # Lime - Maximum visibility
            "#4682B4",  # Steel Blue - Industrial
            "#FFA500",  # Orange - Standard warning
            "#DEB887",  # Burlywood - Neutral natural
            "#5F9EA0",  # Cadet Blue - Muted cool
            "#D2691E",  # Chocolate - Rich warm
            "#CD5C5C",  # Indian Red - Soft warning
            "#708090",  # Slate Gray - Neutral cool
            "#000000"  # Black - Ultimate contrast
        ]

        # Convert hex colors to QColor objects
        return [QColor(color) for color in colors]
    # def generate_color_palette(self):
    #     # Color-blind friendly palette
    #     colors = [
    #         "#0072B2",  # Blue
    #         "#E69F00",  # Orange
    #         "#009E73",  # Green
    #         "#CC79A7",  # Pink
    #         "#56B4E9",  # Sky Blue
    #         "#D55E00",  # Vermillion
    #         "#660099",  # Purple
    #         "#994F00",  # Brown
    #         "#334B5C",  # Dark Slate
    #         "#0000FF",  # Pure Blue
    #         "#FF0000",  # Red
    #         "#006600",  # Dark Green
    #         "#FF00FF",  # Magenta
    #         "#8B4513",  # Saddle Brown
    #         "#800000",  # Maroon
    #         "#808000",  # Olive
    #         "#FF1493",  # Deep Pink
    #         "#00CED1",  # Dark Turquoise
    #         "#8B008B",  # Dark Magenta
    #         "#556B2F",  # Dark Olive Green
    #         "#FF8C00",  # Dark Orange
    #         "#9932CC",  # Dark Orchid
    #         "#8B0000",  # Dark Red
    #         "#008080",  # Teal
    #         "#4B0082",  # Indigo
    #         "#B8860B",  # Dark Goldenrod
    #         "#32CD32",  # Lime Green
    #         "#800080",  # Purple
    #         "#A0522D",  # Sienna
    #         "#FF4500",  # Orange Red
    #         "#00FF00",  # Lime
    #         "#4682B4",  # Steel Blue
    #         "#FFA500",  # Orange
    #         "#DEB887",  # Burlywood
    #         "#5F9EA0",  # Cadet Blue
    #         "#D2691E",  # Chocolate
    #         "#CD5C5C",  # Indian Red
    #         "#708090",  # Slate Gray
    #         "#000000"]  # Black
    #     return [PyQt5.QtGui.QColor(color) for color in colors]
    def get_color_for_index(self, index: int) -> QColor:
        """
        Retrieves a color from the color palette using modulo indexing.

        Safely accesses the color palette by wrapping around to the start when
        the index exceeds the palette length, ensuring a color is always returned
        regardless of the input index value.

        Args:
            index: Integer index to select a color from the palette. Can be any value
                   as modulo arithmetic will be applied

        Returns:
            QColor: Color object from the palette corresponding to the wrapped index

        Notes:
            - Uses modulo operation to wrap indices exceeding palette length
            - Assumes self.color_palette is initialized with QColor objects
            - Part of the color management system for visualization
            - Returns consistent colors for the same index values

        Example:
            >>> color = self.get_color_for_index(5)  # Returns 6th color
            >>> color = self.get_color_for_index(len(palette) + 2)  # Wraps to 3rd color
        """
        return self.color_palette[index % len(self.color_palette)]
    # def get_color_for_index(self, index):
    #     return self.color_palette[index % len(self.color_palette)]

    def createOwnershipLabels(self):
        def wipeModel(lst: List[QWidget]) -> None:
            """
            Removes all widgets from a list and clears their parent relationships.

            Iterates through a list of Qt widgets, removes their parent associations,
            and then clears the list. This is typically used for cleanup before
            recreating UI elements.

            Args:
                lst: List of QWidget objects to be removed and cleared

            Side Effects:
                - Removes parent relationships from all widgets in the list
                - Clears the input list
                - Widgets become candidates for garbage collection after parent removal

            Notes:
                - Important for proper Qt widget cleanup
                - Prevents memory leaks by removing parent references
                - Should be called before recreating UI elements
                - Does not delete the widgets directly, only removes references

            Example:
                >>> label_list = [QLabel("Test1"), QLabel("Test2")]
                >>> wipeModel(label_list)
                >>> print(len(label_list))  # Output: 0
            """
            for label in lst:
                label.setParent(None)  # Remove parent relationship for proper cleanup
            lst.clear()  # Remove all references from the list

        # def wipeModel(lst):
        #     for label in lst:
        #         label.setParent(None)
        #     lst.clear()
        def processOwnershipData(
                model: QAbstractItemModel,
                variable: str,
                variable_color: str,
                lst: List[QLabel],
                layout: QLayout
        ) -> None:
            """
            Creates and styles labels for ownership data visualization.

            Processes each row in the model to create interactive labels with custom
            styling based on ownership data. Labels are colored according to the
            specified variable color and include hover effects.

            Args:
                model: Item model containing ownership data in first column
                variable: Column name to match in ownership data
                variable_color: Column name containing color values
                lst: List to store created label widgets
                layout: Layout widget to add labels to

            Side Effects:
                - Creates new QLabel widgets
                - Adds widgets to provided layout
                - Appends widgets to provided list
                - Applies custom styling to labels

            Notes:
                - Assumes self.docket_ownership_data exists as a pandas DataFrame
                - Labels include white text shadow for visibility
                - Hover effect adds colored border
                - Labels maintain 2px padding
                - Uses transparent borders by default

            Example:
                >>> labels = []
                >>> processOwnershipData(
                ...     model=ownership_model,
                ...     variable='Owner',
                ...     variable_color='OwnerColor',
                ...     lst=labels,
                ...     layout=vertical_layout
                ... )
            """
            for row in range(model.rowCount()):
                item = model.item(row, 0)  # Get item from first column
                if item:
                    # Create and configure label
                    label_text = item.text()
                    label = QLabel(label_text)
                    lst.append(label)
                    layout.addWidget(label)

                    # Get color from ownership data
                    color_used = self.docket_ownership_data[
                        self.docket_ownership_data[variable] == label_text
                        ][variable_color].iloc[0]

                    # Apply custom styling with hover effect
                    label.setStyleSheet(f"""
                        QLabel {{
                            color: {color_used};
                            text-shadow: 0 0 20px #fff;
                            padding: 2px;
                            border: 1px solid transparent;
                        }}
                        QLabel:hover {{
                            border: 1px solid {color_used};
                        }}
                    """)
        # def processOwnershipData(model, variable, variable_color, lst, layout):
        #     for row in range(model.rowCount()):
        #         item = model.item(row, 0)  # Get item from the first column
        #         if item:
        #             label_text = item.text()
        #             label = QLabel(label_text)
        #             lst.append(label)
        #             layout.addWidget(label)
        #             color_used = self.docket_ownership_data[self.docket_ownership_data[variable] == label_text][variable_color].iloc[0]
        #             label.setStyleSheet(f"""
        #                 QLabel {{
        #                     color: {color_used};
        #                     text-shadow: 0 0 20px #fff;
        #                     padding: 2px;
        #                     border: 1px solid transparent;
        #                 }}
        #                 QLabel:hover {{
        #                     border: 1px solid {color_used};
        #                 }}
        #             """)

        wipeModel(self.owner_label_list)
        wipeModel(self.agency_label_list)
        if self.ui.ownership_checkbox.isChecked():
            active_button_id = self.ui.ownership_button_group.checkedId()
            if active_button_id == -2:
                processOwnershipData(self.owner_model, 'owner', 'owner_color', self.owner_label_list, self.owner_layout)
            if active_button_id == -3:
                processOwnershipData(self.agency_model, 'state_legend', 'agency_color', self.agency_label_list, self.owner_layout)

    def create_checkboxes(self):
        def refineBasedOnIfDrilledOrPlanned(df, apis):
            # Convert apis to a set for faster lookup
            apis_set = set(apis)

            # Filter the dataframe to include only the relevant APIs
            df_filtered = df[df['APINumber'].isin(apis_set)]

            # Create two masks
            drilled_mask = df_filtered['CitingType'] != 'planned'
            planned_mask = df_filtered['CitingType'] == 'planned'

            # Group by APINumber and apply the logic
            def select_drilled_or_planned(group):
                group_drilled = group.loc[drilled_mask.loc[group.index]]
                if not group_drilled.empty:
                    return group_drilled
                else:
                    return group.loc[planned_mask.loc[group.index]]

            # result = df_filtered.groupby('APINumber', group_keys=False, include_groups=False).apply(select_drilled_or_planned)
            result = df_filtered.groupby('APINumber').apply(lambda x: select_drilled_or_planned(x), include_groups=False).reset_index()

            # Reset index and drop duplicates
            return result.reset_index(drop=True).drop_duplicates(keep='first')

        for checkbox in self.operator_checkbox_list:
            checkbox.setParent(None)
        self.operator_checkbox_list.clear()
        tester_lst = []

        # Create checkboxes based on the first column of the table view
        for row in range(self.operators_model.rowCount()):
            item = self.operators_model.item(row, 0)  # Get item from the first column
            if item:
                checkbox_text = item.text()
                checkbox = QCheckBox(checkbox_text)
                self.checkbox_layout.addWidget(checkbox)

                color_used = self.get_color_for_index(row)
                # checkbox.setStyleSheet(f"""
                #     QCheckBox {{color: {color_used.name()};text-shadow: 0 0 20px #fff;}}""")
                # checkbox.setStyleSheet(f"""
                #     QCheckBox {{
                #         color: {color_used.name()};
                #         padding: 2px;
                #         border: 1px solid transparent;
                #         border-radius: 3px;
                #     }}
                #     QCheckBox:hover {{
                #         border: 1px solid white;
                #         box-shadow: 0 0 5px white;
                #     }}
                # """)
                shadow = QGraphicsDropShadowEffect()
                shadow.setColor(QColor('white'))
                shadow.setBlurRadius(10)
                shadow.setOffset(0, 0)
                checkbox.setGraphicsEffect(shadow)
                checkbox.setStyleSheet(f"QCheckBox {{color: {color_used.name()}}}")

                # Connect the checkbox to the signal handler
                checkbox.stateChanged.connect(lambda state, index=row, text=checkbox_text, color=color_used:
                                              self.on_checkbox_state_changed(index, text, state, color))

                # Store the checkbox in the list
                self.operator_checkbox_list.append(checkbox)
                operator_data = self.df_docket[self.df_docket['Operator'] == checkbox_text]

                apis = operator_data['WellID'].unique()

                """Restrict down to the dx data for the specific well"""

                try:
                    df_wells = self.dx_df[self.dx_df['APINumber'].isin(apis)]
                    df_wells = refineBasedOnIfDrilledOrPlanned(df_wells, apis)
                    df_wells = df_wells.sort_values(by=['APINumber', 'MeasuredDepth'])
                except KeyError:
                    pass

                xy_points_dict_drilled = {k: [[x, y, spx, spy] for x, y, spx, spy, in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float))] for k, g in df_wells.groupby('APINumber')}
                output = [[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in apis]
                tester_lst.append(output)
                colors = [color_used.name()] * len(output)
                line_widths = [4] * len(output)
                current_segment_data = LineCollection(output, color=color_used.name(), linewidth=1, linestyle="-", zorder=1)
                vertical_data = self.ax2d.scatter([], [], s=45, zorder=1, edgecolors='black')
                self.all_wells_2d_operators.append(current_segment_data)
                self.all_wells_2d_operators_vertical.append(vertical_data)
                self.ax2d.add_collection(current_segment_data)
                self.drawModelBasedOnParameters2d(current_segment_data, output, colors, line_widths, self.ax2d, vertical_data)
                self.all_wells_2d_operators[-1].set_visible(False)
                self.all_wells_2d_operators_vertical[-1].set_visible(False)

    def update_checkboxes(self):
        self.create_checkboxes()

    def updateOwnershipCheckboxes(self):
        # pass
        self.createOwnershipLabels()

    def on_checkbox_state_changed(self, index, checkbox_text, state, color):
        # Emit the custom signal
        self.checkbox_state_changed.emit(index, checkbox_text, state == Qt.Checked, color)

        # You can also handle the state change directly here if needed
        self.update_plot()

    # def get_checkbox_state(self, index):
    #     if 0 <= index < len(self.operator_checkbox_list):
    #         return self.operator_checkbox_list[index].isChecked()
    #     return None

    # def set_checkbox_state(self, index, state):
    #     if 0 <= index < len(self.operator_checkbox_list):
    #         self.operator_checkbox_list[index].setChecked(state)
    #
    # def get_checkbox_count(self):
    #     return len(self.operator_checkbox_list)
    #
    # def get_checkbox_text(self, index):
    #     if 0 <= index < len(self.operator_checkbox_list):
    #         return self.operator_checkbox_list[index].text()
    #     return None
    #
    # def get_checkbox_color(self, index):
    #     if 0 <= index < len(self.operator_checkbox_list):
    #         return self.get_color_for_index(index)
    #     return None

    def update_plot(self):
        for index, checkbox in enumerate(self.operator_checkbox_list):
            if checkbox.isChecked():
                self.all_wells_2d_operators[index].set_visible(True)
                self.all_wells_2d_operators_vertical[index].set_visible(True)
            else:
                self.all_wells_2d_operators[index].set_visible(False)
                self.all_wells_2d_operators_vertical[index].set_visible(False)
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()

    def returnWellsWithParameters(self):
        # Dictionary mapping well types to colors
        colors_type = {'Oil Well': '#c34c00',  # Red
                       'Gas Well': '#f1aa00',  # Orange
                       'Water Disposal Well': '#0032b0',  # Blue
                       'Oil Well/Water Disposal Well': '#0032b0',  # Blue
                       'Water Injection Well': '#93ebff',  # Cyan
                       'Gas Injection Well': '#93ebff',  # Cyan
                       'Dry Hole': '#4f494b',  # Dark Gray
                       'Unknown': '#985bee',  # Magenta
                       'Test Well': '#985bee',  # Magenta
                       'Water Source Well': '#985bee'}  # Magenta

        colors_status = {
            'Producing': '#a2e361',  # Green
            'Plugged & Abandoned': '#4c2d77',  # Purple
            'Shut In': '#D2B48C',  # tan
            'Drilling': '#001958',  # Navy
            'Other': '#4a7583'  # Teal
        }

        necessary_columns = ['APINumber', 'X', 'Y', 'Targeted Elevation', 'CitingType', 'SPX', 'SPY',
                             'CurrentWellType', 'CurrentWellStatus', 'WellAge', 'MeasuredDepth', 'ConcCode_y']
        # Extract unique API numbers from docket DataFrame
        apis = self.df_docket['WellID'].unique()
        operators = self.df_docket['Operator'].unique()
        # Isolate directional surveys based on present API Numbers
        dx_filtered = self.dx_df[self.dx_df['APINumber'].isin(apis)]
        # Filter self.df_docket to only items with directional surveys
        docket_filtered = self.df_docket[self.df_docket['WellID'].isin(apis)]
        # merge the dataframes so we have dataframes with the df_docket data, but also the directional surveys. The new dataframe will be large.
        merged_df = pd.merge(dx_filtered, docket_filtered, left_on='APINumber', right_on='WellID')
        # Manipulate the data, dropping duplicates, sorting, eliminating some columns, etc.
        merged_df = merged_df.drop_duplicates(keep='first')
        merged_df = merged_df.sort_values(by=['APINumber', 'MeasuredDepth'])
        final_df = merged_df[necessary_columns]
        final_df.reset_index(drop=True, inplace=True)
        # create a new column based on current well type being mapped with colors.
        final_df['WellTypeColor'] = final_df['CurrentWellType'].map(colors_type)
        final_df['WellStatusColor'] = final_df['CurrentWellStatus'].apply(lambda x: colors_status.get(x, '#4a7583'))
        final_df = final_df.sort_values(by=['APINumber', 'MeasuredDepth'])
        return final_df

    """This preps the township and range sections for graphing."""

    def draw2dModelSections(self):
        def transform_string(s):
            # Split the string into parts using regular expressions
            parts = re.match(r'(\d{2})(\d{2}S)(\d{2}W)([A-Z])', s)
            if not parts:
                return s  # If the string doesn't match the pattern, return it as is

            # Remove leading zeros from each part
            part1 = str(int(parts.group(1)))
            part2 = str(int(parts.group(2)[:-1])) + parts.group(2)[-1]
            part3 = str(int(parts.group(3)[:-1])) + parts.group(3)[-1]
            part4 = parts.group(4)

            return f"{part1} {part2} {part3} {part4}"

        # generate a list of data of the plat, with its xy and ID values
        plat_data = self.df_plat[['Easting', 'Northing', 'Conc']].values.tolist()

        # group it into a list
        plat_data = [list(group) for _, group in itertools.groupby(plat_data, lambda x: x[2])]

        # get the labels
        plat_labels = [i[0][2] for i in plat_data]

        # I don't think this ever gets used
        self.all_wells_plat_labels_for_editing = plat_labels

        # transform the string in the label to what will be displayed
        plat_labels = [transform_string(i) for i in plat_labels]

        # reformat the plat xy data
        plat_data = [[j[:2] for j in i] for i in plat_data]
        return plat_data, plat_labels

    def retrievePlatDataRelevant(self):
        pass

    def calculate_centroid_np(self, points):
        # Flatten the list of lists and convert to a numpy array, then get a standard deviation array and the mean
        flat_array = array([point for sublist in points for point in sublist])
        std_vals = std(flat_array, axis=0)
        centroid = flat_array.mean(axis=0)

        return tuple(centroid), tuple(std_vals)

    def ownershipSelection(self):
        if self.ui.ownership_checkbox.isChecked():
            active_button_id = self.ui.ownership_button_group.checkedId()
            if active_button_id == -2:
                self.ownership_sections_agency.set_visible(False)
                self.ownership_sections_owner.set_visible(True)
            if active_button_id == -3:
                self.ownership_sections_owner.set_visible(False)
                self.ownership_sections_agency.set_visible(True)
            self.updateOwnershipCheckboxes()
        else:
            self.ownership_sections_agency.set_visible(False)
            self.ownership_sections_owner.set_visible(False)
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()

    """This function is used for drawing the production graphic on the production graphic tab. Format the data, process the data, display the data"""

    def drawProductionGraphic(self):
        def millions_formatter(x, pos):
            """Formats the y-axis tick labels to display millions."""
            if abs(x) >= 1e6:
                return f"{x / 1e6:.1f}M"  # Format as millions with 1 decimal place
            else:
                return f"{x:.0f}"

        # create a data frame that isolates out the production data just for the targeted well.
        current_data_row = self.df_prod[self.df_prod['WellID'] == self.targeted_well]

        # Sort the data by date
        current_data_row = current_data_row.sort_values(by='Date')

        # Drop unneeded columns that never seem to sum up write, drop duplicates, sort values, reset index, etc
        current_data_row = current_data_row.drop('Potential Cumulative Gas Profit', axis=1).drop('Cumulative Potential Gas Production (mcf)', axis=1).drop('Cumulative Potential Oil Production (bbl)', axis=1).drop('Potential Cumulative Oil Profit', axis=1)
        current_data_row.drop_duplicates(keep='first', inplace=True)
        current_data_row = current_data_row.sort_values(by='Date')
        current_data_row = current_data_row.reset_index(drop=True)

        # Edit the date so that the hours/minutes/sections is removed.
        current_data_row['Date'] = current_data_row['Date'].str.slice(0, 7).str.pad(7, side='right')

        # create new cumsum rows. Because it only seems to work here for some reason.
        current_data_row['Potential Cumulative Gas Profit'] = current_data_row['Potential Gas Profit'].cumsum()
        current_data_row['Potential Cumulative Oil Profit'] = current_data_row['Potential Oil Profit'].cumsum()
        current_data_row['Cumulative Potential Oil Production (bbl)'] = current_data_row['Oil Volume (bbl)'].cumsum()
        current_data_row['Cumulative Potential Gas Production (mcf)'] = current_data_row['Gas Volume (mcf)'].cumsum()

        # convert to a datatype data type
        current_data_row['Date'] = pd.to_datetime(current_data_row['Date'])

        # figure out what sort of production we're looking at. Oil or Gas?
        active_button_id = self.ui.prod_button_group.checkedId()

        # This is for formatting the tick marks depending on how much data there is. If there's too many data points, the axes labels get merged together. That's bad.
        if len(current_data_row) > 10:
            self.ax_prod_1.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))
            self.ax_prod_2.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))
            if active_button_id == -2:
                self.current_prod = 'gas'
            elif active_button_id == -3:
                self.current_prod = 'oil'
        if self.current_prod == 'oil':
            self.ax_prod_1.set_title('Potential Profit')
            self.ax_prod_2.set_title('Produced Oil (bbl)')
            self.profit_line.set_data(current_data_row['Date'], current_data_row['Potential Oil Profit'])
            self.profit_line_cum.set_data(current_data_row['Date'], current_data_row['Potential Cumulative Oil Profit'])
            self.prod_line.set_data(current_data_row['Date'], current_data_row['Oil Volume (bbl)'])
            self.prod_line_cum.set_data(current_data_row['Date'],
                                        current_data_row['Cumulative Potential Oil Production (bbl)'])

            # Update labels if needed
            self.profit_line.set_label('Monthly Oil Profit')
            self.profit_line_cum.set_label('Cumulative Oil Profit')
            self.prod_line.set_label('Monthly Oil Production')
            self.prod_line_cum.set_label('Cumulative Oil Production')

        elif self.current_prod == 'gas':
            self.ax_prod_1.set_title('Potential Profit')
            self.ax_prod_2.set_title('Produced Gas Volume (mcf)')
            self.profit_line.set_data(current_data_row['Date'], current_data_row['Potential Gas Profit'])
            self.profit_line_cum.set_data(current_data_row['Date'], current_data_row['Potential Cumulative Gas Profit'])
            self.prod_line.set_data(current_data_row['Date'], current_data_row['Gas Volume (mcf)'])
            self.prod_line_cum.set_data(current_data_row['Date'],
                                        current_data_row['Cumulative Potential Gas Production (mcf)'])

            # Update labels if needed
            self.profit_line.set_label('Monthly Gas Profit')
            self.profit_line_cum.set_label('Cumulative Gas Profit')
            self.prod_line.set_label('Monthly Gas Production')
            self.prod_line_cum.set_label('Cumulative Gas Production')

        # Create legends after all the plotting is done




        # # Depending on if it's oil or gas, plot these dataframes and titles and stuff to match accordingly.
        # if self.current_prod == 'oil':
        #     self.ax_prod_1.set_title('Potential Profit')
        #     self.ax_prod_2.set_title('Produced Oil  (bbl)')
        #     self.profit_line.set_data(current_data_row['Date'], current_data_row['Potential Oil Profit'])
        #     self.profit_line_cum.set_data(current_data_row['Date'], current_data_row['Potential Cumulative Oil Profit'])
        #     self.prod_line.set_data(current_data_row['Date'], current_data_row['Oil Volume (bbl)'])
        #     self.prod_line_cum.set_data(current_data_row['Date'], current_data_row['Cumulative Potential Oil Production (bbl)'])
        #
        # elif self.current_prod == 'gas':
        #     self.ax_prod_1.set_title('Potential Profit')
        #     self.ax_prod_2.set_title('Produced Gas Volume (mcf)')
        #     self.profit_line.set_data(current_data_row['Date'], current_data_row['Potential Gas Profit'])
        #     self.profit_line_cum.set_data(current_data_row['Date'], current_data_row['Potential Cumulative Gas Profit'])
        #     self.prod_line.set_data(current_data_row['Date'], current_data_row['Gas Volume (mcf)'])
        #     self.prod_line_cum.set_data(current_data_row['Date'], current_data_row['Cumulative Potential Gas Production (mcf)'])

        # Format the axes some more
        self.ax_prod_1.xaxis.set_major_locator(mdates.YearLocator())
        self.ax_prod_1.xaxis.set_minor_locator(mdates.MonthLocator())
        self.ax_prod_1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        self.ax_prod_2.xaxis.set_major_locator(mdates.YearLocator())
        self.ax_prod_2.xaxis.set_minor_locator(mdates.MonthLocator())
        self.ax_prod_2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        # Work on the views and stuff.
        self.ax_prod_1.relim()
        self.ax_prod_1.autoscale_view()
        self.ax_prod_2.relim()
        self.ax_prod_2.autoscale_view()
        formatter = ScalarFormatter(useOffset=False)
        formatter.set_scientific(False)
        self.ax_prod_1.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
        handles1, labels1 = self.ax_prod_1.get_legend_handles_labels()
        handles2, labels2 = self.ax_prod_2.get_legend_handles_labels()
        self.ax_prod_1.legend(loc='upper left', bbox_to_anchor=(-0.15, -0.25))
        self.ax_prod_2.legend(loc='upper left', bbox_to_anchor=(-0.15, -0.25))
        # self.ax_prod_1.legend(handles=handles1, labels=labels1, loc='upper left', bbox_to_anchor=(-0.15, -0.25))
        # self.ax_prod_2.legend(handles=handles2, labels=labels2, loc='upper left', bbox_to_anchor=(-0.15, -0.25))
        # # First, verify your handles and labels existy


        # Blit, draw, etc
        self.canvas_prod_1.blit(self.ax_prod_1.bbox)
        self.canvas_prod_2.blit(self.ax_prod_2.bbox)
        self.canvas_prod_1.draw()
        self.canvas_prod_2.draw()

    """This function is used to open the .db file and then process the found data accordingly, depteending on which tables and datasets are used."""

    def load_data2(self):
        # Load the data for the oil and gas fields
        self.df_field = read_sql('select * from Field', self.conn_db)
        self.df_owner = read_sql('select * from Owner', self.conn_db)
        self.loadDfFields()
        self.loadBoardData()
        self.loadPlatData()
        dx_data_unique = self.loadDirectionalData()
        self.loadWellData(dx_data_unique)

        self.used_dockets = self.dx_data['Board_Docket'].unique()
        self.used_years = self.dx_data['Board_Year'].unique()
        self.df_prod = read_sql('select * from Production', self.conn_db)
        self.df_prod.drop_duplicates(keep='first', inplace=True)


    def loadPlatData(self):
        self.df_plat = read_sql('select * from PlatData', self.conn_db)
        self.df_adjacent_plats = read_sql('select * from Adjacent', self.conn_db)
        self.df_plat.drop_duplicates(keep='first', inplace=True)
        self.df_plat = self.df_plat.dropna(subset=['Lat', 'Lon'])
        # anywhere the condition is met, adjust the well age to 0

        self.df_plat['Easting'], self.df_plat['Northing'] = zip(*self.df_plat.apply(lambda row: utm.from_latlon(row['Lat'], row['Lon'])[:2], axis=1))
        self.df_plat['geometry'] = self.df_plat.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)

    def loadDfFields(self):
        adjacent_fields = []
        # Generate a geometry column based on turning easting and northing into shapely points. This is used later for assembling pandas columns of LineStrings
        self.df_field['geometry'] = self.df_field.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)

        # Filter down to specific fields
        used_fields = self.df_field[['Field_Name', 'Easting', 'Northing']]

        # Create polygons for each field
        polygons = used_fields.groupby('Field_Name').apply(lambda x: Polygon(zip(x['Easting'], x['Northing'])), include_groups=False).reset_index()


        polygons.columns = ['Field_Name', 'geometry']
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(polygons, geometry='geometry')
        gdf['buffer'] = gdf['geometry'].buffer(10)  # create a buffer of 10 units for purposes of finding intersections

        # Find adjacent fields
        for _, row in gdf.iterrows():  # loop while ignoring the index
            neighbors = gdf[gdf['buffer'].intersects(row['geometry'])]['Field_Name'].tolist()  # filter out only where neighbors exist.
            neighbors.remove(row['Field_Name'])  # remove field name
            adjacent_fields.extend([{'Field_Name': row['Field_Name'], 'adjacent_Field_Name': neighbor} for neighbor in neighbors])  # extent the data out in adjacent fields so we have a list of fields and adjacent fields

        self.df_adjacent_fields = pd.DataFrame(adjacent_fields)  # turn it into a data frame.

    """Load the board data, the links, etc. Add in the concatenation data for ease of reference"""

    def loadBoardData(self):
        self.df_BoardData = read_sql('select * from BoardData', self.conn_db)
        self.df_BoardDataLinks = read_sql('select * from BoardDataLinks', self.conn_db)
        # Add in the conc codes for tsr sections for ease of reference.
        self.df_BoardData['Conc'] = self.df_BoardData[['Sec', 'Township', 'TownshipDir', 'Range', 'RangeDir', 'PM']].apply(lambda x: ma.reTranslateData(x), axis=1)

    """Load the directional data and then process it"""

    def loadDirectionalData(self):
        translated_fields = {'AAGARD RANCH': 'AAGARD RANCH FIELD', 'ANDERSON JUNCTION': 'ANDERSON JUNCTION FIELD', 'ANSCHUTZ RANCH WEBER': 'ANSCHUTZ RANCH (WEBER) FIELD', 'BAR X': 'BAR X FIELD', 'BIG FLAT': 'BIG FLAT FIELD', 'BIG FLAT WEST': 'BIG FLAT WEST FIELD', 'BIG INDIAN SOUTH': 'BIG INDIAN (SOUTH) FIELD', 'BONANZA': 'BONANZA FIELD', 'BOUNDARY BUTTE': 'BOUNDARY BUTTE FIELD', 'BRADFORD CYN': 'BRADFORD CANYON FIELD', 'BUZZARD BENCH': 'BUZZARD BENCH FIELD', 'CABALLO': 'CABALLO FIELD',
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

        month_dict = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5,
                      'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10,
                      'November': 11, 'December': 12}
        # Load the data
        self.dx_data = read_sql('select * from WellInfo', self.conn_db)
        self.dx_data = self.dx_data.rename(columns={'entityname': 'Operator'})
        # Drop any plugged data and duplicates
        self.dx_data = self.dx_data[self.dx_data['WorkType'] != 'PLUG']
        self.dx_data.drop_duplicates(keep='first', inplace=True)
        # Create a new column, display name, for displaying in the combo boxes
        self.dx_data['DisplayName'] = self.dx_data['WellID'].astype(str) + ' - ' + self.dx_data['WellName'].astype(str)

        # Convert to a datetime type and adjust accordingly for well age (in months)
        self.dx_data['DrySpud'] = to_datetime(self.dx_data['DrySpud'])
        self.dx_data['WellAge'] = (datetime.now().year - self.dx_data['DrySpud'].dt.year) * 12 + datetime.now().month - self.dx_data['DrySpud'].dt.month
        self.dx_data['DrySpud'] = self.dx_data['DrySpud'].dt.strftime('%Y-%m-%d')

        # Convert to a datetime type and adjust accordingly for well age (in months)

        # Conditional for non-existant well age and approved permits (IE, stuff that is planned)
        condition = pd.isna(self.dx_data['WellAge']) & (self.dx_data['CurrentWellStatus'] == 'Approved Permit')

        # anywhere the condition is met, adjust the well age to 0
        self.dx_data.loc[condition, 'WellAge'] = 0
        # Add it to an actual month value (since I can't find any way to sort by months because I'm ignorant)
        self.dx_data['month_order'] = self.dx_data['Docket_Month'].map(month_dict)

        # Sort by the month order
        df_sorted = self.dx_data.sort_values(by=['Board_Year', 'month_order'])

        # Drop that column
        self.dx_data = df_sorted.drop('month_order', axis=1)

        # Add in the fieldname, adjusted for what the official AGRC data lists the field names at
        self.dx_data['FieldName'] = self.dx_data['FieldName'].map(translated_fields)
        dx_data_unique = self.dx_data.drop_duplicates(subset=['WellID'])
        return dx_data_unique

    """Load the actual data for the well. All sorts of non-directional parameters"""

    def loadWellData(self, dx_data_unique):
        self.dx_df = read_sql('select * from DX', self.conn_db)
        self.dx_df.drop_duplicates(keep='first', inplace=True)
        """Merge in the data for better analysis"""
        self.dx_df = pd.merge(self.dx_df, dx_data_unique[['WellID', 'Elevation', 'FieldName', 'Mineral Lease', 'ConcCode']],
                              how='left', left_on='APINumber', right_on='WellID')
        self.dx_df['X'] = self.dx_df['X'].astype(float)
        self.dx_df['Y'] = self.dx_df['Y'].astype(float)
        """What we're doing here is converting to a true elevation compared to the elevation of the well. Namely, if the well is X ft deep, and the wellHead is at Y ft, what are they relative to each other?"""
        self.dx_df['TrueElevation'] = self.dx_df['Elevation'] - to_numeric(self.dx_df['TrueVerticalDepth'], errors='coerce')
        self.dx_df['MeasuredDepth'] = to_numeric(self.dx_df['MeasuredDepth'], errors='coerce')
        self.dx_df['CitingType'] = self.dx_df['CitingType'].str.lower()
        # This is done so that we can have linestrings for vertical wells (which effectively have one point in 2d)
        self.dx_df.loc[self.dx_df['CitingType'] == 'vertical', 'Y'] += self.dx_df.groupby(['X', 'Y']).cumcount() * 1e-3
        # State plane conversion. I don't think this ever gets used.
        self.dx_df['SPX'] = self.dx_df['X'].astype(float) / 0.3048
        self.dx_df['SPY'] = self.dx_df['Y'].astype(float) / 0.3048
        self.dx_df = self.dx_df.sort_values(by=['WellID', 'MeasuredDepth'])
        # get shl locations based on the first row of each wellid
        self.df_shl = self.dx_df.groupby('WellID').first().reset_index()


class ZoomPan:
    def __init__(self):
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None
        self.text_objects = []  # Store text annotations

    def zoom_factory(self, ax, base_scale):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata  # get event x location
            ydata = event.ydata  # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
            ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])

            # Update the font size of text annotations based on the new zoom level
            scale_factor = ax.get_xlim()[1] - ax.get_xlim()[0]
            for text in self.text_objects:
                new_fontsize = 12 / scale_factor * 2500  # Adjust the 10 as needed for desired scale
                text.set_fontsize(new_fontsize)
            ax.figure.canvas.draw()

        fig = ax.get_figure()  # get the figure of interest
        fig.canvas.mpl_connect('scroll_event', zoom)
        return zoom

    def add_text(self, ax, x, y, text_str):
        scale_factor = ax.get_xlim()[1] - ax.get_xlim()[0]
        text = ax.text(x, y, text_str, ha='center', va='center', fontsize=12 / scale_factor * 2500, transform=ax.transData)
        self.text_objects.append(text)

    def pan_factory(self, ax):
        def onPress(event):
            if event.inaxes != ax: return
            self.cur_xlim = ax.get_xlim()
            self.cur_ylim = ax.get_ylim()
            self.press = self.x0, self.y0, event.xdata, event.ydata
            self.x0, self.y0, self.xpress, self.ypress = self.press

        def onRelease(event):
            self.press = None
            ax.figure.canvas.draw()

        def onMotion(event):
            if self.press is None: return
            if event.inaxes != ax: return
            dx = event.xdata - self.xpress
            dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            self.cur_ylim -= dy
            ax.set_xlim(self.cur_xlim)
            ax.set_ylim(self.cur_ylim)

            ax.figure.canvas.draw()

        fig = ax.get_figure()  # get the figure of interest

        # attach the call back
        fig.canvas.mpl_connect('button_press_event', onPress)
        fig.canvas.mpl_connect('button_release_event', onRelease)
        fig.canvas.mpl_connect('motion_notify_event', onMotion)

        # return the function
        return onMotion


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = wellVisualizationProcess()
    w.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())

main()
