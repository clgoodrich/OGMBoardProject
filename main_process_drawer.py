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

class Drawer2:
    def __init__(self, ui, used_df_dx, well_info_df):
        self.ui = ui

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


class Drawer:
    def __init__(self, ui, used_df_dx, well_info_df):
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

    def prepare_segments(self):
        # Group data by api, citing_type, measured_depth, and drilling_status to form LineStrings
        grouped = self.df_wells.sort_values('sequence').groupby(
            ['api', 'citing_type', 'measured_depth', 'drilling_status'])

        # Initialize a dictionary to hold segments and their properties per drilling status
        self.segments_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}
        self.segment_properties = {status: [] for status in self.drilling_styles.keys()}

        for (api, citing_type, measured_depth, drilling_status), group in grouped:
            coords = list(zip(group['x'], group['y']))
            if len(coords) < 2:
                continue  # Need at least two points to form a line
            line = LineString(coords)
            segment = list(line.coords)
            self.segments_per_drilling_status[drilling_status].append(segment)

            # Assuming all points in a group have the same type and status
            well_type = group['type'].iloc[0]
            well_status = group['status'].iloc[0]
            self.segment_properties[drilling_status].append({
                'api': api,
                'citing_type': citing_type,
                'measured_depth': measured_depth,
                'type': well_type,
                'status': well_status
            })

        # Assign segments and default colors to each LineCollection
        for drilling_status, lc in self.drilling_collections.items():
            lc.set_segments(self.segments_per_drilling_status[drilling_status])
            # Default color: based on well type or well status
            # Initially, color by well type
            colors = [
                self.type_color_map.get(prop['type'], 'black')
                for prop in self.segment_properties[drilling_status]
            ]
            lc.set_color(colors)
            # Store all properties for later filtering
            lc.segment_props = self.segment_properties[drilling_status]



    # def prepare_segments(self, dx_df, well_info_df):
    #     # Group data by well_id and drilling_status to form LineStrings
    #     grouped = dx_df.sort_values('MeasuredDepth').groupby(['APINumber', 'CitingType'])
    #
    #     # Initialize a dictionary to hold segments and their properties per drilling status
    #     segments_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}
    #     colors_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}
    #
    #     # Store mappings from (well_id, drilling_status) to (type, status)
    #     segment_properties = {status: [] for status in self.drilling_styles.keys()}
    #
    #     for (well_id, drilling_status), group in grouped:
    #         print(drilling_status)
    #         well_parameters = well_info_df[well_info_df['WellID']==well_id]
    #         coords = list(zip(group['X'], group['Y']))
    #         if len(coords) < 2:
    #             continue  # Need at least two points to form a line
    #         line = LineString(coords)
    #         segment = list(line.coords)
    #         segments_per_drilling_status[drilling_status].append(segment)
    #
    #         # Assuming all points in a group have the same type and status
    #         well_type = group['type'].iloc[0]
    #         well_status = group['status'].iloc[0]
    #         segment_properties[drilling_status].append({
    #             'type': well_type,
    #             'status': well_status
    #         })
    #
    #     # Assign segments and default colors to each LineCollection
    #     for drilling_status, lc in self.drilling_collections.items():
    #         lc.set_segments(segments_per_drilling_status[drilling_status])
    #         # Default color: based on well type or well status
    #         # Initially, color by well type
    #         colors = [
    #             self.type_color_map.get(prop['type'], 'black')
    #             for prop in segment_properties[drilling_status]
    #         ]
    #         lc.set_color(colors)
    #         # Store all properties for later filtering
    #         lc.segment_props = segment_properties[drilling_status]


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
        # all_wells = self.surveys.groupby('APINumber')
        # # Populate the LineCollections
        # for i, group in enumerate(all_wells):
        #     citing_group = self.surveys.groupby('CitingType')
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
    #     df_well: pd.DataFrame = dx_data[dx_data['APINumber'] == df_well_data['WellID'].iloc[0]]
    #
    #     # Separate data by citing type
    #     drilled_df: pd.DataFrame = df_well[df_well['CitingType'].isin(['asdrilled'])]
    #     planned_df: pd.DataFrame = df_well[df_well['CitingType'].isin(['planned'])]
    #     vert_df: pd.DataFrame = df_well[df_well['CitingType'].isin(['vertical'])]
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
    #     # if df_well['CitingType'].iloc[0] == 'vertical':
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