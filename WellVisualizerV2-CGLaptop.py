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

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QScrollArea, QLabel

from shapely.ops import unary_union
from sqlalchemy import create_engine
from difflib import get_close_matches
from matplotlib.patches import Polygon
from shapely.geometry import Point
from matplotlib.collections import PatchCollection
import time
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
from itertools import chain
from shapely.geometry import Polygon
import PyQt5
from matplotlib.ticker import ScalarFormatter, FuncFormatter
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.collections import LineCollection, PolyCollection
import matplotlib.pyplot as plt
from numpy import array, max, std
from pandas import to_numeric, read_sql, set_option, concat, to_datetime, options
import utm
import sqlite3
from PyQt5.QtWidgets import QMainWindow, QApplication, QStyledItemDelegate, QHeaderView
from datetime import datetime
import ModuleAgnostic as ma
from WellVisualizationUI import Ui_Dialog
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from shapely import wkt

"""Function and class designed for creating bold values in the self.ui.well_lst_combobox, specifically bolding wells of importance."""


class MultiBoldRowDelegate(QStyledItemDelegate):
    def __init__(self, bold_rows, parent=None):
        super().__init__(parent)
        self.bold_rows = set(bold_rows)  # Convert to set for faster lookup

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.row() in self.bold_rows:
            option.font.setBold(True)


class BoldDelegate(QStyledItemDelegate):
    def __init__(self, bold_values, parent=None):
        super().__init__(parent)
        self.bold_values = bold_values

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.data() in self.bold_values:
            font = option.font
            font.setBold(True)
            option.font = font


class wellVisualizationProcess(QMainWindow, BoardMattersVisualizer):
    # checkbox_state_changed = PyQt5.QtCore.pyqtSignal(str, bool)
    checkbox_state_changed = PyQt5.QtCore.pyqtSignal(int, str, bool, PyQt5.QtGui.QColor)

    def __init__(self, flag=True):
        super().__init__()
        self.docket_ownership_data = None
        self.used_plat_codes = None
        self.df_adjacent_plats = None
        self.df_adjacent_fields = None
        set_option('display.max_columns', None)
        # set_option('display.max_colwidth', None)
        # set_option('display.width', None)
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
        # self.ui.ownership_checkbox.setDisabled(True)
        apd_data_dir = os.path.join(os.getcwd(), 'Board_DB.db')
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

        # self.ui.oil_well_check.setStyleSheet(f"""QCheckBox {{color: {'#FF0000'};}}""")
        # self.ui.gas_well_check.setStyleSheet(f"""QCheckBox {{color: {'#FFA500'};}}""")
        # self.ui.water_disposal_check.setStyleSheet(f"""QCheckBox {{color: {'#0000FF'};}}""")
        # self.ui.dry_hole_check.setStyleSheet(f"""QCheckBox {{color: {'#4A4A4A'};}}""")
        # self.ui.injection_check.setStyleSheet(f"""QCheckBox {{color: {'#00FFFF'};}}""")
        # self.ui.other_well_status_check.setStyleSheet(f"""QCheckBox {{color: {'#FF00FF'};}}""")
        #
        # self.ui.producing_check.setStyleSheet(f"""QCheckBox {{color: {'#00FF00'};}}""")
        # self.ui.shut_in_check.setStyleSheet(f"""QCheckBox {{color: {'#8B4513'};}}""")
        # self.ui.pa_check.setStyleSheet(f"""QCheckBox {{color: {'#800080'};}}""")
        # self.ui.drilling_status_check.setStyleSheet(f"""QCheckBox {{color: {'#000080'};}}""")
        # self.ui.misc_well_type_check.setStyleSheet(f"""QCheckBox {{color: {'#008080'};}}""")

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
        # self.database = os.path.join(os.getcwd(), 'Board_DB.db')

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
        # self.all_wells_2d_vertical_planned_test = self.ax2d.scatter([], [], c='black', s=15, zorder=5)

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

        self.profit_line, = self.ax_prod_1.plot([], [], color='red', linewidth=2, zorder=1)  ## create the line graphic for profit
        self.profit_line_cum, = self.ax_prod_1.plot([], [], color='black', linewidth=2, zorder=1)  ## create the line graphic for cumulative profit

        self.prod_line, = self.ax_prod_2.plot([], [], color='blue', linewidth=2, zorder=1)  ## create the line graphic for production
        self.prod_line_cum, = self.ax_prod_2.plot([], [], color='black', linewidth=2, zorder=1)  ## create the line graphic for cumulative production
        self.current_prod = 'oil'  ### create an initial default for oil. fig 1 can switch between gas and oil

        """Board Data"""
        self.board_table_model = QStandardItemModel()
        self.all_wells_model = QStandardItemModel()
        self.used_plat_codes_for_boards = None
        """Assemble, organize, and produce the actual data from the .db item,"""
        self.table_model = QStandardItemModel()
        apd_data_dir = os.path.join(os.getcwd(), 'Board_DB.db')
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
        print('years done')
        """Setting up the radio buttons. Specifically their ID because QT Designer won't #@$@#$ing do it. This is for ease of reference when clicking different radio buttons"""

        # self.ui.sections_button_group.setId(self.ui.board_sections_radio_1, 0)
        # self.ui.sections_button_group.setId(self.ui.board_sections_radio_4, 1)
        # self.ui.sections_button_group.setId(self.ui.board_sections_radio_3, 2)
        # self.ui.board_sections_radio_1.setChecked(True)
        # self.ui.sections_button_group.buttonClicked.connect(self.drawTSRPlat)

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

        self.ui.ownership_checkbox.stateChanged.connect(self.ownershipSelection)

        self.ui.well_type_or_status_button_group.buttonClicked.connect(self.manipulateTheDfDocketDataDependingOnCheckboxes)

    """This process is designed to prepare the tables that are located on the main page as well as the board data element
    This is for allowing inserted data."""

    def setupTables(self):
        for i in [self.ui.well_data_table_1, self.ui.well_data_table_2, self.ui.well_data_table_3]:
            for j in range(12):
                i.setItem(0, j, PyQt5.QtWidgets.QTableWidgetItem())
        for j in range(3):
            self.ui.board_data_table.setItem(j, 0, PyQt5.QtWidgets.QTableWidgetItem())

    def zoom(self, event, ax, centroid, fig):
        """
        This function performs zooming based on the scroll event, using the centroid as anchor.
        """
        # Get the current zoom factor (can be adjusted for different behavior)
        current_zoom = ax.get_xlim3d()[1] - ax.get_xlim3d()[0]

        # Determine zoom direction based on scroll direction (adjust sensitivity as needed)
        zoom_factor = 1.1 if event.button == 'up' else 0.9

        # Calculate zoom amount based on current zoom and factor
        zoom_amount = (current_zoom * zoom_factor) / 2

        # Apply zoom relative to the centroid
        new_xlim = [centroid[0] - zoom_amount, centroid[0] + zoom_amount]
        new_ylim = [centroid[1] - zoom_amount, centroid[1] + zoom_amount]
        new_zlim = [centroid[2] - zoom_amount, centroid[2] + zoom_amount]

        # Set the new limits for all axes
        ax.set_xlim3d(new_xlim)
        ax.set_ylim3d(new_ylim)
        ax.set_zlim3d(new_zlim)
        # Re-draw the plot for the updated view
        fig.canvas.draw_idle()
        # self.fig3d.canvas.draw_idle()

    """Run this to setup the years combo box"""

    def comboBoxSetupYear(self):
        self.ui.year_lst_combobox.clear()
        model = QStandardItemModel()
        for item_text in self.used_years:
            print('item text', item_text)
            item = QStandardItem(item_text)
            model.appendRow(item)
        self.ui.year_lst_combobox.setModel(model)
        # [[model.data(model.index(row, column)) for column in range(model.columnCount())]
        #     for row in range(model.rowCount())
        # ]

    """Run this to setup the months tab when the year tab is changed. Ran when year_lst_combobox is used"""

    def comboBoxSetupMonthWhenYearChanges(self):
        self.ui.well_lst_combobox.clear()
        self.ui.board_matter_lst_combobox.clear()
        self.ui.month_lst_combobox.clear()
        # Create new dataframes that will be limited by the data in the year comboboxes

        self.used_months = self.dx_data[self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText()]['Docket_Month'].unique()
        self.df_year = self.dx_data[(self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText())]
        model = QStandardItemModel()
        for item_text in self.used_months:
            item = QStandardItem(item_text)
            model.appendRow(item)
        self.ui.month_lst_combobox.setModel(model)

    """Run this to setup the board matters tab when the month tab is changed. Ran when month_lst_combobox is used"""


    def comboBoxSetupBoardWhenMonthChanges(self):
        self.ui.well_lst_combobox.clear()
        self.ui.board_matter_lst_combobox.clear()
        self.clearDataFrom2dAnd3d()
        # Create new dataframes that will be limited by the data in the year and month comboboxes
        df_month = self.dx_data[(self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText()) & (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText())]
        self.df_month = self.df_year[(self.df_year['Docket_Month'] == self.ui.month_lst_combobox.currentText())]

        # get all the board matters for the month
        board_matters = df_month['Board_Docket'].unique()
        model = QStandardItemModel()
        for item_text in board_matters:
            item = QStandardItem(item_text)
            model.appendRow(item)
        self.ui.board_matter_lst_combobox.setModel(model)

    """Run this to setup the list of wells tab when the board matter tab is changed. It is run when the combobox board_matter_lst_combobox is used"""

    def comboBoxSetupWellsWhenDocketChanges(self):
        time_start1 = time.perf_counter()
        self.clearDataFrom2dAnd3d()

        # Setup a dataframe that is further filtered. I know I could be calling previous dataframes. But I don't wanna.
        self.df_docket = self.dx_data[(self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText())
                                      & (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText())
                                      & (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())]
        print(self.df_docket_data)
        operators = self.df_docket['Operator'].unique()
        operators = sorted(operators)

        self.operators_model.clear()
        for row in operators:
            self.operators_model.appendRow(QStandardItem(row))
        time_start2 = time.perf_counter()

        # get the apis and unique count of display names from the docket. This is all for purposes of A. Populating the well combobox and B. Highlighting the wells of interest.
        apis, unique_count = self.df_docket['WellID'].unique(), sorted(self.df_docket['DisplayName'].unique())
        # This dataframe limits the directional dataframe to just the wells that are used in self.df_docket
        test_df = (self.dx_df[self.dx_df['APINumber'].isin(apis)].drop_duplicates(keep='first').sort_values(by=['APINumber', 'MeasuredDepth']))

        # This restricts only to data that actually is present (has apis present). IE, no directional data? No good.
        unique_apis_with_data = test_df['APINumber'].unique()
        self.df_docket = self.df_docket[self.df_docket['WellID'].isin(unique_apis_with_data)]
        time_start3 = time.perf_counter()

        # Figure out which wells are of import to this board item. The Mainwell Column should show it equal to 1
        master_data = self.df_docket[self.df_docket['MainWell'] == 1]

        # Sort it alphabetically
        masters_apds = sorted(master_data['DisplayName'].unique())

        # Find which wells are *NOT* main wells, and sort those.
        sorted_list = sorted([x for x in unique_count if x not in masters_apds])
        time_start4 = time.perf_counter()

        # Merge the two together, so there is a list of alphabetic master wells, then an alphabetic list of other wells.
        final_list = masters_apds + sorted_list

        # this will then populate the all wells table in the all wells tab
        self.fillInAllWellsTable(final_list)
        time_start5 = time.perf_counter()

        # Prep and input the model
        self.ui.well_lst_combobox.clear()
        model = QStandardItemModel()
        for item_text in final_list:
            item = QStandardItem(item_text)
            model.appendRow(item)
        self.ui.well_lst_combobox.setModel(model)
        time_start6 = time.perf_counter()

        # This will let us then make the master wells in the combo box to be bold (to differentiate)
        delegate = BoldDelegate(masters_apds)
        self.ui.well_lst_combobox.setItemDelegate(delegate)
        time_start7 = time.perf_counter()

        # This will update the 2d data. Relative Elevation, targeted data, etc
        self.update2dWhenDocketChanges()
        time_start8 = time.perf_counter()

        # Create a new dataframe based on the docket data that includes directional surveys
        self.df_docket_data = self.returnWellsWithParameters()
        time_start9 = time.perf_counter()

        # setup the axes for the data.
        self.setAxesLimits()
        # setup the township and range boundaries
        time_start10 = time.perf_counter()

        # Setup the data so that it can be filtered based on age parameters
        self.setupDataForBoardDrillingInformation()
        time_start11 = time.perf_counter()

        # Manipulate the axes for the 3d data depending on the centroid of the current data.
        if self.drilled_segments_3d:
            self.centroid, std_vals = self.calculate_centroid_np(self.drilled_segments_3d)
            new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
            new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
            new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]
            self.ax3d.set_xlim3d(new_xlim)
            self.ax3d.set_ylim3d(new_ylim)
            self.ax3d.set_zlim3d(new_zlim)
        time_start12 = time.perf_counter()
        self.used_sections, self.all_wells_plat_labels = self.draw2dModelSections()
        # Prep the data for oil fields.
        self.colorInFields()

        self.update_checkboxes()
        time_start13 = time.perf_counter()

        # get the centroids for where the township and range section labels will be.
        self.centroids_lst = []
        for i, val in enumerate(self.used_sections):
            self.used_sections[i].append(self.used_sections[i][0])
            centroid = Polygon(self.used_sections[i]).centroid
            self.centroids_lst.append(centroid)
        time_start14 = time.perf_counter()

        self.returnWellDataDependingOnParametersTest()
        self.drawTSRPlat()
        time_start15 = time.perf_counter()

        # ma.analyzeTimeNoArgs(lambda: self.returnWellDataDependingOnParametersTest())
        # ma.analyzeTimeNoArgs(lambda: self.ownershipSelection())

        self.colorInOwnership()
        self.ownershipSelection()
        time_start16 = time.perf_counter()

        owners = sorted(self.docket_ownership_data['owner'].unique())
        agencies = sorted(self.docket_ownership_data['state_legend'].unique())

        self.owner_model.clear()
        self.agency_model.clear()
        for row in owners:
            self.owner_model.appendRow(QStandardItem(row))
        for row in agencies:
            self.agency_model.appendRow(QStandardItem(row))
        time_start17 = time.perf_counter()

        self.updateOwnershipCheckboxes()
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()
        time_start18 = time.perf_counter()

        self.combo_box_data = [self.ui.well_lst_combobox.itemText(i)[:10] for i in range(self.ui.well_lst_combobox.count())]
        self.prodButtonsActivate()

        # type_value_counts = self.df_docket['CurrentWellType'].value_counts()
        # status_value_counts = self.df_docket['CurrentWellStatus'].value_counts()
        main_statuses = [
            'Plugged & Abandoned',
            'Producing',
            'Shut-in',
            'Drilling']

        # Define the statuses to be merged into 'Other'
        other_statuses = [
            'Location Abandoned - APD rescinded',
            'Returned APD (Unapproved)',
            'Approved Permit',
            'Active',
            'Drilling Operations Suspended',
            'New Permit',
            'Inactive',
            'Temporarily-abandoned',
            'Test Well or Monitor Well']
        main_types = [
            'Unknown',
            'Oil Well',
            'Dry Hole',
            'Gas Well',
            'Test Well',
            'Water Source Well']
        merged_types = {
            'Injection Well': ['Water Injection Well', 'Gas Injection Well'],
            'Disposal Well': ['Water Disposal Well', 'Oil Well/Water Disposal Well'],
            'Other': ['Test Well', 'Water Source Well', 'Unknown']}
        self.getCountersForStatus(main_statuses, other_statuses)
        self.getCountersForType(main_types, merged_types)

        #
        # self.ui.producing_check.setStyleSheet(f"""QCheckBox {{color: {'#a2e361'};}}""")
        # self.ui.shut_in_check.setStyleSheet(f"""QCheckBox {{color: {'#D2B48C'};}}""")
        # self.ui.pa_check.setStyleSheet(f"""QCheckBox {{color: {'#4c2d77'};}}""")
        # self.ui.drilling_status_check.setStyleSheet(f"""QCheckBox {{color: {'#001958'};}}""")
        # self.ui.misc_well_type_check.setStyleSheet(f"""QCheckBox {{color: {'#4a7583'};}}""")
        # Convert the dictionary to a DataFrame for better visualization
        # result_df = pd.DataFrame.from_dict(status_counts, orient='index', columns=['Count'])
        # result_df.index.name = 'Status'
        # result_df = result_df.sort_values('Count', ascending=False)
        # print(result_df)

        # print(type_value_counts)
        # print(status_value_counts)

        time_start19 = time.perf_counter()
        #
        # print('\n\ncomboBoxSetupWellsWhenDocketChanges', time_start8 - time_start1)
        # ma.printLineBreak()
        # print('2-1', round(time_start2 - time_start1,3))
        # print('3-2', round(time_start3 - time_start2,3))
        # print('4-3', round(time_start4 - time_start3,3))
        # print('5-4', round(time_start5 - time_start4,3))
        # print('6-5', round(time_start6 - time_start5,3))
        # print('7-6', round(time_start7 - time_start6,3))
        # print('8-7', round(time_start8 - time_start7,3))
        # print('9-8', round(time_start9 - time_start8,3))
        # print('10-9', round(time_start10 - time_start9,3))
        # print('11-10', round(time_start11 - time_start10,3))
        # print('12-11', round(time_start12 - time_start11,3))
        # print('13-12', round(time_start13 - time_start12,3))
        # print('14-13', round(time_start14 - time_start13,3))
        # print('15-14', round(time_start15 - time_start14,3))
        # print('16-15', round(time_start16 - time_start15,3))
        # print('17-16', round(time_start17  - time_start16,3))
        # print('18-17', round(time_start18 - time_start17,3))
        # print('19-18', round(time_start19 - time_start18,3))

    def getCountersForStatus(self, main_status, other_status):

        # Initialize a dictionary to store the counts
        status_counts = {status: 0 for status in main_status}
        status_counts['Other'] = 0

        # Count occurrences
        for status in main_status:
            status_counts[status] = self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)

        # Count and sum up 'Other' category
        for status in other_status:
            status_counts['Other'] += self.df_docket['CurrentWellStatus'].value_counts().get(status, 0)

        self.ui.producing_check.setText(f"""Producing ({str(status_counts['Producing'])})""")
        self.ui.shut_in_check.setText(f"""Shut In ({str(status_counts['Shut-in'])})""")
        self.ui.pa_check.setText(f"""Plugged and Abandoned ({str(status_counts['Plugged & Abandoned'])})""")
        self.ui.drilling_status_check.setText(f"""Drilling ({str(status_counts['Drilling'])})""")
        self.ui.misc_well_type_check.setText(f"""Misc ({str(status_counts['Other'])})""")

        print(status_counts)

    def getCountersForType(self, main_types, merged_types):
        # self.ui.oil_well_check.setStyleSheet(f"""QCheckBox {{color: {'#c34c00'};}}""")
        # self.ui.gas_well_check.setStyleSheet(f"""QCheckBox {{color: {'#f1aa00'};}}""")
        # self.ui.water_disposal_check.setStyleSheet(f"""QCheckBox {{color: {'#0032b0'};}}""")
        # self.ui.dry_hole_check.setStyleSheet(f"""QCheckBox {{color: {'#4f494b'};}}""")
        # self.ui.injection_check.setStyleSheet(f"""QCheckBox {{color: {'#93ebff'};}}""")
        # self.ui.other_well_status_check.setStyleSheet(f"""QCheckBox {{color: {'#985bee'};}}""")
        type_counts = {well_type: 0 for well_type in main_types}
        type_counts.update({merged: 0 for merged in merged_types})
        # print(self.df_docket)
        # Count occurrences
        for well_type in main_types:
            type_counts[well_type] = self.df_docket['CurrentWellType'].value_counts().get(well_type, 0)

        # Count and sum up merged categories
        for merged, subtypes in merged_types.items():
            for subtype in subtypes:
                type_counts[merged] += self.df_docket['CurrentWellType'].value_counts().get(subtype, 0)

        self.ui.oil_well_check.setText(f"""Oil Well ({str(type_counts['Oil Well'])})""")
        self.ui.gas_well_check.setText(f"""Gas Well ({str(type_counts['Gas Well'])})""")
        self.ui.water_disposal_check.setText(f"""Water Disposal ({str(type_counts['Disposal Well'])})""")
        self.ui.dry_hole_check.setText(f"""Dry Hole ({str(type_counts['Dry Hole'])})""")
        self.ui.injection_check.setText(f"""Injection Well ({str(type_counts['Injection Well'])})""")
        self.ui.other_well_status_check.setText(f"""Other ({str(type_counts['Other'])})""")

        # print(type_counts)

    def colorInOwnership(self):
        polygons_lst_owner, polygons_lst_agency = [], []
        # '#000000', '#003f5c', '#2f4b7c', '#665191'

        colors_owner = {'Private': '#D2B48C',
                        'Tribal': '#800000',
                        'State': '#0000FF',
                        'Federal': '#008000'}
        colors_agency = {'None': 'white',
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
                         'Tribal': '#800000'}

        # all_used_plats = self.df_docket['ConcCode'].unique()
        docket_ownership_data = self.df_owner[self.df_owner['conc'].isin(self.used_plat_codes_for_boards)]
        docket_ownership_data['geometry'] = docket_ownership_data['geometry'].apply(wkt.loads)
        docket_ownership_data = gpd.GeoDataFrame(docket_ownership_data, geometry='geometry', crs='EPSG:4326')
        docket_ownership_data = docket_ownership_data.to_crs(epsg=26912)
        docket_ownership_data['owner_color'] = docket_ownership_data['owner'].map(colors_owner)
        docket_ownership_data['agency_color'] = docket_ownership_data['state_legend'].map(colors_agency)

        docket_ownership_data['owner_order'] = docket_ownership_data.groupby('owner').cumcount() + 1
        docket_ownership_data['agency_order'] = docket_ownership_data.groupby('state_legend').cumcount() + 1

        docket_ownership_data = docket_ownership_data.drop_duplicates(keep='first')
        self.docket_ownership_data = docket_ownership_data
        grouped_rows_owner = docket_ownership_data.groupby('owner')
        grouped_rows_agency = docket_ownership_data.groupby('state_legend')
        colors_owner_used, colors_agency_used = [], []
        for conc, group in grouped_rows_owner:
            for idx, row in group.iterrows():
                coordinates = list(row['geometry'].exterior.coords)
                polygons_lst_owner.append(np.array(coordinates))
                colors_owner_used.append(row['owner_color'])

        for conc, group in grouped_rows_agency:
            for idx, row in group.iterrows():
                coordinates = list(row['geometry'].exterior.coords)
                polygons_lst_agency.append(np.array(coordinates))
                colors_agency_used.append(row['agency_color'])

        self.ownership_sections_agency.set_color(colors_agency_used)
        self.ownership_sections_agency.set_paths(polygons_lst_agency)
        self.ownership_sections_agency.set_visible(False)

        self.ownership_sections_owner.set_color(colors_owner_used)
        self.ownership_sections_owner.set_paths(polygons_lst_owner)
        self.ownership_sections_owner.set_visible(False)
        self.createOwnershipLabels()

    def colorInFields(self):
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
        # cx.add_basemap(self.ax2d, zoom=15, source=cx.providers.Google.satellite)

    def fillInAllWellsTable(self, lst):
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
        # self.ui.all_wells_qtableview.horizontalHeader().setVisible(False)
        self.ui.all_wells_qtableview.verticalHeader().setVisible(False)

        self.ui.all_wells_qtableview.setModel(self.all_wells_model)

    def on_row_clicked(self, index: QModelIndex):
        row = index.row()
        row_data = [self.all_wells_model.data(self.all_wells_model.index(row, column)) for column in range(self.all_wells_model.columnCount())]
        self.comboUpdateWhenSelectedFromAllWellsTable(row_data)

    """This just clears all the data."""

    def clearDataFrom2dAnd3d(self):
        self.used_plat_codes = []
        self.ui.sectionsBoardComboBox.clear()
        self.ui.board_matter_files.clear()
        self.ui.board_brief_text.clear()
        self.ui.board_brief_text.clear()

        self.drawModelBasedOnParameters2d(self.all_wells_2d_current, [], [], [], self.ax2d, self.all_wells_2d_vertical_asdrilled)
        self.drawModelBasedOnParameters(self.all_wells_3d_current, [], [], [], self.ax3d)

        self.drawModelBasedOnParameters2d(self.all_wells_2d_planned, [], [], [], self.ax2d, self.all_wells_2d_vertical_planned)
        self.drawModelBasedOnParameters(self.all_wells_3d_planned, [], [], [], self.ax3d)

        self.drawModelBasedOnParameters2d(self.all_wells_2d_asdrilled, [], [], [], self.ax2d, self.all_wells_2d_vertical_current)
        self.drawModelBasedOnParameters(self.all_wells_3d_asdrilled, [], [], [], self.ax3d)

        for i in range(len(self.all_wells_2d_operators)):
            self.drawModelBasedOnParameters2d(self.all_wells_2d_operators[i], [], [], [], self.ax2d, self.all_wells_2d_operators_vertical[i])

        self.spec_well_3d.set_data([], [])
        self.spec_well_3d.set_3d_properties([])

        self.spec_well_3d_solo.set_data([], [])
        self.spec_well_3d_solo.set_3d_properties([])
        self.spec_well_3d.set_data([], [])
        self.spec_well_3d.set_3d_properties([])
        self.all_vertical_wells_2d.set_offsets([None, None])
        self.spec_vertical_wells_2d.set_offsets([None, None])
        self.spec_well_2d.set_data([], [])
        self.plats_2d.set_segments([])
        self.plats_2d_main.set_segments([])
        self.plats_2d_1adjacent.set_segments([])
        self.plats_2d_2adjacent.set_segments([])

        self.ownership_sections_agency.set_paths([])
        self.ownership_sections_owner.set_paths([])
        self.field_sections.set_paths([])
        self.profit_line.set_data([], [])
        self.profit_line_cum.set_data([], [])
        self.prod_line.set_data([], [])
        self.prod_line_cum.set_data([], [])
        self.outlined_board_sections.set_paths([])
        self.specific_well_data_model.removeRows(0, self.specific_well_data_model.rowCount())

        for i in range(11):
            self.ui.well_data_table_1.item(0, i).setText('')
            self.ui.well_data_table_2.item(0, i).setText('')
            self.ui.well_data_table_3.item(0, i).setText('')

        for text in self.zp.text_objects:
            text.remove()
        self.zp.text_objects = []
        self.canvas_prod_1.draw()
        self.canvas_prod_2.draw()
        self.ax2d.draw_artist(self.all_vertical_wells_2d)
        self.canvas3d_solo.draw()
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()
        self.canvas3d.blit(self.ax3d.bbox)
        self.canvas3d.draw()
        self.ui.all_wells_qtableview.setModel(None)
        self.all_wells_2d_operators = []
        self.all_wells_2d_operators_vertical = []
        self.ui.producing_check.setText(f"""Producing)""")
        self.ui.shut_in_check.setText(f"""Shut In""")
        self.ui.pa_check.setText(f"""Plugged and Abandoned""")
        self.ui.drilling_status_check.setText(f"""Drilling""")
        self.ui.misc_well_type_check.setText(f"""Misc""")
        self.ui.oil_well_check.setText(f"""Oil Well""")
        self.ui.gas_well_check.setText(f"""Gas Well""")
        self.ui.water_disposal_check.setText(f"""Water Disposal""")
        self.ui.dry_hole_check.setText(f"""Dry Hole""")
        self.ui.injection_check.setText(f"""Injection Well""")
        self.ui.other_well_status_check.setText(f"""Other""")

    """Set the axes limits for the 2d image based on the data that is found."""

    def setAxesLimits(self):
        # Generate all line segments
        segments = self.returnSegmentsFromDF(self.df_docket_data)

        # flatten the whole thing into one list and then convert it into a numpy array
        flattened_list = [tuple(point) for sublist in segments for point in sublist]
        unique_points = np.array(list(set(flattened_list)))

        # get mins and maxes and adjust the 2d axes accordingly.
        min_x = np.min(unique_points[:, 0])
        max_x = np.max(unique_points[:, 0])
        min_y = np.min(unique_points[:, 1])
        max_y = np.max(unique_points[:, 1])
        self.ax2d.set_xlim([min_x - 16000, max_x + 16000])
        self.ax2d.set_ylim([min_y - 16000, max_y + 16000])

    """This function is run whenever the user clicks on a well that is currently displayed. Nothing will happen if there are no wells displayed. 
    It should:
    A. Highlight the well that is clicked (in 2d and 3d)
    B. Fill in the data in the main table
    C. Populate the production data
    D. Update the combobox for wells
    """

    def onClick2d(self, event):
        if event.inaxes is not None:
            x_selected, y_selected = event.xdata, event.ydata
            # When you click to select wells, there needs to be a threshold established for how close you have to click before it is registered as selected

            # Find that rough selection distance
            limit = (np.diff(self.ax2d.get_xlim())[0] + np.diff(self.ax2d.get_ylim())[0]) / 80

            # Find the distance from the point that was selected to all other wells that are currently displayed
            # self.currently_used_lines is established at manipulateTheDfDocketDataDependingOnCheckboxes()
            self.currently_used_lines['distance'] = np.sqrt((self.currently_used_lines['X'].astype(float) - x_selected) ** 2 + (self.currently_used_lines['Y'].astype(float) - y_selected) ** 2)

            # Create a dataframe of points that are within the limit distance of the actively found points
            closest_points = self.currently_used_lines[self.currently_used_lines['distance'] < limit]

            # do this assuming there *are* points within that distance
            if not closest_points.empty:
                # Find the closest point
                closest_point = closest_points.loc[closest_points['distance'].idxmin()]

                # get the api identification for that closest point
                selected_well_api = closest_point['APINumber']

                # generate a dataframe that is the full data for the well with that API Number
                filtered_df = self.currently_used_lines[self.currently_used_lines['APINumber'] == selected_well_api]

                # convert data types (partly routine)
                data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
                data_select_3d = filtered_df[['SPX', 'SPY', 'Targeted Elevation']].to_numpy().astype(float)

                # Add the data to the self. elements
                self.selected_well_2d_path = data_select_2d.tolist()
                self.selected_well_3d_path = data_select_3d.tolist()
                self.targeted_well = selected_well_api

                # Search the combo box and find the index where this occurs
                target_index = self.combo_box_data.index(self.targeted_well)

                # Update the combobox with the found index
                self.ui.well_lst_combobox.setCurrentIndex(target_index)

                # Run all the appropriate processes that should be run when the selected well is instantiated(?)
                self.comboUpdateWhenWellChanges()

    """# This will update the 2d data. Relative Elevation, targeted data, etc"""

    def update2dWhenDocketChanges(self):
        # get the current text
        current_text = self.ui.well_lst_combobox.currentText()

        # filter down the api numbers at 10 values
        filtered_df = self.dx_df[self.dx_df['APINumber'] == current_text[:10]]

        # set to appropriate data types
        data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
        data_select_3d = filtered_df[['X', 'Y', 'TrueVerticalDepth']].to_numpy().astype(float)
        # add to lists
        self.selected_well_2d_path = data_select_2d.tolist()
        self.selected_well_3d_path = data_select_3d.tolist()
        # set the targeted well to the current text (again, 10 data values)
        self.targeted_well = current_text[:10]

        # This is for creating a relative elevation for a deprecated function. the idea was that if the targeted well was at elevation 0, what would the other well elevations be relative to it?
        self.targeted_well_elevation = self.dx_data['Elevation'].iloc[0]
        self.dx_df['Targeted Elevation'] = self.dx_df['TrueElevation'] - self.targeted_well_elevation
        self.dx_data['Relative Elevation'] = self.dx_data['Elevation'] - self.targeted_well_elevation

    """Setup the displays and information when a well is selected through well_lst_combobox. This is also called when a well is clicked"""

    def comboUpdateWhenWellChanges(self):
        # filter and restrict the data frame down to the relevant docket and well data

        df_month = self.dx_data[(self.dx_data['Board_Year'] == self.ui.year_lst_combobox.currentText())
                                & (self.dx_data['Docket_Month'] == self.ui.month_lst_combobox.currentText())
                                & (self.dx_data['Board_Docket'] == self.ui.board_matter_lst_combobox.currentText())]

        # get the current text in the combo box so that we know what we're looking at.
        current_text = self.ui.well_lst_combobox.currentText()

        # restrict down to the current data row.
        current_data_row = df_month[df_month['DisplayName'] == current_text]
        if len(current_data_row) > 1:
            current_data_row = current_data_row.sort_values(by='APDApprovedDate', ascending=False).head(1)
        misc_data = self.df_docket_data[self.df_docket_data['APINumber'] == current_data_row['WellID'].item()]
        print(misc_data)
        # I'm sure there's a better way to do this, but this is for filling out data in the table with the appropriate value in case for some reason the data order is scrambled.
        row_1_data = ['WellID', 'WellName', 'SideTrack', 'CurrentWellStatus', 'CurrentWellType', 'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud']
        # row_2_data = ['WCRCompletionDate', 'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType']
        row_2_data = ['WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'WCRCompletionDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType']

        # row_3_data = ['MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'CurrentWellStatus', 'CurrentWellType', 'Total Gas Prod', 'Total Oil Prod', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In']
        row_3_data = ['GasVolume', 'OilVolume', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In', 'Operator', 'MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'WorkType', 'Slant', ]
        row_3_data = ['GasVolume', 'OilVolume', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In', 'Operator', 'MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'WorkType', 'Slant', ]

        self.setupTableData([row_1_data, row_2_data, row_3_data], current_data_row)
        for i, value in enumerate(row_1_data):
            self.ui.well_data_table_1.item(0, i).setText(str(current_data_row[value].item()))
        for i, value in enumerate(row_2_data):
            self.ui.well_data_table_2.item(0, i).setText(str(current_data_row[value].iloc[0]))
        for i, value in enumerate(row_3_data):
            self.ui.well_data_table_3.item(0, i).setText(str(current_data_row[value].iloc[0]))
        self.update2dSelectedWhenWellChanges()

    def setupTableData(self, row_data, df):
        self.specific_well_data_model.removeRows(0, self.specific_well_data_model.rowCount())
        data_used_lst = [row_data[0], [], row_data[1], [], row_data[2], []]
        for i, value in enumerate(row_data[0]):
            data_used_lst[1].append(str(df[value].values[0]))
        for i, value in enumerate(row_data[1]):
            data_used_lst[3].append(str(df[value].values[0]))
        for i, value in enumerate(row_data[2]):
            data_used_lst[5].append(str(df[value].values[0]))

        for row in data_used_lst:
            items = [QStandardItem(str(item)) for item in row]
            self.specific_well_data_model.appendRow(items)

        self.ui.well_data_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.well_data_table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.well_data_table_view.horizontalHeader().setVisible(False)
        self.ui.well_data_table_view.verticalHeader().setVisible(False)
        self.ui.well_data_table_view.setModel(self.specific_well_data_model)

        bold_rows = [0, 2, 4]  # The row you want to bold (0-indexed)
        delegate = MultiBoldRowDelegate(bold_rows)
        self.ui.well_data_table_view.setItemDelegate(delegate)

    """This is a continuation of comboUpdateWhenWellChanges. Why? I don't know. Setup the displays and information when a well is selected through well_lst_combobox. This is also called when a well is clicked"""

    def update2dSelectedWhenWellChanges(self):
        self.update2dWhenDocketChanges()
        self.draw2dModelSelectedWell()

    """Called when a row is clicked in the all well table."""

    def comboUpdateWhenSelectedFromAllWellsTable(self, data):

        """Filter based on API Number"""
        filtered_df = self.currently_used_lines[self.currently_used_lines['APINumber'] == data[0]]
        data_select_2d = filtered_df[['X', 'Y']].to_numpy().astype(float)
        data_select_3d = filtered_df[['SPX', 'SPY', 'Targeted Elevation']].to_numpy().astype(float)

        """Add wells to list"""
        self.selected_well_2d_path = data_select_2d.tolist()
        self.selected_well_3d_path = data_select_3d.tolist()

        """Set the selected well, and change the combo box to match"""
        self.targeted_well = data[0]
        target_index = self.combo_box_data.index(self.targeted_well)
        self.ui.well_lst_combobox.setCurrentIndex(target_index)

        """Fill in the data rows"""
        row_1_data = ['WellID', 'WellName', 'SideTrack', 'WorkType', 'Slant', 'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud']
        row_2_data = ['WCRCompletionDate', 'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType']
        row_3_data = ['MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'CurrentWellStatus', 'CurrentWellType', 'Total Gas Prod', 'Total Oil Prod', 'WellAge', 'Last Production (if Shut In)', 'Months Shut In']
        all_columns = row_1_data + row_2_data + row_3_data
        result_dict = {col: value for col, value in zip(all_columns, data)}
        test_df = pd.DataFrame([result_dict])
        # Parse and fill out the data rows
        for i, value in enumerate(row_1_data):
            self.ui.well_data_table_1.item(0, i).setText(str(test_df[value].item()))
        for i, value in enumerate(row_2_data):
            self.ui.well_data_table_2.item(0, i).setText(str(test_df[value].iloc[0]))
        for i, value in enumerate(row_3_data):
            self.ui.well_data_table_3.item(0, i).setText(str(test_df[value].iloc[0]))
        self.update2dSelectedWhenWellChanges()
        # self.draw2dModelSelectedWell()

    """This is for specifically drawing the 2d selected well."""

    def draw2dModelSelectedWell(self):

        """Get the well's parameter data"""
        df_well_data = self.df_docket.loc[self.dx_data['DisplayName'] == self.ui.well_lst_combobox.currentText()]

        """Restrict down to the dx data for the specific well"""
        df_well = self.dx_df[self.dx_df['APINumber'] == df_well_data['WellID'].iloc[0]]

        """Differentiate between the citing types (generate seperate data frames)"""
        drilled_df = df_well[df_well['CitingType'].isin(['asdrilled'])]
        planned_df = df_well[df_well['CitingType'].isin(['planned'])]
        vert_df = df_well[df_well['CitingType'].isin(['vertical'])]

        """This will prioritize the data, making sure that *something* gets plotted, even if you're just trying to look at asDrilled data and this well doesn't have anything."""
        df_well = self.findPopulatedDataframeForSelection(drilled_df, planned_df, vert_df)
        df_well.drop_duplicates(keep='first', inplace=True)
        df_well['X'] = df_well['X'].astype(float)
        df_well['Y'] = df_well['Y'].astype(float)

        """Isolate out the xy data into a list."""
        xy_data = df_well[['X', 'Y']].values

        """Setup the data for the vertical well data"""
        if df_well['CitingType'].iloc[0] == 'vertical':
            self.spec_vertical_wells_2d.set_offsets(xy_data)
            self.spec_well_2d.set_data([], [])
        else:
            self.spec_vertical_wells_2d.set_offsets([None, None])
            self.spec_well_2d.set_data(xy_data[:, 0], xy_data[:, 1])
        x = to_numeric(df_well['SPX'], errors='coerce')
        y = to_numeric(df_well['SPY'], errors='coerce')
        z = to_numeric(df_well['Targeted Elevation'], errors='coerce')
        self.centroid = (x.mean(), y.mean(), z.mean())
        self.spec_well_3d.set_data(x, y)
        self.spec_well_3d.set_3d_properties(z)

        self.spec_well_3d_solo.set_data(x, y)
        self.spec_well_3d_solo.set_3d_properties(z)
        # self.ax3d.relim()  # Ensure this is called if not done automatically
        # self.ax3d.autoscale_view()

        self.canvas2d.draw()
        self.canvas3d.draw()

        new_xlim = [self.centroid[0] - 8000, self.centroid[0] + 8000]
        new_ylim = [self.centroid[1] - 8000, self.centroid[1] + 8000]
        new_zlim = [self.centroid[2] - 8000, self.centroid[2] + 8000]

        self.ax3d_solo.set_xlim3d(new_xlim)
        self.ax3d_solo.set_ylim3d(new_ylim)
        self.ax3d_solo.set_zlim3d(new_zlim)

        self.canvas3d_solo.draw()
        self.drawProductionGraphic()

    """Sort through the data, trying to find dataframes that aren't empty"""

    def findPopulatedDataframeForSelection(self, drilled_df, planned_df, vert_df):
        if not drilled_df.empty:
            return drilled_df
            # If the first is empty, check the second DataFrame
        elif not planned_df.empty:
            return planned_df
            # If the first two are empty, default to the third DataFrame
        else:
            return vert_df

    def drawTSRPlat(self):
        self.used_plat_codes = []

        def fieldsTester1(df_field):
            df_field['geometry'] = df_field.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)
            used_fields = df_field[['Conc', 'Easting', 'Northing', 'geometry']]
            used_fields['geometry'] = used_fields.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)

            def create_polygon(group):
                return Polygon(zip(group['Easting'], group['Northing']))

            # Use include_groups=False to exclude the grouping columns from the operation
            polygons = used_fields.groupby('Conc', group_keys=False).apply(create_polygon).reset_index()

            # Rename the column containing the polygons
            polygons = polygons.rename(columns={0: 'geometry'})

            # polygons = used_fields.groupby('Conc').apply(lambda x: Polygon(zip(x['Easting'], x['Northing']))).reset_index()
            merged_data = used_fields.merge(polygons, on='Conc')

            merged_data = merged_data.drop('geometry_y', axis=1).rename(columns={'geometry_x': 'geometry'})
            # merged_data = merged_data.drop('geometry', axis=1).rename(columns={0: 'geometry'})

            df_new = merged_data.groupby('Conc').apply(lambda x: Polygon(zip(x['Easting'], x['Northing']))).reset_index()
            df_new.columns = ['Conc', 'geometry']
            df_new['centroid'] = df_new.apply(lambda x: x['geometry'].centroid, axis=1)
            df_new['label'] = df_new.apply(lambda x: transform_string(x['Conc']), axis=1)
            return df_new

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

        board_data = self.ui.board_matter_lst_combobox.currentText()
        adjacent_all = self.df_adjacent_plats[self.df_adjacent_plats['Board_Docket'] == board_data]
        df_plat_docket = self.df_plat[self.df_plat['Board_Docket'] == board_data]

        """Isolate out each adjacent list by adjacency order"""
        adjacent_main = adjacent_all[adjacent_all['Order'] == 0]
        adjacent_1 = adjacent_all[adjacent_all['Order'] == 1]
        adjacent_2 = adjacent_all[adjacent_all['Order'] == 2]

        """Get the plat data values for each adjacency list"""
        adjacent_main_plats = df_plat_docket[df_plat_docket['Conc'].isin(adjacent_main['src_FullCo'].unique())]
        adjacent_1_plats = df_plat_docket[df_plat_docket['Conc'].isin(adjacent_1['src_FullCo'].unique())]
        adjacent_2_plats = df_plat_docket[df_plat_docket['Conc'].isin(adjacent_2['src_FullCo'].unique())]

        plat_data_main = fieldsTester1(adjacent_main_plats)
        plat_data_adjacent_1 = fieldsTester1(adjacent_1_plats)
        plat_data_adjacent_2 = fieldsTester1(adjacent_2_plats)

        """Set labels"""
        paths_main = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red") for coord, text in zip(plat_data_main['centroid'], plat_data_main['label'])]
        paths_adjacent_1 = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red") for coord, text in zip(plat_data_adjacent_1['centroid'], plat_data_adjacent_1['label'])]
        paths_adjacent_2 = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red") for coord, text in zip(plat_data_adjacent_2['centroid'], plat_data_adjacent_2['label'])]
        self.labels_plats_2d_main.set_paths(paths_main)
        self.labels_plats_2d_1adjacent.set_paths(paths_adjacent_1)
        self.labels_plats_2d_2adjacent.set_paths(paths_adjacent_2)

        """Set Paths"""
        self.plats_2d_main.set_segments(plat_data_main['geometry'].apply(lambda x: x.exterior.coords))
        self.plats_2d_1adjacent.set_segments(plat_data_adjacent_1['geometry'].apply(lambda x: x.exterior.coords))
        self.plats_2d_2adjacent.set_segments(plat_data_adjacent_2['geometry'].apply(lambda x: x.exterior.coords))

        all_polygons = unary_union(plat_data_main['geometry'].tolist())
        overall_centroid = all_polygons.centroid
        centroid_x = overall_centroid.x
        centroid_y = overall_centroid.y

        #
        self.ax2d.set_xlim(centroid_x - 10000, centroid_x + 10000)
        self.ax2d.set_ylim(centroid_y - 10000, centroid_y + 10000)

        self.used_plat_codes = plat_data_main['Conc'].unique().tolist()
        self.plats_2d_main.set_visible(True)
        self.plats_2d_1adjacent.set_visible(True)
        self.plats_2d_2adjacent.set_visible(True)
        if self.ui.section_label_checkbox.isChecked():
            self.labels_plats_2d_main.set_visible(True)
            self.labels_plats_2d_1adjacent.set_visible(True)
            self.labels_plats_2d_2adjacent.set_visible(True)
        else:
            self.labels_plats_2d_main.set_visible(True)
            self.labels_plats_2d_1adjacent.set_visible(True)
            self.labels_plats_2d_2adjacent.set_visible(True)

        self.used_plat_codes_for_boards = plat_data_main['Conc'].unique().tolist() + plat_data_adjacent_1['Conc'].unique().tolist() + plat_data_adjacent_2['Conc'].unique().tolist()
        self.used_plat_codes_for_boards = list(set(self.used_plat_codes_for_boards))
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()

        try:
            self.manipulateTheDfDocketDataDependingOnCheckboxes()
        except AttributeError as e:
            pass
        pass

    """This is going to manipulate and organize the data into new dataframes based on when the wells were drilled. This is used when the radio buttons are changed """

    def setupDataForBoardDrillingInformation(self):
        def filterPlannedData(df1, df2):
            planned_year = df2[~df2['APINumber'].isin(df1['APINumber']) & (df2['CurrentWellStatus'] != 'Drilling')]
            return planned_year

        # Clear and prep the data
        self.df_docket_data = self.df_docket_data.drop_duplicates(keep='first').sort_values(by='APINumber').reset_index(drop=True)
        self.df_docket_data['WellAge'].fillna(0, inplace=True)
        self.planned_xy_2d, self.planned_xy_3d, self.drilled_xy_2d, self.drilled_xy_3d, self.currently_drilling_xy_2d, self.currently_drilling_xy_3d = [], [], [], [], [], []
        # self.used_plat_codes

        # generate masks that will be used for filtering the data (based on drilled, planned, drilling, etc. Honestly, vertical isn't necessary
        # out1 = self.df_docket_data[self.df_docket_data['CitingType'].isin(['asdrilled', 'vertical'])]['APINumber'].unique().tolist()
        # out2 = self.df_docket_data[self.df_docket_data['CitingType'].isin(['planned', 'vertical'])]['APINumber'].unique().tolist()
        # out3 = self.df_docket_data[self.df_docket_data['CitingType'].isin(['Drilling'])]['APINumber'].unique().tolist()
        # full = out1 + out2 + out3
        mask_drilled = (self.df_docket_data['CitingType'].isin(['asdrilled', 'vertical']))
        mask_planned = (self.df_docket_data['CitingType'].isin(['planned', 'vertical']))
        mask_drilling = (self.df_docket_data['CurrentWellStatus'].isin(['Drilling']))

        # Generate masks on df_docket_data (which is docket data but also has directional surveys) based on the age in months
        age_masks = [(self.df_docket_data['WellAge'] <= 12),
                     (self.df_docket_data['WellAge'] <= 60),
                     (self.df_docket_data['WellAge'] <= 120),
                     (self.df_docket_data['WellAge'] <= 9999)]

        # Remove any null data in targeted elevation
        self.df_docket_data = self.df_docket_data.dropna(subset=['Targeted Elevation'])

        # Using the two massks, generate 4x dataframes for each parameter that can then be referred back to.
        drilled_df_year = self.df_docket_data.loc[mask_drilled & age_masks[0]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        drilled_df_5years = self.df_docket_data.loc[mask_drilled & age_masks[1]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        drilled_df_10years = self.df_docket_data.loc[mask_drilled & age_masks[2]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        drilled_df_all = self.df_docket_data.loc[mask_drilled & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])

        planned_year = self.df_docket_data.loc[mask_planned & age_masks[0]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        planned_5years = self.df_docket_data.loc[mask_planned & age_masks[1]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        planned_10years = self.df_docket_data.loc[mask_planned & age_masks[2]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        # planned_all = self.df_docket_data[mask_planned & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        planned_all = self.df_docket_data.loc[mask_planned & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])

        # filter out data is currently being drilled.
        planned_year = filterPlannedData(drilled_df_year, planned_year)
        planned_5years = filterPlannedData(drilled_df_5years, planned_5years)
        planned_10years = filterPlannedData(drilled_df_10years, planned_10years)
        planned_all = filterPlannedData(drilled_df_all, planned_all)

        currently_drilling_year = self.df_docket_data.loc[mask_drilling & age_masks[0]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        currently_drilling_5years = self.df_docket_data.loc[mask_drilling & age_masks[1]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        currently_drilling_10years = self.df_docket_data.loc[mask_drilling & age_masks[2]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])
        currently_drilling_all = self.df_docket_data.loc[mask_drilling & age_masks[3]].reset_index(drop=True).sort_values(by=['APINumber', 'MeasuredDepth'])

        # turn into tuples
        self.drilled = (drilled_df_year, drilled_df_5years, drilled_df_10years, drilled_df_all)
        self.planned = (planned_year, planned_5years, planned_10years, planned_all)
        self.currently_drilling = (currently_drilling_year, currently_drilling_5years, currently_drilling_10years, currently_drilling_all)
        out1 = drilled_df_all['APINumber'].unique().tolist()
        out2 = planned_all['APINumber'].unique().tolist()
        out3 = currently_drilling_all['APINumber'].unique().tolist()
        full = out1 + out2 + out3
        used_data = list(set(full))

        # just get rid of those vertical things
        for i in range(4):
            self.drilled[i]['CitingType'] = 'asdrilled'
            self.planned[i]['CitingType'] = 'planned'

        # create dictionaries of the data for further manipulationg
        xy_points_dict_drilled = {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float), g['Targeted Elevation'].astype(float))] for k, g in drilled_df_all.groupby('APINumber')}
        xy_points_dict_planned = {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float), g['Targeted Elevation'].astype(float))] for k, g in planned_all.groupby('APINumber')}
        xy_points_dict_drilling = {k: [[x, y, spx, spy, z] for x, y, spx, spy, z in zip(g['X'].astype(float), g['Y'].astype(float), g['SPX'].astype(float), g['SPY'].astype(float), g['Targeted Elevation'].astype(float))] for k, g in currently_drilling_all.groupby('APINumber')}

        # Get the api numbers for each column
        drilled_apinums_year = set(self.drilled[0]['APINumber'])
        drilled_apinums_5years = set(self.drilled[1]['APINumber'])
        drilled_apinums_10years = set(self.drilled[2]['APINumber'])
        drilled_apinums_all = set(self.drilled[3]['APINumber'])

        planned_apinums_year = set(self.planned[0]['APINumber'])
        planned_apinums_5years = set(self.planned[1]['APINumber'])
        planned_apinums_10years = set(self.planned[2]['APINumber'])
        planned_apinums_all = set(self.planned[3]['APINumber'])

        drilling_apinums_year = set(self.currently_drilling[3]['APINumber'])
        drilling_apinums_5years = set(self.currently_drilling[3]['APINumber'])
        drilling_apinums_10years = set(self.currently_drilling[3]['APINumber'])
        drilling_apinums_all = set(self.currently_drilling[3]['APINumber'])

        # Assemble these into lists that are easier to call later (so when the radio button is clicked, it immediately knows what data to call)
        self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_year])
        self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_year])

        self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_5years])
        self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_5years])

        self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_10years])
        self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_10years])

        self.drilled_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_all])
        self.drilled_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilled.items() if k in drilled_apinums_all])

        self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_year])
        self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_year])

        self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_5years])
        self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_5years])

        self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_10years])
        self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_10years])

        self.planned_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_all])
        self.planned_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_planned.items() if k in planned_apinums_all])

        self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_year])
        self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_year])

        self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_5years])
        self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_5years])

        self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_10years])
        self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_10years])

        self.currently_drilling_xy_2d.append([[r[:2] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_all])
        self.currently_drilling_xy_3d.append([[r[2:] for r in v] for k, v in xy_points_dict_drilling.items() if k in drilling_apinums_all])

    """This will figure out what data is currently being stored due to the radio buttons that are looking at well drilling timeframes
     It just finds the radio button currently clicked and looks at the data that was assembled in df_adjacent_fields and puts in the corresponding data"""

    def returnWellDataDependingOnParametersTest(self):

        id_1 = self.ui.drilling_within_button_group.checkedId()
        self.drilled_df = self.drilled[id_1]
        self.planned_df = self.planned[id_1]
        self.currently_drilling_df = self.currently_drilling[id_1]
        self.drilled_segments = self.drilled_xy_2d[id_1]
        self.drilled_segments_3d = self.drilled_xy_3d[id_1]
        self.planned_segments = self.planned_xy_2d[id_1]
        self.planned_segments_3d = self.planned_xy_3d[id_1]
        self.currently_drilling_segments = self.currently_drilling_xy_2d[id_1]
        self.currently_drilling_segments_3d = self.currently_drilling_xy_3d[id_1]
        # self.manipulateTheDfDocketDataDependingOnCheckboxes()

    """This is the main function that serves the biggest purpose. It looks at what check boxes are currently activated and manipulates the data accordingly."""

    def manipulateTheDfDocketDataDependingOnCheckboxes(self):
        def platBounded(df, segments, segments_3d):

            df = df.sort_values(by=['APINumber', 'MeasuredDepth'])
            api = df[['APINumber']].drop_duplicates().reset_index(drop=True)
            api['index'] = api.index
            # df = df[df['ConcCode_y'].isin(self.used_plat_codes)]
            merged = pd.merge(api, df, left_on='APINumber', right_on='APINumber')
            segments = [segments[i] for i in range(len(segments)) if i in merged['index'].unique()]
            segments_3d = [segments_3d[i] for i in range(len(segments_3d)) if i in merged['index'].unique()]
            return df, segments, segments_3d

        # This function is run on each checkbox. Type refers to the type of well (oil, gas, etc) and column refers to the dataframe column where that well type will be referenced.
        def wellChecked(type, column):
            if column == 'CurrentWellType':
                colors_lst = 'WellTypeColor'
            else:
                colors_lst = 'WellStatusColor'
            # restrict the data to the first rows of each api number (since we only need one row to define the color)
            drilled_df_restricted = drilled_df.groupby('APINumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('APINumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('APINumber').first().reset_index()

            # Filter the data to only the specific type of well (oil, gas, etc)
            drilled_well_mask = drilled_df_restricted[column] == type
            planned_well_mask = planned_df_restricted[column] == type
            currently_drilling_well_mask = currently_drilling_df_restricted[column] == type

            # Here, we change the colors and size of the well. So that if we're looking at all oil wells, they'll be changed from the default black to the relevant color, and the size of the line is increased.
            df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[drilled_well_mask, colors_lst]
            df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5
            df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[planned_well_mask, colors_lst]
            df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5

            df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[currently_drilling_well_mask, colors_lst]
            df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5

        def wellCheckedMultiple(types, column):
            print('checked multiple')
            if column == 'CurrentWellType':
                colors_lst = 'WellTypeColor'
            else:
                colors_lst = 'WellStatusColor'
            # restrict the data to the first rows of each api number (since we only need one row to define the color)
            drilled_df_restricted = drilled_df.groupby('APINumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('APINumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('APINumber').first().reset_index()

            # Filter the data to only the specific type of well (oil, gas, etc)
            drilled_well_mask = drilled_df_restricted[column].isin(types)
            planned_well_mask = planned_df_restricted[column].isin(types)
            currently_drilling_well_mask = currently_drilling_df_restricted[column].isin(types)
            # Here, we change the colors and size of the well. So that if we're looking at all oil wells, they'll be changed from the default black to the relevant color, and the size of the line is increased.
            df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[drilled_well_mask, colors_lst]
            df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5

            df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[planned_well_mask, colors_lst]
            df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5

            df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[currently_drilling_well_mask, colors_lst]
            df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5
            # print(df_planned_parameters)

        self.currently_used_lines = None

        # store in the data locally.
        drilled_segments = self.drilled_segments
        planned_segments = self.planned_segments
        currently_drilling_segments = self.currently_drilling_segments
        drilled_segments_3d = self.drilled_segments_3d
        planned_segments_3d = self.planned_segments_3d
        currently_drilling_segments_3d = self.currently_drilling_segments_3d
        drilled_df = self.drilled_df
        planned_df = self.planned_df
        currently_drilling_df = self.currently_drilling_df

        drilled_df, drilled_segments, drilled_segments_3d = platBounded(drilled_df, drilled_segments, drilled_segments_3d)
        planned_df, planned_segments, planned_segments_3d = platBounded(planned_df, planned_segments, planned_segments_3d)
        currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d = platBounded(currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d)

        # This sets up the default coloration for the wells. These will be edited appropriately when different checkboxes are activated.
        data_drilled = {'color': ['black'] * len(drilled_segments), 'width': [0.5] * len(drilled_segments)}
        data_planned = {'color': ['black'] * len(planned_segments), 'width': [0.5] * len(planned_segments)}
        data_drilling = {'color': ['black'] * len(currently_drilling_segments), 'width': [0.5] * len(currently_drilling_segments)}

        # Generate some dataframes populated with that data.
        df_drilled_parameters = pd.DataFrame(data_drilled)
        df_planned_parameters = pd.DataFrame(data_planned)
        df_drilling_parameters = pd.DataFrame(data_drilling)

        active_button_id_type_status = self.ui.well_type_or_status_button_group.checkedId()
        # run through each checkbox, looking to see if it is checked, and coloring the wells accordingly.
        # type_checks = [self.ui.oil_well_check, self.ui.gas_well_check, self.ui.water_disposal_check, self.ui.dry_hole_check, self.ui.injection_check, self.ui.other_well_status_check]
        # status_checks = [self.ui.shut_in_check, self.ui.pa_check, self.ui.producing_check, self.ui.drilling_status_check, self.ui.producing_check]
        if active_button_id_type_status == -2:
            for q in self.status_checks:
                q.blockSignals(True)
                q.setChecked(False)
            if self.ui.oil_well_check.isChecked():
                wellChecked('Oil Well', 'CurrentWellType')
            if self.ui.gas_well_check.isChecked():
                wellChecked('Gas Well', 'CurrentWellType')
            if self.ui.water_disposal_check.isChecked():
                wellCheckedMultiple(['Water Disposal Well', 'Oil Well/Water Disposal Well'], 'CurrentWellType')
            if self.ui.dry_hole_check.isChecked():
                wellChecked('Dry Hole', 'CurrentWellType')
            if self.ui.injection_check.isChecked():
                wellCheckedMultiple(['Water Injection Well', 'Gas Injection Well'], 'CurrentWellType')
            if self.ui.other_well_status_check.isChecked():
                wellCheckedMultiple(['Unknown', 'Test Well', 'Water Source Well'], 'CurrentWellType')
            for q in self.status_checks:
                q.blockSignals(False)

        elif active_button_id_type_status == -3:
            for q in self.type_checks:
                q.blockSignals(True)
                q.setChecked(False)
            if self.ui.shut_in_check.isChecked():
                wellChecked('Shut-in', 'CurrentWellStatus')
            if self.ui.pa_check.isChecked():
                wellChecked('Plugged & Abandoned', 'CurrentWellStatus')
            if self.ui.producing_check.isChecked():
                wellChecked('Producing', 'CurrentWellStatus')
            if self.ui.drilling_status_check.isChecked():
                wellChecked('Drilling', 'CurrentWellStatus')
            if self.ui.misc_well_type_check.isChecked():
                wellCheckedMultiple(['Location Abandoned - APD rescinded',
                                     'Returned APD (Unapproved)', 'Approved Permit',
                                     'Active', 'Drilling Operations Suspended', 'New Permit', 'Inactive',
                                     'Temporarily-abandoned', 'Test Well or Monitor Well'], 'CurrentWellStatus')
            for q in self.type_checks:
                q.blockSignals(False)
        # This one is for the oil field labels.
        if self.ui.field_names_checkbox.isChecked():
            self.field_sections.set_visible(True)
            paths = [
                PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
                for coord, text in zip(self.field_centroids_lst, self.field_labels)]
            self.labels_field.set_paths(paths)
            self.labels_field.set_visible(True)
        else:
            self.field_sections.set_visible(False)
            self.labels_field.set_visible(False)

        # Extract the colors and line widths that have seen been filled in or altered.
        drilled_colors_init, drilled_line_width = df_drilled_parameters['color'].tolist(), df_drilled_parameters['width'].tolist()
        planned_colors_init, planned_line_width = df_planned_parameters['color'].tolist(), df_planned_parameters['width'].tolist()
        currently_drilling_colors_init, currently_drilling_width = df_drilling_parameters['color'].tolist(), df_drilling_parameters['width'].tolist()

        # Now the colors and lines have been set, we can just check to see if any of them actually get drawn. So here, we check to see if the main three category checkboxes are checked or not.
        # for each one, we'll add to the self.currently_used_lines dataframe that will record all wells that are currently to be drawn.
        # then we draw the model based on the parameters, and select the visibility of the wells.

        if self.ui.asdrilled_check.isChecked():
            self.currently_used_lines = concat([self.currently_used_lines, drilled_df]).drop_duplicates(keep='first').reset_index(drop=True)
            self.drawModelBasedOnParameters2d(self.all_wells_2d_asdrilled, drilled_segments, drilled_colors_init, drilled_line_width, self.ax2d, self.all_wells_2d_vertical_asdrilled)
            self.drawModelBasedOnParameters(self.all_wells_3d_asdrilled, drilled_segments_3d, drilled_colors_init, drilled_line_width, self.ax3d)
            self.all_wells_2d_asdrilled.set_visible(True)
            self.all_wells_3d_asdrilled.set_visible(True)
            self.all_wells_2d_vertical_asdrilled.set_visible(True)
        else:
            self.all_wells_2d_asdrilled.set_visible(False)
            self.all_wells_3d_asdrilled.set_visible(False)
            self.all_wells_2d_vertical_asdrilled.set_visible(False)

        if self.ui.planned_check.isChecked():
            planned_colors_init = ['black'] * len(planned_colors_init)
            self.currently_used_lines = concat([self.currently_used_lines, planned_df]).drop_duplicates(keep='first').reset_index(drop=True)
            self.drawModelBasedOnParameters2d(self.all_wells_2d_planned, planned_segments, planned_colors_init, planned_line_width, self.ax2d, self.all_wells_2d_vertical_planned)
            self.drawModelBasedOnParameters(self.all_wells_3d_planned, planned_segments_3d, planned_colors_init, planned_line_width, self.ax3d)
            self.all_wells_2d_planned.set_visible(True)
            self.all_wells_3d_planned.set_visible(True)
            self.all_wells_2d_vertical_planned.set_visible(True)
        else:
            self.all_wells_2d_planned.set_visible(False)
            self.all_wells_3d_planned.set_visible(False)
            self.all_wells_2d_vertical_planned.set_visible(False)

        if self.ui.currently_drilling_check.isChecked():
            self.currently_used_lines = concat([self.currently_used_lines, currently_drilling_df]).drop_duplicates(keep='first').reset_index(drop=True)
            self.drawModelBasedOnParameters2d(self.all_wells_2d_current, currently_drilling_segments, currently_drilling_colors_init, currently_drilling_width, self.ax2d, self.all_wells_2d_vertical_current)
            self.drawModelBasedOnParameters(self.all_wells_3d_current, currently_drilling_segments_3d, currently_drilling_colors_init, currently_drilling_width, self.ax3d)
            self.all_wells_2d_current.set_visible(True)
            self.all_wells_3d_current.set_visible(True)
            self.all_wells_2d_vertical_current.set_visible(True)
        else:
            self.all_wells_2d_current.set_visible(False)
            self.all_wells_3d_current.set_visible(False)
            self.all_wells_2d_vertical_current.set_visible(False)

        # If there are drilled segments 3d performed, then adjust the axes as follows
        if drilled_segments_3d:
            self.centroid, std_vals = self.calculate_centroid_np(drilled_segments_3d)
            new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
            new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
            new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]

            self.ax3d.set_xlim3d(new_xlim)
            self.ax3d.set_ylim3d(new_ylim)
            self.ax3d.set_zlim3d(new_zlim)

        # Update, and draw, etc.
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()
        self.canvas3d.blit(self.ax3d.bbox)
        self.canvas3d.draw()

    """Generate a group of data based on the grouped xy data into line segments"""

    def returnSegmentsFromDF(self, df):
        return [[[float(x), float(y)] for x, y in zip(group['X'], group['Y'])]  # Convert each x, y to float and store as list
                for _, group in df.groupby('APINumber')]

    """Draw model based on these parameters
    lst = LineCollection previously defined in init
    segments = segments as defined by the data that is filtered by well age in returnWellDataDependingOnParametersTest 
    colors = colors defined previously
    line_width = line_width defined previously
    ax = ax2d, previously defined
    scat_line = the scatter plots for vertical wells defined in init"""

    def drawModelBasedOnParameters2d(self, lst, segments, colors, line_width, ax, scat_line):
        colors_scatter = []
        collapsed_points = []
        try:
            # get the index and the data
            lst_vertical_indexes, lst_vertical_data = zip(*[(i, val) for i, val in enumerate(segments) if len(val) == 2])
            # transform to a list of tuples
            lst_vertical_data = [tuple(i[0]) for i in lst_vertical_data]

            # get colors
            data_color = [colors[i] for i in lst_vertical_indexes]
            # set offsets and face colors
            scat_line.set_offsets(lst_vertical_data)
            scat_line.set_facecolor(data_color)
        except ValueError:
            scat_line.set_offsets([None, None])
        # write it all to the graphic
        if len(segments) == 0:
            scat_line.set_offsets([None, None])
        else:
            for i in range(len(segments)):
                if len(segments[i]) <= 2:
                    used_colors = [colors[i]] * len(segments[i])
                    colors_scatter.extend(used_colors)
                    collapsed_points.extend(segments[i])
            # collapsed_points = list(chain.from_iterable(segments))
            if len(collapsed_points) > 0:
                scat_line.set_offsets(collapsed_points)

        scat_line.set_facecolor(colors_scatter)
        lst.set_segments(segments)
        lst.set_colors(colors)
        lst.set_linewidth(line_width)
        ax.draw_artist(lst)

    """Draws the model based on the parameters. This is the same as drawModelBasedOnParameters2d, but in 3d."""

    def drawModelBasedOnParameters(self, lst, segments, colors, line_width, ax):

        """Set the segments, the colors, the line width and then draw the artist."""
        lst.set_segments(segments)
        lst.set_colors(colors)
        lst.set_linewidth(line_width)
        ax.draw_artist(lst)

    """When called, this will go into the self.df_docket dataframe, and add in well colors. This potentially could be done in Load_data2"""

    def generate_color_palette(self):
        # Color-blind friendly palette
        colors = [
            "#0072B2",  # Blue
            "#E69F00",  # Orange
            "#009E73",  # Green
            "#CC79A7",  # Pink
            "#56B4E9",  # Sky Blue
            "#D55E00",  # Vermillion
            "#660099",  # Purple
            "#994F00",  # Brown
            "#334B5C",  # Dark Slate
            "#0000FF",  # Pure Blue
            "#FF0000",  # Red
            "#006600",  # Dark Green
            "#FF00FF",  # Magenta
            "#8B4513",  # Saddle Brown
            "#800000",  # Maroon
            "#808000",  # Olive
            "#FF1493",  # Deep Pink
            "#00CED1",  # Dark Turquoise
            "#8B008B",  # Dark Magenta
            "#556B2F",  # Dark Olive Green
            "#FF8C00",  # Dark Orange
            "#9932CC",  # Dark Orchid
            "#8B0000",  # Dark Red
            "#008080",  # Teal
            "#4B0082",  # Indigo
            "#B8860B",  # Dark Goldenrod
            "#32CD32",  # Lime Green
            "#800080",  # Purple
            "#A0522D",  # Sienna
            "#FF4500",  # Orange Red
            "#00FF00",  # Lime
            "#4682B4",  # Steel Blue
            "#FFA500",  # Orange
            "#DEB887",  # Burlywood
            "#5F9EA0",  # Cadet Blue
            "#D2691E",  # Chocolate
            "#CD5C5C",  # Indian Red
            "#708090",  # Slate Gray
            "#000000"]  # Black
        return [PyQt5.QtGui.QColor(color) for color in colors]

    def get_color_for_index(self, index):
        return self.color_palette[index % len(self.color_palette)]

    def createOwnershipLabels(self):
        def wipeModel(lst):
            for label in lst:
                label.setParent(None)
            lst.clear()

        def processOwnershipData(model, variable, variable_color, lst, layout):
            for row in range(model.rowCount()):
                item = model.item(row, 0)  # Get item from the first column
                if item:
                    label_text = item.text()
                    label = QLabel(label_text)
                    lst.append(label)
                    layout.addWidget(label)
                    color_used = self.docket_ownership_data[self.docket_ownership_data[variable] == label_text][variable_color].iloc[0]
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

            result = df_filtered.groupby('APINumber', group_keys=False).apply(select_drilled_or_planned)

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
                checkbox.setStyleSheet(f"""
                    QCheckBox {{color: {color_used.name()};text-shadow: 0 0 20px #fff;}}""")

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
        # print(f"Checkbox {index} ('{checkbox_text}') {'checked' if state == Qt.Checked else 'unchecked'} with color {color.name()}")
        self.update_plot()

    def get_checkbox_state(self, index):
        if 0 <= index < len(self.operator_checkbox_list):
            return self.operator_checkbox_list[index].isChecked()
        return None

    def set_checkbox_state(self, index, state):
        if 0 <= index < len(self.operator_checkbox_list):
            self.operator_checkbox_list[index].setChecked(state)

    def get_checkbox_count(self):
        return len(self.operator_checkbox_list)

    def get_checkbox_text(self, index):
        if 0 <= index < len(self.operator_checkbox_list):
            return self.operator_checkbox_list[index].text()
        return None

    def get_checkbox_color(self, index):
        if 0 <= index < len(self.operator_checkbox_list):
            return self.get_color_for_index(index)
        return None

    def update_plot(self):
        # self.ax2d.clear()
        x_data, y_data = [], []
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

        # colors_status = {'Oil Well': '#FF0000',  #Red
        #                  'Gas Well': '#FFA500',  #Orange
        #                  'Water Disposal Well': '#0000FF',  #Blue
        #                  'Oil Well/Water Disposal Well': '#0000FF',  #Blue
        #                  'Water Injection Well': '#00FFFF',  #Cyan
        #                  'Gas Injection Well': '#00FFFF',  #Cyan
        #                  'Dry Hole': '#4A4A4A',  #Dark Gray
        #                  'Unknown': '#FF00FF',  #Magenta
        #                  'Test Well': '#FF00FF',  #Magenta
        #                  'Water Source Well': '#FF00FF'}  #Magenta
        #
        # colors_type = {
        #     'Producing': '#00FF00',  #Green
        #     'Plugged & Abandoned': '#800080',  #Purple
        #     'Shut In': '#8B4513',  #Brown
        #     'Drilling': '#000080',  #Navy
        #     'Other': '#008080'  #Teal
        # }

        necessary_columns = ['APINumber', 'X', 'Y', 'Targeted Elevation', 'CitingType', 'SPX', 'SPY',
                             'CurrentWellType', 'CurrentWellStatus', 'WellAge', 'MeasuredDepth', 'ConcCode_y']
        # Extract unique API numbers from docket DataFrame
        apis = self.df_docket['WellID'].unique()
        operators = self.df_docket['Operator'].unique()
        operators = sorted(operators)

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
        # final_df['WellStatusColor'] = final_df['CurrentWellStatus'].map(colors_status)

        # final_df['WellColor'] = final_df['CurrentWellType'].map(colors)
        # final_df['WellColor'] = final_df['CurrentWellType'].apply(lambda x: colors.get(x, 'black'))
        # final_df['WellColor'] = final_df['CurrentWellType'].apply(lambda x: colors.get(x, 'black'))

        # final_df['WellTypeColor'] = final_df['CurrentWellType'].apply(lambda x: colors_type.get(x, 'purple'))
        final_df['WellStatusColor'] = final_df['CurrentWellStatus'].apply(lambda x: colors_status.get(x, '#4a7583'))
        # print(final_df)
        # print('type', final_df['CurrentWellType'].unique())
        # print('colors', colors_type)
        # Sort it again
        final_df = final_df.sort_values(by=['APINumber', 'MeasuredDepth'])
        # print(final_df[final_df['WellTypeColor']=='#985bee'])
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

        # Depending on if it's oil or gas, plot these dataframes and titles and stuff to match accordingly.
        if self.current_prod == 'oil':
            self.ax_prod_1.set_title('Potential Profit')
            self.ax_prod_2.set_title('Produced Oil  (bbl)')
            self.profit_line.set_data(current_data_row['Date'], current_data_row['Potential Oil Profit'])
            self.profit_line_cum.set_data(current_data_row['Date'], current_data_row['Potential Cumulative Oil Profit'])
            self.prod_line.set_data(current_data_row['Date'], current_data_row['Oil Volume (bbl)'])
            self.prod_line_cum.set_data(current_data_row['Date'], current_data_row['Cumulative Potential Oil Production (bbl)'])

        elif self.current_prod == 'gas':
            self.ax_prod_1.set_title('Potential Profit')
            self.ax_prod_2.set_title('Produced Gas Volume (mcf)')
            self.profit_line.set_data(current_data_row['Date'], current_data_row['Potential Gas Profit'])
            self.profit_line_cum.set_data(current_data_row['Date'], current_data_row['Potential Cumulative Gas Profit'])
            self.prod_line.set_data(current_data_row['Date'], current_data_row['Gas Volume (mcf)'])
            self.prod_line_cum.set_data(current_data_row['Date'], current_data_row['Cumulative Potential Gas Production (mcf)'])

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
        self.ax_prod_1.legend(handles=handles1, labels=labels1, loc='upper left', bbox_to_anchor=(-0.15, -0.25))
        self.ax_prod_2.legend(handles=handles2, labels=labels2, loc='upper left', bbox_to_anchor=(-0.15, -0.25))

        # Blit, draw, etc
        self.canvas_prod_1.blit(self.ax_prod_1.bbox)
        self.canvas_prod_2.blit(self.ax_prod_2.bbox)
        self.canvas_prod_1.draw()
        self.canvas_prod_2.draw()

    """This function is used to open the .db file and then process the found data accordingly, depending on which tables and datasets are used."""

    def load_data2(self):

        # string_sql_owner = 'select * from Ownership'
        # self.df_owner = read_sql(string_sql_owner, self.conn_db)

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
        self.testProcess()
    def testProcess(self):
        apis = [4301931230,
                4301930571,
                4301930451,
                4301930500,
                4301931224,
                4304731674,
                4301931237,
                4301931266,
                4301931368,
                4301930433,
                4301931243,
                4301930670,
                4301916213,
                4301920006,
                4301930310,
                4301931472,
                4301930634,
                4301930670,
                4301930648,
                4301930758,
                4301930759,
                4301931360,
                4301931075,
                4304731307,
                4301911310,
                4301915022,
                4301915024,
                4301915025,
                4301915027,
                4301915048,
                4301915482,
                4301915697,
                4301915699,
                4301915700,
                4301916203,
                4301916209,
                4301916210,
                4301916212,
                4301916214,
                4301930218,
                4301930224,
                4301930412,
                4301930416,
                4301930462,
                4301930468,
                4301930472,
                4301930494,
                4301930507,
                4301930516,
                4301930517,
                4301930541,
                4301930552,
                4301930572,
                4301930574,
                4301930578,
                4301930598,
                4301930617,
                4301930639,
                4301930640,
                4301930657,
                4301930686,
                4301930698,
                4301930702,
                4301930748,
                4301930773,
                4301930779,
                4301930780,
                4301930792,
                4301930797,
                4301930798,
                4301930799,
                4301930833,
                4301930857,
                4301930893,
                4301930960,
                4301930990,
                4301931002,
                4301931009,
                4301931013,
                4301931020,
                4301931027,
                4301931031,
                4301931066,
                4301931092,
                4301931093,
                4301931108,
                4301931109,
                4301931114,
                4301931130,
                4301931131,
                4301931169,
                4301931183,
                4301931195,
                4301931196,
                4301931225,
                4301931226,
                4301931231,
                4301931235,
                4301931240,
                4301931241,
                4301931246,
                4301931263,
                4301931267,
                4301931304,
                4301931306,
                4301931320,
                4301931337,
                4301931347,
                4301931351,
                4301931352,
                4301931359,
                4301931382,
                4301931383,
                4301931384,
                4301931385,
                4301931391,
                4301931393,
                4301931282,
                4301931289,
                4301931290,
                4301931291,
                4301931299,
                4301931301,
                4301931316,
                4301931318]
        test_all1 = self.dx_data[self.dx_data['WellID'].isin(apis)]

        apis = [str(i) for i in apis]
        test_all2 = self.dx_data[self.dx_data['WellID'].isin(apis)]
        # print(self.dx_data[self.dx_data['WellID'] == '43019030639'])
        ids_lst = self.dx_data['WellID'].unique().tolist()

        print(test_all2)
        print(len(apis))
    """This function is used for specifically processing the data for fields"""

    # def loadPlatData(self):
    #     self.df_plat = read_sql('select * from PlatData', self.conn_db)
    #     self.df_plat['Easting'], self.df_plat['Northing'] = zip(*self.df_plat.apply(lambda row: utm.from_latlon(row['Lat'], row['Lon'])[:2], axis=1))
    #     self.df_plat['geometry'] = self.df_plat.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)

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
        polygons = used_fields.groupby('Field_Name').apply(lambda x: Polygon(zip(x['Easting'], x['Northing']))).reset_index()
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
