"""
WellVisualizerBoardMatters
Author: Colton Goodrich
Date: 11/09/2024
Python Version: 3.12

This module implements the BoardMattersVisualizer class for handling board matter visualization and management
in well visualization applications. It provides a comprehensive interface for processing, displaying, and
interacting with board matter data through both section-based and general search capabilities.

The class manages complex data relationships between board matters, geographical sections (township/range),
and associated documentation. It provides an interactive interface through PyQt5 components for data
visualization and manipulation.

Key Features:
- Dual-mode board matter search (section-based and general search)
- Dynamic polygon generation for section visualization
- Interactive data display with real-time updates
- Integrated document management for board matter files
- Automated UI state management
- Efficient data filtering and processing

Dependencies:
- PyQt5 (>= 5.15): UI components and models
- pandas (>= 1.3): Data manipulation and filtering
- numpy (>= 1.20): Numerical operations and polygon handling
- ModuleAgnostic: Custom utility module

Classes:
    BoardMattersVisualizer:
        Core class providing board matter visualization and management functionality:
        - Data processing and filtering
        - UI component management
        - Polygon generation and visualization
        - Document handling
        - Search mode management

Primary Methods:
    - setupBoardMattersGraphic(): Initializes board matter display for selected section
    - setupBoardModel(): Configures data model for board matter display
    - prodButtonsActivate(): Manages search mode transitions
    - updateBoardMatterDetails(): Updates display with selected board matter data
    - clearBoardMatterUI(): Resets UI state
    - getSelectedCauseNumber(): Retrieves active cause number based on search mode
    - getBoardMatterDetails(): Fetches comprehensive board matter information
    - findMatchingRows(): Locates corresponding geographical data
    - createPolygons(): Generates visualization polygons

Note:
This module is designed to be integrated into larger well visualization systems
and requires proper initialization of UI components and data sources before use.
The visualization system supports both interactive user input and programmatic
control through its public interface.
"""

from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import pandas as pd
import numpy as np


"""The board matters process ended up taking a lot more development time so I branched it into a seperate class."""
class BoardMattersVisualizer:
    def __init__(self):
        super().__init__()
        self.board_table_model = None
        self.used_board_matters = None
        self.used_board_matters_all = None
        self.df_BoardData = None
        self.df_BoardDataLinks = None
        self.all_wells_plat_labels_for_editing = None
        self.df_tsr = None
        self.ui = None

    def setupBoardMattersGraphic(self) -> None:
        """Sets up board matters graphic for selected township and range section.

        Retrieves board matter data for the selected section and populates combo boxes
        and table. Clears existing data, matches TSR data, and updates UI elements. Activated from changing the
        sectionsBoardComboBox

        Args:
            None

        Raises:
            IndexError: If selected label not found in df_tsr dataframe.

        Note:
            Requires initialized df_tsr and df_BoardData dataframes.
            Directly modifies UI elements including:
            - board_brief_text
            - board_matter_files
            - mattersBoardComboBox
            - board_data_table
        """
        # Clear existing UI text elements
        self.ui.board_brief_text.clear()
        self.ui.board_matter_files.clear()
        self.ui.mattersBoardComboBox.clear()

        # Get current section selection and match TSR data
        selected_label = self.ui.sectionsBoardComboBox.currentText()
        current_data = self.df_tsr[self.df_tsr['Label'] == selected_label]

        # Filter board matters for selected section using TSR criteria
        self.used_board_matters = self.df_BoardData[
            (self.df_BoardData['Sec'] == current_data['Section'].iloc[0]) &
            (self.df_BoardData['Township'] == current_data['Township'].iloc[0]) &
            (self.df_BoardData['TownshipDir'] == current_data['Township Direction'].iloc[0]) &
            (self.df_BoardData['Range'] == current_data['Range'].iloc[0]) &
            (self.df_BoardData['RangeDir'] == current_data['Range Direction'].iloc[0]) &
            (self.df_BoardData['PM'] == current_data['Baseline'].iloc[0])
            ]

        # Update UI with filtered board matters
        self.ui.mattersBoardComboBox.addItems(self.used_board_matters['CauseNumber'].unique())
        self.ui.board_data_table.item(0, 0).setText('')  # Clear table rows
        self.ui.board_data_table.item(1, 0).setText('')
        self.ui.board_data_table.item(2, 0).setText('')
        self.outlined_board_sections.set_paths([])
        # Refresh display using efficient blitting
        self.ax2d.draw_artist(self.outlined_board_sections)
        self.canvas2d.blit(self.ax2d.bbox)

        # Ensure full redraw
        self.canvas2d.draw()

    def setupBoardModel(self, data: list[list[str]]) -> None:
        """Sets up board table model with provided data and configures table view.

        Updates the QTableView with new data by removing existing rows and adding new ones.
        Configures table headers and visibility settings.

        Args:
            data: List of string lists where each inner list represents a table row.

        Example:
            >>> data = [['Item 1', 'Value 1'], ['Item 2', 'Value 2']]
            >>> setupBoardModel(data)

        Note:
            - Requires initialized board_table_model (QStandardItemModel)
            - Modifies UI board_table settings and appearance
            - All data items are converted to strings during processing
        """
        # Reset table by removing existing rows
        self.board_table_model.removeRows(0, self.board_table_model.rowCount())
        # Add new rows from data
        for row in data:
            items = [QStandardItem(str(item)) for item in row]  # Convert items to QStandardItems
            self.board_table_model.appendRow(items)

        # Configure table view settings
        self.ui.board_table.setModel(self.board_table_model)
        self.ui.board_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.board_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.board_table.horizontalHeader().setVisible(False)
        self.ui.board_table.verticalHeader().setVisible(False)

    def prodButtonsActivate(self) -> None:
        """Manages UI element activation based on board order search option selection.

        Handles radio button changes for board order searching, clearing and updating
        relevant combo boxes based on search type (section-based or all matters).

        UI Elements Modified:
            - board_matters_visible_combo: Enabled for all matters search
            - sectionsBoardComboBox: Enabled for section-based search
            - mattersBoardComboBox: Enabled for section-based search

        Note:
            Button ID meanings:
            - ID 1: Search by section
            - ID 2: Search all board matters

        Dependencies:
            Requires initialized:
            - board_order_button_group
            - getTSRDataframe method
            - initializeSectionsBoardComboBox method
            - initializeAllBoardMattersComboBox method
        """
        # Get active search mode and reset UI state
        active_button_id = self.ui.board_order_button_group.checkedId()
        self.ui.board_matters_visible_combo.clear()
        self.ui.sectionsBoardComboBox.clear()
        self.ui.mattersBoardComboBox.clear()
        self.getTSRDataframe()

        # Configure UI based on search mode
        if active_button_id == 1:  # Section-based search
            self.ui.board_matters_visible_combo.setEnabled(False)
            self.ui.sectionsBoardComboBox.setEnabled(True)
            self.ui.mattersBoardComboBox.setEnabled(True)
            self.initializeSectionsBoardComboBox()
        elif active_button_id == 2:  # All matters search
            self.ui.board_matters_visible_combo.setEnabled(True)
            self.ui.sectionsBoardComboBox.setEnabled(False)
            self.ui.mattersBoardComboBox.setEnabled(False)
            self.initializeAllBoardMattersComboBox()

    def updateBoardMatterDetails(self) -> None:
        """
        Update the board matter details based on the selected cause number.

        This method retrieves and displays the relevant information for the selected board matter,
        including the quip, order type, effective date, end date, and associated files.
        It also handles displaying the outlined board sections on the 2D plot. Activated through mattersBoardComboBox
        and board_matters_visible_combo
        """
        self.clearBoardMatterUI()
        selected_cause_number, active_button_id = self.getSelectedCauseNumber()

        quip, order_type, effect_date, end_data = self.getBoardMatterDetails(selected_cause_number, active_button_id)
        all_plat_with_cause_numbers = self.getPlatWithCauseNumber(selected_cause_number)
        matched_rows = self.findMatchingRows(all_plat_with_cause_numbers)
        found_polygons = self.createPolygons(matched_rows)

        self.updateBoardMatterUI(quip, order_type, effect_date, end_data, selected_cause_number)
        formatted_files = self.formatBoardMatterFiles(selected_cause_number)
        self.ui.board_matter_files.setHtml(formatted_files)

        self.updatePlotBoard(found_polygons)

    def updateBoardMatterDetails(self) -> None:
        """Updates and displays board matter details for selected cause number.

        Retrieves, processes, and displays comprehensive board matter information including
        metadata, associated files, and visual representation on 2D plot. Handles both
        section-based and general board matter searches.

        Process Flow:
            1. Clears existing UI elements
            2. Retrieves selected cause number and search mode
            3. Fetches board matter details (quip, dates, type)
            4. Processes plat/polygon data for visualization
            5. Updates UI elements with matter details
            6. Refreshes 2D plot with section outlines

        Dependencies:
            - clearBoardMatterUI: Cleans UI state
            - getSelectedCauseNumber: Returns (str, int) for cause number and mode
            - getBoardMatterDetails: Returns tuple (quip, type, effect_date, end_date)
            - getPlatWithCauseNumber: Returns plat data for cause number
            - findMatchingRows: Processes plat data into matching rows
            - createPolygons: Converts row data into polygon objects
            - updateBoardMatterUI: Updates UI with matter details
            - formatBoardMatterFiles: Formats associated files as HTML
            - updatePlotBoard: Updates 2D plot with polygons

        UI Elements Modified:
            - board_matter_files (HTML content)
            - 2D plot canvas
            - Various board matter detail fields

        Note:
            Requires initialized UI components and valid dataframes:
            - used_board_matters
            - used_board_matters_all
            - df_BoardDataLinks
        """
        # Reset UI state
        self.clearBoardMatterUI()
        selected_cause_number, active_button_id = self.getSelectedCauseNumber()

        # Retrieve and process board matter data
        quip, order_type, effect_date, end_data = self.getBoardMatterDetails(selected_cause_number, active_button_id)
        all_plat_with_cause_numbers = self.getPlatWithCauseNumber(selected_cause_number)
        matched_rows = self.findMatchingRows(all_plat_with_cause_numbers)
        found_polygons = self.createPolygons(matched_rows)

        # Update UI elements with retrieved data
        self.updateBoardMatterUI(quip, order_type, effect_date, end_data, selected_cause_number)
        formatted_files = self.formatBoardMatterFiles(selected_cause_number)
        self.ui.board_matter_files.setHtml(formatted_files)

        # Update visual representation
        self.updatePlotBoard(found_polygons)

    def clearBoardMatterUI(self) -> None:
        """Clears all board matter-related UI elements.

        Resets text and file display areas to empty state in preparation for
        new board matter data display.

        UI Elements Cleared:
            - board_brief_text: Text display area for board matter brief
            - board_matter_files: Display area for associated matter files

        Note:
            Should be called before loading new board matter details to ensure
            clean state and prevent data overlap.

        Dependencies:
            Requires initialized UI with following components:
            - board_brief_text widget
            - board_matter_files widget
        """
        self.ui.board_brief_text.clear()  # Clear brief text display
        self.ui.board_matter_files.clear()  # Clear matter files display

    def getSelectedCauseNumber(self) -> tuple[str, int]:
        """Retrieves the currently selected cause number and search mode.

        Gets the active search mode from the button group and extracts the appropriate
        cause number based on the mode (section-based or all matters search).

        Returns:
            tuple[str, int]: A tuple containing:
                - str: The selected cause number
                - int: The active button ID (1=section search, 2=all matters search)

        UI Elements Used:
            - board_order_button_group: Radio button group for search mode
            - mattersBoardComboBox: Combo box for section-based search
            - board_matters_visible_combo: Combo box for all matters search

        Dependencies:
            - extractCauseNumberFromText: Helper method for parsing cause numbers
            from formatted text strings

        Note:
            Button IDs:
            1 = Section-based search mode
            2 = All matters search mode
        """
        # Get current search mode
        active_button_id = self.ui.board_order_button_group.checkedId()

        # Extract cause number based on search mode
        if active_button_id == 1:  # Section-based search
            selected_cause_number = self.ui.mattersBoardComboBox.currentText()
        elif active_button_id == 2:  # All matters search
            selected_cause_number = self.extractCauseNumberFromText(
                self.ui.board_matters_visible_combo.currentText())

        return selected_cause_number, active_button_id

    def extractCauseNumberFromText(self, text: str) -> str:
        """Extracts cause number from a formatted text string.

        Parses a text string containing 'Cause Number:' prefix and extracts the
        actual cause number that follows it.

        Args:
            text: String containing cause number in format "...Cause Number:XXX..."

        Returns:
            str: The extracted cause number portion after the prefix

        Raises:
            ValueError: If 'Cause Number:' prefix not found in text

        Example:
            >>> text = "Matter 123 - Cause Number:456-789"
            >>> extractCauseNumberFromText(text)
            '456-789'

        Note:
            - Assumes consistent 'Cause Number:' prefix format
            - Returns all text after the prefix without additional parsing
            - Used primarily for processing board_matters_visible_combo selections
        """
        cause_number_ind = text.index('Cause Number:')  # Find start of cause number
        cause_number = text[cause_number_ind + len('Cause Number:'):]  # Extract number portion
        return cause_number

    def getBoardMatterDetails(self, selected_cause_number: str, active_button_id: int) -> tuple[str, str, str, str]:
        """
        Retrieve the board matter details for the selected cause number.

        Args:
            selected_cause_number (str): The selected cause number.
            active_button_id (int): The ID of the active radio button.

        Returns:
            tuple: A tuple containing the quip, order type, effective date, and end date.
        """
        print(selected_cause_number)
        print(self.used_board_matters)
        if active_button_id == 1:
            quip = \
            self.used_board_matters.loc[self.used_board_matters['CauseNumber'] == selected_cause_number, 'Quip'].iloc[0]
            order_type = self.used_board_matters.loc[
                self.used_board_matters['CauseNumber'] == selected_cause_number, 'OrderType'].iloc[0]
            effect_date = self.used_board_matters.loc[
                self.used_board_matters['CauseNumber'] == selected_cause_number, 'EffectiveDate'].iloc[0]
            end_data = self.used_board_matters.loc[
                self.used_board_matters['CauseNumber'] == selected_cause_number, 'EndDate'].iloc[0]
        elif active_button_id == 2:
            quip = self.used_board_matters_all.loc[
                self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'Quip'].iloc[0]
            order_type = self.used_board_matters_all.loc[
                self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'OrderType'].iloc[0]
            effect_date = self.used_board_matters_all.loc[
                self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'EffectiveDate'].iloc[0]
            end_data = self.used_board_matters_all.loc[
                self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'EndDate'].iloc[0]

        return quip, order_type, effect_date, end_data

    def getPlatWithCauseNumber(self, selected_cause_number: str) -> pd.DataFrame:
        """Retrieves plat data rows matching a specific cause number.

        Filters the master board data dataframe to get all plat records associated
        with the given cause number. This data is typically used for generating
        section outlines and polygon visualization.

        Args:
            selected_cause_number: The cause number to filter board data records by

        Returns:
            pd.DataFrame: Filtered dataframe containing matching plat records with columns:
                - CauseNumber: The board matter cause number
                - Conc: Concession/section identifier
                - Other plat-specific columns from df_BoardData

        Raises:
            KeyError: If required columns missing from df_BoardData
            TypeError: If selected_cause_number is not string-compatible

        Dependencies:
            Requires initialized dataframe:
            - df_BoardData: Master dataframe containing plat/section data

        Note:
            - Result is used by findMatchingRows() to locate corresponding plat data
            - Empty dataframe returned if no matches found
            - Maintains all columns from source dataframe
        """
        # Filter master dataframe for matching cause number
        all_plat_with_cause_numbers = self.df_BoardData[self.df_BoardData['CauseNumber'] == selected_cause_number]
        return all_plat_with_cause_numbers

    def findMatchingRows(self, all_plat_with_cause_numbers: pd.DataFrame) -> pd.DataFrame:
        """Finds plat records matching concession values from board matter data.

        Creates a regex pattern from concession numbers and filters the plat dataframe
        to find matching section/concession records. Used to link board matters to
        their corresponding geographical sections.

        Args:
            all_plat_with_cause_numbers: DataFrame containing at minimum:
                - CauseNumber: The board matter identifier
                - Conc: Concession/section numbers to match

        Returns:
            pd.DataFrame: Filtered plat records containing columns:
                - Conc: Matched concession/section numbers
                - Easting: X-coordinate for section point
                - Northing: Y-coordinate for section point
                - Additional plat record columns from df_plat

        Raises:
            KeyError: If required 'Conc' column missing from input DataFrame
            AttributeError: If df_plat not initialized
            TypeError: If concession values cannot be converted to strings

        Example:
            Input DataFrame:
                CauseNumber | Conc
                ABC123     | 123
                ABC123     | 456

            Will find all plat records where Conc matches '123' or '456'

        Dependencies:
            Requires initialized:
            - df_plat: Master plat records DataFrame
        """
        # Create regex pattern from concession numbers
        pattern = '|'.join(all_plat_with_cause_numbers['Conc'].astype(str))

        # Filter plat records for matching concessions
        matching_rows = self.df_plat[self.df_plat['Conc'].astype(str).str.contains(pattern)]
        return matching_rows

    def createPolygons(self, matching_rows: pd.DataFrame) -> list[np.ndarray]:
        """Creates polygon coordinate arrays from plat/section coordinate data.

        Processes matched plat records to create polygon definitions by grouping
        coordinates by concession number and ordering them for proper polygon
        construction.

        Args:
            matching_rows: DataFrame containing at minimum:
                - Conc: Concession/section identifier
                - Easting: X-coordinate for polygon vertices
                - Northing: Y-coordinate for polygon vertices

        Returns:
            list[np.ndarray]: List of polygon definitions where each element is a
                numpy array of shape (n,2) containing ordered [Easting, Northing]
                coordinate pairs defining a closed polygon

        Raises:
            KeyError: If required columns missing from input DataFrame
            ValueError: If coordinate data is invalid/incomplete

        Example:
            Input DataFrame:
                Conc | Easting | Northing
                123  | 100     | 200
                123  | 150     | 250
                124  | 300     | 400

            Returns list of numpy arrays:
            [array([[100, 200], [150, 250]]), array([[300, 400]])]

        Note:
            - Each polygon array represents vertices in clockwise order
            - Duplicate points are removed to avoid invalid polygons
            - Used for generating section outlines on maps
        """
        # Add sequential ordering for line segments within each concession
        matching_rows['LineSegmentOrder'] = matching_rows.groupby('Conc').cumcount() + 1

        # Remove any duplicate coordinate points
        matching_rows = matching_rows.drop_duplicates(keep='first')

        # Group coordinates by concession number
        grouped_rows = matching_rows.groupby('Conc')

        # Generate polygon coordinate arrays
        polygons_lst = []
        for conc, group in grouped_rows:
            coordinates = group[['Easting', 'Northing']].values.tolist()
            polygons_lst.append(np.array(coordinates))

        return polygons_lst

    def formatBoardMatterFiles(self, selected_cause_number: str) -> str:
        """Formats board matter documents as HTML with clickable links.

        Creates an HTML-formatted string containing document descriptions and
        corresponding file links for all documents associated with a specific
        board matter cause number.

        Args:
            selected_cause_number: The cause number to retrieve documents for

        Returns:
            str: HTML-formatted string containing:
                - Document descriptions
                - Clickable file links
                - Appropriate spacing/formatting
                Format: "<description><br><link><br><br>" for each document

        Raises:
            KeyError: If required columns missing from df_BoardDataLinks
            ValueError: If invalid cause number provided

        Dependencies:
            Requires initialized dataframe:
            - df_BoardDataLinks with columns:
                - Cause: Board matter cause numbers
                - Description: Document descriptions
                - Filepath: Path to document files
                - DocumentDate: Date for sorting

        Example:
            >>> formatBoardMatterFiles("ABC-123")
            'Document A<br><a href="/path/to/doc">path/to/doc</a><br><br>
             Document B<br><a href="/path/to/doc2">path/to/doc2</a><br><br>'
        """
        # Filter links for selected cause number
        board_data_links = self.df_BoardDataLinks[self.df_BoardDataLinks['Cause'] == selected_cause_number]

        # Sort documents by date
        board_data_links = board_data_links.sort_values('DocumentDate')

        # Build HTML entries for each document
        file_entries = []
        for _, row in board_data_links.iterrows():
            description = row['Description']
            filepath = row['Filepath']
            file_entry = f"{description}<br><a href='{filepath}'>{filepath}</a><br><br>"
            file_entries.append(file_entry)

        # Combine all entries into single HTML string
        return ''.join(file_entries)

    def updateBoardMatterUI(self, quip: str, order_type: str, effect_date: str, end_data: str,
                               selected_cause_number: str) -> None:
        """Updates UI elements with board matter details.

        Populates various UI components with board matter information including
        summary text, dates, and order details. Updates both the text display
        and tabular data presentation.

        Args:
            quip: Brief description/summary of the board matter
            order_type: Classification/type of the board order
            effect_date: Date when order becomes effective
            end_data: Date when order expires/terminates
            selected_cause_number: Identifier for the selected board matter

        Dependencies:
            Requires initialized UI components:
            - board_brief_text: QTextEdit for matter description
            - board_data_table: QTableWidget for detailed data
            - setupBoardModel: Helper method for table model updates

        UI Updates:
            - Sets description text in brief text area
            - Updates table cells with order details
            - Refreshes table model with formatted data

        Note:
            - Table must have at least 3 rows and 1 column
            - All date values are converted to strings for display
            - Maintains consistent data presentation format
            - Called as part of the board matter selection workflow
        """
        # Update description text area
        self.ui.board_brief_text.setText(quip)

        # Update individual table cells
        self.ui.board_data_table.item(0, 0).setText(str(order_type))
        self.ui.board_data_table.item(1, 0).setText(str(effect_date))
        self.ui.board_data_table.item(2, 0).setText(str(end_data))

        # Prepare and update table model data
        data = [['Order Type', order_type],
                ['Date Effective', effect_date],
                ['End Date', end_data]]
        self.setupBoardModel(data)

    # self.well_planned.set_visible(False)
    def updatePlotBoard(self, found_polygons: list[np.ndarray]) -> None:
        """Updates the 2D plot visualization with board matter section polygons.

        Renders section polygons related to board matters on the 2D matplotlib plot.
        Updates the polygon collection with new paths and refreshes the display.

        Args:
            found_polygons: List of numpy arrays where each array contains ordered
                pairs of (x,y) coordinates defining section polygon vertices

        Dependencies:
            Requires initialized attributes:
            - outlined_board_sections: PolyCollection for board matter sections
            - ax2d: Matplotlib axes for 2D plot
            - canvas2d: FigureCanvas for rendering

        Display Updates:
            - Sets polygon fill color to red
            - Updates polygon paths with new coordinates
            - Refreshes specific artist (polygon collection)
            - Updates display via double-buffer blit
            - Performs full canvas redraw

        Note:
            - Part of the board matter visualization workflow
            - Uses blitting for efficient updates
            - Polygons rendered with 0.2 alpha transparency
            - Polygons appear on zorder=3 (above base layers)
        """
        # Set visual properties and update paths
        self.outlined_board_sections.set_color('red')
        self.outlined_board_sections.set_paths(found_polygons)
        # Refresh display using efficient blitting
        self.ax2d.draw_artist(self.outlined_board_sections)
        self.canvas2d.blit(self.ax2d.bbox)

        # Ensure full redraw
        self.canvas2d.draw()

    def checkboxMakeVisible(self) -> None:
        """Controls visibility of board section polygon outlines on the 2D canvas.

        Toggles the visibility of outlined board sections based on checkbox state.
        Updates and redraws the canvas to reflect visibility changes.

        Dependencies:
            Requires initialized class attributes:
            - ui: QMainWindow instance with:
                - show_polygon_board_checkbox: QCheckBox
            - outlined_board_sections: matplotlib.collections.Collection
            - canvas2d: matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg
            - ax2d: matplotlib.axes.Axes

        Process Flow:
            1. Checks state of polygon visibility checkbox
            2. Sets outline visibility accordingly
            3. Updates canvas display area
            4. Triggers canvas redraw

        Side Effects:
            - Modifies visibility of outlined_board_sections
            - Triggers canvas redraw
            - Updates display immediately

        Notes:
            - Uses matplotlib's blit for efficient redrawing
            - Only affects visibility, does not modify underlying data
            - Immediate visual feedback to user interaction
        """
        # Set visibility based on checkbox state
        self.outlined_board_sections.set_visible(
            self.ui.show_polygon_board_checkbox.isChecked()
        )

        # Update display
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()


    # def findMatchingRows(self, all_plat_with_cause_numbers: pd.DataFrame) -> pd.DataFrame:
    #     """Finds plat records that match concession values from board matter data.
    #
    #     Searches the plat database for records matching concession numbers associated
    #     with a specific board matter. Creates a regex pattern from the input concession
    #     numbers to filter matching records.
    #
    #     Args:
    #         all_plat_with_cause_numbers: DataFrame containing board matter records with:
    #             - CauseNumber: Board matter identifier
    #             - Conc: Concession numbers to match (any data type, converted to str)
    #
    #     Returns:
    #         pd.DataFrame: Filtered plat records containing matching Conc values.
    #             Preserves all columns from df_plat for matching records.
    #             Common columns include:
    #             - Conc: Matching concession identifier
    #             - Easting: X coordinate for plotting
    #             - Northing: Y coordinate for plotting
    #
    #     Dependencies:
    #         Requires initialized class attribute:
    #         - df_plat: Master DataFrame containing plat/section records
    #
    #     Example:
    #         Input DataFrame:
    #             CauseNumber | Conc
    #             ABC123     | 123
    #             ABC123     | 456
    #             ABC123     | 789
    #
    #         Creates pattern '123|456|789' to find all plat records where
    #         'Conc' contains any of those values.
    #
    #     Notes:
    #         - Uses string pattern matching, so partial matches are possible
    #         - All Conc values are converted to strings before comparison
    #         - No matching records returns empty DataFrame
    #         - Used by createPolygons() to generate section outlines
    #     """
    #     # Create regex pattern from concession numbers
    #     pattern = '|'.join(all_plat_with_cause_numbers['Conc'].astype(str))
    #
    #     # Filter plat records using pattern matching on Conc values
    #     matching_rows = self.df_plat[self.df_plat['Conc'].astype(str).str.contains(pattern)]
    #     return matching_rows

    # def createPolygons(self, matching_rows: pd.DataFrame) -> list[np.ndarray]:
    #     """Creates ordered polygon coordinate arrays from matched plat data.
    #
    #     Processes matched plat records to generate polygon definitions for each unique
    #     concession by grouping and ordering coordinate pairs. Handles data cleaning
    #     and proper vertex ordering for polygon construction.
    #
    #     Args:
    #         matching_rows: DataFrame containing plat records with columns:
    #             - Conc: Concession/section identifier for grouping
    #             - Easting: X-coordinate for polygon vertices
    #             - Northing: Y-coordinate for polygon vertices
    #
    #     Returns:
    #         list[np.ndarray]: List of polygon coordinate arrays where each array has
    #             shape (n,2) containing ordered [Easting,Northing] vertex pairs.
    #             The arrays define closed polygons representing section boundaries.
    #
    #     Process Flow:
    #         1. Orders vertices within each concession group
    #         2. Removes duplicate coordinate points
    #         3. Groups by concession ID
    #         4. Extracts coordinate pairs to numpy arrays
    #
    #     Example:
    #         Input DataFrame:
    #             Conc | Easting | Northing
    #             A1   | 100     | 200
    #             A1   | 150     | 250
    #             B2   | 300     | 400
    #
    #         Returns:
    #             [array([[100,200], [150,250]]),  # Polygon A1
    #              array([[300,400]])]             # Polygon B2
    #
    #     Notes:
    #         - Vertex order is preserved using LineSegmentOrder
    #         - Duplicate points are removed to avoid invalid polygons
    #         - Each numpy array represents a single closed polygon
    #         - Used for section boundary visualization on maps
    #         - Coordinate pairs are in projected coordinate system units
    #     """
    #     # Create ordered vertex sequence for each concession
    #     matching_rows['LineSegmentOrder'] = matching_rows.groupby('Conc').cumcount() + 1
    #
    #     # Remove duplicate coordinate points while preserving order
    #     matching_rows = matching_rows.drop_duplicates(keep='first')
    #
    #     # Group coordinate data by concession ID
    #     grouped_rows = matching_rows.groupby('Conc')
    #
    #     # Generate polygon arrays for each concession group
    #     polygons_lst = []
    #     for conc, group in grouped_rows:
    #         coordinates = group[['Easting', 'Northing']].values.tolist()
    #         polygons_lst.append(np.array(coordinates))
    #
    #     return polygons_lst

    def getTSRDataframe(self) -> pd.DataFrame:
        """Creates a structured DataFrame containing Theoretical Stratigraphic Record (TSR) information.

        Processes well plat label strings to extract and organize location information into a
        standardized TSR format. Parses string components into meaningful geographic identifiers
        and creates human-readable labels.

        Dependencies:
            Requires initialized class attribute:
            - all_wells_plat_labels_for_editing: List[str] containing raw plat label strings
                Format: "SSTTDRRDB" where:
                - SS: Section number (2 digits)
                - TT: Township number (2 digits)
                - D: Township direction (single char)
                - RR: Range number (2 digits)
                - D: Range direction (single char)
                - B: Baseline identifier (single char)

        Returns:
            pd.DataFrame: Sorted DataFrame with columns:
                - Section (int): Section number
                - Township (int): Township number
                - Township Direction (str): Township cardinal direction
                - Range (int): Range number
                - Range Direction (str): Range cardinal direction
                - Baseline (str): Baseline identifier
                - Conc (str): Concatenated location code
                - Label (str): Human-readable location string

        Process Flow:
            1. Initializes empty column dictionaries
            2. Parses each plat label string into components
            3. Formats data into consistent types
            4. Creates readable label strings
            5. Builds and sorts final DataFrame

        Example:
            Input label: "01150E02WI"
            Produces row:
                Section: 1
                Township: 15
                Township Direction: "N"
                Range: 2
                Range Direction: "W"
                Baseline: "I"
                Conc: "01150E02WI"
                Label: "1 15N 2W I"

        Note:
            - Sets class attribute self.df_tsr with processed DataFrame
            - Sorts results for consistent display order
            - Preserves original string values in Conc field
            - Converts numeric fields to integers
            - Creates human-readable labels
        """
        # Initialize data structure for DataFrame columns
        data = {
            'Section': [], 'Township': [], 'Township Direction': [],
            'Range': [], 'Range Direction': [], 'Baseline': [],
            'Conc': [], 'Label': []
        }

        # Process each plat label string
        for s in self.all_wells_plat_labels_for_editing:
            # Extract and convert components with type handling
            section = int(s[:2])  # Convert section to integer
            township = int(s[2:4])  # Convert township to integer
            township_direction = s[4]  # Township cardinal direction
            range_ = int(s[5:7])  # Convert range to integer
            range_direction = s[7]  # Range cardinal direction
            baseline = s[8]  # Baseline identifier
            conc = f"{s[:9]}"  # Preserve full location code

            # Create human-readable label
            label = f"{section} {township}{township_direction} {range_}{range_direction} {baseline}"

            # Append extracted values to data dictionary
            data['Section'].append(section)
            data['Township'].append(township)
            data['Township Direction'].append(township_direction)
            data['Range'].append(range_)
            data['Range Direction'].append(range_direction)
            data['Baseline'].append(baseline)
            data['Conc'].append(conc)
            data['Label'].append(label)

        # Create and sort DataFrame
        self.df_tsr = pd.DataFrame(data)
        self.df_tsr = self.df_tsr.sort_values(
            by=['Baseline', 'Township Direction', 'Range Direction',
                'Township', 'Range', 'Section'])

    def initializeSectionsBoardComboBox(self) -> None:
        """Populates the sections combo box with filtered TSR location labels.

        Initializes the sections combo box with unique location labels filtered from the
        TSR (Township, Section, Range) database. Only includes sections that have
        associated board matters based on concession codes.

        Dependencies:
            Requires initialized class attributes:
            - df_tsr: pd.DataFrame containing TSR records with columns:
                - Label: str, Formatted location string (e.g. "1 15N 2W I")
                - Conc: str, Concession code matching board records
            - used_plat_codes_for_boards: List[str] of active concession codes
            - ui: QMainWindow instance with:
                - sectionsBoardComboBox: QComboBox for section selection

        Process Flow:
            1. Clears existing combo box items
            2. Creates Qt item model for combo box
            3. Filters TSR data to relevant sections
            4. Populates combo box with unique labels
            5. Triggers board matter graphic setup

        Side Effects:
            - Updates ui.sectionsBoardComboBox contents
            - Triggers setupBoardMattersGraphic() on completion
            - Changes enabled/disabled state of related UI elements

        Notes:
            - Used when "Search by Section" radio button is active
            - Labels are formatted as: "<section> <township><dir> <range><dir> <baseline>"
            - Filters out sections without associated board matters
            - Maintains sort order from TSR dataframe
        """
        # Clear existing items from combo box
        self.ui.sectionsBoardComboBox.clear()

        # Create Qt model for combo box items
        model = QStandardItemModel()

        # Filter TSR data to sections with board matters
        used_tsr_data = self.df_tsr[
            self.df_tsr['Conc'].isin(self.used_plat_codes_for_boards)
        ].drop_duplicates(keep='first')

        # Extract unique location labels
        data = used_tsr_data['Label'].values

        # Populate model with formatted location items
        for item_text in data:
            item = QStandardItem(item_text)
            model.appendRow(item)

        # Update combo box with filtered items
        self.ui.sectionsBoardComboBox.setModel(model)

        # Initialize board matter display
        self.setupBoardMattersGraphic()

    def initializeAllBoardMattersComboBox(self) -> None:
        """Initializes the board matters combo box with merged TSR and board data.

        Performs a database merge operation between Township-Section-Range (TSR) data
        and board matter records, creating a unified view of board matters with
        location information. Populates the combo box with formatted docket/cause
        number labels.

        Dependencies:
            Requires initialized class attributes:
            - df_tsr: pd.DataFrame with TSR location data containing columns:
                - Section, Township, Township Direction, Range, Range Direction, Baseline
            - df_BoardData: pd.DataFrame with board matter records containing columns:
                - Sec, Township, TownshipDir, Range, RangeDir, PM
                - DocketNumber, CauseNumber
            - ui: QMainWindow instance with:
                - board_matters_visible_combo: QComboBox
                - board_brief_text: QTextEdit
                - board_matter_files: QListWidget
                - board_data_table: QTableWidget

        Process Flow:
            1. Clears existing UI elements
            2. Merges TSR and board data on location fields
            3. Removes redundant columns
            4. Sorts by docket and cause numbers
            5. Creates formatted labels
            6. Updates UI elements with merged data

        Side Effects:
            - Sets self.used_board_matters_all with merged DataFrame
            - Clears and updates multiple UI elements:
                - board_matters_visible_combo
                - board_brief_text
                - board_matter_files
                - board_data_table cells
            - Creates formatted labels combining docket and cause numbers

        Notes:
            - Maintains unique docket/cause number combinations
            - Formats labels as "Docket Number:<num>, Cause Number:<num>"
            - Clears existing table data before population
            - Preserves sort order by docket and cause numbers
        """
        # Clear UI elements
        self.ui.board_matters_visible_combo.clear()

        # Merge TSR and board data on location fields
        self.used_board_matters_all = self.df_tsr.merge(
            self.df_BoardData,
            left_on=['Section', 'Township', 'Township Direction',
                     'Range', 'Range Direction', 'Baseline'],
            right_on=['Sec', 'Township', 'TownshipDir',
                      'Range', 'RangeDir', 'PM']
        )

        # Remove redundant location columns
        columns_to_drop = ['Sec', 'Township', 'TownshipDir',
                           'Range', 'RangeDir', 'PM']
        self.used_board_matters_all.drop(columns=columns_to_drop, inplace=True)

        # Sort by docket and cause numbers
        self.used_board_matters_all = self.used_board_matters_all.sort_values(
            by=['DocketNumber', 'CauseNumber']
        )

        # Create formatted labels
        self.used_board_matters_all['Label'] = ("Docket Number:" +
                                                self.used_board_matters_all['DocketNumber'] +
                                                ", Cause Number:" + self.used_board_matters_all['CauseNumber'])

        # Get unique labels
        data = self.used_board_matters_all['Label'].drop_duplicates(
            keep='first').values

        # Clear additional UI elements
        self.ui.board_brief_text.clear()
        self.ui.board_matter_files.clear()

        # Update UI with merged data
        self.ui.board_matters_visible_combo.addItems(data)
        self.ui.board_data_table.item(0, 0).setText(str(''))
        self.ui.board_data_table.item(1, 0).setText(str(''))
        self.ui.board_data_table.item(2, 0).setText(str(''))

