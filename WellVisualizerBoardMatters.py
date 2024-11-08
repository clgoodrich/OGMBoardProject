"""
WellVisualizerBoardMatters
Author: Colton Goodrich
Date: 8/31/2024

This module defines the BoardMattersVisualizer class, which handles the board matter-related functionality
for the well visualization application. It provides methods for setting up the board matter graphic,
updating board matter details, initializing combo boxes, and managing the display of relevant data
based on user selections.

The class interacts with various data sources, including dataframes for board data, links, and township/range
sections. It also interfaces with the main application's user interface (UI) components, such as combo boxes
and tables, to display and manipulate board matter-related information.

Dependencies:
- PyQt5
- pandas
- numpy
- ModuleAgnostic (custom module)

Classes:
    BoardMattersVisualizer:
        - Handles board matter-related data processing and visualization.
        - Provides methods for setting up the board matter graphic, updating board matter details,
          initializing combo boxes, and managing the display of relevant data.
        - Interacts with the main application's user interface (UI) components.

Functions:
    - setupBoardMattersGraphic()
    - setupBoardModel()
    - prodButtonsActivate()
    - updateBoardMatterDetails()
    - find_matching_rows()
    - create_polygons()
    - getTSRDataframe()
    - initializeSectionsBoardComboBox()
    - initializeAllBoardMattersComboBox()
"""

from PyQt5.QtWidgets import QApplication, QTableView, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import pandas as pd
import numpy as np

import ModuleAgnostic

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
        """
        Set up the board matters graphic based on the selected township and range section.

        This method retrieves the relevant board matter data for the selected section
        and populates the corresponding combo boxes and table. It performs the following steps:

        1. Clear the text boxes for brief text and matter files.
        2. Retrieve the currently selected label (township and range section) from the combo box.
        3. Get the TSR (Township, Section, Range) data for the selected label.
        4. Isolate the used board matters for the selected section from the `df_BoardData` dataframe.
        5. Add the board matter items to the second combo box (`mattersBoardComboBox`).
        6. Clear the board data table.

        This method does not return any value.

        Raises:
            IndexError: If the selected label is not found in the `df_tsr` dataframe.
        """
        # Clear the text boxes
        self.ui.board_brief_text.clear()
        self.ui.board_matter_files.clear()

        # Retrieve the combobox current data (township and range section)
        selected_label = self.ui.sectionsBoardComboBox.currentText()

        # Get the TSR data for that section
        current_data = self.df_tsr[self.df_tsr['Label'] == selected_label]

        # Isolate out the used board matters for *that* section
        self.used_board_matters = self.df_BoardData[
            (self.df_BoardData['Sec'] == current_data['Section'].iloc[0]) &
            (self.df_BoardData['Township'] == current_data['Township'].iloc[0]) &
            (self.df_BoardData['TownshipDir'] == current_data['Township Direction'].iloc[0]) &
            (self.df_BoardData['Range'] == current_data['Range'].iloc[0]) &
            (self.df_BoardData['RangeDir'] == current_data['Range Direction'].iloc[0]) &
            (self.df_BoardData['PM'] == current_data['Baseline'].iloc[0])
            ]

        # Add those board items to the 2nd combo box and fill the table
        self.ui.mattersBoardComboBox.addItems(self.used_board_matters['CauseNumber'].unique())
        self.ui.board_data_table.item(0, 0).setText(str(''))
        self.ui.board_data_table.item(1, 0).setText(str(''))
        self.ui.board_data_table.item(2, 0).setText(str(''))


    # """Setup process for the board matters graphic."""
    # def setupBoardMattersGraphic(self):
    #     """Clear the text boxes """
    #     self.ui.board_brief_text.clear()
    #     self.ui.board_matter_files.clear()
    #     self.ui.mattersBoardComboBox.clear()
    #
    #     """Retrieve the combobox current data (township and range section)"""
    #     selected_label = self.ui.sectionsBoardComboBox.currentText()
    #
    #     """Get the TSR data for that section"""
    #     current_data = self.df_tsr[self.df_tsr['Label'] == selected_label]
    #
    #     """Isolate out the used board matters for *that* section"""
    #     self.used_board_matters = self.df_BoardData[(self.df_BoardData['Sec'] == current_data['Section'].iloc[0]) &
    #                                                 (self.df_BoardData['Township'] == current_data['Township'].iloc[0]) &
    #                                                 (self.df_BoardData['TownshipDir'] == current_data['Township Direction'].iloc[0]) &
    #                                                 (self.df_BoardData['Range'] == current_data['Range'].iloc[0]) &
    #                                                 (self.df_BoardData['RangeDir'] == current_data['Range Direction'].iloc[0]) &
    #                                                 (self.df_BoardData['PM'] == current_data['Baseline'].iloc[0])]
    #     """Add those board items to the 2nd combo box and fill the table"""
    #     self.ui.mattersBoardComboBox.addItems(self.used_board_matters['CauseNumber'].unique())
    #     self.ui.board_data_table.item(0, 0).setText(str(''))
    #     self.ui.board_data_table.item(1, 0).setText(str(''))
    #     self.ui.board_data_table.item(2, 0).setText(str(''))

    # def setupBoardModel(self, data):
    #     self.board_table_model.removeRows(0, self.board_table_model.rowCount())
    #     for row in data:
    #         items = [QStandardItem(str(item)) for item in row]
    #         self.board_table_model.appendRow(items)
    #     # Set the model to the QTableView
    #     self.ui.board_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    #     self.ui.board_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    #     self.ui.board_table.horizontalHeader().setVisible(False)
    #     self.ui.board_table.verticalHeader().setVisible(False)
    #     self.ui.board_table.setModel(self.board_table_model)

    def setupBoardModel(self, data: list[list[str]]) -> None:
        """
        Set up the board table model with the provided data.

        This method removes existing rows from the board table model and appends
        new rows with the provided data. It performs the following steps:

        1. Remove all existing rows from the board table model.
        2. Iterate over the provided data (a list of lists containing table data).
        3. For each row in the data, create a list of QStandardItem objects with the row data.
        4. Append the list of QStandardItem objects as a new row to the board table model.
        5. Set the board table model to the `board_table` QTableView.
        6. Adjust the horizontal and vertical header settings of the `board_table` QTableView.

        Args:
            data (list[list[str]]): A list of lists containing table data, where each inner list
                represents a row in the table.

        This method does not return any value.
        """
        # Remove existing rows from the board table model
        self.board_table_model.removeRows(0, self.board_table_model.rowCount())

        # Iterate over the provided data
        for row in data:
            # Create a list of QStandardItem objects with the row data
            items = [QStandardItem(str(item)) for item in row]
            # Append the row to the board table model
            self.board_table_model.appendRow(items)

        # Set the board table model to the QTableView
        self.ui.board_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.board_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.board_table.horizontalHeader().setVisible(False)
        self.ui.board_table.verticalHeader().setVisible(False)
        self.ui.board_table.setModel(self.board_table_model)

    # """This process is ran when the radio button for searching for board orders is clicked or changed"""
    # def prodButtonsActivate(self):
    #     # Check the active button
    #     active_button_id = self.ui.board_order_button_group.checkedId()
    #     # Clear the data comboboxes and such
    #     self.ui.board_matters_visible_combo.clear()
    #     self.ui.sectionsBoardComboBox.clear()
    #     self.ui.mattersBoardComboBox.clear()
    #     self.getTSRDataframe()
    #
    #     """Determine which sort of searching we'll do for board orders, either by section or just by board orders in general"""
    #     if active_button_id == 1:
    #         self.ui.board_matters_visible_combo.setEnabled(False)
    #         self.ui.sectionsBoardComboBox.setEnabled(True)
    #         self.ui.mattersBoardComboBox.setEnabled(True)
    #         self.initializeSectionsBoardComboBox()
    #
    #     elif active_button_id == 2:
    #         self.ui.board_matters_visible_combo.setEnabled(True)
    #         self.ui.sectionsBoardComboBox.setEnabled(False)
    #         self.ui.mattersBoardComboBox.setEnabled(False)
    #         self.initializeAllBoardMattersComboBox()

    def prodButtonsActivate(self) -> None:
        """
        Handle the activation of UI elements based on the selected board order search option.

        This method is called when the radio button for searching board orders is clicked or changed.
        It performs the following steps:

        1. Get the ID of the currently active radio button from the `board_order_button_group`.
        2. Clear the `board_matters_visible_combo`, `sectionsBoardComboBox`, and `mattersBoardComboBox` combo boxes.
        3. Call the `getTSRDataframe` method to generate the township, section, and range (TSR) dataframe.
        4. Based on the active radio button ID:
            - If the ID is 1 (search by section):
                - Disable the `board_matters_visible_combo` combo box.
                - Enable the `sectionsBoardComboBox` and `mattersBoardComboBox` combo boxes.
                - Call the `initializeSectionsBoardComboBox` method to populate the `sectionsBoardComboBox`.
            - If the ID is 2 (search all board matters):
                - Enable the `board_matters_visible_combo` combo box.
                - Disable the `sectionsBoardComboBox` and `mattersBoardComboBox` combo boxes.
                - Call the `initializeAllBoardMattersComboBox` method to populate the `board_matters_visible_combo`.

        This method does not return any value.
        """
        # Get the active button ID
        active_button_id = self.ui.board_order_button_group.checkedId()

        # Clear the data combo boxes
        self.ui.board_matters_visible_combo.clear()
        self.ui.sectionsBoardComboBox.clear()
        self.ui.mattersBoardComboBox.clear()

        # Call the getTSRDataframe method
        self.getTSRDataframe()

        # Determine which sort of searching we'll do for board orders, either by section or just by board orders in general
        if active_button_id == 1:  # Search by section
            self.ui.board_matters_visible_combo.setEnabled(False)
            self.ui.sectionsBoardComboBox.setEnabled(True)
            self.ui.mattersBoardComboBox.setEnabled(True)
            self.initializeSectionsBoardComboBox()

        elif active_button_id == 2:  # Search all board matters
            self.ui.board_matters_visible_combo.setEnabled(True)
            self.ui.sectionsBoardComboBox.setEnabled(False)
            self.ui.mattersBoardComboBox.setEnabled(False)
            self.initializeAllBoardMattersComboBox()

    # def updateBoardMatterDetails(self):
    #     """Clear the data"""
    #     self.ui.board_brief_text.clear()
    #     self.ui.board_matter_files.clear()
    #     """Find what button is active"""
    #     active_button_id = self.ui.board_order_button_group.checkedId()
    #
    #     """If the active button is Search by Section, do this"""
    #     if active_button_id == 1:
    #         selected_cause_number = self.ui.mattersBoardComboBox.currentText()
    #         quip = self.used_board_matters.loc[self.used_board_matters['CauseNumber'] == selected_cause_number, 'Quip'].iloc[0]
    #         order_type = self.used_board_matters.loc[self.used_board_matters['CauseNumber'] == selected_cause_number, 'OrderType'].iloc[0]
    #         effect_date = self.used_board_matters.loc[self.used_board_matters['CauseNumber'] == selected_cause_number, 'EffectiveDate'].iloc[0]
    #         end_data = self.used_board_matters.loc[self.used_board_matters['CauseNumber'] == selected_cause_number, 'EndDate'].iloc[0]
    #     elif active_button_id == 2:
    #         selected_cause_number = self.ui.board_matters_visible_combo.currentText()
    #         selected_cause_number_ind = selected_cause_number.index('Cause Number:')
    #         selected_cause_number = selected_cause_number[selected_cause_number_ind+len('Cause Number:'):]
    #
    #         quip = self.used_board_matters_all.loc[self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'Quip'].iloc[0]
    #         order_type = self.used_board_matters_all.loc[self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'OrderType'].iloc[0]
    #         effect_date = self.used_board_matters_all.loc[self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'EffectiveDate'].iloc[0]
    #         end_data = self.used_board_matters_all.loc[self.used_board_matters_all['CauseNumber'] == selected_cause_number, 'EndDate'].iloc[0]
    #
    #     all_plat_with_cause_numbers = self.df_BoardData[self.df_BoardData['CauseNumber'] == selected_cause_number]
    #     matched_rows = self.find_matching_rows(all_plat_with_cause_numbers)
    #     found_polygons = self.create_polygons(matched_rows)
    #     self.ui.board_brief_text.setText(quip)
    #     board_data_links = self.df_BoardDataLinks[self.df_BoardDataLinks['Cause'] == selected_cause_number]
    #     board_data_links = board_data_links.sort_values('DocumentDate')
    #     self.ui.board_data_table.item(0, 0).setText(str(order_type))
    #     self.ui.board_data_table.item(1, 0).setText(str(effect_date))
    #     self.ui.board_data_table.item(2, 0).setText(str(end_data))
    #     data = [['Order Type', order_type],
    #             ['Date Effective', effect_date],
    #             ['End Date', end_data]]
    #     self.setupBoardModel(data)
    #     # Combine the Description and Filepath columns into an HTML-formatted string
    #     file_entries = []
    #     for _, row in board_data_links.iterrows():
    #         description = row['Description']
    #         filepath = row['Filepath']
    #         file_entry = f"{description}<br><a href='{filepath}'>{filepath}</a><br><br>"
    #         file_entries.append(file_entry)
    #
    #     # Join the file entries with newline characters and set the HTML of self.ui.board_matter_files
    #     self.ui.board_matter_files.setHtml(''.join(file_entries))
    #
    #     self.outlined_board_sections.set_color('red')
    #     self.outlined_board_sections.set_paths(found_polygons)
    #     self.ax2d.draw_artist(self.outlined_board_sections)
    #     self.canvas2d.blit(self.ax2d.bbox)
    #     self.canvas2d.draw()

    def updateBoardMatterDetails(self) -> None:
        """
        Update the board matter details based on the selected cause number.

        This method retrieves and displays the relevant information for the selected board matter,
        including the quip, order type, effective date, end date, and associated files.
        It also handles displaying the outlined board sections on the 2D plot.
        """
        self.clear_board_matter_ui()
        selected_cause_number, active_button_id = self.get_selected_cause_number()

        quip, order_type, effect_date, end_data = self.get_board_matter_details(selected_cause_number, active_button_id)
        all_plat_with_cause_numbers = self.get_plat_with_cause_number(selected_cause_number)
        matched_rows = self.find_matching_rows(all_plat_with_cause_numbers)
        found_polygons = self.create_polygons(matched_rows)

        self.update_board_matter_ui(quip, order_type, effect_date, end_data, selected_cause_number)
        formatted_files = self.format_board_matter_files(selected_cause_number)
        self.ui.board_matter_files.setHtml(formatted_files)

        self.update_plot(found_polygons)

    def clear_board_matter_ui(self) -> None:
        """Clear the board matter-related UI elements."""
        self.ui.board_brief_text.clear()
        self.ui.board_matter_files.clear()

    def get_selected_cause_number(self) -> tuple[str, int]:
        """
        Get the selected cause number and the active button ID.

        Returns:
            tuple: A tuple containing the selected cause number and the active button ID.
        """
        active_button_id = self.ui.board_order_button_group.checkedId()

        if active_button_id == 1:
            selected_cause_number = self.ui.mattersBoardComboBox.currentText()
        elif active_button_id == 2:
            selected_cause_number = self.extract_cause_number_from_text(
                self.ui.board_matters_visible_combo.currentText())

        return selected_cause_number, active_button_id

    def extract_cause_number_from_text(self, text: str) -> str:
        """
        Extract the cause number from the given text.

        Args:
            text (str): The text containing the cause number.

        Returns:
            str: The extracted cause number.
        """
        cause_number_ind = text.index('Cause Number:')
        cause_number = text[cause_number_ind + len('Cause Number:'):]
        return cause_number

    def get_board_matter_details(self, selected_cause_number: str, active_button_id: int) -> tuple[str, str, str, str]:
        """
        Retrieve the board matter details for the selected cause number.

        Args:
            selected_cause_number (str): The selected cause number.
            active_button_id (int): The ID of the active radio button.

        Returns:
            tuple: A tuple containing the quip, order type, effective date, and end date.
        """
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

    def get_plat_with_cause_number(self, selected_cause_number: str) -> pd.DataFrame:
        """
        Get the rows from the df_BoardData dataframe that match the selected cause number.

        Args:
            selected_cause_number (str): The selected cause number.

        Returns:
            pd.DataFrame: A dataframe containing the rows with the selected cause number.
        """
        all_plat_with_cause_numbers = self.df_BoardData[self.df_BoardData['CauseNumber'] == selected_cause_number]
        return all_plat_with_cause_numbers

    def find_matching_rows(self, all_plat_with_cause_numbers: pd.DataFrame) -> pd.DataFrame:
        """
        Find the rows in the df_plat dataframe that match the Conc values from the provided dataframe.

        Args:
            all_plat_with_cause_numbers (pd.DataFrame): A dataframe containing the cause numbers and Conc values.

        Returns:
            pd.DataFrame: A dataframe containing the matching rows from the df_plat dataframe.
        """
        pattern = '|'.join(all_plat_with_cause_numbers['Conc'].astype(str))
        matching_rows = self.df_plat[self.df_plat['Conc'].astype(str).str.contains(pattern)]
        return matching_rows

    def create_polygons(self, matching_rows: pd.DataFrame) -> list[np.ndarray]:
        """
        Create polygons from the matching rows based on the Easting and Northing coordinates.

        Args:
            matching_rows (pd.DataFrame): A dataframe containing the matching rows.

        Returns:
            list[np.ndarray]: A list of numpy arrays representing the polygons.
        """
        matching_rows['LineSegmentOrder'] = matching_rows.groupby('Conc').cumcount() + 1
        matching_rows = matching_rows.drop_duplicates(keep='first')
        grouped_rows = matching_rows.groupby('Conc')
        polygons_lst = []
        for conc, group in grouped_rows:
            coordinates = group[['Easting', 'Northing']].values.tolist()
            polygons_lst.append(np.array(coordinates))
        return polygons_lst

    def format_board_matter_files(self, selected_cause_number: str) -> str:
        """
        Format the board matter files as HTML-formatted strings with links.

        Args:
            selected_cause_number (str): The selected cause number.

        Returns:
            str: An HTML-formatted string with links to the board matter files.
        """
        board_data_links = self.df_BoardDataLinks[self.df_BoardDataLinks['Cause'] == selected_cause_number]
        board_data_links = board_data_links.sort_values('DocumentDate')
        file_entries = []
        for _, row in board_data_links.iterrows():
            description = row['Description']
            filepath = row['Filepath']
            file_entry = f"{description}<br><a href='{filepath}'>{filepath}</a><br><br>"
            file_entries.append(file_entry)
        return ''.join(file_entries)

    def update_board_matter_ui(self, quip: str, order_type: str, effect_date: str, end_data: str,
                               selected_cause_number: str) -> None:
        """
        Update the board matter-related UI elements with the provided data.

        Args:
            quip (str): The quip for the selected board matter.
            order_type (str): The order type for the selected board matter.
            effect_date (str): The effective date for the selected board matter.
            end_data (str): The end date for the selected board matter.
            selected_cause_number (str): The selected cause number.
        """
        self.ui.board_brief_text.setText(quip)
        self.ui.board_data_table.item(0, 0).setText(str(order_type))
        self.ui.board_data_table.item(1, 0).setText(str(effect_date))
        self.ui.board_data_table.item(2, 0).setText(str(end_data))
        data = [['Order Type', order_type],
                ['Date Effective', effect_date],
                ['End Date', end_data]]
        self.setupBoardModel(data)

    def update_plot(self, found_polygons: list[np.ndarray]) -> None:
        """
        Update the 2D plot with the provided polygons.

        Args:
            found_polygons (list[np.ndarray]): A list of numpy arrays representing the polygons.
        """
        self.outlined_board_sections.set_color('red')
        self.outlined_board_sections.set_paths(found_polygons)
        self.ax2d.draw_artist(self.outlined_board_sections)
        self.canvas2d.blit(self.ax2d.bbox)
        self.canvas2d.draw()

    # def find_matching_rows(self, all_plat_with_cause_numbers):
    #     # Create a regular expression pattern based on the Conc values from self.df_BoardData
    #     pattern = '|'.join(all_plat_with_cause_numbers['Conc'].astype(str))
    #
    #     # Find rows in self.df_plat where the Conc column partially matches the pattern
    #     matching_rows = self.df_plat[self.df_plat['Conc'].astype(str).str.contains(pattern)]
    #
    #     return matching_rows

    def find_matching_rows(self, all_plat_with_cause_numbers: pd.DataFrame) -> pd.DataFrame:
        """
        Find the rows in the df_plat dataframe that match the Conc values from the provided dataframe.

        This function is used to find the rows in the `df_plat` dataframe that correspond to the Conc (concession) values
        associated with a specific cause number. It works by creating a pattern string from the Conc values in the
        `all_plat_with_cause_numbers` dataframe, and then using that pattern to search for matching Conc values in the
        `df_plat` dataframe.

        Args:
            all_plat_with_cause_numbers (pd.DataFrame): A dataframe containing the cause numbers and Conc values.
                This dataframe is typically a subset of the `df_BoardData` dataframe, filtered by the selected cause number.

        Returns:
            pd.DataFrame: A dataframe containing the matching rows from the `df_plat` dataframe.
                These rows correspond to the Conc values associated with the selected cause number.

        Example:
            Suppose `all_plat_with_cause_numbers` contains the following data:
                CauseNumber | Conc
                ABC123      | 123
                ABC123      | 456
                ABC123      | 789

            This function will create the pattern string '123|456|789' and search for rows in `df_plat` where the 'Conc'
            column contains any of those values. The resulting dataframe will contain all rows from `df_plat` that have
            a 'Conc' value of 123, 456, or 789.
        """
        pattern = '|'.join(all_plat_with_cause_numbers['Conc'].astype(str))
        matching_rows = self.df_plat[self.df_plat['Conc'].astype(str).str.contains(pattern)]
        return matching_rows
    # def create_polygons(self, matching_rows):
    #     # Group the matching rows by Conc
    #     matching_rows['LineSegmentOrder'] = matching_rows.groupby('Conc').cumcount() + 1
    #     matching_rows = matching_rows.drop_duplicates(keep='first')
    #     grouped_rows = matching_rows.groupby('Conc')
    #     # Create a dictionary to store the polygons for each Conc
    #     polygons_lst = []
    #     # Iterate over each group
    #     for conc, group in grouped_rows:
    #         # Extract the coordinates from the group
    #         coordinates = group[['Easting', 'Northing']].values.tolist()
    #         polygons_lst.append(np.array(coordinates))
    #     return polygons_lst

    # """This is for generating labels to be displayed in the combobox for board data. Then turn it into a dataframe"""

    def create_polygons(self, matching_rows: pd.DataFrame) -> list[np.ndarray]:
        """
        Create polygons from the matching rows based on the Easting and Northing coordinates.

        This function takes a dataframe `matching_rows` containing rows from the `df_plat` dataframe that match the Conc
        (concession) values associated with a selected cause number. It then creates polygons from these matching rows
        based on their Easting and Northing coordinates.

        Args:
            matching_rows (pd.DataFrame): A dataframe containing the matching rows from the `df_plat` dataframe,
                corresponding to the Conc values associated with the selected cause number.

        Returns:
            list[np.ndarray]: A list of numpy arrays, where each array represents a polygon defined by the Easting
                and Northing coordinates of the matching rows for a single concession.
        """

        # Add a new column 'LineSegmentOrder' to the `matching_rows` dataframe.
        # This column is created by grouping the rows by 'Conc' and applying a cumulative count to each group, starting from 1.
        # This order is necessary for correctly connecting the points within each concession polygon.
        matching_rows['LineSegmentOrder'] = matching_rows.groupby('Conc').cumcount() + 1

        # Remove any duplicate rows from `matching_rows`, keeping only the first occurrence of each row.
        # This is done using the `drop_duplicates` method with `keep='first'`.
        matching_rows = matching_rows.drop_duplicates(keep='first')

        # Group the rows in `matching_rows` by 'Conc' using the `groupby` method.
        # This creates a grouped object where each group corresponds to a single concession polygon.
        grouped_rows = matching_rows.groupby('Conc')

        # Initialize an empty list to store the polygons
        polygons_lst = []

        # Iterate over the grouped object, and for each group (i.e., concession):
        for conc, group in grouped_rows:
            # Extract the 'Easting' and 'Northing' columns as a list of coordinate pairs.
            coordinates = group[['Easting', 'Northing']].values.tolist()

            # Convert the list of coordinate pairs to a numpy array.
            polygon = np.array(coordinates)

            # Append the numpy array representing the polygon to the `polygons_lst` list.
            polygons_lst.append(polygon)

        # Return the `polygons_lst` list containing all the concession polygons as numpy arrays.
        return polygons_lst

    # def getTSRDataframe(self):
    #     data = {
    #         'Section': [],
    #         'Township': [],
    #         'Township Direction': [],
    #         'Range': [],
    #         'Range Direction': [],
    #         'Baseline': [],
    #         'Conc': [],
    #         'Label': []
    #     }
    #     for s in self.all_wells_plat_labels_for_editing:
    #         section = int(s[:2])
    #         township = int(s[2:4])
    #         township_direction = s[4]
    #         range_ = int(s[5:7])
    #         range_direction = s[7]
    #         baseline = s[8]
    #         conc = f"{s[:9]}"
    #         label = f"{section} {township}{township_direction} {range_}{range_direction} {baseline}"
    #         data['Section'].append(section)
    #         data['Township'].append(township)
    #         data['Township Direction'].append(township_direction)
    #         data['Range'].append(range_)
    #         data['Range Direction'].append(range_direction)
    #         data['Baseline'].append(baseline)
    #         data['Conc'].append(conc)
    #         data['Label'].append(label)
    #
    #     self.df_tsr = pd.DataFrame(data)
    #     self.df_tsr = self.df_tsr.sort_values(by=['Baseline', 'Township Direction', 'Range Direction', 'Township', 'Range', 'Section'])
    #
    #     """Generate the combobox for the sections"""

    def getTSRDataframe(self):
        """
        Create a pandas dataframe containing Theoretical Stratigraphic Record (TSR) information.

        This function creates a dataframe `df_tsr` with columns 'Section', 'Township', 'Township Direction',
        'Range', 'Range Direction', 'Baseline', 'Conc', and 'Label'. The data for this dataframe is derived
        from the `all_wells_plat_labels_for_editing` attribute, which is assumed to be a list of strings
        representing well plat labels.

        The function performs the following steps:
        1. Initialize an empty dictionary `data` with keys corresponding to the desired column names.
        2. Iterate over each well plat label string `s` in `all_wells_plat_labels_for_editing`.
        3. For each string `s`, extract the section, township, township direction, range, range direction,
           baseline, and concession (Conc) values using string slicing and integer conversion.
        4. Construct a label string by combining the extracted values.
        5. Append the extracted and constructed values to the corresponding lists in the `data` dictionary.
        6. Create a pandas dataframe `df_tsr` from the `data` dictionary.
        7. Sort the `df_tsr` dataframe based on the values in the 'Baseline', 'Township Direction',
           'Range Direction', 'Township', 'Range', and 'Section' columns.

        After executing this function, the `df_tsr` attribute of the class will be populated with the
        Theoretical Stratigraphic Record dataframe, sorted based on the specified columns.
        """
        data = {
            'Section': [],
            'Township': [],
            'Township Direction': [],
            'Range': [],
            'Range Direction': [],
            'Baseline': [],
            'Conc': [],
            'Label': []
        }

        # Iterate over each well plat label string in `all_wells_plat_labels_for_editing`
        for s in self.all_wells_plat_labels_for_editing:
            # Extract the section, township, township direction, range, range direction, and baseline values
            section = int(s[:2])
            township = int(s[2:4])
            township_direction = s[4]
            range_ = int(s[5:7])
            range_direction = s[7]
            baseline = s[8]
            conc = f"{s[:9]}"  # Construct the concession (Conc) value

            # Construct the label string
            label = f"{section} {township}{township_direction} {range_}{range_direction} {baseline}"

            # Append the extracted and constructed values to the corresponding lists in the `data` dictionary
            data['Section'].append(section)
            data['Township'].append(township)
            data['Township Direction'].append(township_direction)
            data['Range'].append(range_)
            data['Range Direction'].append(range_direction)
            data['Baseline'].append(baseline)
            data['Conc'].append(conc)
            data['Label'].append(label)

        # Create a pandas dataframe from the `data` dictionary
        self.df_tsr = pd.DataFrame(data)

        # Sort the `df_tsr` dataframe based on the specified columns
        self.df_tsr = self.df_tsr.sort_values(
            by=['Baseline', 'Township Direction', 'Range Direction', 'Township', 'Range', 'Section'])
    # def initializeSectionsBoardComboBox(self):
    #     self.ui.sectionsBoardComboBox.clear()
    #     model = QStandardItemModel()
    #     used_tsr_data = self.df_tsr[self.df_tsr['Conc'].isin(self.used_plat_codes_for_boards)].drop_duplicates(keep='first')
    #     data = used_tsr_data['Label'].values
    #
    #     for item_text in data:
    #         item = QStandardItem(item_text)
    #         model.appendRow(item)
    #     self.ui.sectionsBoardComboBox.setModel(model)
    #     self.setupBoardMattersGraphic()

    def initializeSectionsBoardComboBox(self):
        """
        Initialize the sectionsBoardComboBox with unique labels from the TSR dataframe.

        This function initializes the `sectionsBoardComboBox` with unique labels from the `df_tsr` dataframe.
        The labels are filtered based on the concessions (Conc) present in the `used_plat_codes_for_boards` attribute.
        After populating the `sectionsBoardComboBox` with the unique labels, it calls the `setupBoardMattersGraphic` function.

        Steps:
        1. Clear the `sectionsBoardComboBox` to remove any existing items.
        2. Create a `QStandardItemModel` to store the items for the combo box.
        3. Filter the `df_tsr` dataframe to only include rows where the 'Conc' value is present in `used_plat_codes_for_boards`.
           Remove any duplicate rows, keeping the first occurrence.
        4. Extract the 'Label' values from the filtered dataframe.
        5. Iterate over the labels and create a `QStandardItem` for each label.
        6. Append each `QStandardItem` to the `QStandardItemModel`.
        7. Set the `QStandardItemModel` as the model for the `sectionsBoardComboBox`.
        8. Call the `setupBoardMattersGraphic` function.
        """
        self.ui.sectionsBoardComboBox.clear()
        model = QStandardItemModel()

        # Filter the `df_tsr` dataframe based on the concessions in `used_plat_codes_for_boards`
        # and remove any duplicate rows, keeping the first occurrence
        used_tsr_data = self.df_tsr[self.df_tsr['Conc'].isin(self.used_plat_codes_for_boards)].drop_duplicates(
            keep='first')

        # Extract the 'Label' values from the filtered dataframe
        data = used_tsr_data['Label'].values

        # Create a `QStandardItem` for each label and append it to the model
        for item_text in data:
            item = QStandardItem(item_text)
            model.appendRow(item)

        # Set the model for the `sectionsBoardComboBox`
        self.ui.sectionsBoardComboBox.setModel(model)

        # Call the `setupBoardMattersGraphic` function
        self.setupBoardMattersGraphic()
    """"""
    def initializeAllBoardMattersComboBox(self):
        """Clear the all board matters combobox"""
        self.ui.board_matters_visible_combo.clear()

        """Merge the township and range and the board matters all together. We want the conc codes and the labels"""
        self.used_board_matters_all = self.df_tsr.merge(
            self.df_BoardData,
            left_on=['Section', 'Township', 'Township Direction', 'Range', 'Range Direction', 'Baseline'],
            right_on=['Sec', 'Township', 'TownshipDir', 'Range', 'RangeDir', 'PM']
        )
        """Drop columns"""
        columns_to_drop = ['Sec', 'Township','TownshipDir', 'Range', 'RangeDir', 'PM']
        self.used_board_matters_all.drop(columns=columns_to_drop, inplace=True)

        """Sort the data"""
        self.used_board_matters_all = self.used_board_matters_all.sort_values(by=['DocketNumber', 'CauseNumber'])

        """Generate a new colum for docket number labels"""
        self.used_board_matters_all['Label'] = "Docket Number:" + self.used_board_matters_all['DocketNumber'] + ", Cause Number:" + self.used_board_matters_all['CauseNumber']
        data = self.used_board_matters_all['Label'].drop_duplicates(keep='first').values
        self.ui.board_brief_text.clear()
        self.ui.board_matter_files.clear()

        """Populate the various fields"""
        self.ui.board_matters_visible_combo.addItems(data)
        self.ui.board_data_table.item(0, 0).setText(str(''))
        self.ui.board_data_table.item(1, 0).setText(str(''))
        self.ui.board_data_table.item(2, 0).setText(str(''))
