import tempfile

from PyQt5.QtGui import QGuiApplication
from shapely.geometry import Point, LineString
from matplotlib.collections import PatchCollection

from PyQt5.QtCore import Qt
from matplotlib.textpath import TextPath
from matplotlib.patches import PathPatch
import utm
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pandas as pd
from PyQt5.QtCore import QUrl
import plotly.graph_objects as go
import numpy as np
from PyQt5.QtWidgets import QAbstractItemView, QSizePolicy
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
from typing import *
class Drawer:
    def __init__(self, ui, used_df_dx, well_info_df):
        self.ui = ui
        self.df_docket_data = well_info_df
        self.dx_df = used_df_dx
        print(well_info_df.columns)
        print(used_df_dx.columns)

        # self.df_docket_data = self.df_tsr.merge(
        #     self.df_BoardData,
        #     left_on=['Section', 'Township', 'Township Direction',
        #              'Range', 'Range Direction', 'Baseline'],
        #     right_on=['Sec', 'Township', 'TownshipDir',
        #               'Range', 'RangeDir', 'PM']
        # )
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

        self.setupDataForBoardDrillingInformation()

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
                - apinumber: Well identification number
                - well_age: Age of the well (can contain NaN values)

        Returns:
            pd.DataFrame: Processed DataFrame with:
                - No duplicates
                - Sorted by apinumber
                - Reset index
                - well_age filled with 0 for missing values

        Notes:
            - Preserves all original columns except duplicates
            - Assumes apinumber is a valid sorting key
            - Treatment of NaN well ages as 0 typically indicates planned/permitted wells
            - Original index is dropped during reset

        Example:
            >>> df = pd.DataFrame({
            ...     'well_id': [2, 1, 2, 3],
            ...     'well_age': [5.0, None, 5.0, 3.0]
            ... })
            >>> processed_df = preprocessData(self, df)
            >>> processed_df['well_id'].tolist()
            [1, 2, 3]
        """
        # Remove duplicates and sort
        print(df)
        df = df.drop_duplicates(keep='first')
        df = df.sort_values(by='well_id')

        # Reset index and handle missing ages
        df = df.reset_index(drop=True)
        df['well_age'] = df['well_age'].fillna(0)

        return df
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
                    - citing_type: Type of well citation
                    - current_well_status: Current status of the well

        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: Three boolean masks:
                - mask_drilled: True for already drilled/completed wells
                - mask_planned: True for planned/permitted wells
                - mask_drilling: True for currently drilling wells

        Notes:
            - citing_type values considered as drilled: ['asdrilled', 'vertical']
            - citing_type values considered as planned: ['planned', 'vertical']
            - current_well_status value for drilling: ['Drilling']
            - Masks can be used directly for DataFrame filtering

        Example:
            >>> drilled, planned, drilling = self.generateMasks()
            >>> drilled_wells = self.df_docket_data[drilled]
            >>> planned_wells = self.df_docket_data[planned]
            >>> drilling_wells = self.df_docket_data[drilling]
        """
        # Generate mask for drilled/completed wells
        mask_drilled = self.dx_df['citing_type'].isin(['asdrilled', 'vertical'])

        # Generate mask for planned/permitted wells
        mask_planned = self.dx_df['citing_type'].isin(['planned', 'vertical'])

        # Generate mask for currently drilling wells
        mask_drilling = self.dx_df['current_well_status'].isin(['Drilling'])

        return mask_drilled, mask_planned, mask_drilling

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
                    - well_age: Age of wells in months

        Returns:
            List[pd.Series]: List of four boolean masks where True indicates
            wells within the respective age thresholds:
            - mask[0]: Age ≤ 12 months
            - mask[1]: Age ≤ 60 months
            - mask[2]: Age ≤ 120 months
            - mask[3]: Age ≤ 9999 months (effectively all wells)

        Notes:
            - well_age is expected to be in months
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
            (self.df_docket_data['well_age'] <= 12),  # 1 year threshold
            (self.df_docket_data['well_age'] <= 60),  # 5 year threshold
            (self.df_docket_data['well_age'] <= 120),  # 10 year threshold
            (self.df_docket_data['well_age'] <= 9999)  # All wells threshold
        ]

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

    def generateDataframes(
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
                    - apinumber: Well identification number
                    - measured_depth: Well depth measurement
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
            - All DataFrames are sorted by apinumber and measured_depth
            - Indexes are reset for all DataFrames
            - Empty DataFrames may be returned if no wells match criteria
            - Original data is not modified

        Example:
            >>> drilled_dfs = generateDataframes(self, 'drilled', mask_drilled, age_masks)
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
                by=['apinumber', 'measured_depth']
            )

        return dataframes
    def returnWellsWithParameters(self, info_df, dx_df) -> DataFrame:
        """
        Processes and returns well data with color-coded parameters for visualization.

        Creates a filtered and enriched DataFrame containing well information with
        standardized color mappings for well types and operational status. Merges
        directional survey data with docket information for comprehensive visualization.

        Color Schemes:
            Well Types:
                - Oil Wells: Red (#c34c00)
                - Gas Wells: Orange (#f1aa00)
                - Water Disposal Wells: Blue (#0032b0)
                - Injection Wells: Cyan (#93ebff)
                - Dry Holes: Dark Gray (#4f494b)
                - Unknown/Test Wells: Magenta (#985bee)

            Well Status:
                - Producing: Green (#a2e361)
                - Plugged & Abandoned: Purple (#4c2d77)
                - Shut In: Tan (#D2B48C)
                - Drilling: Navy (#001958)
                - Other: Teal (#4a7583)

        Returns:
            DataFrame with columns:
                - APINumber: Well identifier
                - X, Y: Well coordinates
                - Targeted Elevation
                - CitingType
                - SPX, SPY: Surface point coordinates
                - CurrentWellType
                - CurrentWellStatus
                - WellAge
                - MeasuredDepth
                - ConcCode_y
                - WellTypeColor: Hex color based on well type
                - WellStatusColor: Hex color based on well status

        Side Effects:
            None - Pure data processing function

        Notes:
            - Merges directional survey data with docket information
            - Removes duplicate entries
            - Sorts by APINumber and MeasuredDepth
            - Maps colors based on standardized industry visualization schemes
            - Handles unknown status values with default teal color
        """
        # Define color mappings for well types
        colors_type = {
            'Oil Well': '#c34c00',  # Red
            'Gas Well': '#f1aa00',  # Orange
            'Water Disposal Well': '#0032b0',  # Blue
            'Oil Well/Water Disposal Well': '#0032b0',  # Blue
            'Water Injection Well': '#93ebff',  # Cyan
            'Gas Injection Well': '#93ebff',  # Cyan
            'Dry Hole': '#4f494b',  # Dark Gray
            'Unknown': '#985bee',  # Magenta
            'Test Well': '#985bee',  # Magenta
            'Water Source Well': '#985bee'  # Magenta
        }

        # Define color mappings for well status
        colors_status = {
            'Producing': '#a2e361',  # Green
            'Plugged & Abandoned': '#4c2d77',  # Purple
            'Shut In': '#D2B48C',  # tan
            'Drilling': '#001958',  # Navy
            'Other': '#4a7583'  # Teal
        }

        # Define required columns for final dataset
        necessary_columns = [
            'apinumber', 'x', 'y', 'targeted_elevation', 'citing_type',
            'spx', 'spy', 'current_well_type', 'current_well_status',
            'well_age', 'measured_depth', 'conc_code_y'
        ]

        # Process and filter data
        apis = info_df['well_id'].unique()
        # operators = self.df_docket['Operator'].unique()
        dx_filtered = dx_df[dx_df['apinumber'].isin(apis)]
        docket_filtered = info_df[info_df['well_id'].isin(apis)]

        # Merge and clean data
        merged_df = pd.merge(dx_filtered, docket_filtered,
                             left_on='apinumber', right_on='well_id')
        merged_df = merged_df.drop_duplicates(keep='first')
        merged_df = merged_df.sort_values(by=['apinumber', 'measured_depth'])

        # Create final dataset with necessary columns
        print(merged_df)
        final_df = merged_df[necessary_columns]
        final_df.reset_index(drop=True, inplace=True)

        # Add color coding
        final_df['well_type_color'] = final_df['current_well_type'].map(colors_type)
        final_df['well_status_color'] = final_df['current_well_status'].apply(
            lambda x: colors_status.get(x, '#4a7583')
        )

        return final_df.sort_values(by=['apinumber', 'measured_depth'])


    def setupDataForBoardDrillingInformation(self):
        self.df_docket_data = self.returnWellsWithParameters(self.df_docket_data, self.dx_df)
        print(self.df_docket_data)
        # Clear and prep the data
        self.df_docket_data = self.preprocessData(self.df_docket_data)
        print(self.df_docket_data)
        print(foo)
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
        drilled_dfs = self.generateDataframes('drilled', mask_drilled, age_masks)
        # For planned
        planned_dfs = self.generateDataframes('planned', mask_planned, age_masks)
        # For currently drilling
        currently_drilling_dfs = self.generateDataframes('currently_drilling', mask_drilling, age_masks)


        drilled_dataframes = [drilled_dfs['drilled_year'], drilled_dfs['drilled_5years'], drilled_dfs['drilled_10years'], drilled_dfs['drilled_all']]
        planned_dataframes = [planned_dfs['planned_year'], planned_dfs['planned_5years'], planned_dfs['planned_10years'], planned_dfs['planned_all']]
        currently_drilling_dataframes = [currently_drilling_dfs['currently_drilling_year'], currently_drilling_dfs['currently_drilling_5years'], currently_drilling_dfs['currently_drilling_10years'], currently_drilling_dfs['currently_drilling_all']]

        # Filter out planned data based on drilled data
        planned_dataframes = self.filterPlannedData(drilled_dataframes, planned_dataframes)

        # Prepare final data structures
        self.prepareFinalData(drilled_dataframes, planned_dataframes, currently_drilling_dataframes)

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
    def filterPlannedDataForYear(
            self,
            drilled_df: pd.DataFrame,
            planned_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filters planned wells by removing those that have been drilled or are currently drilling.

        Takes a DataFrame of planned wells and removes any wells that:
        1. Already exist in the drilled wells dataset (based on apinumber)
        2. Have a current status of "Drilling"

        Args:
            self: Parent class instance
            drilled_df (pd.DataFrame): DataFrame containing drilled well data
                Required columns:
                - apinumber: Unique well identifier
            planned_df (pd.DataFrame): DataFrame containing planned well data
                Required columns:
                - apinumber: Unique well identifier
                - current_well_status: Current status of the well

        Returns:
            pd.DataFrame: Filtered planned wells DataFrame with:
                - Wells that exist in drilled_df removed
                - Wells with 'Drilling' status removed
                - All other columns and data preserved
                - Original index structure maintained

        Notes:
            - Uses apinumber for well identification and matching
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
            ~planned_df['apinumber'].isin(drilled_df['apinumber']) &
            (planned_df['current_well_status'] != 'Drilling')
            ]

        return planned_year

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

    def processXYData(self, dataframes: Dict[str, pd.DataFrame], data_type: Literal['drilled', 'planned', 'currently_drilling']) -> None:
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
                - apinumber: Unique well identifier
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
        apinums: Set[str] = set(df['apinumber'])

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
                - apinumber: Unique well identifier
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
            - Groups data by apinumber to maintain well identity
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
            for k, g in df.groupby('apinumber')}



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
               - toggleWellDisplay(): Controls well visibility
               - calculateCentroidNP(): Computes 3D view center
           """

        def platBounded(
                df: pd.DataFrame,
                segments: List[List[List[float]]],
                segments_3d: List[List[List[float]]]
        ) -> Tuple[pd.DataFrame, List[List[List[float]]], List[List[List[float]]]]:

            # Sort DataFrame by API number and measured depth
            df = df.sort_values(by=['apinumber', 'measured_depth'])

            # Create index mapping for API numbers
            api = df[['apinumber']].drop_duplicates().reset_index(drop=True)
            api['index'] = api.index

            # Merge to maintain relationships
            merged = pd.merge(api, df, left_on='apinumber', right_on='apinumber')

            # Filter segments to match DataFrame wells
            segments = [segments[i] for i in range(len(segments)) if i in merged['index'].unique()]
            segments_3d = [segments_3d[i] for i in range(len(segments_3d)) if i in merged['index'].unique()]

            return df, segments, segments_3d

        def setupData(
                df: pd.DataFrame,
                segments: List[List[List[float]]],
                segments_3d: List[List[List[float]]]
        ) -> Tuple[pd.DataFrame, List[List[List[float]]], List[List[List[float]]], Dict, pd.DataFrame]:

            # Filter and align data using platBounded
            df, segments, segments_3d = platBounded(df, segments, segments_3d)

            # Create default styling parameters
            data = {'color': ['black'] * len(segments), 'width': [0.5] * len(segments)}

            # Convert styling parameters to DataFrame
            df_parameters = pd.DataFrame(data)

            return df, segments, segments_3d, data, df_parameters

        def wellChecked(
                type: str,
                column: Literal['CurrentWellType', 'current_well_status']
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
                    For current_well_status:
                        - Status values from well database
                column (Literal['CurrentWellType', 'current_well_status']):
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
            drilled_df_restricted = drilled_df.groupby('apinumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('apinumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('apinumber').first().reset_index()

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

        def wellCheckedMultiple(
                types: List[str],
                column: Literal['CurrentWellType', 'current_well_status']
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
                    For current_well_status:
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
                column (Literal['CurrentWellType', 'current_well_status']):
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
            drilled_df_restricted = drilled_df.groupby('apinumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('apinumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('apinumber').first().reset_index()

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

        def toggleWellDisplay(
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
                >>> toggleWellDisplay(True, new_wells_df, segs_2d, 'blue', 1.0,
                                      well2d, well3d, vert_well, segs_3d)
                # Shows wells and updates with new data
                >>> toggleWellDisplay(False, new_wells_df, segs_2d, 'blue', 1.0,
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
                wellChecked('Shut-in', 'current_well_status')

            # Handle Plugged & Abandoned wells
            if self.ui.pa_check.isChecked():
                wellChecked('Plugged & Abandoned', 'current_well_status')

            # Handle Producing wells
            if self.ui.producing_check.isChecked():
                wellChecked('Producing', 'current_well_status')

            # Handle Currently Drilling wells
            if self.ui.drilling_status_check.isChecked():
                wellChecked('Drilling', 'current_well_status')

            # Handle Miscellaneous well statuses
            if self.ui.misc_well_type_check.isChecked():
                wellCheckedMultiple(['Location Abandoned - APD rescinded',
                                     'Returned APD (Unapproved)', 'Approved Permit',
                                     'Active', 'Drilling Operations Suspended', 'New Permit', 'Inactive',
                                     'Temporarily-abandoned', 'Test Well or Monitor Well'], 'current_well_status')

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
        toggleWellDisplay(
            self.ui.asdrilled_check.isChecked(), drilled_df,
            drilled_segments, drilled_colors_init, drilled_line_width,
            self.all_wells_2d_asdrilled, self.all_wells_3d_asdrilled,
            self.all_wells_2d_vertical_asdrilled, drilled_segments_3d)

        toggleWellDisplay(
            self.ui.planned_check.isChecked(), planned_df,
            planned_segments, planned_colors_init, planned_line_width,
            self.all_wells_2d_planned, self.all_wells_3d_planned,
            self.all_wells_2d_vertical_planned, planned_segments_3d)

        toggleWellDisplay(
            self.ui.currently_drilling_check.isChecked(), currently_drilling_df,
            currently_drilling_segments, currently_drilling_colors_init, currently_drilling_width,
            self.all_wells_2d_current, self.all_wells_3d_current,
            self.all_wells_2d_vertical_current, currently_drilling_segments_3d)

        # Update 3D plot boundaries if drilled segments exist
        if drilled_segments_3d:
            self.centroid, std_vals = self.calculateCentroidNP(drilled_segments_3d)
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


class Drawer2:
    def __init__(self, ui, used_df_dx, well_info_df):
        self.segment_properties = None
        self.df_wells = None
        self.segments_per_drilling_status = None
        self.field_sections = None

        def clear_widget(widget):
            for i in reversed(range(widget.layout().count())):
                widget.layout().itemAt(i).widget().setParent(None)

        def clear_layout(layout):
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        self.ui = ui
        self.well_info_df = well_info_df
        self.surveys = used_df_dx
        self.type_color_map = {
            'Oil Well': '#c34c00',  # Red
            'Gas Well': '#f1aa00',  # Orange
            'Water Disposal Well': '#0032b0',  # Blue
            'Oil Well/Water Disposal Well': '#0032b0',  # Blue
            'Water Injection Well': '#93ebff',  # Cyan
            'Gas Injection Well': '#93ebff',  # Cyan
            'Dry Hole': '#4f494b',  # Dark Gray
            'Unknown': '#985bee',  # Magenta
            'Test Well': '#985bee',  # Magenta
            'Water Source Well': '#985bee'  # Magenta
        }

        # Define color mappings for well status
        self.status_color_map = {
            'Producing': '#a2e361',  # Green
            'Plugged & Abandoned': '#4c2d77',  # Purple
            'Shut In': '#D2B48C',  # tan
            'Drilling': '#001958',  # Navy
            'Other': '#4a7583'  # Teal
        }
        self.drilling_styles = {
            'drilled': {'linestyle': '-'},
            'planned': {'linestyle': '--'},
            'currently_drilling': {'linestyle': ':'}
        }

        self.figure2d = plt.figure()
        self.canvas2d = FigureCanvas(self.figure2d)
        self.ax2d = self.figure2d.subplots()
        self.ui.well_graphic_mp_2d_model.addWidget(self.canvas2d)
        self.all_wells_2d_planned = LineCollection([], colors='black', linewidths=0.5, linestyles='--', zorder=1)
        self.ax2d.add_collection(self.all_wells_2d_planned)

        self.draw_2d_data_all(well_info_df, used_df_dx)

    # def manipulateTheDfDocketDataDependingOnCheckboxes(self):
    #     """
    #        Main function for managing well visualization based on UI checkbox states.
    #
    #        Controls the display of different well types (drilled, planned, currently drilling)
    #        and their properties in both 2D and 3D views. Handles well filtering, visibility,
    #        styling, and related UI elements like field names.
    #
    #        Attributes Modified:
    #            currently_used_lines (DataFrame): Tracks which well lines are currently displayed
    #            field_sections (Artist): Visual elements for field sections
    #            labels_field (Artist): Text labels for fields
    #            Various matplotlib artists for well visualization
    #
    #        Side Effects:
    #            - Updates 2D and 3D matplotlib canvases
    #            - Modifies well line visibility and styling
    #            - Updates field name labels
    #            - Adjusts 3D view limits based on well positions
    #            - Triggers well type/status filtering
    #
    #        Processing Steps:
    #            1. Initializes local data references
    #            2. Sets up data parameters for each well category
    #            3. Applies type/status filtering
    #            4. Handles field name visibility
    #            5. Processes well display parameters
    #            6. Toggles visibility for different well categories
    #            7. Adjusts 3D view boundaries
    #            8. Updates visualization canvases
    #
    #        Notes:
    #            - Central function for well visualization control
    #            - Connected to multiple UI checkbox events
    #            - Manages both 2D and 3D visualizations
    #            - Handles three main well categories:
    #                * As-drilled wells
    #                * Planned wells
    #                * Currently drilling wells
    #            - Maintains visualization consistency across views
    #            - Uses helper functions for data setup and display
    #
    #        Dependencies:
    #            - setupData(): Prepares well data parameters
    #            - statusAndTypesEnabler(): Manages well filtering
    #            - toggleWellDisplay(): Controls well visibility
    #            - calculateCentroidNP(): Computes 3D view center
    #        """
    #
    #     def platBounded(
    #             df: pd.DataFrame,
    #             segments: List[List[List[float]]],
    #             segments_3d: List[List[List[float]]]
    #     ) -> Tuple[pd.DataFrame, List[List[List[float]]], List[List[List[float]]]]:
    #         """
    #         Filters and reorders well data and segments based on API numbers and measured depth.
    #
    #         Sorts well data by API number and measured depth, then filters the 2D and 3D
    #         segment data to match only the wells present in the DataFrame. Maintains data
    #         consistency across different representations of the same wells.
    #
    #         Args:
    #             df (pd.DataFrame): Well data containing:
    #                 Required columns:
    #                 - apinumber: Unique well identifier
    #                 - measured_depth: Depth measurement along wellbore
    #             segments (List[List[List[float]]]): 2D coordinate segments for visualization
    #                 Format: [well][segment][x,y coordinates]
    #             segments_3d (List[List[List[float]]]): 3D coordinate segments for visualization
    #                 Format: [well][segment][z coordinates]
    #
    #         Returns:
    #             Tuple containing:
    #             - pd.DataFrame: Sorted and filtered well data
    #             - List[List[List[float]]]: Filtered 2D segments matching DataFrame wells
    #             - List[List[List[float]]]: Filtered 3D segments matching DataFrame wells
    #
    #         Notes:
    #             - Maintains data consistency by filtering segments to match DataFrame wells
    #             - Preserves original data structure and relationships
    #             - Handles potential mismatches between DataFrame and segment data
    #             - Returns empty lists for segments if no matches found
    #
    #         Example:
    #             >>> df_filtered, seg_2d, seg_3d = platBounded(well_df, segments_2d, segments_3d)
    #             >>> print(f"Filtered to {len(seg_2d)} wells")
    #         """
    #         # Sort DataFrame by API number and measured depth
    #         df = df.sort_values(by=['apinumber', 'measured_depth'])
    #
    #         # Create index mapping for API numbers
    #         api = df[['apinumber']].drop_duplicates().reset_index(drop=True)
    #         api['index'] = api.index
    #
    #         # Merge to maintain relationships
    #         merged = pd.merge(api, df, left_on='apinumber', right_on='apinumber')
    #
    #         # Filter segments to match DataFrame wells
    #         segments = [segments[i] for i in range(len(segments)) if i in merged['index'].unique()]
    #         segments_3d = [segments_3d[i] for i in range(len(segments_3d)) if i in merged['index'].unique()]
    #
    #         return df, segments, segments_3d
    #
    #     def setupData(
    #             df: pd.DataFrame,
    #             segments: List[List[List[float]]],
    #             segments_3d: List[List[List[float]]]
    #     ) -> Tuple[pd.DataFrame, List[List[List[float]]], List[List[List[float]]], Dict, pd.DataFrame]:
    #         """
    #         Prepares well data and visualization parameters by filtering data and setting up default styling.
    #
    #         Processes well data through platBounded filter and creates default visualization
    #         parameters for well segments including color and width attributes.
    #
    #         Args:
    #             df (pd.DataFrame): Well data containing:
    #                 Required columns:
    #                 - apinumber: Unique well identifier
    #                 - measured_depth: Depth measurement along wellbore
    #             segments (List[List[List[float]]]): 2D coordinate segments for visualization
    #                 Format: [well][segment][x,y coordinates]
    #             segments_3d (List[List[List[float]]]): 3D coordinate segments for visualization
    #                 Format: [well][segment][z coordinates]
    #
    #         Returns:
    #             Tuple containing:
    #             - pd.DataFrame: Filtered and sorted well data
    #             - List[List[List[float]]]: Filtered 2D segments
    #             - List[List[List[float]]]: Filtered 3D segments
    #             - Dict: Default styling parameters dictionary with:
    #                 - color: List of colors (default 'black')
    #                 - width: List of line widths (default 0.5)
    #             - pd.DataFrame: Styling parameters as DataFrame
    #
    #         Notes:
    #             - Uses platBounded to filter and align data
    #             - Creates consistent default styling for all well segments
    #             - Styling can be modified later by other functions
    #             - Returns both dict and DataFrame versions of styling parameters
    #             - All segments receive identical initial styling
    #
    #         Example:
    #             >>> df, segs_2d, segs_3d, style_dict, style_df = setupData(wells_df, segments_2d, segments_3d)
    #             >>> print(f"Styled {len(style_df)} well segments")
    #         """
    #         # Filter and align data using platBounded
    #         df, segments, segments_3d = platBounded(df, segments, segments_3d)
    #
    #         # Create default styling parameters
    #         data = {'color': ['black'] * len(segments), 'width': [0.5] * len(segments)}
    #
    #         # Convert styling parameters to DataFrame
    #         df_parameters = pd.DataFrame(data)
    #
    #         return df, segments, segments_3d, data, df_parameters
    #
    #     def wellChecked(
    #             type: str,
    #             column: Literal['CurrentWellType', 'current_well_status']
    #     ) -> None:
    #         """
    #         Updates well visualization parameters based on specified well type or status filter.
    #
    #         Modifies the styling (color and line width) of well segments in the visualization
    #         based on either well type (e.g., Oil, Gas) or well status (e.g., Producing,
    #         Shut-in). Wells matching the filter criteria are highlighted with specific colors
    #         and increased line width.
    #
    #         Args:
    #             type (str): Well type or status to filter by. Valid values depend on column:
    #                 For CurrentWellType:
    #                     - 'Oil Well'
    #                     - 'Gas Well'
    #                     - 'Water Disposal Well'
    #                     - 'Water Injection Well'
    #                     - 'Gas Injection Well'
    #                     - 'Dry Hole'
    #                     - 'Test Well'
    #                     - 'Water Source Well'
    #                     - 'Unknown'
    #                 For current_well_status:
    #                     - Status values from well database
    #             column (Literal['CurrentWellType', 'current_well_status']):
    #                 Column to filter on, determines color mapping used
    #
    #         Side Effects:
    #             Updates these visualization parameter DataFrames:
    #             - df_drilled_parameters
    #             - df_planned_parameters
    #             - df_drilling_parameters
    #
    #             Modifies:
    #             - 'color': Changed from default black to type-specific color
    #             - 'width': Increased from 0.5 to 1.5 for matching wells
    #
    #         Notes:
    #             - Only processes first row per API number since color/type is constant per well
    #             - Handles three well categories: drilled, planned, and currently drilling
    #             - Uses predefined color mappings stored in WellTypeColor or WellStatusColor
    #             - Non-matching wells retain default black color and 0.5 width
    #             - Changes are reflected immediately in visualization
    #
    #         Example:
    #             >>> wellChecked('Oil Well', 'CurrentWellType')
    #             # Updates visualization to highlight all oil wells in red
    #         """
    #         # Determine color mapping column based on filter type
    #         colors_lst = 'WellTypeColor' if column == 'CurrentWellType' else 'WellStatusColor'
    #
    #         # Get first row for each API number to determine well properties
    #         drilled_df_restricted = drilled_df.groupby('apinumber').first().reset_index()
    #         planned_df_restricted = planned_df.groupby('apinumber').first().reset_index()
    #         currently_drilling_df_restricted = currently_drilling_df.groupby('apinumber').first().reset_index()
    #
    #         # Create masks for wells matching specified type/status
    #         drilled_well_mask = drilled_df_restricted[column] == type
    #         planned_well_mask = planned_df_restricted[column] == type
    #         currently_drilling_well_mask = currently_drilling_df_restricted[column] == type
    #
    #         # Update styling for drilled wells
    #         df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[
    #             drilled_well_mask, colors_lst]
    #         df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5
    #
    #         # Update styling for planned wells
    #         df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[
    #             planned_well_mask, colors_lst]
    #         df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5
    #
    #         # Update styling for currently drilling wells
    #         df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[
    #             currently_drilling_well_mask, colors_lst]
    #         df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5
    #
    #     def wellCheckedMultiple(
    #             types: List[str],
    #             column: Literal['CurrentWellType', 'current_well_status']
    #     ) -> None:
    #         """
    #         Updates well visualization parameters for multiple well types or statuses simultaneously.
    #
    #         Similar to wellChecked() but handles multiple types/statuses at once. Modifies the styling
    #         (color and line width) of well segments in the visualization based on a list of well
    #         types or statuses. Wells matching any of the filter criteria are highlighted.
    #
    #         Args:
    #             types (List[str]): List of well types or statuses to filter by. Valid values depend on column:
    #                 For CurrentWellType:
    #                     - 'Oil Well'
    #                     - 'Gas Well'
    #                     - 'Water Disposal Well'
    #                     - 'Oil Well/Water Disposal Well'
    #                     - 'Water Injection Well'
    #                     - 'Gas Injection Well'
    #                     - 'Dry Hole'
    #                     - etc.
    #                 For current_well_status:
    #                     - 'Location Abandoned - APD rescinded'
    #                     - 'Returned APD (Unapproved)'
    #                     - 'Approved Permit'
    #                     - 'Active'
    #                     - 'Drilling Operations Suspended'
    #                     - 'New Permit'
    #                     - 'Inactive'
    #                     - 'Temporarily-abandoned'
    #                     - 'Test Well or Monitor Well'
    #                     - etc.
    #             column (Literal['CurrentWellType', 'current_well_status']):
    #                 Column to filter on, determines color mapping used
    #
    #         Side Effects:
    #             Updates these visualization parameter DataFrames:
    #             - df_drilled_parameters
    #             - df_planned_parameters
    #             - df_drilling_parameters
    #
    #             Modifies:
    #             - 'color': Changed from default black to type-specific color
    #             - 'width': Increased from 0.5 to 1.5 for matching wells
    #
    #         Notes:
    #             - Only processes first row per API number since color/type is constant per well
    #             - Handles three well categories: drilled, planned, and currently drilling
    #             - Uses predefined color mappings stored in WellTypeColor or WellStatusColor
    #             - Non-matching wells retain default black color and 0.5 width
    #             - Changes are reflected immediately in visualization
    #             - Commonly used for grouping related well types (e.g., all injection wells)
    #             - Used by the GUI checkbox handlers to update multiple well types at once
    #
    #         Example:
    #             >>> wellCheckedMultiple(['Water Injection Well', 'Gas Injection Well'], 'CurrentWellType')
    #             # Updates visualization to highlight all injection wells
    #         """
    #         # Determine color mapping column based on filter type
    #         colors_lst = 'WellTypeColor' if column == 'CurrentWellType' else 'WellStatusColor'
    #
    #         # Get first row for each API number to determine well properties
    #         drilled_df_restricted = drilled_df.groupby('apinumber').first().reset_index()
    #         planned_df_restricted = planned_df.groupby('apinumber').first().reset_index()
    #         currently_drilling_df_restricted = currently_drilling_df.groupby('apinumber').first().reset_index()
    #
    #         # Create masks for wells matching any specified type/status
    #         drilled_well_mask = drilled_df_restricted[column].isin(types)
    #         planned_well_mask = planned_df_restricted[column].isin(types)
    #         currently_drilling_well_mask = currently_drilling_df_restricted[column].isin(types)
    #
    #         # Update styling for drilled wells
    #         df_drilled_parameters.loc[drilled_well_mask, 'color'] = drilled_df_restricted.loc[
    #             drilled_well_mask, colors_lst]
    #         df_drilled_parameters.loc[drilled_well_mask, 'width'] = 1.5
    #
    #         # Update styling for planned wells
    #         df_planned_parameters.loc[planned_well_mask, 'color'] = planned_df_restricted.loc[
    #             planned_well_mask, colors_lst]
    #         df_planned_parameters.loc[planned_well_mask, 'width'] = 1.5
    #
    #         # Update styling for currently drilling wells
    #         df_drilling_parameters.loc[currently_drilling_well_mask, 'color'] = currently_drilling_df_restricted.loc[
    #             currently_drilling_well_mask, colors_lst]
    #         df_drilling_parameters.loc[currently_drilling_well_mask, 'width'] = 1.5
    #
    #     def toggleWellDisplay(
    #             condition: bool,
    #             data_frame: pd.DataFrame,
    #             segments_2d: List[List[float]],
    #             colors_init: Union[str, List[str]],
    #             line_width: Union[float, List[float]],
    #             well_2d: Line2D,
    #             well_3d: Line2D,
    #             vertical_well: Line2D,
    #             segments_3d: List[List[float]]
    #     ) -> None:
    #         """
    #         Toggles the visibility and updates data for well visualization elements based on a boolean condition.
    #
    #         Controls the display state and data updates for 2D, 3D and vertical well representations in the
    #         visualization. When enabled, updates the data and makes wells visible. When disabled, hides the wells
    #         without removing the underlying data.
    #
    #         Args:
    #             condition (bool): Toggle state - True to show and update wells, False to hide them
    #             data_frame (pd.DataFrame): Well data to incorporate into currently displayed wells
    #                 Required columns:
    #                 - Well identifiers
    #                 - Coordinate data
    #                 - Well properties
    #             segments_2d (List[List[float]]): 2D coordinate segments for well paths
    #                 Format: [[x1,y1], [x2,y2], ...]
    #             colors_init (Union[str, List[str]]): Color specification for well lines
    #                 Either single color string or list of colors per segment
    #             line_width (Union[float, List[float]]): Width specification for well lines
    #                 Either single width value or list of widths per segment
    #             well_2d (Line2D): Matplotlib line object for 2D well representation
    #             well_3d (Line2D): Matplotlib line object for 3D well representation
    #             vertical_well (Line2D): Matplotlib line object for vertical well projection
    #             segments_3d (List[List[float]]): 3D coordinate segments for well paths
    #                 Format: [[x1,y1,z1], [x2,y2,z2], ...]
    #
    #         Side Effects:
    #             - Updates self.currently_used_lines with new well data when enabled
    #             - Modifies visibility of well_2d, well_3d and vertical_well line objects
    #             - Triggers redraw of well visualizations when enabled
    #             - Changes persist until next toggle operation
    #
    #         Notes:
    #             - Uses drawModelBasedOnParameters2d() for 2D visualization updates
    #             - Uses drawModelBasedOnParameters() for 3D visualization updates
    #             - Maintains data state even when wells are hidden
    #             - Deduplicates data when adding new wells
    #             - Preserves existing well properties when toggling visibility
    #
    #         Example:
    #             >>> toggleWellDisplay(True, new_wells_df, segs_2d, 'blue', 1.0,
    #                                   well2d, well3d, vert_well, segs_3d)
    #             # Shows wells and updates with new data
    #             >>> toggleWellDisplay(False, new_wells_df, segs_2d, 'blue', 1.0,
    #                                   well2d, well3d, vert_well, segs_3d)
    #             # Hides wells without removing data
    #         """
    #         if condition:
    #             # Update data and show wells
    #             self.currently_used_lines = concat([self.currently_used_lines, data_frame]).drop_duplicates(
    #                 keep='first').reset_index(drop=True)
    #
    #             # Redraw 2D and 3D visualizations with updated parameters
    #             self.drawModelBasedOnParameters2d(well_2d, segments_2d, colors_init, line_width, self.ax2d,
    #                                               vertical_well)
    #             self.drawModelBasedOnParameters(well_3d, segments_3d, colors_init, line_width, self.ax3d)
    #
    #             # Make all well representations visible
    #             well_2d.set_visible(True)
    #             well_3d.set_visible(True)
    #             vertical_well.set_visible(True)
    #         else:
    #             # Hide all well representations
    #             well_2d.set_visible(False)
    #             well_3d.set_visible(False)
    #             vertical_well.set_visible(False)
    #
    #     def statusAndTypesEnabler() -> NoReturn:
    #         """
    #         Manages well visualization filters and field label visibility based on UI state.
    #
    #         Coordinates the mutual exclusivity between well type and status filters while
    #         maintaining independent control of field label visibility. Handles three main
    #         aspects of visualization:
    #         1. Well type filtering (for Oil, Gas, Injection, Disposal wells etc.)
    #         2. Well status filtering (Producing, Shut-in, P&A, Drilling etc.)
    #         3. Field name label visibility
    #
    #         Radio Button IDs:
    #             -2: Well Type filtering mode (Oil, Gas, Injection, etc.)
    #             -3: Well Status filtering mode (Producing, Shut-in, etc.)
    #
    #         Field Labels:
    #             - Displayed as red text at field centroids when enabled
    #             - Size: 75 units
    #             - Visibility tied to field_names_checkbox state
    #
    #         Side Effects:
    #             - Updates well visibility based on selected filter mode
    #             - Modifies field label and section visibility
    #             - Changes currently_used_lines DataFrame content
    #             - Triggers field label rendering when enabled
    #             - Maintains field visibility state independent of filter changes
    #
    #         Notes:
    #             - Part of the well visualization control system
    #             - Connected to radio button and checkbox state changes
    #             - Preserves field label state across filter changes
    #             - Ensures proper layering of visual elements
    #             - Manages memory by creating field labels only when visible
    #             - Coordinates with wellTypesEnable() and wellStatusEnable()
    #
    #         Example:
    #             Called when switching between well type/status or toggling field names:
    #             >>> self.ui.well_type_or_status_button_group.buttonClicked.connect(
    #                     self.statusAndTypesEnabler)
    #             >>> self.ui.field_names_checkbox.stateChanged.connect(
    #                     self.statusAndTypesEnabler)
    #         """
    #         # Store field checkbox state to preserve across filter changes
    #         field_checkbox_state = self.ui.field_names_checkbox.isChecked()
    #
    #         # Get the ID of currently selected radio button
    #         active_button_id_type_status = self.ui.well_type_or_status_button_group.checkedId()
    #
    #         # Enable well type filtering mode
    #         if active_button_id_type_status == -2:
    #             wellTypesEnable()
    #         # Enable well status filtering mode
    #         elif active_button_id_type_status == -3:
    #             wellStatusEnable()
    #
    #         # Handle field label visibility independent of filter state
    #         if field_checkbox_state:
    #             self.field_sections.set_visible(True)
    #             # Create field label paths with consistent styling
    #             paths = [
    #                 PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
    #                 for coord, text in zip(self.field_centroids_lst, self.field_labels)
    #             ]
    #             self.labels_field.set_paths(paths)
    #             self.labels_field.set_visible(True)
    #         else:
    #             self.field_sections.set_visible(False)
    #             self.labels_field.set_visible(False)
    #
    #     def wellTypesEnable() -> NoReturn:
    #         """
    #         Enables well type filtering while temporarily disabling well status filters.
    #
    #         Updates the visualization based on selected well type checkboxes in the UI.
    #         Temporarily blocks signals from status checkboxes to prevent interference
    #         between type and status filters.
    #
    #         Well Types Handled:
    #             - Oil Wells
    #             - Gas Wells
    #             - Water Disposal Wells (including dual-purpose Oil/Disposal wells)
    #             - Dry Holes
    #             - Injection Wells (Water and Gas)
    #             - Other Wells (Unknown, Test Wells, Water Source Wells)
    #
    #         Side Effects:
    #             # - Temporarily blocks signals from status checkboxes
    #             - Unchecks all status checkboxes
    #             - Updates well visualization based on checked type filters
    #             # - Restores signal handling for status checkboxes
    #             - Modifies well colors and visibility in the visualization
    #             - Updates currently_used_lines DataFrame
    #
    #         Notes:
    #             - Uses wellChecked() for single well types
    #             - Uses wellCheckedMultiple() for grouped well types
    #             - Ensures mutual exclusivity between type and status filters
    #             - Part of the well visualization control system
    #             - Connected to UI checkbox state changes
    #             - Maintains separation between well type and status filtering
    #
    #         Example:
    #             Called when user interacts with well type checkboxes:
    #             >>> self.ui.oil_well_check.stateChanged.connect(self.wellTypesEnable)
    #         """
    #         # Temporarily disable status checkbox signals
    #         # for q in self.status_checks:
    #         #     q.blockSignals(True)
    #         #     q.setChecked(False)
    #
    #         # Handle Oil Well selection
    #         if self.ui.oil_well_check.isChecked():
    #             wellChecked('Oil Well', 'CurrentWellType')
    #
    #         # Handle Gas Well selection
    #         if self.ui.gas_well_check.isChecked():
    #             wellChecked('Gas Well', 'CurrentWellType')
    #
    #         # Handle Water Disposal Well selection (including combination wells)
    #         if self.ui.water_disposal_check.isChecked():
    #             wellCheckedMultiple(['Water Disposal Well', 'Oil Well/Water Disposal Well'], 'CurrentWellType')
    #
    #         # Handle Dry Hole selection
    #         if self.ui.dry_hole_check.isChecked():
    #             wellChecked('Dry Hole', 'CurrentWellType')
    #
    #         # Handle Injection Well selection (both water and gas)
    #         if self.ui.injection_check.isChecked():
    #             wellCheckedMultiple(['Water Injection Well', 'Gas Injection Well'], 'CurrentWellType')
    #
    #         # Handle Other Well Types selection
    #         if self.ui.other_well_status_check.isChecked():
    #             wellCheckedMultiple(['Unknown', 'Test Well', 'Water Source Well'], 'CurrentWellType')
    #
    #         # Re-enable status checkbox signals
    #         # for q in self.status_checks:
    #         # q.blockSignals(False)
    #
    #     def wellStatusEnable() -> NoReturn:
    #         """
    #         Enables well status filtering while temporarily disabling well type filters.
    #
    #         Updates the visualization based on selected well status checkboxes in the UI.
    #         Temporarily blocks signals from type checkboxes to prevent interference
    #         between status and type filters.
    #
    #         Well Statuses Handled:
    #             - Shut-in wells
    #             - Plugged & Abandoned wells
    #             - Producing wells
    #             - Currently drilling wells
    #             - Miscellaneous statuses:
    #                 - Location Abandoned (APD rescinded)
    #                 - Returned APD (Unapproved)
    #                 - Approved Permit
    #                 - Active
    #                 - Drilling Operations Suspended
    #                 - New Permit
    #                 - Inactive
    #                 - Temporarily-abandoned
    #                 - Test/Monitor Wells
    #
    #         Side Effects:
    #             - Temporarily blocks signals from type checkboxes
    #             - Unchecks all type checkboxes
    #             - Updates well visualization based on checked status filters
    #             - Restores signal handling for type checkboxes
    #             - Modifies well colors and visibility in visualization
    #             - Updates currently_used_lines DataFrame
    #
    #         Notes:
    #             - Uses wellChecked() for single well statuses
    #             - Uses wellCheckedMultiple() for grouped miscellaneous statuses
    #             - Ensures mutual exclusivity between status and type filters
    #             - Part of the well visualization control system
    #             - Connected to UI checkbox state changes
    #             - Maintains separation between well status and type filtering
    #
    #         Example:
    #             Called when user interacts with well status checkboxes:
    #             >>> self.ui.shut_in_check.stateChanged.connect(self.wellStatusEnable)
    #         """
    #         # Temporarily disable type checkbox signals
    #         # for q in self.type_checks:
    #         #     q.blockSignals(True)
    #         #     q.setChecked(False)
    #
    #         # Handle Shut-in wells
    #         if self.ui.shut_in_check.isChecked():
    #             wellChecked('Shut-in', 'current_well_status')
    #
    #         # Handle Plugged & Abandoned wells
    #         if self.ui.pa_check.isChecked():
    #             wellChecked('Plugged & Abandoned', 'current_well_status')
    #
    #         # Handle Producing wells
    #         if self.ui.producing_check.isChecked():
    #             wellChecked('Producing', 'current_well_status')
    #
    #         # Handle Currently Drilling wells
    #         if self.ui.drilling_status_check.isChecked():
    #             wellChecked('Drilling', 'current_well_status')
    #
    #         # Handle Miscellaneous well statuses
    #         if self.ui.misc_well_type_check.isChecked():
    #             wellCheckedMultiple(['Location Abandoned - APD rescinded',
    #                                  'Returned APD (Unapproved)', 'Approved Permit',
    #                                  'Active', 'Drilling Operations Suspended', 'New Permit', 'Inactive',
    #                                  'Temporarily-abandoned', 'Test Well or Monitor Well'], 'current_well_status')
    #
    #         # Re-enable type checkbox signals
    #         # for q in self.type_checks:
    #         #     q.blockSignals(False)
    #
    #     # Reset current line tracking
    #     self.currently_used_lines = None
    #
    #     # Store segment and DataFrame references locally
    #     drilled_segments = self.drilled_segments
    #     planned_segments = self.planned_segments
    #     currently_drilling_segments = self.currently_drilling_segments
    #
    #     drilled_segments_3d = self.drilled_segments_3d
    #     planned_segments_3d = self.planned_segments_3d
    #     currently_drilling_segments_3d = self.currently_drilling_segments_3d
    #
    #     drilled_df = self.drilled_df
    #     planned_df = self.planned_df
    #     currently_drilling_df = self.currently_drilling_df
    #
    #     # Process each well category data
    #     drilled_df, drilled_segments, drilled_segments_3d, data_drilled, df_drilled_parameters = setupData(
    #         drilled_df, drilled_segments, drilled_segments_3d)
    #     planned_df, planned_segments, planned_segments_3d, data_planned, df_planned_parameters = setupData(
    #         planned_df, planned_segments, planned_segments_3d)
    #     currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d, data_drilling, df_drilling_parameters = setupData(
    #         currently_drilling_df, currently_drilling_segments, currently_drilling_segments_3d)
    #
    #     # Update well type/status filters
    #     statusAndTypesEnabler()
    #     # Handle field name visibility
    #     if self.ui.field_names_checkbox.isChecked():
    #         self.field_sections.set_visible(True)
    #         paths = [PathPatch(TextPath((coord.x, coord.y), text, size=75), color="red")
    #                  for coord, text in zip(self.field_centroids_lst, self.field_labels)]
    #         self.labels_field.set_paths(paths)
    #         self.labels_field.set_visible(True)
    #     else:
    #         self.field_sections.set_visible(False)
    #         self.labels_field.set_visible(False)
    #
    #     # Extract visualization parameters
    #     drilled_colors_init, drilled_line_width = df_drilled_parameters['color'].tolist(), df_drilled_parameters[
    #         'width'].tolist()
    #     planned_colors_init, planned_line_width = df_planned_parameters['color'].tolist(), df_planned_parameters[
    #         'width'].tolist()
    #     currently_drilling_colors_init, currently_drilling_width = df_drilling_parameters['color'].tolist(), \
    #         df_drilling_parameters['width'].tolist()
    #
    #     # Toggle visibility for each well category
    #     toggleWellDisplay(
    #         self.ui.asdrilled_check.isChecked(), drilled_df,
    #         drilled_segments, drilled_colors_init, drilled_line_width,
    #         self.all_wells_2d_asdrilled, self.all_wells_3d_asdrilled,
    #         self.all_wells_2d_vertical_asdrilled, drilled_segments_3d)
    #
    #     toggleWellDisplay(
    #         self.ui.planned_check.isChecked(), planned_df,
    #         planned_segments, planned_colors_init, planned_line_width,
    #         self.all_wells_2d_planned, self.all_wells_3d_planned,
    #         self.all_wells_2d_vertical_planned, planned_segments_3d)
    #
    #     toggleWellDisplay(
    #         self.ui.currently_drilling_check.isChecked(), currently_drilling_df,
    #         currently_drilling_segments, currently_drilling_colors_init, currently_drilling_width,
    #         self.all_wells_2d_current, self.all_wells_3d_current,
    #         self.all_wells_2d_vertical_current, currently_drilling_segments_3d)
    #
    #     # Update 3D plot boundaries if drilled segments exist
    #     if drilled_segments_3d:
    #         self.centroid, std_vals = self.calculateCentroidNP(drilled_segments_3d)
    #         new_xlim = [self.centroid[0] - 10000, self.centroid[0] + 10000]
    #         new_ylim = [self.centroid[1] - 10000, self.centroid[1] + 10000]
    #         new_zlim = [self.centroid[2] - 10000, self.centroid[2] + 10000]
    #         self.ax3d.set_xlim3d(new_xlim)
    #         self.ax3d.set_ylim3d(new_ylim)
    #         self.ax3d.set_zlim3d(new_zlim)
    #
    #     # Refresh all canvases
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()
    #     self.canvas3d.blit(self.ax3d.bbox)
    #     self.canvas3d.draw()

    def init_plot(self):
        for drilling_status, style in self.drilling_styles.items():
            lc = LineCollection([], linestyles=style['linestyle'], linewidths=1.5, zorder=2)
            self.drilling_collections[drilling_status] = lc
            self.ax2d.add_collection(lc)

            # Prepare segments and their properties
        self.prepare_segments()

        # Create Legend
        # self.create_legend()

        # Adjust plot limits
        self.ax2d.autoscale()
        self.ax2d.set_aspect('equal', 'datalim')

        # Draw the initial canvas
        self.canvas2d.draw()

    def prepare_segments(self, used_df_dx, well_info_df):
        # Group data by api, citing_type, measured_depth, and drilling_status to form LineStrings
        grouped = used_df_dx.sort_values('measured_depth').groupby(
            ['apinumber', 'citing_type'])

        # Initialize a dictionary to hold segments and their properties per drilling status
        self.segments_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}
        self.segment_properties = {status: [] for status in self.drilling_styles.keys()}

        for (api, citing_type), group in grouped:
            used_info = well_info_df[well_info_df['well_id']==api]
            used_group = group.sort_values('measured_depth')
            coords = list(zip(used_group['x'], used_group['y']))
            if len(coords) < 2:
                continue  # Need at least two points to form a line
            line = LineString(coords)
            segment = list(line.coords)
            print(segment)
            self.segments_per_drilling_status[citing_type].append(segment)
            #
            # # Assuming all points in a group have the same type and status
            well_type = used_info['current_well_type'].iloc[0]
            well_status = used_info['current_well_status'].iloc[0]
            self.segment_properties[citing_type].append({
                'api': api,
                'citing_type': citing_type,
                'type': well_type,
                'status': well_status
            })

        # Assign segments and default colors to each LineCollection
        # for drilling_status, lc in self.drilling_collections.items():
        #     lc.set_segments(self.segments_per_drilling_status[drilling_status])
        #     # Default color: based on well type or well status
        #     # Initially, color by well type
        #     colors = [
        #         self.type_color_map.get(prop['type'], 'black')
        #         for prop in self.segment_properties[drilling_status]
        #     ]
        #     lc.set_color(colors)
        #     # Store all properties for later filtering
        #     lc.segment_props = self.segment_properties[drilling_status]






    def draw_2d_data_all(self, well_info_df, used_df_dx):
            # Create a default LineCollection for all wells
        main_statuses = ['Plugged & Abandoned',
                                    'Producing',
                                    'Shut-in',
                                    'Drilling']
        main_types = ['Unknown',
                                 'Oil Well',
                                 'Dry Hole',
                                 'Gas Well',
                                 'Test Well',
                                 'Water Source Well']
        other_statuses= ['Location Abandoned - APD rescinded',
                                     'Returned APD (Unapproved)',
                                     'Approved Permit',
                                     'Active',
                                     'Drilling Operations Suspended',
                                     'New Permit',
                                     'Inactive',
                                     'Temporarily-abandoned',
                                     'Test Well or Monitor Well']


        self.drilling_collections = {}
        for drilling_status, style in self.drilling_styles.items():
            lc = LineCollection([], linestyles=style['linestyle'], linewidths=1.5, zorder=2)
            self.drilling_collections[drilling_status] = lc
            self.ax2d.add_collection(lc)

        # Prepare segments and their properties
        self.prepare_segments(used_df_dx, well_info_df)

        # Adjust plot limits
        self.ax2d.autoscale()
        self.ax2d.set_aspect('equal', 'datalim')

        # Create Legend
        # self.create_legend()

        self.canvas2d.draw()

        # # Define color mapping based on well type and well status
        # self.type_color_map = {
        #     'oil': 'red',
        #     'gas': 'green',
        #     'water': 'blue',
        #     'injection': 'purple'
        #     # Add more types and colors as needed
        # }

        # self.status_color_map = {
        #     'producing': 'cyan',
        #     'shut in': 'magenta',
        #     'injecting': 'orange'
        #     # Add more statuses and colors as needed
        # }

        # self.status_collections = {}
        # for status, style in status_styles.items():
        #     lc = LineCollection([], linestyles=style['linestyle'], linewidths=1.0, zorder=2)
        #     self.status_collections[status] = lc
        #     self.ax2d.add_collection(lc)
        # grouped = self.df_wells.sort_values('sequence').groupby(['well_id', 'status'])
        #
        #     # Dictionaries to hold LineCollections per type
        # self.type_collections = {}
        # # types = self.df_wells['type'].unique()
        # for well_type in main_statuses:
        #     # Initialize with empty LineCollections
        #     lc = LineCollection([], linewidths=1.0, zorder=2)
        #     self.type_collections[well_type] = lc
        #     self.ax2d.add_collection(lc)
        # all_wells = self.surveys.groupby('apinumber')
        # # Populate the LineCollections
        # for i, group in enumerate(all_wells):
        #     citing_group = self.surveys.groupby('citing_type')
        #     for j in group2 in
        #     print(group)
        # for idx, row in self.surveys.iterrows():
        #     line = row['geometry']
        #     coords = list(line.coords)
        #     if row['type'] in self.type_collections:
        #         self.type_collections[row['type']].get_segments = getattr(self.type_collections[row['type']],
        #                                                                   'get_segments', [])
        #         self.type_collections[row['type']].get_segments.append(coords)
        #
        # # After collecting all segments, set them
        # for well_type, lc in self.type_collections.items():
        #     segments = [list(line.coords) for line in self.df_wells[self.df_wells['type'] == well_type]['geometry']]
        #     lc.set_segments(segments)
        #     # Set default color (same as all_wells)
        #     lc.set_color('black')
        #     lc.set_linewidth(0.5)
        #
        # # Adjust plot limits
        # self.ax.autoscale()
        # self.canvas.draw()
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
               - toggleWellDisplay(): Controls well visibility
               - calculateCentroidNP(): Computes 3D view center
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
                    - apinumber: Unique well identifier
                    - measured_depth: Depth measurement along wellbore
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
            df = df.sort_values(by=['apinumber', 'measured_depth'])

            # Create index mapping for API numbers
            api = df[['apinumber']].drop_duplicates().reset_index(drop=True)
            api['index'] = api.index

            # Merge to maintain relationships
            merged = pd.merge(api, df, left_on='apinumber', right_on='apinumber')

            # Filter segments to match DataFrame wells
            segments = [segments[i] for i in range(len(segments)) if i in merged['index'].unique()]
            segments_3d = [segments_3d[i] for i in range(len(segments_3d)) if i in merged['index'].unique()]

            return df, segments, segments_3d

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
                    - apinumber: Unique well identifier
                    - measured_depth: Depth measurement along wellbore
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

        def wellChecked(
                type: str,
                column: Literal['CurrentWellType', 'current_well_status']
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
                    For current_well_status:
                        - Status values from well database
                column (Literal['CurrentWellType', 'current_well_status']):
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
            drilled_df_restricted = drilled_df.groupby('apinumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('apinumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('apinumber').first().reset_index()

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

        def wellCheckedMultiple(
                types: List[str],
                column: Literal['CurrentWellType', 'current_well_status']
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
                    For current_well_status:
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
                column (Literal['CurrentWellType', 'current_well_status']):
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
            drilled_df_restricted = drilled_df.groupby('apinumber').first().reset_index()
            planned_df_restricted = planned_df.groupby('apinumber').first().reset_index()
            currently_drilling_df_restricted = currently_drilling_df.groupby('apinumber').first().reset_index()

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

        def toggleWellDisplay(
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
                >>> toggleWellDisplay(True, new_wells_df, segs_2d, 'blue', 1.0,
                                      well2d, well3d, vert_well, segs_3d)
                # Shows wells and updates with new data
                >>> toggleWellDisplay(False, new_wells_df, segs_2d, 'blue', 1.0,
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
                wellChecked('Shut-in', 'current_well_status')

            # Handle Plugged & Abandoned wells
            if self.ui.pa_check.isChecked():
                wellChecked('Plugged & Abandoned', 'current_well_status')

            # Handle Producing wells
            if self.ui.producing_check.isChecked():
                wellChecked('Producing', 'current_well_status')

            # Handle Currently Drilling wells
            if self.ui.drilling_status_check.isChecked():
                wellChecked('Drilling', 'current_well_status')

            # Handle Miscellaneous well statuses
            if self.ui.misc_well_type_check.isChecked():
                wellCheckedMultiple(['Location Abandoned - APD rescinded',
                                     'Returned APD (Unapproved)', 'Approved Permit',
                                     'Active', 'Drilling Operations Suspended', 'New Permit', 'Inactive',
                                     'Temporarily-abandoned', 'Test Well or Monitor Well'], 'current_well_status')

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
        toggleWellDisplay(
            self.ui.asdrilled_check.isChecked(), drilled_df,
            drilled_segments, drilled_colors_init, drilled_line_width,
            self.all_wells_2d_asdrilled, self.all_wells_3d_asdrilled,
            self.all_wells_2d_vertical_asdrilled, drilled_segments_3d)

        toggleWellDisplay(
            self.ui.planned_check.isChecked(), planned_df,
            planned_segments, planned_colors_init, planned_line_width,
            self.all_wells_2d_planned, self.all_wells_3d_planned,
            self.all_wells_2d_vertical_planned, planned_segments_3d)

        toggleWellDisplay(
            self.ui.currently_drilling_check.isChecked(), currently_drilling_df,
            currently_drilling_segments, currently_drilling_colors_init, currently_drilling_width,
            self.all_wells_2d_current, self.all_wells_3d_current,
            self.all_wells_2d_vertical_current, currently_drilling_segments_3d)

        # Update 3D plot boundaries if drilled segments exist
        if drilled_segments_3d:
            self.centroid, std_vals = self.calculateCentroidNP(drilled_segments_3d)
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

    # def draw_2d_data_all(self, well_info_df, dx_data):
    #     def find_populated_dataframe():
    #         if not drilled_df.empty:
    #             return drilled_df
    #         elif not planned_df.empty:
    #             return planned_df
    #         else:
    #             return vert_df
    #
    #     Get well parameter data from current selection
    #     # df_well_data: pd.DataFrame = well_info_df.loc[dx_data['DisplayName'] == self.ui.well_lst_combobox.currentText()]
    #
    #     # Filter directional survey data for selected well
    #     df_well: pd.DataFrame = dx_data[dx_data['apinumber'] == df_well_data['WellID'].iloc[0]]
    #
    #     # Separate data by citing type
    #     drilled_df: pd.DataFrame = df_well[df_well['citing_type'].isin(['asdrilled'])]
    #     planned_df: pd.DataFrame = df_well[df_well['citing_type'].isin(['planned'])]
    #     vert_df: pd.DataFrame = df_well[df_well['citing_type'].isin(['vertical'])]
    #
    #     # Get best available data based on priority
    #     df_well = find_populated_dataframe()
    #     df_well.drop_duplicates(keep='first', inplace=True)
    #     df_well['X'] = df_well['X'].astype(float)
    #     df_well['Y'] = df_well['Y'].astype(float)
    #
    #     # # Extract coordinate data
    #     # xy_data = df_well[['X', 'Y']].values
    #     #
    #     # # Update appropriate plot based on well type
    #     # if df_well['citing_type'].iloc[0] == 'vertical':
    #     #     self.spec_vertical_wells_2d.set_offsets(xy_data)
    #     #     self.spec_well_2d.set_data([], [])
    #     # else:
    #     #     self.spec_vertical_wells_2d.set_offsets([None, None])
    #     #     self.spec_well_2d.set_data(xy_data[:, 0], xy_data[:, 1])
    #     #
    #     # # Process 3D coordinates
    #     # x = to_numeric(df_well['SPX'], errors='coerce')
    #     # y = to_numeric(df_well['SPY'], errors='coerce')
    #     # z = to_numeric(df_well['Targeted Elevation'], errors='coerce')
    #     # self.centroid = (x.mean(), y.mean(), z.mean())
    #     #
    #     # # Update 3D visualizations
    #     # self.spec_well_3d.set_data(x, y)
    #     # self.spec_well_3d.set_3d_properties(z)
    #     # self.spec_well_3d_solo.set_data(x, y)
    #     # self.spec_well_3d_solo.set_3d_properties(z)
    #     #
    #     # # Refresh canvases
    #     # self.canvas2d.draw()
    #     # self.canvas3d.draw()
    #     #
    #     # # Set new view limits centered on well
    #     # new_xlim = [self.centroid[0] - 8000, self.centroid[0] + 8000]
    #     # new_ylim = [self.centroid[1] - 8000, self.centroid[1] + 8000]
    #     # new_zlim = [self.centroid[2] - 8000, self.centroid[2] + 8000]
    #     #
    #     # # Update 3D solo view limits
    #     # self.ax3d_solo.set_xlim3d(new_xlim)
    #     # self.ax3d_solo.set_ylim3d(new_ylim)
    #     # self.ax3d_solo.set_zlim3d(new_zlim)
    #     #
    #     # # Refresh solo canvas and production graphic
    #     # self.canvas3d_solo.draw()
    #     # self.drawProductionGraphic()