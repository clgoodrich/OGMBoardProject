"""
WellVisualizerLoader
Author: Colton Goodrich
Date: 8/31/2024

This module contains functions for loading and processing well data, board data, and
production data for the well visualization application. It handles tasks such as
connecting to databases, retrieving data, and generating dataframes for further
processing and visualization.

The module provides functionality to retrieve well information, directional survey data,
township and range data, board matter information, and production data from various
data sources. It also includes helper functions for data manipulation, formatting, and
database operations.

Functions:
- mainProcess(): The main function that orchestrates the data retrieval and processing
  workflow.
- setup(): Sets up the database connection and tables for storing well data.
- doEverything(): Retrieves and processes well data, board data, and production data for
  a given set of well API numbers and board matter details.
- createDataFrame(): Retrieves well data, directional survey data, board data, and plat
  data for a given set of well API numbers and board matter details.
- retrieveBoardInformation(): Retrieves board matter information and associated file
  links from the database.
- recordPlatData(): Records plat data (concession information) in a dataframe.
- recordOutputLocation(): Records well location data in a dataframe.
- findMissingDirectionals(): Finds missing directional survey data for wells.
- assembleVerticalWell(): Assembles data for vertical wells (placeholder).
- findPlatsSurroundingSectionsGiven(): Finds relevant plats based on provided section
  data.
- findPlatsSurrounding(): Finds relevant plats surrounding a given set of well API
  numbers.
- findMorePlats(): Finds additional plats based on well API numbers.
- findDatabaseInfoForSections(): Finds database information for given sections
  (placeholder).
- writeToDatabase(): Writes data to the database tables.
- writeToDB(): Helper function for writing data to a specific database table.
- checkIfDuplicates(): Checks if duplicates exist between two datasets (placeholder).
- retrieveConstructDataAll(): Retrieves well construction data for a given set of well
  API numbers.
- retrieveConstructDataAllMega(): Retrieves well construction data using a more
  comprehensive query.
- findDepthsIfInitFailed(): Retrieves well depth data if initial retrieval failed.
- findDepthsIfInitFailedMass(): Retrieves well depth data in bulk if initial retrieval
  failed.
- sqlProdData(): Retrieves production data for a given set of well API numbers.
- sqlProdDataOil(): Retrieves oil production data for a given well API number.
- sqlProdDataGas(): Retrieves gas production data for a given well API number.
- sqlConnect(): Establishes a connection to the SQL Server database.
- sqlConnectPlats(): Connects to the SQLite database for plat data.
- fetch_ref_codes(): Fetches reference codes (e.g., well status, well type) from the
  database.
- dbRefCodesTranslateStatus(): Translates a well status code to its description.
- dbRefCodesTranslateType(): Translates a well type code to its description.
- sqlFindAllInSection(): Finds all wells in a given section.
- sqlFindAllInSectionAll(): Finds all wells in multiple sections.
- sqlFindBoardMatterInformationAll(): Finds board matter information for multiple
  sections.
- sqlFindBoardMatterInformation(): Finds board matter information for a single section.
- sqlFindBoardMatterLinks(): Finds board matter file links for given cause numbers.
- sqlFindProduction(): Finds production data for a given well API number (placeholder).
- determineAdjacentVals(): Determines adjacent values for a given section (helper
  function).
- processSections(): Processes sections based on township, range, and meridian data
  (helper function).
- platAdjacentLsts(): Returns lists of adjacent sections and translation values (helper
  function).
- modTownship(): Modifies the township value based on translation values (helper
  function).
- modRange(): Modifies the range value based on translation values (helper function).
- rewriteCode(): Rewrites section codes in a specific format (helper function).
- processAndReturnMonthlyPrices(): Processes and retrieves monthly oil and gas prices
  (helper function).
- sqlProductionDFGenerate(): Generates a production dataframe for a given set of well
  API numbers.
- findDataSecondTime(): Retrieves production data from a SQL Server database (helper
  function).
- formatSecondProd(): Formats production data for a single well API number (helper
  function).
- formatSecondProdAll(): Formats production data for multiple well API numbers (helper
  function).

This module is an essential component of the well visualization application, providing
the necessary data retrieval and processing capabilities for visualizing well
information, board matters, and production data.
"""

import urllib
import yfinance as yf
from sqlalchemy import create_engine
from pyproj import Proj, Geod
import time
import copy
from collections import defaultdict
import sqlite3
import os
import pandas as pd
import pandas.errors
import pyodbc
import ModuleAgnostic as ma
import utm
import warnings

# Suppress all future warnings
warnings.filterwarnings('ignore', category=FutureWarning)
# warnings.filterwarnings('ignore', category=SettingWithCopyWarning)
warnings.simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)
# Suppress all user warnings
warnings.filterwarnings('ignore', category=UserWarning)


def mainProcess():
    pd.set_option('display.max_columns', None)
    setup()
    time_start = time.perf_counter()

    current_dir = os.getcwd()
    name_used = 'UsedBoardData.db'
    apd_data_dir_used = os.path.join(current_dir, name_used)
    conn_db_used = sqlite3.connect(apd_data_dir_used)
    cursor_db_used = conn_db_used.cursor()

    string_sql = 'select * from Main'
    df_main = pd.read_sql(string_sql, conn_db_used)
    string_sql = 'select * from Apds'
    df_apd = pd.read_sql(string_sql, conn_db_used)
    string_sql = 'select * from TSR'
    df_tsr = pd.read_sql(string_sql, conn_db_used)
    all_matters = df_main['Label'].unique()
    df_many = findDataSecondTime()

    for i in all_matters:
        main_i = df_main[(df_main['Label'] == i)]
        tsr_i = df_tsr[(df_tsr['Label'] == i)]
        tsr_data = tsr_i.drop('Label', axis=1).values
        year = main_i['Year'].tolist()[0]
        month = main_i['Month'].tolist()[0]
        apds = df_apd[(df_apd['Label'] == i)]['APINumber'].values
        if month =='June':
            doEverything(i, apds, year, month, df_many, tsr_data)







    # df_many = []
    print('Data Retrieval Time: ', time.perf_counter() - time_start)
    #
    # label = 'Docket 2024-018 - Cause No. 132-35'
    # apds = [4301354451, 4301354351, 4301354352]
    # year, month = '2024', 'March'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-023 Cause No. 132-36'
    # apds = [4301350923, 4301351203]
    # year, month = '2024', 'April'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-021 Cause No. 600-06'
    # apds = [4301333982, 4301353441, 4301353442, 4304731981, 4304752435]
    # year, month = '2024', 'April'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-024 Cause No. 132-37'
    # apds = [43013515010000, 43013522700000, 43013521050000, 43013534940000, 43013534660100, 43013521060000, 43013512240000, 43013518530000, 43013523160000, 43013523170000, 43013515080000,
    #         43013510670000]
    # year, month = '2024', 'April'
    # doEverything(label, apds, year, month, df_many, [])
    # #
    # label = 'Docket No. 2024-026 Cause No. 132-38'
    # apds = [4301354473, 4301354366]
    # year, month = '2024', 'May'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # #
    # label = 'Docket No. 2024-029 Cause No. 130-31'
    # apds = [4301354208, 4301354449, 4301354144, 4301353506, 4301354206, 4301354148, 4301354427, 4301354234, 4301354238, 4301354235, 4301353798, 4301353627, 4301354308, 4301354329, 4301353634,
    #         4301354260, 4301353821, 4301353743, 4301354163, 4301354281, 4301354310, 4301354259, 4301353504, 4301354113, 4301354086, 4301354373, 4301354149, 4301353625, 4301354371, 4301354211,
    #         4301353408, 4301353548, 4301354070, 4301354428, 4301353376, 4301354207, 4301354241, 4301354315, 4301354138, 4301354319, 4301354159, 4301354273, 4301354263, 4301354168, 4301353741,
    #         4301354278, 4301354240, 4301354372, 4301353491, 4301354167, 4301354446, 4301354080, 4301354264, 4301353748, 4301354162, 4301354443, 4301354333, 4301353558, 4301354004, 4301354432,
    #         4301354077, 4301354158, 4301354169, 4301354112, 4301354306, 4301354108, 4301354277, 4301354173, 4301353614, 4301354377, 4301354210, 4301354280, 4301353742, 4301353377, 4301354174,
    #         4301354258, 4301354444, 4301354147, 4301354430, 4301354266, 4301354305, 4301354115, 4301353502, 4301354335, 4301354318, 4301353626, 4301354285, 4301354236, 4301354262, 4301354313,
    #         4301353505, 4301354317, 4301353797, 4301354075, 4301354156, 4301354251, 4301354164, 4301353410, 4301354109, 4301354332, 4301353353, 4301354374, 4301354117, 4301354445, 4301354079,
    #         4301354433, 4301354431, 4301354118, 4301353403, 4301354331, 4301354146, 4301354279, 4301354006, 4301354212, 4301354171, 4301354237, 4301354267, 4301353899, 4301354076, 4301353378,
    #         4301353556, 4301354213, 4301354435, 4301354307, 4301354311, 4301354170, 4301354154, 4301354312, 4301354257, 4301354337, 4301353907, 4301353698, 4301353379, 4301354141, 4301354442,
    #         4301354426, 4301353633, 4301353500, 4301354209, 4301354074, 4301354275, 4301354005, 4301353773, 4301354314, 4301353628, 4301353499, 4301354283, 4301354272, 4301353352, 4301354276,
    #         4301354150, 4301354153, 4301354255, 4301354370, 4301354330, 4301353822, 4301354145, 4301354239, 4301354434, 4301354085, 4301354139, 4301354165, 4301354334, 4301354081, 4301354311,
    #         4301354435, 4301354307, 4301353378, 4301354076, 4301354544, 4301353403, 4301354579, 4301354237, 4301354279, 4301354146, 4301354212, 4301354162, 4301354264, 4301354582, 4301353748,
    #         4301354171, 4301331070, 4301354445, 4301354117, 4301353353, 4301354374, 4301354332, 4301354585, 4301354118, 4301331216, 4301331113, 4301354431, 4301354079, 4301354433, 4301353073,
    #         4301354164, 4301352128, 4301354156, 4301354251, 4301354075, 4301353797, 4301354285, 4301353626, 4301354318, 4301353410, 4301354542, 4301352103, 4301350273, 4301354313, 4301354236,
    #         4301354262, 4301354266, 4301354594, 4301354317, 4301354305, 4301354115, 4301354554, 4301354426, 4301353633, 4301354141, 4301353379, 4301354335, 4301354442, 4301354371, 4301354211,
    #         4301353408, 4301351586, 4301354552, 4301354281, 4301354163, 4301354316, 4301353743, 4301354113, 4301354259, 4301354310, 4301351845, 4301351486, 4301354144, 4301354541, 4301330161,
    #         4301354165, 4301350570, 4301354085, 4301354434, 4301354239, 4301354309, 4301354592, 4301353629, 4301354334, 4301354081, 4301354139, 4301354150, 4301354283, 4301353352, 4301354272,
    #         4301353628, 4301354449, 4301354208, 4301353822, 4301332149, 4301354330, 4301354370, 4301354255, 4301354153, 4301331354, 4301354276, 4301331140, 4301354475, 4301353548, 4301354145,
    #         4301354428, 4301354207, 4301353376, 4301354551, 4301354149, 4301331325, 4301353625, 4301351162, 4301354373, 4301331121, 4301354086, 4301353614, 4301351160, 4301354173, 4301353377,
    #         4301354584, 4301354280, 4301330349, 4301354210, 4301354377, 4301354477, 4301354472, 4301354265, 4301354169, 4301330204, 4301354306, 4301354112, 4301353742, 4301350526, 4301350275,
    #         4301354277, 4301354077, 4301354593, 4301354432, 4301353558, 4301354206, 4301354581, 4301353063, 4301354158, 4301354238, 4301354235, 4301354234, 4301354427, 4301354148, 4301353821,
    #         4301354329, 4301353634, 4301354308, 4301354260, 4301353798, 4301353627, 4301354550, 4301354333, 4301354443, 4301354372, 4301354240, 4301353133, 4301351053, 4301354446, 4301354080,
    #         4301353491, 4301354468, 4301354167, 4301353741, 4301350088, 4301354273, 4301354476, 4301354282, 4301331379, 4301354278, 4301354168, 4301354263, 4301354138, 4301350487, 4301354556,
    #         4301354159, 4301354319, 4301354539, 4301354241, 4301354315, 4301354174, 4301354469, 4301354430, 4301354147, 4301352028, 4301333616, 4301354444, 4301354258, 4301353773, 4301354074,
    #         4301354314, 4301354275, 4301354209, 4301354257, 4301354312, 4301354170, 4301354154, 4301331136, 4301353698, 4301354143, 4301351389, 4301353907, 4301354337, 4301353556, 4301350407,
    #         4301354474, 4301332755, 4301353899, 4301354267, 4301351366, 4301354478, 4301354213]
    # tsr_data = [[19, 2, "S", 1, "W", "U"],
    #             [30, 2, "S", 1, "W", "U"],
    #             [31, 2, "S", 1, "W", "U"],
    #             [3, 2, "S", 2, "W", "U"],
    #             [4, 2, "S", 2, "W", "U"],
    #             [5, 2, "S", 2, "W", "U"],
    #             [6, 2, "S", 2, "W", "U"],
    #             [7, 2, "S", 2, "W", "U"],
    #             [8, 2, "S", 2, "W", "U"],
    #             [9, 2, "S", 2, "W", "U"],
    #             [10, 2, "S", 2, "W", "U"],
    #             [15, 2, "S", 2, "W", "U"],
    #             [16, 2, "S", 2, "W", "U"],
    #             [17, 2, "S", 2, "W", "U"],
    #             [18, 2, "S", 2, "W", "U"],
    #             [19, 2, "S", 2, "W", "U"],
    #             [20, 2, "S", 2, "W", "U"],
    #             [21, 2, "S", 2, "W", "U"],
    #             [22, 2, "S", 2, "W", "U"],
    #             [23, 2, "S", 2, "W", "U"],
    #             [26, 2, "S", 2, "W", "U"],
    #             [27, 2, "S", 2, "W", "U"],
    #             [28, 2, "S", 2, "W", "U"],
    #             [29, 2, "S", 2, "W", "U"],
    #             [30, 2, "S", 2, "W", "U"],
    #             [31, 2, "S", 2, "W", "U"],
    #             [32, 2, "S", 2, "W", "U"],
    #             [33, 2, "S", 2, "W", "U"],
    #             [34, 2, "S", 2, "W", "U"],
    #             [35, 2, "S", 2, "W", "U"],
    #             [1, 2, "S", 3, "W", "U"],
    #             [2, 2, "S", 3, "W", "U"],
    #             [3, 2, "S", 3, "W", "U"],
    #             [4, 2, "S", 3, "W", "U"],
    #             [5, 2, "S", 3, "W", "U"],
    #             [6, 2, "S", 3, "W", "U"],
    #             [7, 2, "S", 3, "W", "U"],
    #             [8, 2, "S", 3, "W", "U"],
    #             [9, 2, "S", 3, "W", "U"],
    #             [10, 2, "S", 3, "W", "U"],
    #             [11, 2, "S", 3, "W", "U"],
    #             [12, 2, "S", 3, "W", "U"],
    #             [13, 2, "S", 3, "W", "U"],
    #             [14, 2, "S", 3, "W", "U"],
    #             [15, 2, "S", 3, "W", "U"],
    #             [16, 2, "S", 3, "W", "U"],
    #             [17, 2, "S", 3, "W", "U"],
    #             [18, 2, "S", 3, "W", "U"],
    #             [19, 2, "S", 3, "W", "U"],
    #             [20, 2, "S", 3, "W", "U"],
    #             [21, 2, "S", 3, "W", "U"],
    #             [22, 2, "S", 3, "W", "U"],
    #             [23, 2, "S", 3, "W", "U"],
    #             [24, 2, "S", 3, "W", "U"],
    #             [25, 2, "S", 3, "W", "U"],
    #             [26, 2, "S", 3, "W", "U"],
    #             [27, 2, "S", 3, "W", "U"],
    #             [28, 2, "S", 3, "W", "U"],
    #             [29, 2, "S", 3, "W", "U"],
    #             [30, 2, "S", 3, "W", "U"],
    #             [31, 2, "S", 3, "W", "U"],
    #             [32, 2, "S", 3, "W", "U"],
    #             [33, 2, "S", 3, "W", "U"],
    #             [34, 2, "S", 3, "W", "U"],
    #             [35, 2, "S", 3, "W", "U"],
    #             [36, 2, "S", 3, "W", "U"]]
    # year, month = '2024', 'May'
    # doEverything(label, [], year, month, df_many, tsr_data)
    #
    # label = 'Docket No. 2024-026 Cause No. 132-38'
    # apds = [4301354473, 301354366, 4301354436]
    # year, month = '2024', 'May'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-027 Cause No. 472-02'
    # apds = [4304756954]
    # year, month = '2024', 'May'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-030 Cause No. 130-32'
    # apds = [430135429800, 430135429900, 430135474300, 430135474400, 430135474500, 430135474600, 430135190700, 430135452800, 430135452900, 430135003700, 430133429300, 430135163600, 430135200700,
    #         4301351073, 4301351034, 4301351429, 4301351430, 4301352089, 4301350928, 4301350929, 4301351260, 4301351343, 4301351705, 4301351743, 4301351745, 4301351902, 4301351535, 4301351819,
    #         4301351820, 4301352402, 4301352656, 4301352657, 4301352658, 4301331805, 4301332931, 4301330756, 4301330924, 4301351226, 4301352148, 4301352149, 4301352150, 4301352151, 4301352234,
    #         4301352235, 4301352236, 4301352237, 4301352249, 4301352250, 4301352251, 4301352298, 4301352300, 4301352299, 4301352145, 4301352146, 4301352147, 4301352302, 4301352303, 4301352305,
    #         4301352307, 4301352343, 4301352344, 4301352345, 4301352346, 4301350997, 4301351111, 4301351303, 4301351520, 4301352180, 4301352181, 4301352182, 4301352184, 4301352185, 4301352480,
    #         4301352484, 4301352493, 4301352545, 4301352546, 4301352547, 4301352548, 4301332664, 4301351227, 4301351948, 4301351949, 4301351950, 4301351952, 4301352326, 4301352394, 4301352395,
    #         4301352396, 4301352452, 4301352453, 4301352454, 4301352455, 4301351228, 4301352051, 4301352426, 4301352427, 4301352428, 4301352429, 4301352431, 4301352432, 4301352433, 4301351701,
    #         4301354385, 4301354386, 4301354387, 4301354388, 4301354389, 4301354447, 4301354448, 4301351126, 4301351127, 4301351128, 4301351143, 4301351259, 4301351271, 4301351272, 4301352465,
    #         4301352466, 4301332663, 4301334295, 4301334296, 4301350245, 4301350247, 4301350686, 4301351129, 4301351365, 4301351411, 4301351414, 4301352561, 4301350488, 4301350861, 4301352165,
    #         4301352166, 4301352167, 4301352168, 4301352169, 4301352170, 4301352171, 4301352330, 4301352331, 4301352332, 4301331705, 4301351541, 4301351840, 4301351843, 4301352400, 4301352401,
    #         4301351229, 4301351583, 4301352646, 4301352647, 4301352648, 4301352649, 4301351230, 4301351584, 4301351236, 4301351237, 4301351239, 4301351024, 4301350888, 4301332721, 4301333055,
    #         4301351310, 4301351596, 4301352369, 4301352390, 4301352643, 4301352644, 4301352645]
    # tsr_data = [[26, 4, "S", 4, "W", "U"],
    #             [27, 4, "S", 4, "W", "U"],
    #             [28, 4, "S", 4, "W", "U"],
    #             [29, 4, "S", 4, "W", "U"],
    #             [30, 4, "S", 4, "W", "U"],
    #             [31, 4, "S", 4, "W", "U"],
    #             [32, 4, "S", 4, "W", "U"],
    #             [33, 4, "S", 4, "W", "U"],
    #             [34, 4, "S", 4, "W", "U"],
    #             [35, 4, "S", 4, "W", "U"],
    #             [25, 4, "S", 5, "W", "U"],
    #             [26, 4, "S", 5, "W", "U"],
    #             [27, 4, "S", 5, "W", "U"],
    #             [28, 4, "S", 5, "W", "U"],
    #             [29, 4, "S", 5, "W", "U"],
    #             [35, 4, "S", 5, "W", "U"],
    #             [36, 4, "S", 5, "W", "U"],
    #             [1, 5, "S", 4, "W", "U"],
    #             [2, 5, "S", 4, "W", "U"],
    #             [3, 5, "S", 4, "W", "U"],
    #             [4, 5, "S", 4, "W", "U"],
    #             [5, 5, "S", 4, "W", "U"],
    #             [10, 5, "S", 4, "W", "U"],
    #             [11, 5, "S", 4, "W", "U"],
    #             [12, 5, "S", 4, "W", "U"],
    #             [1, 5, "S", 5, "W", "U"],
    #             [2, 5, "S", 5, "W", "U"],
    #             [3, 5, "S", 5, "W", "U"],
    #             [4, 5, "S", 5, "W", "U"],
    #             [5, 5, "S", 5, "W", "U"],
    #             [10, 5, "S", 5, "W", "U"],
    #             [11, 5, "S", 5, "W", "U"],
    #             [12, 5, "S", 5, "W", "U"],
    #             [6, 5, "S", 3, "W", "U"]]
    # year, month = '2024', 'May'
    # doEverything(label, [], year, month, df_many, tsr_data)
    #
    # label = 'Docket No. 2024-023 Cause No. 132-36'
    # apds = [4301354408, 4301354407, 4301354384]
    # year, month = '2024', 'June'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-031 Cause No. 132-39'
    # apds = [4301352761, 4301352760]
    # year, month = '2024', 'June'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-032 Cause No. 132-40'
    # apds = [4301353586]
    # year, month = '2024', 'June'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-034 Cause No. 132-41'
    # apds = [4301354087]
    # year, month = '2024', 'June'
    # doEverything(label, apds, year, month, df_many, [])
    #
    # label = 'Docket No. 2024-035 Cause No. 132-42'
    # apds = [4301354304]
    # year, month = '2024', 'June'
    # doEverything(label, apds, year, month, df_many, [])
    # #
    # label = 'Docket No. 2024-033 Cause No. 130-33'
    # apds = [4301354304]
    # year, month = '2024', 'June'
    # tsr_data = [[15, 4, "S", 4, "W", "U"],
    #             [16, 4, "S", 4, "W", "U"],
    #             [17, 4, "S", 4, "W", "U"],
    #             [18, 4, "S", 4, "W", "U"],
    #             [19, 4, "S", 4, "W", "U"],
    #             [20, 4, "S", 4, "W", "U"],
    #             [21, 4, "S", 4, "W", "U"],
    #             [22, 4, "S", 4, "W", "U"],
    #             [13, 4, "S", 5, "W", "U"],
    #             [24, 4, "S", 5, "W", "U"]]
    # doEverything(label, apds, year, month, df_many, tsr_data)
    #
    # label = 'Docket No. 2024-028 Cause No. 470-13'
    # apds = []
    # year, month = '2024', 'June'
    # tsr_data = [[16, 11, "S", 23, "E", "S"],
    #             [21, 11, "S", 23, "E", "S"],
    #             [28, 11, "S", 23, "E", "S"],
    #             [33, 11, "S", 23, "E", "S"]]
    # doEverything(label, apds, year, month, df_many, tsr_data)

    # apds = list(set(apds))
    # apds = [int(float(str(i)[:10])) for i in apds]
    # conn, cursor = sqlConnect()
    #
    # df, df_dx, df_plat = createDataFrame(apds, cursor, label, conn)
    #
    # # df_prod = sqlProductionDFGenerate(df['WellID'].unique().tolist(), cursor, conn)
    #
    # df['MainWell'] = df['WellID'].isin([str(i) for i in apds])
    # current_dir = os.getcwd()
    # # name = label + " Viz Data.db"
    # name = 'Board_DB.db'
    # apd_data_dir = os.path.join(current_dir, name)
    # conn_db = sqlite3.connect(apd_data_dir)
    # cursor_db = conn_db.cursor()
    # df['Board_Docket'] = label
    # df['Docket_Month'] = month
    # df['Board_Year'] = year
    # # foo = df_dx[df_dx['WellNameNumber'].str.contains('Dill', case=False)]
    # df_prod = None
    # writeToDatabase(conn_db, cursor_db, df, df_dx, df_plat, df_prod)


def setup():
    name = 'Board_DB.db'
    current_dir = os.getcwd()
    apd_data_dir = os.path.join(current_dir, name)
    conn_db = sqlite3.connect(apd_data_dir)
    cursor = conn_db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    # Fetch all results
    tables = cursor.fetchall()

    # Print the table names
    print("Tables in the database:")
    for table in tables:
        print(table[0])

    conn_db.execute('DROP TABLE IF EXISTS WellInfo')
    conn_db.execute('DROP TABLE IF EXISTS DX')
    conn_db.execute('DROP TABLE IF EXISTS PlatData')
    conn_db.execute('DROP TABLE IF EXISTS Production')
    conn_db.execute('DROP TABLE IF EXISTS Adjacent')
    conn_db.execute('DROP TABLE IF EXISTS BoardDataLinks')
    conn_db.execute('DROP TABLE IF EXISTS BoardData')


def doEverything(label, apds, year, month, df_many, tsr_data):
    ma.printLineBreak()
    ma.printLineBreak()
    ma.printLineBreak()
    ma.printLineBreak()

    print(label)
    print(apds)
    current_dir = os.getcwd()
    name = 'Board_DB.db'
    apd_data_dir = os.path.join(current_dir, name)
    conn_db = sqlite3.connect(apd_data_dir)
    cursor_db = conn_db.cursor()

    apds = list(set(apds))
    apds = [int(float(str(i)[:10])) for i in apds]
    conn, cursor = sqlConnect()
    time_start = time.perf_counter()

    df, df_dx, df_plat, df_board_data, df_links_data = createDataFrame(apds, cursor, label, conn, tsr_data)
    print('createDataFrame Retrieval Time: ', time.perf_counter() - time_start)

    time_start = time.perf_counter()

    df_prod = sqlProductionDFGenerate(df['WellID'].unique().tolist(), cursor, conn, df_many)
    print('sqlProductionDFGenerate Retrieval Time: ', time.perf_counter() - time_start)

    time_start = time.perf_counter()

    df_prod['Date'] = pd.to_datetime(df_prod['Date'], format='%Y-%m')
    df_prod = df_prod.sort_values(by=['WellID', 'Date'], ascending=[True, True])
    print('Data Retrieval Time: ', time.perf_counter() - time_start)

    time_start = time.perf_counter()

    df['MainWell'] = df['WellID'].isin([str(i) for i in apds])

    df['Board_Docket'] = label
    df['Docket_Month'] = month
    df['Board_Year'] = year
    # foo = df_dx[df_dx['WellNameNumber'].str.contains('Dill', case=False)]
    # df_prod = None
    print('Data Retrieval Time: ', time.perf_counter() - time_start)

    # writeToDatabase(conn_db, cursor_db, df, df_dx, df_plat, df_prod, df_links_data, df_board_data)


def createDataFrame(apds, cursor, label, conn, tsr_data):
    all_found_data = []
    dx_data_all = []
    apds_original = copy.deepcopy(apds)
    time_start = time.perf_counter()
    if not tsr_data.any():
        apds, all_plats_lst = findPlatsSurrounding(cursor, apds)
    else:
        apds, all_plats_lst = findPlatsSurroundingSectionsGiven(cursor, tsr_data)
    print('findPlatsSurrounding ', time.perf_counter() - time_start)
    time_start = time.perf_counter()

    df_board_data, df_links_data = retrieveBoardInformation(all_plats_lst, cursor)
    print('retrieveBoardInformation ', time.perf_counter() - time_start)
    time_start = time.perf_counter()

    df_plat = recordPlatData(all_plats_lst, label)
    print('recordPlatData ', time.perf_counter() - time_start)
    time_start = time.perf_counter()

    # retrieveConstructDataAllMega
    # output2, columns = retrieveConstructDataAllMega(cursor, apds, apds_original)

    output, columns = retrieveConstructDataAll(cursor, apds, apds_original)
    print('retrieveConstructDataAll ', time.perf_counter() - time_start)
    time_start = time.perf_counter()

    prod_data = sqlProdData(cursor, apds)
    print('sqlProdData ', time.perf_counter() - time_start)
    time_start = time.perf_counter()
    output = [output[i][:-2] + prod_data[output[i][0]] + [output[i][10]] + output[i][-2:] for i in range(len(output))]
    output_nonvert = [i for i in output if i[4] != 'VERTICAL']
    output_vert = [i for i in output if i[4] == 'VERTICAL']
    output_nonvert_apis = [i[0] for i in output_nonvert]
    dx_data_all = dbDXDataAll(cursor, output_nonvert_apis)

    for i in range(len(output_vert)):
        dx = dbSurfaceLocDrilled(cursor, output_vert[i][0], conn, output_vert[i])
        dx[0][0], dx[1][0] = output_vert[i][0], output_vert[i][0]
        dx[0][1], dx[1][1] = output_vert[i][1], output_vert[i][1]
        if dx:
            dx_data_all.extend(dx)


    # for i in range(len(output)):
    #     time_start44 = time.perf_counter()
    #     # output[i] = output[i][:-2] + prod_data[output[i][0]] + [output[i][10]] + output[i][-2:]
    #     if output[i][4] != 'VERTICAL':
    #         dx = dbDXData(cursor, output[i][0])
    #     else:
    #         dx = dbSurfaceLocDrilled(cursor, output[i][0], conn, output[i])
    #         dx[0][0], dx[1][0] = output[i][0], output[i][0]
    #         dx[0][1], dx[1][1] = output[i][1], output[i][1]
    #     if dx:
    #         dx_data_all.append(dx)

    print('dbSurfaceLocDrilled ', time.perf_counter() - time_start)
    time_start = time.perf_counter()
    for i in range(len(output)):
        output[i] = list(output[i])
        for j in range(len(output[i])):
            if output[i][j] is None:
                output[i][j] = ''
            output[i][j] = str(output[i][j]).strip()
    location_df = recordOutputLocation(output, cursor)
    print('recordOutputLocation ', time.perf_counter() - time_start)
    dx_columns = ['APINumber', 'WellNameNumber', 'MeasuredDepth', 'Inclination', 'Azimuth', 'TrueVerticalDepth', 'X', 'Y', 'CitingType']
    new_lst = []
    for i in dx_data_all:
        # for j in i:

            # data_line = j
        data_line = [str(j) for j in i]
        new_lst.append(data_line)
    dx_data_all = new_lst
    dx_data_all = [list(i) for i in dx_data_all]
    dx_data_all = [i for i in dx_data_all if i[1] != 'None']
    # findMissingDirectionals(cursor, dx_data_all, output)
    df_test_dx = [{'APINumber': i[0],
                   'WellNameNumber': i[1],
                   'MeasuredDepth': i[2],
                   'Inclination': i[3],
                   'Azimuth': i[4],
                   'TrueVerticalDepth': i[5],
                   'X': i[6],
                   'Y': i[7],
                   'CitingType': i[8]} for i in dx_data_all]

    df_test = [{'WellID': i[0],
                'WellName': i[1],
                'SideTrack': i[2],
                'WorkType': i[3],
                'Slant': i[4],
                'APDReceivedDate': i[5],
                'APDReturnDate': i[6],
                'APDApprovedDate': i[7],
                'APDExtDate': i[8],
                'APDRescindDate': i[9],
                'DrySpud': i[10],
                'RotarySpud': i[11],
                'WCRCompletionDate': i[12],
                'WellStatusReport': i[13],
                'WellTypeReport': i[14],
                'FirstProdDate': i[15],
                'TestDate': i[16],
                'ProductionMethod': i[17],
                'OilRate': i[18],
                'GasRate': i[19],
                'WaterRate': i[20],
                'DST': i[21],
                'DirSurveyRun': i[22],
                'CompletionType': i[23],
                'MD': i[24],
                'TVD': i[25],
                'Perforation MD': i[26],
                'Perforation TVD': i[27],
                'CurrentWellStatus': i[28],
                'CurrentWellType': i[29],
                'Total Gas Prod': i[30],
                'Total Oil Prod': i[31],
                'Well Age (months)': i[32],
                'Last Production (if Shut In)': i[33],
                'Months Shut In': i[34],
                'FieldName': i[35],
                'MineralLease': i[36]}
               for i in output]

    columns = [i for i, k in df_test[0].items()]
    df_dx = pd.DataFrame(df_test_dx, columns=dx_columns)
    df = pd.DataFrame(df_test, columns=columns)
    df = pd.merge(df, location_df, on='WellID')
    return df, df_dx, df_plat, df_board_data, df_links_data


def retrieveBoardInformation(all_plats_lst, cursor):

    board_matters = sqlFindBoardMatterInformationAll(all_plats_lst, cursor)
    board_matters = ma.removeDupesListOfLists(board_matters)
    know_board_matters = set([i[1] for i in board_matters])
    # board_matters, know_board_matters = [], []
    # for i in all_plats_lst:
    #     output = sqlFindBoardMatterInformation(i, cursor)
    #     if output:
    #         board_matters.extend(output)
    #         for j in output:
    #             if j[1] not in know_board_matters:
    #                 know_board_matters.append(j[1])
    board_matters = [i for i in board_matters if i]
    links_data = sqlFindBoardMatterLinks(know_board_matters, cursor)
    board_matters_dict = [{'DocketNumber': i[0],
                           'CauseNumber': i[1],
                           'OrderType': i[2],
                           'EffectiveDate': i[3],
                           'EndDate': i[4],
                           'FormationName': i[5],
                           'Quarter': i[6],
                           'QuarterQuarter': i[7],
                           'Sec': i[8],
                           'Township': i[9],
                           'TownshipDir': i[10],
                           'Range': i[11],
                           'RangeDir': i[12],
                           'PM': i[13],
                           'CountyName': i[14],
                           'Quip': i[15]} for i in board_matters]
    links_data_dict = [{'Cause': i[0],
                        'OGMDocumentName': i[1],
                        'Description': i[2],
                        'Filepath': i[3],
                        'DocumentDate': i[4]} for i in links_data]

    df_links_data = pd.DataFrame(board_matters_dict, columns=['DocketNumber', 'CauseNumber', 'OrderType', 'EffectiveDate', 'EndDate', 'FormationName',
                                                              'Quarter', 'QuarterQuarter', 'Sec', 'Township', 'TownshipDir', 'Range', 'RangeDir', 'PM', 'CountyName', 'Quip'])
    df_board_data = pd.DataFrame(links_data_dict, columns=['Cause', 'OGMDocumentName', 'Description', 'Filepath', 'DocumentDate'])
    return df_board_data, df_links_data


def recordPlatData(all_plats_lst, label):
    df = sqlConnectPlats()
    df_all = pd.DataFrame(columns=['Section', 'Township', 'Township Direction', 'Range', 'Range Direction',
                                   'Baseline', 'Lat', 'Lon', 'Well', 'Conc', 'Version', 'Apd_no', 'Board_Docket'])
    # print(df['Conc'].unique().tolist())
    def process_plat(group):
        plat_versions = group['Version'].unique()
        if len(plat_versions) > 1:
            plat_versions = [i for i in plat_versions if i != 'AGRC V.1']
            used_version = plat_versions[0]
        else:
            used_version = plat_versions[0]
        filtered_plat = group[group['Version'] == used_version]
        filtered_plat['Board_Docket'] = label
        return filtered_plat

    # Translate the elements of all_plats_lst
    all_plats_lst_translated = [ma.reTranslateDataNoPD(sublist) for sublist in all_plats_lst]


    #############
    conc_values = set(df['Conc'].unique())

    # Convert all_plats_lst_translated to a set
    all_plats_set = set(all_plats_lst_translated)

    # Find the values in all_plats_lst_translated that aren't in the 'Conc' column
    missing_values = all_plats_set - conc_values

    print("Values in all_plats_lst_translated not found in the dataframe:", missing_values)

    ##############

    # Filter the dataframe to include only rows where 'Conc' is in all_plats_lst_translated
    df_filtered = df[df['Conc'].isin(all_plats_lst_translated)]

    # Group the filtered dataframe by 'Conc' and apply the process_plat function
    df_processed = df_filtered.groupby('Conc').apply(process_plat)

    # Concatenate the processed dataframe with df_all
    df_all = pd.concat([df_all, df_processed], ignore_index=True)
    return df_all

    #
    # def process_plat(group):
    #     plat_versions = group['Version'].unique()
    #     if len(plat_versions) > 1:
    #         plat_versions = [i for i in plat_versions if i != 'AGRC V.1']
    #         used_version = plat_versions[0]
    #     else:
    #         used_version = plat_versions[0]
    #     filtered_plat = group[group['Version'] == used_version]
    #     filtered_plat['Board_Docket'] = label
    #     return filtered_plat
    #
    # # Create a dataframe from all_plats_lst
    # all_plats_df = pd.DataFrame(all_plats_lst, columns=['Section', 'Township', 'TownshipDir', 'Range', 'RangeDir', 'Baseline'])
    #
    # # Apply the reTranslateData function to each row of all_plats_df
    # all_plats_df['Conc'] = all_plats_df.apply(ma.reTranslateData, axis=1)
    #
    # # Merge df with all_plats_df based on the 'Conc' column
    # merged_df = pd.merge(df, all_plats_df[['Conc']], on='Conc', how='inner')
    #
    # # Group the merged dataframe by 'Conc' and apply the process_plat function
    # df_processed = merged_df.groupby('Conc').apply(process_plat)
    #
    # # Reset the index of the processed dataframe
    # df_all = df_processed.reset_index(drop=True)

    df_all_parts = []
    for i in all_plats_lst:
        conc = ma.reTranslateData(i)
        current_plat = df[df['Conc'].isin([conc])]
        if not current_plat.empty:
            plat_versions = current_plat['Version'].unique()
            if len(plat_versions) > 1:
                plat_versions = [i for i in plat_versions if i != 'AGRC V.1']
                used_version = plat_versions[0]
            else:
                used_version = plat_versions[0]
            filtered_plat = current_plat[current_plat['Version'] == used_version]
            filtered_plat['Board_Docket'] = label

            df_all_parts.append(filtered_plat)

    df_all = pd.concat([df_all] + df_all_parts)
    #
    # time_start = time.perf_counter()
    # df_all = pd.DataFrame(columns=['Section', 'Township', 'Township Direction', 'Range', 'Range Direction',
    #                                'Baseline', 'Lat', 'Lon', 'Well', 'Conc', 'Version', 'Apd_no', 'Board_Docket'])
    # for i in all_plats_lst:
    #     conc = ma.reTranslateData(i)
    #     current_plat = df[df['Conc'].str.contains(conc)]
    #     plat_versions = current_plat['Version'].unique()
    #     if not current_plat.empty:
    #         if len(plat_versions) > 1:
    #             plat_versions = [i for i in plat_versions if i != 'AGRC V.1']
    #             used_version = plat_versions[0]
    #         else:
    #             used_version = plat_versions[0]
    #         current_plat = current_plat[current_plat['Version'] == used_version]
    #         current_plat['Board_Docket'] = label
    #         df_all = pd.concat([df_all, current_plat])
    #     else:
    #         pass


    # fig, ax = plt.subplots()
    #
    # for conc, group in df_all.groupby('Conc'):
    #     latitudes = group['Lat'].tolist()
    #     longitudes = group['Lon'].tolist()
    #     latitudes.append(group['Lat'].iloc[0])  # Closing the polygon
    #     longitudes.append(group['Lon'].iloc[0])  # Closing the polygon
    #     ax.plot(longitudes, latitudes, marker='o', label=f'Polygon {conc}')
    #
    # ax.set_xlabelagrc
    # ax.set_ylabel('Latitude')
    # ax.legend()
    # plt.title('Polygons by Conc')
    # plt.show()
    return df_all



def recordOutputLocation(lst, cursor):
    # df = pd.DataFrame(columns=['WellAPI', 'Elevation', 'ConcCode'])
    data_line = []
    api_lst = [i[0] for i in lst]
    all_data = dbTownshipAndRangeAndElevationAll(cursor, api_lst)

    for i in lst:
        api = i[0]
        line = all_data[api]
        # line = dbTownshipAndRangeAndElevation(cursor, api)
        conc_data = list(line[2:])
        conc = ma.reTranslateData(conc_data)
        new_line = list(line[:2]) + [conc]
        data_line.append(new_line)

    test_lst = [{'WellID': i[0],
                 'Elevation': i[1],
                 'ConcCode': i[2]} for i in data_line]
    df_test_dx = pd.DataFrame(test_lst, columns=['WellID', 'Elevation', 'ConcCode'])
    return df_test_dx


def findMissingDirectionals(cursor, dx_data_all, output):
    dx_apis = list(set([i[0] for i in output]))
    dx_data_apis = list(set([i[0] for i in dx_data_all]))

    missing_dx = [i for i in dx_apis if i not in dx_data_apis]
    missing_data = [i for i in output if i[0] in missing_dx]
    for i in missing_data:
        if i[4] != 'VERTICAL':
            output = dbDXDataConstruct(cursor, str(i[0]))

    pass


def assembleVerticalWell():
    pass


def findPlatsSurroundingSectionsGiven(cursor, all_plats_lst):
    all_coords_lst = []
    for i in all_plats_lst:
        foo = sqlFindAllInSection(i, cursor)
        if foo:
            for j in foo:
                if str(j[0]) != 'None':
                    all_coords_lst.append(list(j))
    # coords_df = pd.DataFrame(all_coords_lst, columns=['API', 'APDNo', 'Slant', 'X', 'Y']).drop_duplicates(keep="first")
    # coords_df['API'] = coords_df['API'].str.slice(0, 10)
    # coords_df = coords_df[coords_df['API'].isin([str(i) for i in apds])].reset_index(drop=True)
    # used_apds_lst = coords_df.values.tolist()

    # distances = []
    # for i in used_apds_lst:
    #     for j in all_coords_lst:
    #         distances.append(ma.equationDistance(i[-2], i[-1], j[-2], j[-1]))
    all_apds = [int(float(i[0][:10])) for i in all_coords_lst]
    all_apds = list(set(all_apds))
    all_plats_lst = ma.removeDupesListOfLists(all_plats_lst)

    return all_apds, all_plats_lst


def findPlatsSurrounding(cursor, apds):
    plat_data = []
    all_plats_lst = []
    all_coords_lst = []
    plats_apis = []
    data_done = dbTownshipAndRangeMany(cursor, apds)

    test_lst = []
    for output in data_done:
        output[0], output[1], output[3] = int(float(output[0])), int(float(output[1])), int(float(output[3]))
        all_plats_test = processSections(output[0], output[1], output[2], output[3], output[4], output[5])
        test_lst.extend(all_plats_test)
    #     output = dbTownshipAndRange(cursor, i)
    test_lst = ma.removeDupesListOfLists(test_lst)
    all_plats_lst = sorted(test_lst, key=lambda r: r[0])
    # for i in apds:
    #     output = dbTownshipAndRange(cursor, i)
    #     for j in range(len(output)):
    #         output[j][0], output[j][1], output[j][3] = str(int(float(output[j][0]))), str(int(float(output[j][1]))), str(int(float(output[j][3])))
    #     if output and not any(list(output[0]) == sublist for sublist in plat_data):
    #         for j in range(len(output)):
    #             output[j][0], output[j][1], output[j][3] = int(float(output[j][0])), int(float(output[j][1])), int(float(output[j][3]))
    #             all_plats = processSections(output[j][0], output[j][1], output[j][2], output[j][3], output[j][4], output[j][5])
    #             all_plats_lst.extend(all_plats)
    #             all_plats_lst.append(list(output[j]))
    #             plat_data.append(list(output[0]))
    #

    # all_plats_lst = ma.removeDupesListOfLists(all_plats_lst)
    # all_plats_lst = sorted(all_plats_lst, key=lambda r: r[0])
    result = sqlFindAllInSectionAll(all_plats_lst, cursor)
    all_coords_lst = ma.removeDupesListOfLists(result)
    all_coords_lst = [list(i) for i in all_coords_lst]

    # for i in all_plats_lst:
    #     foo = sqlFindAllInSection(i, cursor)
    #     if foo:
    #         for j in foo:
    #             if str(j[0]) != 'None':
    #                 all_coords_lst.append(list(j))
    #
    # all_coords_lst = ma.removeDupesListOfLists(all_coords_lst)

    # coords_df = pd.DataFrame(all_coords_lst, columns=['API', 'APDNo', 'Slant', 'X', 'Y']).drop_duplicates(keep="first")
    # coords_df['API'] = coords_df['API'].str.slice(0, 10)
    # coords_df = coords_df[coords_df['API'].isin([str(i) for i in apds])].reset_index(drop=True)
    # used_apds_lst = coords_df.values.tolist()

    # all_coords_lst = ma.removeDupesListOfLists(all_coords_lst)
    # all_coords_lst = [i for i in all_coords_lst if i[0] is not None]
    # all_coords_lst = [i for i in all_coords_lst if i != []]
    # for i, value in enumerate(all_coords_lst):
    #     all_coords_lst[i][0] = all_coords_lst[i][0][:10]
    #
    # for i, value in enumerate(all_coords_lst):
    #     if int(float(value[0])) in apds:
    #         pass
    #     else:
    #         all_coords_lst[i] = []
    # all_coords_lst = [i for i in all_coords_lst if i != []]

    # used_apds_lst = [[j for j in all_coords_lst if str(i) in j[0]][0] for i in apds]
    # used_apds_lst = [[j for j in all_coords_lst if str(i) in j[0]][0] for i in apds]
    # distances = []
    # for i in used_apds_lst:
    #     for j in all_coords_lst:
    #         distances.append(ma.equationDistance(i[-2], i[-1], j[-2], j[-1]))
    all_apds = [int(float(i[0][:10])) for i in all_coords_lst]
    all_apds = list(set(all_apds))
    all_plats_lst = ma.removeDupesListOfLists(all_plats_lst)
    return all_apds, all_plats_lst


def findMorePlats(apds, cursor):
    all_plats_lst = dbTownshipAndRangeMany(cursor, apds)
    all_plats_lst = ma.removeDupesListOfLists(all_plats_lst)
    return all_plats_lst


def findDatabaseInfoForSections(data):
    section, twsp, twsp_dir, rng, rng_dir, mer = data
    twsp_dir = ma.translateDirectionToNumber('township', str(twsp_dir))
    rng_dir = ma.translateDirectionToNumber('rng', str(rng_dir))
    mer = ma.translateDirectionToNumber('baseline', str(mer))
    current_dir = os.getcwd()
    apd_data_dir = os.path.join(current_dir, "APD_Data.db")
    conn = sqlite3.connect(apd_data_dir)
    cursor = conn.cursor()
    string_sql = f"""select * from SectionDataCoordinates WHERE Township = {twsp} AND [Township Direction] = {twsp_dir} AND Range = {rng} AND [Range Direction] = {rng_dir} AND Baseline = {mer} and Section = {section}"""
    df = pd.read_sql(string_sql, conn, index_col='index')
    # all_sections =


def writeToDatabase(conn, cursor, df_info, df_dx, df_plat, df_prod, df_board_data, df_links_data):
    #
    #
    # string_sql = 'select * from WellInfo'
    # df_foo = pd.read_sql(string_sql, conn, index_col='index')

    # writeToDB(df_info, cursor, conn, 'WellInfo')

    #
    #
    # cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    # tables = cursor.fetchall()
    # # Extract column names from the CREATE TABLE SQL statements
    # columns = set()
    # for table in tables:
    #
    #     create_table_sql = table[0]
    #     start_index = create_table_sql.index('(') + 1
    #     end_index = create_table_sql.rindex(')')
    #     columns_list = create_table_sql[start_index:end_index].split(',')
    #     for column in columns_list:
    #         column_name = column.strip().split()[0]
    #         columns.add(column_name)
    #
    # conn.execute('DROP TABLE IF EXISTS WellInfo')
    try:
        df_info.to_sql('WellInfo', conn, index=False, if_exists='append')
    except ValueError:
        pass
    # conn.execute('DROP TABLE IF EXISTS DX')
    try:
        df_dx.to_sql('DX', conn, index=False, if_exists='append')
    except ValueError:
        pass
    # conn.execute('DROP TABLE IF EXISTS PlatData')
    try:
        df_plat.to_sql('PlatData', conn, index=False, if_exists='append')
    except ValueError:
        pass

    # conn.execute('DROP TABLE IF EXISTS Production')
    try:
        df_prod.to_sql('Production', conn, index=False, if_exists='append')
    except (ValueError, AttributeError):
        pass

    # conn.execute('DROP TABLE IF EXISTS Production')
    try:
        df_board_data.to_sql('BoardData', conn, index=False, if_exists='append')
    except (ValueError, AttributeError):
        pass

    # conn.execute('DROP TABLE IF EXISTS Production')
    try:
        df_links_data.to_sql('BoardDataLinks', conn, index=False, if_exists='append')
    except (ValueError, AttributeError):
        pass

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table[0]}", conn)
        df = df.drop_duplicates()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        conn.commit()
        cursor.execute(f"DELETE FROM {table[0]};")
        conn.commit()
        df.to_sql(table[0], conn, if_exists='append', index=False)
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

    # headers = df_info.columns.tolist()
    # headers_strings = ["'" + str(i) + "'" for i in headers]
    # headers_lst = ', '.join(headers_strings)
    # insert_str = '''INSERT INTO WellInfo(''' + headers_lst + ")"
    # # insert_str = '''INSERT INTO WellInfo('WellID', 'WellName', 'SideTrack', 'WorkType', 'Slant', 'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud', 'WCRCompletionDate', 'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType', 'MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'CurrentWellStatus', 'CurrentWellType', 'Last Production (if Shut In)', 'Months Shut In')'''
    # # insert_str_dx = '''INSERT INTO WellInfo('APINumber', 'WellNameNumber', 'MeasuredDepth', 'Inclination', 'Azimuth', 'TrueVerticalDepth', 'X', 'Y')'''
    # lst = ["?"] * df_info.shape[1]
    # lst = ', '.join([f"{str(elem)}" for elem in lst])
    # values_str = 'VALUES(' + lst + ");"
    # for i in info_data:
    #     data_str = i
    #     data_str = [str(i) for i in data_str]
    #     query = insert_str + values_str
    #     cursor.execute(query, data_str)
    #     conn.commit()
    #
    print("\n\nProd")
    ma.printLineBreak()
    string_sql = 'select * from Production'
    df_foo = pd.read_sql(string_sql, conn)
    print(len(df_foo))

    print("\n\nPlatData")
    ma.printLineBreak()
    string_sql = 'select * from PlatData'
    df_foo = pd.read_sql(string_sql, conn)
    print(len(df_foo))
    print("\n\nWellInfo")
    ma.printLineBreak()
    string_sql = 'select * from WellInfo'
    df_foo = pd.read_sql(string_sql, conn)
    # print(df_foo['Board_Docket'].unique())
    print(len(df_foo))
    print("\n\nDX")
    ma.printLineBreak()
    string_sql = 'select * from DX'
    df_foo = pd.read_sql(string_sql, conn)
    print(len(df_foo))
    # print(len(df_board_data))
    # print('data written')


def writeToDB(df, cursor, conn, table_name):
    try:
        string_sql = f'''select * from "{table_name}"'''
        df_foo = pd.read_sql(string_sql, conn)
    except pandas.errors.DatabaseError:
        df_foo = pd.DataFrame(columns=df.columns)

    info_data = df.to_numpy().tolist()
    headers = df.columns.tolist()
    headers_strings = ["'" + str(i) + "'" for i in headers]
    headers_lst = ', '.join(headers_strings)
    insert_str = f'''INSERT INTO {table_name}(''' + headers_lst + ")"

    # insert_str = '''INSERT INTO WellInfo('WellID', 'WellName', 'SideTrack', 'WorkType', 'Slant', 'APDReceivedDate', 'APDReturnDate', 'APDApprovedDate', 'APDExtDate', 'APDRescindDate', 'DrySpud', 'RotarySpud', 'WCRCompletionDate', 'WellStatusReport', 'WellTypeReport', 'FirstProdDate', 'TestDate', 'ProductionMethod', 'OilRate', 'GasRate', 'WaterRate', 'DST', 'DirSurveyRun', 'CompletionType', 'MD', 'TVD', 'Perforation MD', 'Perforation TVD', 'CurrentWellStatus', 'CurrentWellType', 'Last Production (if Shut In)', 'Months Shut In')'''
    lst = ["?"] * df.shape[1]
    lst = ', '.join([f"{str(elem)}" for elem in lst])
    values_str = 'VALUES(' + lst + ");"
    for i in info_data:
        data_str = i
        data_str = [str(i) for i in data_str]
        query = insert_str + values_str
        cursor.execute(query, data_str)
        conn.commit()


def checkIfDuplicates(data1, data2):
    is_subset = data1.isin(data2).all().all()


# def retrieveConstructDataAll(cursor, well_id, apds_original):
#     apis = [str(i) for i in well_id]
#     apis = ', '.join([f"'{str(elem)}'" for elem in apis])
#     sql_query = f"""
#         SELECT
#             w.WellID,
#             w.WellName,
#             c.SideTrack,
#             wh.WorkType,
#             CASE
#                 When vsl.ConstructType = 'D' then 'DIRECTIONAL'
#                 When vsl.ConstructType = 'H' then 'HORIZONTAL'
#                 When vsl.ConstructType = 'V' then 'VERTICAL'
#             END as 'Slant',
#             CONVERT(char(10), wh.APDReceivedDate, 101) as 'APDReceivedDate',
#             CONVERT(char(10), wh.APDReturnDate, 101) as 'APDReturnDate',
#             CONVERT(char(10), wh.APDApprovedDate, 101) as 'APDApprovedDate',
#             CONVERT(char(10), wh.APDExtDate, 101) as 'APDExtDate',
#             CONVERT(char(10), wh.APDRescindDate, 101) as 'APDRescindDate',
#             vsc.DrySpud,
#             vsc.RotarySpud,
#             CONVERT(char(10), wh.WCRCompletionDate, 101) as 'WCRCompletionDate',
#             wh.ReportStatus as 'WellStatusReport',
#             wh.WellTypeReport,
#             vfp.FirstProdDate,
#             vpt.TestDate,
#             vpt.ProductionMethod,
#             vpt.OilRate,
#             vpt.GasRate,
#             vpt.WaterRate,
#             vs.DST,
#             vs.DirSurveyRun,
#             vs.CompletionType,
#             vd.DTD as 'MD',
#             vd.TVD,
#             vd.PBMD as "Perforation MD",
#             vd.PBTVD as "Perforation TVD",
#             w.WellStatus as 'CurrentWellStatus',
#             w.WellType as 'CurrentWellType',
#             shut.LastProductionPeriod as 'Last Production (if Shut In)',
#             shut.MonthsShutIn as 'Months Shut In'
#         FROM
#             Well w
#             LEFT JOIN WellHistory wh on wh.WellKey = w.pkey
#             LEFT JOIN vw_DON_WH_SPUDdates vsc on vsc.HistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_APDNO van on van.HistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_SLANT vsl on vsl.SlantHistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_FirstProdDate vfp on vfp.FirstProdHistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_ProdTest vpt on vpt.WHPkey = wh.PKey
#             LEFT JOIN vw_DON_WH_Surveys vs on vs.whKey = wh.PKey
#             LEFT JOIN vw_DON_WH_Depths vd on vd.whPkey = wh.PKey
#             LEFT JOIN Construct c on c.pkey = wh.ConstructKey
#             LEFT JOIN ShutInAbandonedSuspendedWellsRpt shut on shut.API10 = w.WellID
#         WHERE
#             w.WellID IN ({apis}) and wh.WorkType != 'REPERF'
#         """
#
#     # Execute the query with the parameter
#     # cursor.execute(sql_query)
#     # columns = [column[0] for column in cursor.description]
#     # result = cursor.fetchall()
#     # new_lst = []
#     # for i in range(len(result)):
#     #     if str(result[i][0]) in [str(j) for j in apds_original]:
#     #         new_lst.append(list(result[i]))
#     #     else:
#     #         if result[i][-8] is not None:
#     #             new_lst.append(list(result[i]))
#     # result = new_lst
#     # result = ma.removeDupesListOfLists(result)
#     #
#     # for i in range(len(result)):
#     #     result[i][13] = dbRefCodesTranslateStatus(cursor, result[i][13])
#     #     result[i][14] = dbRefCodesTranslateType(cursor, result[i][14])
#     #     result[i][-4] = dbRefCodesTranslateStatus(cursor, result[i][-4])
#     #     result[i][-3] = dbRefCodesTranslateType(cursor, result[i][-3])
#     #     if result[i][4] == 'VERTICAL' and result[i][-7] is None and result[i][-8] is not None:
#     #         result[i][-7] = result[i][-8]
#     #
#     # result = [list(i) for i in result]
#     # result = [i for i in result if i[3].lower() in ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug')]
#     #
#     # return list(result), columns
#
#     cursor.execute(sql_query)
#     columns = [column[0] for column in cursor.description]
#     result = cursor.fetchall()
#     for i in range(len(result)):
#         result[i][13] = dbRefCodesTranslateStatus(cursor, result[i][13])
#         result[i][14] = dbRefCodesTranslateType(cursor, result[i][14])
#         result[i][-4] = dbRefCodesTranslateStatus(cursor, result[i][-4])
#         result[i][-3] = dbRefCodesTranslateType(cursor, result[i][-3])
#         if result[i][4] == 'VERTICAL' and result[i][-7] is None and result[i][-8] is not None:
#             result[i][-7] = result[i][-8]
#     new_lst = []
#     for i in range(len(result)):
#         if result[i][-4] not in ['Location Abandoned - APD rescinded', 'Returned APD (Unapproved)']:
#             if str(result[i][0]) in [str(j) for j in apds_original]:
#                 new_lst.append(list(result[i]))
#             else:
#                 if result[i][-8] is not None:
#                     new_lst.append(list(result[i]))
#                 else:
#                     # pass
#                     result[i] = list(result[i])
#                     result[i][24:26] = findDepthsIfInitFailed(cursor, result[i][0], result[i][2])
#                     new_lst.append(list(result[i]))
#
#     result = new_lst
#     result = sorted(result, key=lambda r: r[0])
#
#     result = ma.removeDupesListOfLists(result)
#
#     result = [list(i) for i in result]
#     return list(result), columns
def retrieveConstructDataAllMega(cursor, well_id, apds_original):
    apis = [str(i) for i in well_id]
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    sql_query = f"""
        SELECT 
            w.WellID,
            w.WellName,
            c.SideTrack,
            wh.WorkType, 
            CASE 
                When vsl.ConstructType = 'D' then 'DIRECTIONAL'
                When vsl.ConstructType = 'H' then 'HORIZONTAL'    
                When vsl.ConstructType = 'V' then 'VERTICAL'    
            END as 'Slant', 
            CONVERT(char(10), wh.APDReceivedDate, 101) as 'APDReceivedDate', 
            CONVERT(char(10), wh.APDReturnDate, 101) as 'APDReturnDate',
            CONVERT(char(10), wh.APDApprovedDate, 101) as 'APDApprovedDate', 
            CONVERT(char(10), wh.APDExtDate, 101) as 'APDExtDate', 
            CONVERT(char(10), wh.APDRescindDate, 101) as 'APDRescindDate',
            vsc.DrySpud,
            vsc.RotarySpud, 
            CONVERT(char(10), wh.WCRCompletionDate, 101) as 'WCRCompletionDate', 
            wh.ReportStatus as 'WellStatusReport',
            wh.WellTypeReport, 
            vfp.FirstProdDate, 
            vpt.TestDate,
            vpt.ProductionMethod,
            vpt.OilRate,
            vpt.GasRate,
            vpt.WaterRate,
            vs.DST,
            vs.DirSurveyRun,
            vs.CompletionType, 
            vd.DTD as 'MD',
            vd.TVD, 
            vd.PBMD as "Perforation MD", 
            vd.PBTVD as "Perforation TVD", 
            w.WellStatus as 'CurrentWellStatus', 
            w.WellType as 'CurrentWellType', 
            shut.LastProductionPeriod as 'Last Production (if Shut In)', 
            shut.MonthsShutIn as 'Months Shut In',
            SUM(CASE WHEN pfp.ProdType = 'OIL' THEN CAST(pfp.prodquantity AS FLOAT) ELSE 0 END) AS 'Oil Volume',
            SUM(CASE WHEN pfp.ProdType = 'GAS' THEN CAST(pfp.prodquantity AS FLOAT) ELSE 0 END) AS 'Gas Volume',
            vsc.DrySpud,
            rf.FieldName, 
            CASE 
                when c.LeaseType = 'F' then 'FEDERAL'
                when c.LeaseType = 'I' then 'INDIAN'
                when c.LeaseType = 'S' then 'STATE'
                when c.LeaseType = 'P' then 'FEE'
                Else '5 - UNKNOWN'
            END AS 'Mineral Lease'

        FROM 
            Well w 
            LEFT JOIN WellHistory wh on wh.WellKey = w.pkey 
            LEFT JOIN vw_DON_WH_SPUDdates vsc on vsc.HistKey = wh.PKey 
            LEFT JOIN vw_DON_WH_APDNO van on van.HistKey = wh.PKey
            LEFT JOIN vw_DON_WH_SLANT vsl on vsl.SlantHistKey = wh.PKey
            LEFT JOIN vw_DON_WH_FirstProdDate vfp on vfp.FirstProdHistKey = wh.PKey
            LEFT JOIN vw_DON_WH_ProdTest vpt on vpt.WHPkey = wh.PKey 
            LEFT JOIN vw_DON_WH_Surveys vs on vs.whKey = wh.PKey 
            LEFT JOIN vw_DON_WH_Depths vd on vd.whPkey = wh.PKey 
            LEFT JOIN Construct c on c.pkey = wh.ConstructKey
            LEFT JOIN ShutInAbandonedSuspendedWellsRpt shut on shut.API10 = w.WellID
            LEFT JOIN RefFields rf on rf.PKey = c.FieldKey
            LEFT JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey
        WHERE 
            (wh.WorkType IN ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug')) 
            AND w.WellID IN ({apis}) and wh.WorkType != 'REPERF'
        GROUP BY
            w.WellID,
            w.WellName,
            c.SideTrack,
            wh.WorkType,
            vsl.ConstructType,
            wh.APDReceivedDate,
            wh.APDReturnDate,
            wh.APDApprovedDate,
            wh.APDExtDate,
            wh.APDRescindDate,
            vsc.DrySpud,
            vsc.RotarySpud,
            wh.WCRCompletionDate,
            wh.ReportStatus,
            wh.WellTypeReport,
            vfp.FirstProdDate,
            vpt.TestDate,
            vpt.ProductionMethod,
            vpt.OilRate,
            vpt.GasRate,
            vpt.WaterRate,
            vs.DST,
            vs.DirSurveyRun,
            vs.CompletionType,
            vd.DTD,
            vd.TVD,
            vd.PBMD,
            vd.PBTVD,
            w.WellStatus,
            w.WellType,
            shut.LastProductionPeriod,
            shut.MonthsShutIn,
            rf.FieldName,
            c.LeaseType
    """

    cursor.execute(sql_query)
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    df = pd.DataFrame(result, columns=columns)
    ref_codes = fetch_ref_codes(cursor)
    for i in range(len(result)):
        result[i] = list(result[i])  # Convert tuples to lists
        result[i][13] = ref_codes['WELLSTATUS'].get(result[i][13])
        result[i][14] = ref_codes['WELLTYPE'].get(result[i][14])
        result[i][28] = ref_codes['WELLSTATUS'].get(result[i][28])
        result[i][29] = ref_codes['WELLTYPE'].get(result[i][29])
        if result[i][4] == 'VERTICAL' and result[i][33] is None and result[i][25] is not None:
            result[i][36] = result[i][25]

    new_lst = []
    api_lst = [i[0] for i in result]
    extension_lst = [i[2] for i in result]

    returned_data = findDepthsIfInitFailedMass(cursor, api_lst, extension_lst)

    for i in range(len(result)):
        if result[i][13] not in ['Location Abandoned - APD rescinded', 'Returned APD (Unapproved)', 'Location Abandoned - APD rescinded']:
            if str(result[i][0]) in [str(j) for j in apds_original]:
                new_lst.append(list(result[i]))
            else:
                if result[i][25] is not None:
                    new_lst.append(list(result[i]))
                else:
                    result[i] = list(result[i])
                    out_data = returned_data[result[i][0]]
                    if out_data:
                        result[i][24:26] = out_data
                        new_lst.append(list(result[i]))

    # for i in range(len(result)):
    #     result[i][13] = ref_codes['WELLSTATUS'].get(result[i][13])
    #     result[i][14] = ref_codes['WELLTYPE'].get(result[i][14])
    #     result[i][28] = ref_codes['WELLSTATUS'].get(result[i][28])
    #     result[i][29] = ref_codes['WELLTYPE'].get(result[i][29])
    #     if result[i][4] == 'VERTICAL' and result[i][-9] is None and result[i][-12] is not None:
    #         result[i][-11] = result[i][-12]
    # new_lst = []
    # api_lst = [i[0] for i in result]
    # extension_lst = [i[2] for i in result]
    #
    # returned_data = findDepthsIfInitFailedMass(cursor, api_lst, extension_lst)
    #
    # for i in range(len(result)):
    #     if result[i][13] not in ['Location Abandoned - APD rescinded', 'Returned APD (Unapproved)', 'Location Abandoned - APD rescinded']:
    #         if str(result[i][0]) in [str(j) for j in apds_original]:
    #             new_lst.append(list(result[i]))
    #         else:
    #             if result[i][-12] is not None:
    #                 new_lst.append(list(result[i]))
    #             else:
    #                 result[i] = list(result[i])
    #
    #                 out_data = returned_data[result[i][0]]
    #                 if out_data:
    #                     result[i][24:26] = out_data
    #                     new_lst.append(list(result[i]))

    result = new_lst
    result = sorted(result, key=lambda r: r[0])
    result = ma.removeDupesListOfLists(result)
    result = [list(i) for i in result]
    return list(result), columns


def retrieveConstructDataAll(cursor, well_id, apds_original):
    # apis = [str(i) for i in well_id]
    # apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    # sql_query = f"""
    #         SELECT
    #             w.WellID,
    #             w.WellName,
    #             c.SideTrack,
    #             wh.WorkType,
    #             CASE
    #                 When vsl.ConstructType = 'D' then 'DIRECTIONAL'
    #                 When vsl.ConstructType = 'H' then 'HORIZONTAL'
    #                 When vsl.ConstructType = 'V' then 'VERTICAL'
    #             END as 'Slant',
    #             CONVERT(char(10), wh.APDReceivedDate, 101) as 'APDReceivedDate',
    #             CONVERT(char(10), wh.APDReturnDate, 101) as 'APDReturnDate',
    #             CONVERT(char(10), wh.APDApprovedDate, 101) as 'APDApprovedDate',
    #             CONVERT(char(10), wh.APDExtDate, 101) as 'APDExtDate',
    #             CONVERT(char(10), wh.APDRescindDate, 101) as 'APDRescindDate',
    #             vsc.DrySpud,
    #             vsc.RotarySpud,
    #             CONVERT(char(10), wh.WCRCompletionDate, 101) as 'WCRCompletionDate',
    #             wh.ReportStatus as 'WellStatusReport',
    #             wh.WellTypeReport,
    #             vfp.FirstProdDate,
    #             vpt.TestDate,
    #             vpt.ProductionMethod,
    #             vpt.OilRate,
    #             vpt.GasRate,
    #             vpt.WaterRate,
    #             vs.DST,
    #             vs.DirSurveyRun,
    #             vs.CompletionType,
    #             vd.DTD as 'MD',
    #             vd.TVD,
    #             vd.PBMD as "Perforation MD",
    #             vd.PBTVD as "Perforation TVD",
    #             w.WellStatus as 'CurrentWellStatus',
    #             w.WellType as 'CurrentWellType',
    #             shut.LastProductionPeriod as 'Last Production (if Shut In)',
    #             shut.MonthsShutIn as 'Months Shut In',
    #             SUM(CASE WHEN pfp.ProdType = 'OIL' THEN CAST(pfp.prodquantity AS FLOAT) ELSE 0 END) AS 'Oil Volume',
    #             SUM(CASE WHEN pfp.ProdType = 'GAS' THEN CAST(pfp.prodquantity AS FLOAT) ELSE 0 END) AS 'Gas Volume',
    #             vsc.DrySpud,
    #             rf.FieldName,
    #             CASE
    #                 when c.LeaseType = 'F' then 'FEDERAL'
    #                 when c.LeaseType = 'I' then 'INDIAN'
    #                 when c.LeaseType = 'S' then 'STATE'
    #                 when c.LeaseType = 'P' then 'FEE'
    #                 Else '5 - UNKNOWN'
    #             END AS 'Mineral Lease'
    #
    #         FROM
    #             Well w
    #             LEFT JOIN WellHistory wh on wh.WellKey = w.pkey
    #             LEFT JOIN vw_DON_WH_SPUDdates vsc on vsc.HistKey = wh.PKey
    #             LEFT JOIN vw_DON_WH_APDNO van on van.HistKey = wh.PKey
    #             LEFT JOIN vw_DON_WH_SLANT vsl on vsl.SlantHistKey = wh.PKey
    #             LEFT JOIN vw_DON_WH_FirstProdDate vfp on vfp.FirstProdHistKey = wh.PKey
    #             LEFT JOIN vw_DON_WH_ProdTest vpt on vpt.WHPkey = wh.PKey
    #             LEFT JOIN vw_DON_WH_Surveys vs on vs.whKey = wh.PKey
    #             LEFT JOIN vw_DON_WH_Depths vd on vd.whPkey = wh.PKey
    #             LEFT JOIN Construct c on c.pkey = wh.ConstructKey
    #             LEFT JOIN ShutInAbandonedSuspendedWellsRpt shut on shut.API10 = w.WellID
    #             LEFT JOIN RefFields rf on rf.PKey = c.FieldKey
    #             LEFT JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey
    #         WHERE
    #             (wh.WorkType IN ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug'))
    #             AND w.WellID IN ({apis}) and wh.WorkType != 'REPERF'
    #         GROUP BY
    #             w.WellID,
    #             w.WellName,
    #             c.SideTrack,
    #             wh.WorkType,
    #             vsl.ConstructType,
    #             wh.APDReceivedDate,
    #             wh.APDReturnDate,
    #             wh.APDApprovedDate,
    #             wh.APDExtDate,
    #             wh.APDRescindDate,
    #             vsc.DrySpud,
    #             vsc.RotarySpud,
    #             wh.WCRCompletionDate,
    #             wh.ReportStatus,
    #             wh.WellTypeReport,
    #             vfp.FirstProdDate,
    #             vpt.TestDate,
    #             vpt.ProductionMethod,
    #             vpt.OilRate,
    #             vpt.GasRate,
    #             vpt.WaterRate,
    #             vs.DST,
    #             vs.DirSurveyRun,
    #             vs.CompletionType,
    #             vd.DTD,
    #             vd.TVD,
    #             vd.PBMD,
    #             vd.PBTVD,
    #             w.WellStatus,
    #             w.WellType,
    #             shut.LastProductionPeriod,
    #             shut.MonthsShutIn,
    #             rf.FieldName,
    #             c.LeaseType
    #     """
    # cursor.execute(sql_query)
    # columns = [column[0] for column in cursor.description]
    # result = cursor.fetchall()
    # df_data = [{columns[i]: row[i] for i in range(len(columns))} for row in result]
    # df = pd.DataFrame(df_data, columns=columns)
    #
    # # Fetch reference codes
    # ref_codes = fetch_ref_codes(cursor)
    #
    # df['WellStatusReport'] = df['WellStatusReport'].map(ref_codes['WELLSTATUS'])
    # df['WellTypeReport'] = df['WellTypeReport'].map(ref_codes['WELLTYPE'])
    # df['CurrentWellStatus'] = df['CurrentWellStatus'].map(ref_codes['WELLSTATUS'])
    # df['CurrentWellType'] = df['CurrentWellType'].map(ref_codes['WELLTYPE'])
    # condition = (df['Slant'] == 'VERTICAL') & df['Perforation MD'].isnull() & df['MD'].notnull()
    # df.loc[condition, 'Perforation TVD'] = df.loc[condition, 'MD']
    #
    # new_lst = []
    # api_lst = df['WellID'].tolist()
    # extension_lst = df['SideTrack'].tolist()
    #
    # returned_data = findDepthsIfInitFailedMass(cursor, api_lst, extension_lst)
    # # Create a DataFrame from returned_data
    # returned_data_df = pd.DataFrame(returned_data).T.reset_index()
    # returned_data_df.columns = ['WellID', 'MD', 'TVD']
    #
    # # Merge df with returned_data_df to fill missing 'MD' and 'TVD'
    # df = df.merge(returned_data_df, on='WellID', how='left', suffixes=('', '_new'))
    #
    # # Update 'MD' and 'TVD' columns where applicable
    # df['MD'] = df['MD'].combine_first(df['MD_new'])
    # df['TVD'] = df['TVD'].combine_first(df['TVD_new'])
    #
    # # Drop the temporary '_new' columns
    # df.drop(columns=['MD_new', 'TVD_new'], inplace=True)
    #
    # # Apply the filtering conditions
    # condition1 = ~df['WellStatusReport'].isin(['Location Abandoned - APD rescinded', 'Returned APD (Unapproved)', 'Location Abandoned - APD rescinded'])
    # condition2 = df['WellID'].astype(str).isin([str(j) for j in apds_original])
    # condition3 = df['Perforation MD'].notnull()
    #
    # # Combine conditions to create new_lst
    # new_lst = df[(condition1 & (condition2 | condition3)) | (condition1 & df['MD'].notnull())].values.tolist()
    #
    # # If you need to convert new_lst back to a DataFrame
    # new_lst = pd.DataFrame(new_lst, columns=df.columns).values

    apis = [str(i) for i in well_id]
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    sql_query = f"""
        SELECT
            w.WellID,
            w.WellName,
            c.SideTrack,
            wh.WorkType,
            CASE
                When vsl.ConstructType = 'D' then 'DIRECTIONAL'
                When vsl.ConstructType = 'H' then 'HORIZONTAL'
                When vsl.ConstructType = 'V' then 'VERTICAL'
            END as 'Slant',
            CONVERT(char(10), wh.APDReceivedDate, 101) as 'APDReceivedDate',
            CONVERT(char(10), wh.APDReturnDate, 101) as 'APDReturnDate',
            CONVERT(char(10), wh.APDApprovedDate, 101) as 'APDApprovedDate',
            CONVERT(char(10), wh.APDExtDate, 101) as 'APDExtDate',
            CONVERT(char(10), wh.APDRescindDate, 101) as 'APDRescindDate',
            vsc.DrySpud,
            vsc.RotarySpud,
            CONVERT(char(10), wh.WCRCompletionDate, 101) as 'WCRCompletionDate',
            wh.ReportStatus as 'WellStatusReport',
            wh.WellTypeReport,
            vfp.FirstProdDate,
            vpt.TestDate,
            vpt.ProductionMethod,
            vpt.OilRate,
            vpt.GasRate,
            vpt.WaterRate,
            vs.DST,
            vs.DirSurveyRun,
            vs.CompletionType,
            vd.DTD as 'MD',
            vd.TVD,
            vd.PBMD as "Perforation MD",
            vd.PBTVD as "Perforation TVD",
            w.WellStatus as 'CurrentWellStatus',
            w.WellType as 'CurrentWellType',
            shut.LastProductionPeriod as 'Last Production (if Shut In)',
            shut.MonthsShutIn as 'Months Shut In',
			rf.FieldName,
			CASE
				when c.LeaseType = 'F' then 'FEDERAL'
				when c.LeaseType = 'I' then 'INDIAN'
				when c.LeaseType = 'S' then 'STATE'
				when c.LeaseType = 'P' then 'FEE'
				Else '5 - UNKNOWN'
			END AS 'Mineral Lease'
            FROM
            Well w
            LEFT JOIN WellHistory wh on wh.WellKey = w.pkey
            LEFT JOIN vw_DON_WH_SPUDdates vsc on vsc.HistKey = wh.PKey
            LEFT JOIN vw_DON_WH_APDNO van on van.HistKey = wh.PKey
            LEFT JOIN vw_DON_WH_SLANT vsl on vsl.SlantHistKey = wh.PKey
            LEFT JOIN vw_DON_WH_FirstProdDate vfp on vfp.FirstProdHistKey = wh.PKey
            LEFT JOIN vw_DON_WH_ProdTest vpt on vpt.WHPkey = wh.PKey
            LEFT JOIN vw_DON_WH_Surveys vs on vs.whKey = wh.PKey
            LEFT JOIN vw_DON_WH_Depths vd on vd.whPkey = wh.PKey
            LEFT JOIN Construct c on c.pkey = wh.ConstructKey
            LEFT JOIN ShutInAbandonedSuspendedWellsRpt shut on shut.API10 = w.WellID
			Left join RefFields rf on rf.PKey = c.FieldKey
        WHERE
            (wh.WorkType IN ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug'))
            AND w.WellID IN ({apis}) and wh.WorkType != 'REPERF' ---and wh.ReportStatus NOT IN ('LA', 'RET', 'APD', 'DRL')
        """

    cursor.execute(sql_query)
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    ref_codes = fetch_ref_codes(cursor)

    for i in range(len(result)):
        result[i][13] = ref_codes['WELLSTATUS'].get(result[i][13])
        result[i][14] = ref_codes['WELLTYPE'].get(result[i][14])
        result[i][-6] = ref_codes['WELLSTATUS'].get(result[i][-6])
        result[i][-5] = ref_codes['WELLTYPE'].get(result[i][-5])
        if result[i][4] == 'VERTICAL' and result[i][-9] is None and result[i][-10] is not None:
            result[i][-9] = result[i][-10]
    new_lst = []
    api_lst = [i[0] for i in result]
    extension_lst = [i[2] for i in result]

    returned_data = findDepthsIfInitFailedMass(cursor, api_lst, extension_lst)

    for i in range(len(result)):
        if result[i][13] not in ['Location Abandoned - APD rescinded', 'Returned APD (Unapproved)', 'Location Abandoned - APD rescinded']:
            if str(result[i][0]) in [str(j) for j in apds_original]:
                new_lst.append(list(result[i]))
            else:
                if result[i][-10] is not None:
                    new_lst.append(list(result[i]))
                else:
                    result[i] = list(result[i])

                    out_data = returned_data[result[i][0]]
                    if out_data:
                        result[i][24:26] = out_data
                        new_lst.append(list(result[i]))
    #
    result = new_lst
    result = sorted(result, key=lambda r: r[0])
    result = ma.removeDupesListOfLists(result)
    result = [list(i) for i in result]
    return list(result), columns


def findDepthsIfInitFailed(cursor, api, extension):
    api_mod = api + "000" + str(int(float(extension)))
    query = f"""select Proposed_Depth_TVD, Proposed_Depth_MD from tblAPDLoc where API = '{api_mod}' and Zone_Name = 'Proposed Depth'"""
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        return list(result[0])

    else:
        query = f"""select TrueVerticalDepth, MeasuredDepth 
                    from [dbo].[DirectionalSurveyHeader] dsh
                    join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.PKey
                    where APINumber = '{api}' and CitingType = 'Planned' 
                    order by CitingType, MeasuredDepth ASC"""
        cursor.execute(query)
        result = cursor.fetchall()
        if result:
            return [float(i) for i in result[-1]]
        else:
            selectCommand = 'select DepthBottom, ElevationType'
            fromCommand = ' FROM Well w'
            joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey'
            whereCommand = f""" WHERE WellID = '{api}' and ElevationType in ('TVD', 'DTD')"""
            orderCommand = ' ORDER BY ElevationType'
            line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
            if line:
                if len(line) > 1:
                    return [line[1][0], line[0][0]]
    return []


def findDepthsIfInitFailedMass(cursor, apis, extensions):
    api_depths = {api: [None, None] for api in apis}

    # First query
    apis_with_extensions = [apis[i] + "000" + str(int(float(extensions[i]))) for i in range(len(apis))]
    apis_with_extensions = list(set(apis_with_extensions))
    apis_with_extensions = ', '.join([f"'{str(elem)}'" for elem in apis_with_extensions])

    query = f"""select API, Proposed_Depth_TVD, Proposed_Depth_MD from tblAPDLoc where API IN ({apis_with_extensions}) and Zone_Name = 'Proposed Depth'"""
    cursor.execute(query)
    result = cursor.fetchall()
    for row in result:
        api_depths[row[0][:10]] = [row[1], row[2]]

    # Second query
    apis_str = ', '.join([f"'{str(elem)}'" for elem in apis])
    query = f"""select APINumber, TrueVerticalDepth, MeasuredDepth 
                from [dbo].[DirectionalSurveyHeader] dsh
                join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.PKey
                where APINumber IN ({apis_str}) and CitingType = 'Planned' 
                order by CitingType, MeasuredDepth ASC"""
    cursor.execute(query)
    result = cursor.fetchall()
    for row in result:
        if api_depths[row[0]][0] is None:
            api_depths[row[0]] = [float(row[1]), float(row[2])]

    # Third query
    selectCommand = 'select WellID, DepthBottom, ElevationType'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey'
    whereCommand = f""" WHERE WellID IN ({apis_str}) and ElevationType in ('TVD', 'DTD')"""
    orderCommand = ' ORDER BY ElevationType'
    line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
    for row in line:
        if api_depths[row[0]][0] is None:
            if row[2] == 'TVD':
                api_depths[row[0]][0] = row[1]
            elif row[2] == 'DTD':
                api_depths[row[0]][1] = row[1]
    return api_depths
    # return [api_depths[api] for api in apis]


# def findDepthsIfInitFailedMass(cursor, apis, extensions):
#     apis = [apis[i] + "000" + str(int(float(extensions[i]))) for i in range(len(apis))]
#     apis = ', '.join([f"'{str(elem)}'" for elem in apis])
#     query = f"""select API, Proposed_Depth_TVD, Proposed_Depth_MD from tblAPDLoc where API IN ({apis}) and Zone_Name = 'Proposed Depth'"""
#     cursor.execute(query)
#     result = cursor.fetchall()
#     if result:
#         return list(result[0])
#
#     else:
#         query = f"""select APINumber, TrueVerticalDepth, MeasuredDepth
#                     from [dbo].[DirectionalSurveyHeader] dsh
#                     join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.PKey
#                     where APINumber IN ({apis}) and CitingType = 'Planned'
#                     order by CitingType, MeasuredDepth ASC"""
#         cursor.execute(query)
#         result = cursor.fetchall()
#         if result:
#             return [float(i) for i in result[-1]]
#         else:
#             selectCommand = 'select WellID, DepthBottom, ElevationType'
#             fromCommand = ' FROM Well w'
#             joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey'
#             whereCommand = f""" WHERE WellID IN ({apis}) and ElevationType in ('TVD', 'DTD')"""
#             orderCommand = ' ORDER BY ElevationType'
#             line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
#             if line:
#                 if len(line) > 1:
#                     return [line[1][0], line[0][0]]
#     return []


# def retrieveConstructData(cursor, well_id):
#     sql_query = """
#         SELECT
#             w.WellID,
#             w.WellName,
#             c.SideTrack,
#             wh.WorkType,
#             CASE
#                 When vsl.ConstructType = 'D' then 'DIRECTIONAL'
#                 When vsl.ConstructType = 'H' then 'HORIZONTAL'
#                 When vsl.ConstructType = 'V' then 'VERTICAL'
#             END as 'Slant',
#             CONVERT(char(10), wh.APDReceivedDate, 101) as 'APDReceivedDate',
#             CONVERT(char(10), wh.APDReturnDate, 101) as 'APDReturnDate',
#             CONVERT(char(10), wh.APDApprovedDate, 101) as 'APDApprovedDate',
#             CONVERT(char(10), wh.APDExtDate, 101) as 'APDExtDate',
#             CONVERT(char(10), wh.APDRescindDate, 101) as 'APDRescindDate',
#             vsc.DrySpud,
#             vsc.RotarySpud,
#             CONVERT(char(10), wh.WCRCompletionDate, 101) as 'WCRCompletionDate',
#             wh.ReportStatus as 'WellStatusReport',
#             wh.WellTypeReport,
#             vfp.FirstProdDate,
#             vpt.TestDate,
#             vpt.ProductionMethod,
#             vpt.OilRate,
#             vpt.GasRate,
#             vpt.WaterRate,
#             vs.DST,
#             vs.DirSurveyRun,
#             vs.CompletionType,
#             vd.DTD as 'MD',
#             vd.TVD,
#             vd.PBMD as "Perforation MD",
#             vd.PBTVD as "Perforation TVD",
#             w.WellStatus as 'CurrentWellStatus',
#             w.WellType as 'CurrentWellType',
#             shut.LastProductionPeriod as 'Last Production (if Shut In)',
#             shut.MonthsShutIn as 'Months Shut In'
#         FROM
#             Well w
#             LEFT JOIN WellHistory wh on wh.WellKey = w.pkey
#             LEFT JOIN vw_DON_WH_SPUDdates vsc on vsc.HistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_APDNO van on van.HistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_SLANT vsl on vsl.SlantHistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_FirstProdDate vfp on vfp.FirstProdHistKey = wh.PKey
#             LEFT JOIN vw_DON_WH_ProdTest vpt on vpt.WHPkey = wh.PKey
#             LEFT JOIN vw_DON_WH_Surveys vs on vs.whKey = wh.PKey
#             LEFT JOIN vw_DON_WH_Depths vd on vd.whPkey = wh.PKey
#             LEFT JOIN Construct c on c.pkey = wh.ConstructKey
#             LEFT JOIN ShutInAbandonedSuspendedWellsRpt shut on shut.API10 = w.WellID
#         WHERE
#             (wh.WorkType IN ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug'))
#             AND w.WellID = ?
#         """
#
#     # sql_query = """
#     # SELECT
#     #     w.WellID, w.WellName, c.SideTrack, wh.WorkType,
#     #     CASE
#     #         When vsl.ConstructType = 'D' then 'DIRECTIONAL'
#     #         When vsl.ConstructType = 'H' then 'HORIZONTAL'
#     #         When vsl.ConstructType = 'V' then 'VERTICAL'
#     #     END as 'Slant',
#     #     van.APDKey as 'APDNumber', CONVERT(char(10), wh.APDReceivedDate, 101) as 'APDReceivedDate',
#     #     CONVERT(char(10), wh.APDReturnDate, 101) as 'APDReturnDate', CONVERT(char(10), wh.APDApprovedDate, 101) as 'APDApprovedDate',
#     #     CONVERT(char(10), wh.APDExtDate, 101) as 'APDExtDate',
#     #     CONVERT(char(10), wh.APDRescindDate, 101) as 'APDRescindDate', vsc.DrySpud, vsc.RotarySpud,
#     #     CONVERT(char(10), wh.WCRCompletionDate, 101) as 'WCRCompletionDate',
#     #     CONVERT(char(10), wh.SundryIntentReceivedDate, 101) as 'SundryIntentReceivedDate', CONVERT(char(10), wh.SundryIntentAcceptedDate, 101) as 'SundryIntentAcceptedDate',
#     #     CONVERT(char(10), wh.SundryIntentApprovedDate, 101) as 'SundryIntentApprovedDate', CONVERT(char(10), wh.SundryIntentCancelledDate, 101) as 'SundryIntentCancelledDate',
#     #     CONVERT(char(10), wh.SundrySubsequentReceivedDate, 101) as 'SundrySubsequentReceivedDate', CONVERT(char(10), wh.SundryCompletionDate, 101) as 'SundryCompletionDate',
#     #     wh.ReportStatus as 'WellStatusReport', wh.WellTypeReport,
#     #     vfp.FirstProdDate,
#     #     vpt.TestDate, vpt.ProductionMethod, vpt.Choke64th, vpt.TubingPressure, vpt.CasingPressure,
#     #     vpt.OilRate, vpt.GasRate, vpt.WaterRate, vpt.OilGravity, vpt.BTU, vs.Cored, vs.DST, vs.DirSurveyRun, vs.CompletionType,
#     #     vd.DTD as 'MD', vd.TVD, vd.PBMD as "Perforation MD", vd.PBTVD as "Perforation TVD", w.WellStatus as 'CurrentWellStatus', w.WellType as 'CurrentWellType',
#     #     CASE
#     #         When c.Confidential = 0 then ''
#     #         Else 'YES'
#     #     END as 'Confidential'
#     # FROM
#     #     Well w
#     #     LEFT JOIN WellHistory wh on wh.WellKey = w.pkey
#     #     LEFT JOIN vw_DON_WH_SPUDdates vsc on vsc.HistKey = wh.PKey
#     #     LEFT JOIN vw_DON_WH_APDNO van on van.HistKey = wh.PKey
#     #     LEFT JOIN vw_DON_WH_SLANT vsl on vsl.SlantHistKey = wh.PKey
#     #     LEFT JOIN vw_DON_WH_FirstProdDate vfp on vfp.FirstProdHistKey = wh.PKey
#     #     LEFT JOIN vw_DON_WH_ProdTest vpt on vpt.WHPkey = wh.PKey
#     #     LEFT JOIN vw_DON_WH_Surveys vs on vs.whKey = wh.PKey
#     #     LEFT JOIN vw_DON_WH_Depths vd on vd.whPkey = wh.PKey
#     #     LEFT JOIN Construct c on c.pkey = wh.ConstructKey
#     # WHERE
#     #     (wh.WorkType IN ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug'))
#     #     AND w.WellID = ?
#     # """
#
#     # Execute the query with the parameter
#     cursor.execute(sql_query, (well_id,))
#     columns = [column[0] for column in cursor.description]
#     result = cursor.fetchall()
#
#     # dbRefCodesTranslate(cursor, result)
#
#     result[0][20] = dbRefCodesTranslateStatus(cursor, result[0][20])
#     result[0][21] = dbRefCodesTranslateType(cursor, result[0][21])
#     result[0][-5] = dbRefCodesTranslateStatus(cursor, result[0][-5])
#     result[0][-4] = dbRefCodesTranslateType(cursor, result[0][-4])
#     # status_1, type_1, status_2, type_2 = row[0][13], row[0][14], row[0][-3], row[0][-2]
#     return list(result), columns


def retrieveData2(cursor, well_id):
    sql_query = """
    SELECT 
        w.WellID, w.WellName, w.WellStatus, c.LateralStatus, c.SideTrack,
        cd.Event, cd.EventDate, cd.Comment 
    FROM 
        Well w 
        JOIN Construct c ON w.pkey = c.WellKey 
        JOIN ConstructDate cd on c.PKey = cd.ConstructKey
    --JOIN RefCodes rc on rc.Code = cd.Comment
    WHERE 
        w.WellID = ?
    --WHERE 
    --    cd.comment = 'FP' and cd.event = 'firstproduction'
    ORDER BY 
        cd.ConstructKey, cd.EventDate DESC
    """

    # Execute the query with the parameter
    cursor.execute(sql_query, (well_id,))

    # Fetch the result
    results = cursor.fetchall()
    return results


def dbDXData(cursor, api):
    selectCommand = 'select dsh.APINumber, dsh.WellNameNumber, MeasuredDepth, Inclination, Azimuth, TrueVerticalDepth, dsd.X, dsd.Y, CitingType'
    fromCommand = ' from [dbo].[DirectionalSurveyHeader] dsh'
    joinCommand = ' join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.PKey'
    whereCommand = ' where APINumber = ' + r"'" + str(api) + r"'"
    orderCommand = ' order by CitingType, MeasuredDepth ASC'

    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand)
    line = cursor.fetchall()
    return line

def dbDXDataAll(cursor, api_lst):
    apis = [str(i) for i in api_lst]
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    selectCommand = 'select dsh.APINumber, dsh.WellNameNumber, MeasuredDepth, Inclination, Azimuth, TrueVerticalDepth, dsd.X, dsd.Y, CitingType'
    fromCommand = ' from [dbo].[DirectionalSurveyHeader] dsh'
    joinCommand = ' join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.PKey'
    whereCommand = f""" where APINumber in ({apis})"""
    orderCommand = ' order by CitingType, MeasuredDepth ASC'

    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand)
    line = cursor.fetchall()
    return line

def dbDXDataConstruct(cursor, api):
    selectCommand = 'select dsh.APINumber, dsh.WellNameNumber, MeasuredDepth, Inclination, Azimuth, TrueVerticalDepth, dsd.X, dsd.Y, CitingType'
    fromCommand = ' from [dbo].[DirectionalSurveyHeader] dsh'
    # joinCommand = ' join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.DirectionalSurveyHeaderKey'
    joinCommand = ' join [dbo].[DirectionalSurveyData] dsd on dsd.DirectionalSurveyHeaderKey = dsh.PKey'
    whereCommand = ' where APINumber = ' + r"'" + str(api) + r"'" ' and CitingType =\'Planned\''
    orderCommand = ' order by MeasuredDepth ASC'
    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand)
    line = cursor.fetchall()
    return line


# def dbSurfaceLocDrilled(cursor, api, conn, data_line):
#     query = f"""
#         SELECT
#             CASE WHEN LocType = 'SURF' THEN X ELSE NULL END AS SURF_X,
#             CASE WHEN LocType = 'SURF' THEN Y ELSE NULL END AS SURF_Y,
#             CASE WHEN LocType = 'BH' THEN X ELSE NULL END AS BH_X,
#             CASE WHEN LocType = 'BH' THEN Y ELSE NULL END AS BH_Y,
#             CASE WHEN ElevationType = 'DTD' THEN DepthBottom ELSE NULL END AS DTD,
#             CASE WHEN ElevationType = 'TVD' THEN DepthBottom ELSE NULL END AS TVD
#         FROM Well w
#         LEFT JOIN Construct c ON c.WellKey = w.PKey
#         LEFT JOIN loc l ON l.ConstructKey = c.pkey
#         WHERE WellID = '{api}' AND (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD'))
#     """
#     df_foo = pd.read_sql_query(query, conn)
#
#     if df_foo['TVD'].notnull().any() and df_foo['DTD'].notnull().any():
#         md = df_foo['DTD'].iloc[df_foo['DTD'].first_valid_index()]
#         tvd = df_foo['TVD'].iloc[df_foo['TVD'].first_valid_index()]
#     else:
#         if data_line[24] is not None and data_line[25] is not None:
#             md, tvd = data_line[25], data_line[24]
#         else:
#             md = df_foo['DTD'].iloc[df_foo['DTD'].first_valid_index()]
#             tvd = md

#     surf_loc = [df_foo['SURF_X'].iloc[df_foo['SURF_X'].first_valid_index()], df_foo['SURF_Y'].iloc[df_foo['SURF_Y'].first_valid_index()]]
#     try:
#         bh_loc = [df_foo['BH_X'].iloc[df_foo['BH_X'].first_valid_index()], df_foo['BH_Y'].iloc[df_foo['BH_Y'].first_valid_index()]]
#     except TypeError:
#         bh_loc = surf_loc
#     if pd.isnull(tvd):
#         if ma.equationDistance(surf_loc[0], surf_loc[1], bh_loc[0], bh_loc[1]) < 10:
#             md = data_line[25]
#             tvd = md
#
#     if pd.isnull(bh_loc[0]) or pd.isnull(bh_loc[1]):
#         bh_loc = surf_loc
#
#     point1 = surf_loc + [0]
#     point2 = bh_loc + [tvd]
#     surf_latlon = utm.to_latlon(surf_loc[0], surf_loc[1], 12, 'T')
#     bh_latlon = utm.to_latlon(bh_loc[0], bh_loc[1], 12, 'T')
#     fwd_azimuth, back_azimuth, distance = Geod(ellps='WGS84').inv(surf_latlon[1], surf_latlon[0], bh_latlon[1], bh_latlon[0])
#     inclination, azimuth = ma.xyzEquationIncAzi(point1, point2)
#
#     dx_asDrilled1 = ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']
#     dx_asDrilled2 = ["", "", md, round(inclination, 3), round(fwd_azimuth, 3), tvd, bh_loc[0], bh_loc[1], 'Vertical']
#     drilled = [dx_asDrilled1, dx_asDrilled2]
#
#     return drilled
def dbSurfaceLocDrilled(cursor, api, conn, data_line):
    tvd, md = -1, -2
    selectCommand = 'select LocType, X, Y, DepthBottom, ElevationType'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey'
    whereCommand = f""" WHERE WellID = '{api}' and (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD'))"""
    orderCommand = ' '
    df_foo = pd.read_sql(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand, conn)
    df_foo_vals = df_foo['ElevationType'].unique()
    if 'DTD' not in df_foo_vals or 'TVD' not in df_foo_vals:
        if data_line[24] is not None and data_line[25] is not None:
            md, tvd = data_line[25], data_line[24]
    else:
        md = df_foo.loc[df_foo['ElevationType'] == 'DTD', 'DepthBottom'].values[0]
        try:
            tvd = df_foo.loc[df_foo['ElevationType'] == 'TVD', 'DepthBottom'].values[0]
        except IndexError:
            tvd = df_foo.loc[df_foo['ElevationType'] == 'DTD', 'DepthBottom'].values[0]

    surf_loc = df_foo.loc[df_foo['LocType'] == 'SURF', ['X', 'Y']].values[0].tolist()
    bh_loc = df_foo.loc[df_foo['LocType'] == 'BH', ['X', 'Y']].values[0].tolist()


    if tvd == -1:
        if ma.equationDistance(surf_loc[0], surf_loc[1], bh_loc[0], bh_loc[1]) < 10:
            md = data_line[25]
            tvd = md
    if 'nan' in [str(i) for i in bh_loc]:
        bh_loc = surf_loc
    point1 = surf_loc + [0]
    point2 = bh_loc + [tvd]

    surf_latlon = utm.to_latlon(surf_loc[0], surf_loc[1], 12, 'T')
    bh_latlon = utm.to_latlon(bh_loc[0], bh_loc[1], 12, 'T')
    fwd_azimuth, back_azimuth, distance = Geod(ellps='WGS84').inv(surf_latlon[1], surf_latlon[0], bh_latlon[1], bh_latlon[0])
    if point1 == point2:
        return [["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'], ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']]
    elif point1 != point2:
        if point1[2] is None:
            return [["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'], ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']]
        elif point2[2] is None:
            return [["", "", '0', '0', '0', '0', bh_loc[0], bh_loc[1], 'Vertical'], ["", "", '0', '0', '0', '0', bh_loc[0], bh_loc[1], 'Vertical']]
        else:
            pass

    inclination, azimuth = ma.xyzEquationIncAzi(point1, point2)
    dx_asDrilled1 = ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']
    dx_asDrilled2 = ["", "", md, round(inclination, 3), round(fwd_azimuth, 3), tvd, bh_loc[0], bh_loc[1], 'Vertical']
    drilled = [dx_asDrilled1, dx_asDrilled2]

    return drilled


def dbSurfaceLocData(cursor, api):
    api = str(api) + '0000'
    selectCommand = 'select DISTINCT LEFT(dsd.API_WellNo, 10), Well_Nm, al.Proposed_Depth_MD, al.Proposed_Depth_TVD, [Wh_X],[Wh_Y]'
    fromCommand = ' from [dbo].[tblAPDLoc] al'
    joinCommand = ' join [dbo].[tblAPD] dsd on dsd.API_WellNo = al.API join Well w on LEFT(al.API, 10) = w.WellID'
    whereCommand = f""" where al.API = '{api}' and al.Proposed_Depth_MD > 0"""
    orderCommand = ' '
    line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()[0])
    # line = cursor.execute(f"SELECT [Wh_X], [Wh_Y] FROM [dbo].[tblAPDLoc] WHERE APDNO = '{apd_no}'")
    try:
        line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()[0])
        line.insert(3, 0)
        line.insert(3, 0)

        init_line = copy.deepcopy(line)
        init_line[2], init_line[5] = 0, 0
        final_line = [tuple(init_line), tuple(line)]
        return final_line
    except IndexError:
        line1 = [None] * 7
        return [tuple(line1), tuple(line1)]
    # return test


def dbTownshipAndRangeAndElevation(cursor, api):
    selectCommand = 'select w.WellID, GRELEV, Sec, Township, TownshipDir, Range, RangeDir, PM'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey left join [LocExt] le ON le.lockey = l.Pkey'
    whereCommand = f""" WHERE WellID = '{api}' and (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD')) and LocType = 'SURF'"""
    orderCommand = ' '
    line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())[0]
    if str(line[1]) == 'None':
        try:
            selectCommand = 'select Elevation'
            fromCommand = ' from [dbo].[tblAPDLoc] al '
            joinCommand = ' join [dbo].[tblAPD] dsd on dsd.API_WellNo = al.API join Well w on LEFT(al.API, 10) = w.WellID '
            whereCommand = f""" where al.API = '{api}0000' and Zone_Name = 'Surface Location'"""
            orderCommand = ' '
            line2 = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())[0]
            line[1] = line2[0]
        except IndexError:
            pass
    if str(line[1]) == 'None':
        try:
            query = f"""select SurveySurfaceElevation from [dbo].[DirectionalSurveyHeader]
                    where APINumber = '{api}'"""
            line2 = list(cursor.execute(query).fetchall())[0]
            line[1] = line2[0]
        except IndexError:
            pass
    return line


def dbTownshipAndRangeAndElevationAll(cursor, api_lst):
    apis = [str(i) for i in api_lst]
    apis_extensions = [i + "0000" for i in apis]
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    apis_extensions = ', '.join([f"'{str(elem)}'" for elem in apis_extensions])

    result = {}
    for api in api_lst:
        result[api] = [None] * 8

    # Query 1: Retrieve data from Well, Construct, loc, and LocExt tables
    selectCommand = 'select w.WellID, GRELEV, Sec, Township, TownshipDir, Range, RangeDir, PM'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey left join [LocExt] le ON le.lockey = l.Pkey'
    whereCommand = f""" WHERE WellID in ({apis}) and (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD')) and LocType = 'SURF'"""
    orderCommand = ' '
    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand)
    rows = cursor.fetchall()
    for row in rows:
        result[row[0]] = list(row)

    # Query 2: Retrieve Elevation from tblAPDLoc table
    selectCommand = 'select LEFT(al.API, 10), Elevation'
    fromCommand = ' from [dbo].[tblAPDLoc] al '
    joinCommand = ' join [dbo].[tblAPD] dsd on dsd.API_WellNo = al.API join Well w on LEFT(al.API, 10) = w.WellID '
    whereCommand = f""" where al.API in ({apis_extensions}) and Zone_Name = 'Surface Location'"""
    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand)
    rows = cursor.fetchall()
    for row in rows:
        if result[row[0]][1] is None:
            result[row[0]][1] = row[1]

    # Query 3: Retrieve SurveySurfaceElevation from DirectionalSurveyHeader table
    selectCommand = 'select APINumber, SurveySurfaceElevation'
    fromCommand = ' from [dbo].[DirectionalSurveyHeader]'
    whereCommand = f' where APINumber in ({apis})'
    cursor.execute(selectCommand + fromCommand + whereCommand)
    rows = cursor.fetchall()
    for row in rows:
        if result[row[0]][1] is None:
            result[row[0]][1] = row[1]
    return result
    # return [result[api] for api in api_lst]


def dbTownshipAndRange(cursor, api):
    selectCommand = 'select Wh_Sec, Wh_Twpn , Wh_Twpd, Wh_RngN, Wh_RngD, Wh_Pm'
    fromCommand = ' from Well w'
    joinCommand = ' inner join [dbo].[tblAPD] dsd on LEFT(dsd.API_WellNo, 10) = w.WellID inner join [dbo].[tblAPDLoc] al on al.APDNO = dsd.APDNo'
    # whereCommand = f""" where al.API = '{api}' and al.Proposed_Depth_MD > 0"""
    whereCommand = f""" where w.WellID = '{api}'"""
    orderCommand = ' '
    line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
    return line


def dbTownshipAndRangeMany(cursor, api):
    apis = [str(i) for i in api]
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    selectCommand = 'select Wh_Sec, Wh_Twpn , Wh_Twpd, Wh_RngN, Wh_RngD, Wh_Pm'
    fromCommand = ' from Well w'
    joinCommand = ' inner join [dbo].[tblAPD] dsd on LEFT(dsd.API_WellNo, 10) = w.WellID inner join [dbo].[tblAPDLoc] al on al.APDNO = dsd.APDNo'
    # whereCommand = f""" where al.API = '{api}' and al.Proposed_Depth_MD > 0"""
    whereCommand = f""" where w.WellID in ({apis})"""
    orderCommand = ' '
    line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
    return line


def sqlProdData(cursor, api):
    apis = [str(i) for i in api]
    apis = list(set(apis))
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    selectCommand = f"""SELECT SUM(CAST(prodquantity AS FLOAT)) AS 'Volume', ProdType, w.WellID"""
    fromCommand = ' FROM Well w '
    joinCommand = ' JOIN Construct c on w.PKey = c.WellKey JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     '
    whereCommand = f""" WHERE  w.WellID IN ({apis}) and ProdType != 'WATER'"""
    orderCommand = ' GROUP BY ProdType, w.WellID Order by w.WellID, ProdType Desc'
    line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()

    all_apis = [str(i[2]) for i in line]
    edited_lst = []
    for i in api:
        if str(i) not in all_apis:
            edited_lst.append([None, 'OIL', str(i)])
            edited_lst.append([None, 'GAS', str(i)])
    tot_lst = line + edited_lst
    tot_lst = [list(i) for i in tot_lst]

    grouped_data = defaultdict(list)
    for item in tot_lst:
        grouped_data[item[2]].append(item[0])  # Append only the first element of each tuple
    data = [values for key, values in grouped_data.items()]
    try:
        # return data
        return grouped_data

    except TypeError:
        return [[None, None] for i in api]


def sqlProdDataOil(cursor, api):
    selectCommand = f"""Select SUM(CAST(prodquantity AS FLOAT)) AS 'Volume'"""
    fromCommand = ' FROM Well w '
    joinCommand = ' JOIN Construct c on w.PKey = c.WellKey JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     '
    whereCommand = f""" where pfp.ProdType = 'OIL' and w.WellID = '{api}'"""
    orderCommand = ' '
    line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()[0][0]
    try:
        return str(int(float(line)))
    except TypeError:
        return None


def sqlProdDataGas(cursor, api):
    selectCommand = f"""Select SUM(CAST(prodquantity AS FLOAT)) AS 'Volume'"""
    fromCommand = ' FROM Well w '
    joinCommand = ' JOIN Construct c on w.PKey = c.WellKey JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     '
    whereCommand = f""" where pfp.ProdType = 'GAS' and w.WellID = '{api}'"""
    orderCommand = ' '

    line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()[0][0]
    try:
        return str(int(float(line)))
    except TypeError:
        return None


def sqlConnect():
    # cnxn = pyodbc.connect(
    #     "Driver={SQL Server};"
    #     "Server=CGDESKTOP\SQLEXPRESS;"
    #     "Database=UTRBDMSNET;"
    #     "Trusted_Connection = yes;")
    server = 'oilgas-sql-prod.ogm.utah.gov'
    username = 'coltongoodrich'
    password = '#newUser0615'
    database = 'UTRBDMSNET'
    cnxn = pyodbc.connect('DRIVER={SQL Server};'
                          'SERVER=' + server + ';'
                                               'DATABASE=' + database + ';'
                                                                        'UID=' + username + ';'
                                                                                            'PWD=' + password)
    cursor = cnxn.cursor()
    return cnxn, cursor
    # return cnxn, cnxn.cursor()


def sqlConnectPlats():
    current_dir = os.getcwd()
    apd_data_dir = os.path.join(r'C:\Work\RewriteAPD', "APD_Data.db")
    conn = sqlite3.connect(apd_data_dir)
    cursor = conn.cursor()
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    cursor.execute(query)
    table_names = [row[0] for row in cursor.fetchall()]
    # Fetch all the column names
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    string_sql = 'select * from SectionDataCoordinates'
    df = pd.read_sql(string_sql, conn, index_col='index')

    df["Easting"] = df["Easting"].astype("float")
    df["Northing"] = df["Northing"].astype("float")
    merged_df = df[df['Conc'].str.contains('2842S17WS', case=False)]
    filtered_df = merged_df[merged_df['Version'].str.contains('foo', case=False)]
    unique_values = merged_df['Conc'].unique()

    string_sql_plat = 'select * from SectionPlatData'
    df_plat_data = pd.read_sql(string_sql_plat, conn, index_col='index')
    df_plat_data = df_plat_data.astype(
        {"Section": int, "Township": int, "Township Direction": int, "Range": int, "Range Direction": int,
         "Baseline": int,
         "Length": float, "Degrees": float, "Minutes": float, "Seconds": float, "Alignment": float})
    df_plat_data = df_plat_data.astype({"Degrees": int, "Minutes": int, "Seconds": int, "Alignment": int})
    agrc = r'C:\Work\RewriteAPD'
    # df_coords_agrc_2 = pd.read_csv(r'C:\Work\RewriteAPD\AGRC_Coords.csv')
    df_coords_agrc_2 = pd.read_csv(r'C:\Work\RewriteAPD\PlatDataSectionsMay.csv')
    df_coords_agrc_2.rename(columns={'Township Dir': 'Township Direction'}, inplace=True)
    df_coords_agrc_2.rename(columns={'Range Dir': 'Range Direction'}, inplace=True)

    df_coords_manual = pd.read_csv(r'C:\Work\RewriteAPD\SectionCoordinates.csv')

    df_coords_manual = df_coords_manual.rename(
        columns={'Township Direction (S = 2, N = 1)': 'Township Direction',
                 'Range Direction (W=2, E=1)': 'Range Direction', 'Baseline (U=2, S=1)': 'Baseline'})
    df_coords_manual = df_coords_manual.reindex(
        columns=['Section', 'Township', 'Township Direction', 'Range', 'Range Direction', 'Baseline', 'Lat', 'Lon',
                 'Well', 'Conc', 'Version', 'Apd_no'])
    df_coords = pd.concat([df_coords_manual, df_coords_agrc_2])
    return df_coords


def fetch_ref_codes(cursor):
    selectCommand = 'select Fld, Code, Description from [dbo].[RefCodes] where Fld in (\'WELLSTATUS\', \'WELLTYPE\')'
    ref_codes = {}
    for row in cursor.execute(selectCommand).fetchall():
        fld, code, description = row
        if fld not in ref_codes:
            ref_codes[fld] = {}
        ref_codes[fld][code] = description
    return ref_codes


def dbRefCodesTranslateStatus(cursor, value):
    selectCommand = 'select Description'
    fromCommand = ' from [dbo].[RefCodes]'
    whereCommand = f""" where Fld = 'WELLSTATUS' and Code = '{value}'"""
    line = cursor.execute(selectCommand + fromCommand + whereCommand).fetchall()
    if not line:
        return None
    else:
        return line[0][0]


def dbRefCodesTranslateType(cursor, value):
    selectCommand = 'select Description'
    fromCommand = ' from [dbo].[RefCodes]'
    whereCommand = f""" where Fld = 'WELLTYPE' and Code = '{value}'"""
    line = cursor.execute(selectCommand + fromCommand + whereCommand).fetchall()
    if not line:
        return None
    else:
        return line[0][0]


def sqlFindAllInSection(data, cursor):
    section, twsp, twsp_dir, rng, rng_dir, mer = data
    selectCommand = 'select ap.API_WellNo, al.APDNO, ap.Slant, Wh_X, Wh_Y'
    fromCommand = ' from [dbo].[tblAPDLoc] al'
    joinCommand = ' inner join [dbo].[tblAPD] ap on ap.APDNo = al.APDNO '
    whereCommand = f"""    WHERE [Wh_Twpn] = '{twsp}' AND [Wh_Twpd] = '{twsp_dir}' AND [Wh_RngN] = '{rng}' AND [Wh_RngD] = '{rng_dir}' AND [Wh_Pm] = '{mer}' and Wh_Sec = '{section}'"""
    orderCommand = ' '
    line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()
    return line

def sqlFindAllInSectionAll(data_list, cursor):
    selectCommand = 'select ap.API_WellNo, al.APDNO, ap.Slant, Wh_X, Wh_Y'
    fromCommand = ' from [dbo].[tblAPDLoc] al'
    joinCommand = ' inner join [dbo].[tblAPD] ap on ap.APDNo = al.APDNO '
    whereCommand = ' WHERE '
    conditions = []

    for sublist in data_list:
        section, twsp, twsp_dir, rng, rng_dir, mer = sublist
        condition = f"""(Wh_Sec = '{section}' AND Wh_Twpn = '{twsp}' AND Wh_Twpd = '{twsp_dir}' AND Wh_RngN = '{rng}' AND Wh_RngD = '{rng_dir}' AND Wh_Pm = '{mer}')"""
        conditions.append(condition)

    whereCommand += ' OR '.join(conditions)
    whereCommand += " AND ap.API_WellNo IS NOT NULL AND ap.API_WellNo <> '' AND LEN(ap.API_WellNo) = 14"
    orderCommand = ' '
    line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()
    line = [i for i in line if str(i[0]) != 'None']
    return line


def sqlFindBoardMatterInformationAll(data_list, cursor):
    selectCommand = '''
            select DISTINCT di.DocketNumber, di.CauseNumber, rc2.Description AS 'OrderType', di.EffectiveDate, di.EndDate, rf.FormationName, 
            ds.Quarter, ds.QuarterQuarter, ds.Sec, da.Township, da.TownshipDir, da.Range, da.RangeDir, da.PM, rc.CountyName, Quip
        '''
    fromCommand = '''
            from docketitem di
            left join DocketItemArea da on da.DocketItemKey = di.PKey
            left join DocketItemAreaSection ds on ds.DocketItemAreaKey = da.PKey
            left join RefCounty rc on rc.PKey = da.CountyKey
            left join RefFormation rf on rf.PKey = di.FormationKey
            left join RefCodes rc2 on rc2.Code = di.DocketItemType and fld = 'BoardOrderType'
        '''
    whereCommand = ' WHERE '
    conditions = []

    for sublist in data_list:
        section, twsp, twsp_dir, rng, rng_dir, mer = sublist
        condition = f"""(da.Range = '{rng}' AND da.RangeDir = '{rng_dir}' AND da.Township = '{twsp}' AND da.TownshipDir = '{twsp_dir}' AND ds.Sec = '{section}' AND da.PM = '{mer}')"""
        conditions.append(condition)

    whereCommand += ' OR '.join(conditions)
    orderCommand = '''
            order by di.CauseNumber, da.PM, rc.CountyName, da.Range, da.RangeDir, da.Township, da.TownshipDir, ds.Sec, ds.QuarterQuarter
        '''
    line = cursor.execute(selectCommand + fromCommand + whereCommand + orderCommand).fetchall()
    return line

def sqlFindBoardMatterInformation(plat_information, cursor):
    section, twsp, twsp_dir, rng, rng_dir, mer = plat_information
    query = f"""select distinct di.DocketNumber, di.CauseNumber, rc2.Description AS 'OrderType', di.EffectiveDate, di.EndDate, rf.FormationName, 
            ds.Quarter, ds.QuarterQuarter, ds.Sec, da.Township, da.TownshipDir, da.Range, da.RangeDir, da.PM, rc.CountyName, Quip 
            from docketitem di 
            left join DocketItemArea da on da.DocketItemKey = di.PKey
            left join DocketItemAreaSection ds on ds.DocketItemAreaKey = da.PKey
            left join RefCounty rc on rc.PKey = da.CountyKey
            left join RefFormation rf on rf.PKey = di.FormationKey
            left join RefCodes rc2 on rc2.Code = di.DocketItemType and fld = 'BoardOrderType'
            where da.Range = '{rng}' and da.RangeDir = '{rng_dir}' and da.Township = '{twsp}' and da.TownshipDir = '{twsp_dir}' and ds.Sec = '{section}' and da.PM = '{mer}'  
            
            order by di.CauseNumber, da.PM, rc.CountyName, da.Range, da.RangeDir, da.Township, da.TownshipDir, ds.Sec, ds.QuarterQuarter"""
    line = cursor.execute(query).fetchall()
    if line:
        return line
    else:
        return []


def sqlFindBoardMatterLinks(data, cursor):
    datas = [str(i) for i in data]
    datas = ', '.join([f"'{str(elem)}'" for elem in datas])
    query = f"""select Cause, OGMDocumentName, Description, Filepath, DocumentDate
            from [dbo].[DocketImageSalesForce]
            where Cause in ({datas})
            Order by DocumentDate"""
    line = cursor.execute(query).fetchall()
    return line


def sqlFindProduction(cursor, well_api, conn):
    # findDataSecondTime()

    selectCommand = "SELECT w.WellID, year(pfp.ReportPeriod) as 'Year', month(pfp.ReportPeriod) as 'Month', SUM(CAST(prodquantity AS FLOAT)) AS 'Volume', pfp.ProdType as 'ProdType', w.WellName"
    fromCommand = ' FROM Well w '
    joinCommand = ' JOIN Construct c on w.PKey = c.WellKey JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey '
    whereCommand = f"""    where (pfp.ProdType = 'GAS' or pfp.ProdType = 'OIL') and w.WellID = '{well_api[:10]}' and Cumulative is Null"""
    orderCommand = ' GROUP BY year(pfp.ReportPeriod), month(pfp.ReportPeriod), pfp.ProdType,w.WellName, w.WellID'
    time_start = time.perf_counter()
    prod_line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand + " HAVING SUM(CAST(prodquantity AS FLOAT)) > 0").fetchall()
    prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i in prod_line]

    return prod_line


# def findDataSecondTime():
#     # params = urllib.parse.quote_plus(
#     #     "Driver={SQL Server};"
#     #     "Server=CGDESKTOP\SQLEXPRESS;"
#     #     "Database=UTRBDMSNET;"
#     #     "Trusted_Connection = yes;"
#     # )
#     server = 'oilgas-sql-prod.ogm.utah.gov'
#     username = 'coltongoodrich'
#     password = '#newUser0615'
#     database = 'UTRBDMSNET'
#
#     params = urllib.parse.quote_plus('DRIVER={SQL Server};'
#                                      'SERVER=' + server + ';'
#                                                           'DATABASE=' + database + ';'
#                                                                                    'UID=' + username + ';'
#                                                                                                        'PWD=' + password)
#
#     engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
#
#     # df = pd.read_sql('select * from well', engine)
#
#
#     query = "SELECT Cumulative, w.WellID, year(pfp.ReportPeriod) as 'Year', month(pfp.ReportPeriod) as 'Month', SUM(CAST(prodquantity AS FLOAT)) AS 'Volume', pfp.ProdType as 'ProdType', w.WellName " \
#             "FROM Well w  " \
#             "JOIN Construct c on w.PKey = c.WellKey " \
#             "JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     " \
#             "where (pfp.ProdType = 'GAS' or pfp.ProdType = 'OIL') " \
#             "GROUP BY year(pfp.ReportPeriod), month(pfp.ReportPeriod), pfp.ProdType,w.WellName,pfp.Cumulative, w.WellID HAVING SUM(CAST(prodquantity AS FLOAT)) > 0"
#     #
#     # query = """
#     #     SELECT
#     #         w.WellID,
#     #         YEAR(pfp.ReportPeriod) AS 'Year',
#     #         MONTH(pfp.ReportPeriod) AS 'Month',
#     #         SUM(prodquantity) AS 'Volume',
#     #         pfp.ProdType AS 'ProdType',
#     #         w.WellName
#     #     FROM Well w
#     #     JOIN Construct c ON w.PKey = c.WellKey
#     #     JOIN ProdFacilityProduction pfp ON c.PKey = pfp.ConstructKey
#     #     WHERE
#     #         pfp.ProdType IN ('GAS', 'OIL')
#     #         AND prodquantity > 0
#     #     GROUP BY
#     #         YEAR(pfp.ReportPeriod),
#     #         MONTH(pfp.ReportPeriod),
#     #         pfp.ProdType,
#     #         w.WellName,
#     #         w.WellID
#     # """
#     df = pd.read_sql(query, engine)
#     df['Cumulative'] = df['Cumulative'].astype(str)
#     df = df[df['Cumulative'] != 'True']
#     df = df.drop('Cumulative', axis=1)
#     return df
def findDataSecondTime():
    # params = urllib.parse.quote_plus(
    #     "Driver={SQL Server};"
    #     "Server=CGDESKTOP\SQLEXPRESS;"
    #     "Database=UTRBDMSNET;"
    #     "Trusted_Connection = yes;"
    # )
    df_prod = pd.DataFrame(columns=['Cumulative', 'WellID', 'Year', 'Month', 'Volume', 'ProdType',
                                    'WellName'])

    server = 'oilgas-sql-prod.ogm.utah.gov'
    username = 'coltongoodrich'
    password = '#newUser0615'
    database = 'UTRBDMSNET'

    params = urllib.parse.quote_plus('DRIVER={SQL Server};'
                                     'SERVER=' + server + ';'
                                                          'DATABASE=' + database + ';'
                                                                                   'UID=' + username + ';'
                                                                                                       'PWD=' + password)

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    time_start = time.perf_counter()
    # Query and load into DataFrame
    prod_years = list(range(2023, 2025))
    prod_type = ['GAS', 'OIL']
    for i in prod_years:

        for j in range(2):
            test_query = f"""WITH cte AS (
                            SELECT Cumulative, ConstructKey, ReportPeriod, ProdType, CONVERT(FLOAT, prodquantity) AS prodquantity
                            FROM ProdFacilityProduction
                            WHERE ProdType = '{prod_type[j]}' AND prodquantity > 0 AND YEAR(ReportPeriod) = '{i}'
                        )
                        SELECT 
                            pfp.Cumulative,
                            w.WellID,
                            YEAR(pfp.ReportPeriod) AS 'Year',
                            MONTH(pfp.ReportPeriod) AS 'Month',
                            SUM(pfp.prodquantity) AS 'Volume',
                            pfp.ProdType,
                            w.WellName
                        FROM Well w
                        JOIN Construct c ON w.PKey = c.WellKey
                        JOIN cte pfp ON c.PKey = pfp.ConstructKey
                        GROUP BY 
                            YEAR(pfp.ReportPeriod),
                            MONTH(pfp.ReportPeriod),
                            pfp.ProdType,
                            w.WellName,
                            pfp.Cumulative,
                            w.WellID;"""
            df_test = pd.read_sql(test_query, engine)
            df_prod = pd.concat([df_prod, df_test])
    df = df_prod.sort_values(by=['Year', 'Month', 'ProdType', 'WellName', 'Cumulative', 'WellID'])

    # query = "SELECT Cumulative, w.WellID, year(pfp.ReportPeriod) as 'Year', month(pfp.ReportPeriod) as 'Month', SUM(CAST(prodquantity AS FLOAT)) AS 'Volume', pfp.ProdType as 'ProdType', w.WellName " \
    #         "FROM Well w  " \
    #         "JOIN Construct c on w.PKey = c.WellKey " \
    #         "JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     " \
    #         "where (pfp.ProdType = 'GAS' or pfp.ProdType = 'OIL') " \
    #         "GROUP BY year(pfp.ReportPeriod), month(pfp.ReportPeriod), pfp.ProdType,w.WellName,pfp.Cumulative, w.WellID HAVING SUM(CAST(prodquantity AS FLOAT)) > 0"
    #
    # df = pd.read_sql(query, engine)
    # df['Cumulative'] = df['Cumulative'].astype(str)
    df = df[df['Cumulative'] != 'True']
    df = df.drop('Cumulative', axis=1)

    # time_start = time.perf_counter()
    # query = "SELECT Cumulative, w.WellID, year(pfp.ReportPeriod) as 'Year', month(pfp.ReportPeriod) as 'Month', SUM(CAST(prodquantity AS FLOAT)) AS 'Volume', pfp.ProdType as 'ProdType', w.WellName " \
    #         "FROM Well w  " \
    #         "JOIN Construct c on w.PKey = c.WellKey " \
    #         "JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     " \
    #         "where (pfp.ProdType = 'GAS' or pfp.ProdType = 'OIL') AND YEAR(ReportPeriod) is not Null" \
    #         "GROUP BY year(pfp.ReportPeriod), month(pfp.ReportPeriod), pfp.ProdType,w.WellName,pfp.Cumulative, w.WellID HAVING SUM(CAST(prodquantity AS FLOAT)) > 0"
    #
    # df = pd.read_sql(query, engine)
    # df['Cumulative'] = df['Cumulative'].astype(str)
    # df = df[df['Cumulative'] != 'True']
    # df = df.drop('Cumulative', axis=1)
    return df


def formatSecondProd(df, api):

    new_df = df[df['WellID'] == str(api)]
    if api == '4301330574':
        pass

    prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i in new_df.values]
    return prod_line
    # prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i in prod_line]

def formatSecondProdAll(df, apis):
    new_df = df[df['WellID'].isin([str(i) for i in apis])]
    # if api == '4301330574':
    #     pass

    prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i in new_df.values]
    return prod_line

def determineAdjacentVals(data):
    # section, township, township_dir, range_val, range_dir, meridian = int(data[:2]), int(data[2:4]), data[4], int(data[5:7]), data[7], data[8]

    section, township, township_dir, range_val, range_dir, meridian = int(data[:2]), int(data[2:4]), data[4], int(data[5:7]), data[7], data[8]

    all_data_lst = processSections(section, township, township_dir, range_val, range_dir, meridian)
    all_data_lst.append([section, township, township_dir, range_val, range_dir, meridian])
    for i in all_data_lst:
        output = processSections(i[0], i[1], i[2], i[3], i[4], i[5])
        all_data_lst = all_data_lst + output
    all_data_lst = [list(t) for t in set(tuple(element) for element in all_data_lst)]
    all_data_lst = sorted(all_data_lst)
    code_lst = rewriteCode(all_data_lst)
    return code_lst


def processSections(section, township, township_dir, range_val, range_dir, meridian):
    all_data_lst = []
    lst = platAdjacentLsts(int(section))
    sections = lst[1]
    for i in range(len(lst[1])):
        tsr_mod = lst[2][i]
        for j in range(len(sections[i])):
            sec_val = sections[i][j]
            township_new, township_dir_new = modTownship(tsr_mod[0], township, township_dir)
            range_val_new, range_dir_new = modRange(tsr_mod[1], range_val, range_dir)
            all_data_lst.append([sec_val, township_new, township_dir_new, range_val_new, range_dir_new, meridian])
    return all_data_lst


def platAdjacentLsts(index):
    lst = [[[1], [[2, 11, 12], [35, 36], [6, 7], [31]], [[0, 0], [1, 0], [0, 1], [1, 1]]],
           [[2], [[3, 10, 11, 12, 1], [34, 35, 36]], [[0, 0], [1, 0]]],
           [[3], [[4, 9, 10, 11, 2], [33, 34, 35]], [[0, 0], [1, 0]]],
           [[4], [[5, 8, 9, 10, 3], [32, 33, 34]], [[0, 0], [1, 0]]],
           [[5], [[6, 7, 8, 9, 4], [31, 32, 33]], [[0, 0], [1, 0]]],
           [[6], [[7, 5, 8], [31, 32], [1, 12], [36]], [[0, 0], [1, 0], [0, -1], [1, -1]]],
           [[7], [[6, 5, 8, 17, 18], [1, 12, 13]], [[0, 0], [0, -1]]],
           [[18], [[7, 8, 17, 19, 20], [12, 13, 14]], [[0, 0], [0, -1]]],
           [[19], [[18, 17, 20, 29, 30], [13, 14, 25]], [[0, 0], [0, -1]]],
           [[30], [[19, 20, 29, 32, 31], [14, 25, 36]], [[0, 0], [0, -1]]],
           [[31], [[30, 29, 32], [6, 5], [25, 36], [1]], [[0, 0], [-1, 0], [0, -1], [-1, -1]]],
           [[12], [[13, 14, 11, 2, 1], [18, 7, 6]], [[0, 0], [0, 1]]],
           [[13], [[24, 23, 14, 11, 12], [19, 18, 7]], [[0, 0], [0, 1]]],
           [[24], [[25, 26, 23, 14, 13], [30, 19, 18]], [[0, 0], [0, 1]]],
           [[25], [[36, 35, 26, 23, 24], [31, 30, 19]], [[0, 0], [0, 1]]],
           [[32], [[31, 30, 29, 28, 33], [6, 5, 4]], [[0, 0], [-1, 0]]],
           [[33], [[32, 29, 28, 27, 34], [5, 4, 3]], [[0, 0], [-1, 0]]],
           [[34], [[33, 28, 27, 26, 35], [4, 3, 2]], [[0, 0], [-1, 0]]],
           [[35], [[34, 27, 26, 25, 36], [2, 3, 1]], [[0, 0], [-1, 0]]],
           [[36], [[35, 26, 25], [2, 1], [31, 30], [6]], [[0, 0], [-1, 0], [0, 1], [-1, 1]]],
           [[8], [[5, 4, 9, 16, 17, 18, 7, 6]], [[0, 0]]],
           [[9], [[4, 3, 10, 15, 16, 17, 8, 5]], [[0, 0]]],
           [[10], [[3, 2, 11, 14, 15, 16, 9, 4]], [[0, 0]]],
           [[11], [[2, 1, 12, 13, 14, 15, 10, 3]], [[0, 0]]],
           [[17], [[8, 9, 16, 21, 20, 19, 18, 7]], [[0, 0]]],
           [[16], [[9, 10, 15, 22, 21, 20, 17, 8]], [[0, 0]]],
           [[15], [[10, 11, 14, 23, 22, 21, 16, 9]], [[0, 0]]],
           [[14], [[11, 12, 13, 24, 23, 22, 15, 10]], [[0, 0]]],
           [[20], [[17, 16, 21, 28, 29, 30, 19, 18]], [[0, 0]]],
           [[21], [[16, 15, 22, 27, 28, 29, 20, 17]], [[0, 0]]],
           [[22], [[15, 14, 23, 26, 27, 28, 21, 16]], [[0, 0]]],
           [[23], [[14, 13, 24, 25, 26, 27, 22, 15]], [[0, 0]]],
           [[29], [[20, 21, 28, 33, 32, 31, 30, 19]], [[0, 0]]],
           [[28], [[21, 22, 27, 34, 33, 32, 29, 20]], [[0, 0]]],
           [[27], [[22, 23, 26, 35, 34, 33, 28, 21]], [[0, 0]]],
           [[26], [[23, 24, 25, 36, 35, 34, 27, 22]], [[0, 0]]]]
    for i in lst:
        if i[0][0] == index:
            return i


def modTownship(tsr_val, tsr_base, tsr_direction):
    if tsr_val == 0:
        return tsr_base, tsr_direction
    else:
        if tsr_direction == 'N':
            if tsr_val == -1:
                tsr_base -= 1
            elif tsr_val == 1:
                tsr_base += 1
        elif tsr_direction == 'S':
            if tsr_val == -1:
                tsr_base += 1
            elif tsr_val == 1:
                tsr_base -= 1
        if tsr_direction == 'N' and tsr_base == 0:
            tsr_direction, tsr_base = 'S', 1
        elif tsr_direction == 'S' and tsr_base == 0:
            tsr_direction, tsr_base = 'N', 1

        return tsr_base, tsr_direction


def modRange(tsr_val, tsr_base, tsr_direction):
    if tsr_val == 0:
        return tsr_base, tsr_direction
    else:
        if tsr_direction == 'W':
            if tsr_val == -1:
                tsr_base += 1
            elif tsr_val == 1:
                tsr_base -= 1
        elif tsr_direction == 'E':
            if tsr_val == -1:
                tsr_base -= 1
            elif tsr_val == 1:
                tsr_base += 1

        if tsr_direction == 'E' and tsr_base == 0:
            tsr_direction, tsr_base = 'W', 1
        elif tsr_direction == 'W' and tsr_base == 0:
            tsr_direction, tsr_base = 'E', 1
        return tsr_base, tsr_direction


def rewriteCode(lst):
    new_lst = []
    lst = sorted(lst)
    for i in lst:
        section, township, township_dir, range_val, range_dir, meridian = str(i[0]), str(i[1]), i[2], str(i[3]), i[4], i[5]
        if len(section) == 1:
            section = "0" + section
        if len(township) == 1:
            township = "0" + township
        if len(range_val) == 1:
            range_val = "0" + range_val
        fullLine = section + township + township_dir + range_val + range_dir + meridian
        new_lst.append(fullLine)
    return new_lst


def processAndReturnMonthlyPrices():
    pd.set_option('display.max_columns', None)
    df_tot = pd.read_csv('ProdData.csv', encoding="ISO-8859-1")
    df_tot['Date'] = df_tot['Date'].str.slice(0, 7).str.pad(7, side='right')
    oil = yf.download("CL=F", start='1900-01-01')
    ng_prices = yf.download("NG=F", start='1900-01-01')
    monthly_oil_prices = oil["Close"].resample("ME").mean()
    monthly_gas_prices = ng_prices["Close"].resample("ME").mean()

    monthly_oil_prices_df = monthly_oil_prices.to_frame()
    monthly_gas_prices_df = monthly_gas_prices.to_frame()

    monthly_oil_prices_df.reset_index(inplace=True)
    monthly_gas_prices_df.reset_index(inplace=True)

    monthly_oil_prices_df.columns = ['Date', 'Cost']
    monthly_gas_prices_df.columns = ['Date', 'Cost']

    monthly_oil_prices_df['Date'] = monthly_oil_prices_df['Date'].astype(str).str.slice(0, 7).str.pad(7, side='right')
    monthly_gas_prices_df['Date'] = monthly_gas_prices_df['Date'].astype(str).str.slice(0, 7).str.pad(7, side='right')
    monthly_gas_prices_df['ProdType'] = 'GAS'
    index_to_remove = df_tot[df_tot['Date'] == str(monthly_oil_prices_df['Date'].iloc[0])].index[0]
    df_tot = df_tot.iloc[:index_to_remove]
    all_df = pd.concat([df_tot, monthly_oil_prices_df])
    all_df['ProdType'] = 'OIL'
    all_df = pd.concat([all_df, monthly_gas_prices_df])
    all_df = all_df.sort_values('Date')
    all_df['Date'] = all_df['Date'].astype(str)
    return all_df


def sqlProductionDFGenerate(all_data_apis, cursor, conn, df_many):
    df_all = pd.DataFrame(columns=['WellID', 'Year', 'Month', 'Oil Volume (bbl)', 'WellName', 'Date',
                                   'Oil Price (bbl)', 'Potential Oil Profit',
                                   'Cumulative Potential Oil Production (bbl)',
                                   'Potential Cumulative Oil Profit', 'Gas Volume (mcf)',
                                   'Gas Price (mcf)', 'Potential Gas Profit',
                                   'Potential Cumulative Gas Profit',
                                   'Cumulative Potential Gas Production (mcf)'])

    # if len(all_data_apis) > 10:
    #     df_many = findDataSecondTime()
    all_df = processAndReturnMonthlyPrices()
    # output_all = formatSecondProdAll(df_many, all_data_apis)

    # output_all = output_all.reset_index(drop=True)



    for i in all_data_apis:
        # if len(all_data_apis) < 10:
        #     prod_output = sqlFindProduction(cursor, i, conn)
        # else:
        prod_output = formatSecondProd(df_many, i)
        if prod_output:
            temp_prod_df = pd.DataFrame(prod_output, columns=['WellID', 'Year', 'Month', 'Volume', 'ProdType', 'WellName'])
            temp_prod_df['Year'] = temp_prod_df['Year'].astype(int).astype(str)
            temp_prod_df['Month'] = temp_prod_df['Month'].astype(int).astype(str).str.zfill(2)
            temp_prod_df['Date'] = temp_prod_df['Year'].astype(int).astype(str) + '-' + temp_prod_df['Month'].astype(str)
            merged_df = pd.merge(temp_prod_df, all_df, on=['Date', 'ProdType'], how='left')
            merged_df['Profit'] = merged_df.apply(lambda x: x['Volume'] * x['Cost'], axis=1)
            merged_df['Profit'] = merged_df['Profit'].astype(float)
            df_summed = merged_df.groupby('Date')['Profit'].sum().reset_index()
            df_summed['Cumulative Profit'] = df_summed['Profit'].cumsum()
            df_summed['Cumulative Profit'] = df_summed['Cumulative Profit'].astype(float)
            df_summed['Profit'] = df_summed['Profit'].astype(float)
            merged_df_gas = merged_df[(merged_df['ProdType'] == 'GAS')]
            merged_df_gas['Cumulative Production'] = merged_df_gas['Volume'].cumsum()
            df_summed_gas = merged_df_gas.groupby('Date')['Profit'].sum().reset_index()
            df_summed_gas['Cumulative Profit'] = df_summed['Profit'].cumsum()
            merged_df_oil = merged_df[(merged_df['ProdType'] == 'OIL')]
            merged_df_oil['Cumulative Production'] = merged_df_oil['Volume'].cumsum()
            df_summed_oil = merged_df_oil.groupby('Date')['Profit'].sum().reset_index()
            df_summed_oil['Cumulative Profit'] = df_summed['Profit'].cumsum()
            df_summed_oil_new, merged_df_oil_new, df_summed_gas_new, merged_df_gas_new = copy.deepcopy(df_summed_oil), copy.deepcopy(merged_df_oil), copy.deepcopy(df_summed_gas), copy.deepcopy(
                merged_df_gas)
            merged_df_oil_new['Potential Cumulative Oil Profit'] = merged_df_oil_new['Profit'].cumsum()
            merged_df_gas_new['Potential Cumulative Gas Profit'] = merged_df_gas_new['Profit'].cumsum()
            merged_df_oil_new = merged_df_oil_new.rename(
                columns={'Volume': 'Oil Volume (bbl)', 'Cost': 'Oil Price (bbl)', 'Profit': 'Potential Oil Profit', 'Cumulative Production': 'Cumulative Potential Oil Production (bbl)'})
            merged_df_oil_new = merged_df_oil_new.drop('ProdType', axis=1)
            merged_df_gas_new = merged_df_gas_new.rename(
                columns={'Volume': 'Gas Volume (mcf)', 'Cost': 'Gas Price (mcf)', 'Profit': 'Potential Gas Profit', 'Cumulative Production': 'Cumulative Potential Gas Production (mcf)'})
            merged_df_gas_new_cut = merged_df_gas_new[
                ['Date', 'Gas Volume (mcf)', 'Gas Price (mcf)', 'Potential Gas Profit', 'Potential Cumulative Gas Profit', 'Cumulative Potential Gas Production (mcf)']]
            merged_df = pd.merge(merged_df_oil_new, merged_df_gas_new_cut, on='Date')
            df_all = pd.concat([df_all, merged_df], ignore_index=True)  # Avoid index duplication
    return df_all


# return df_all
# database_connect = r'C:\Work\RewriteAPD\Docket 2024-018 - Cause No. 132-35 Viz Data.db'
# database_connect = r'C:\Work\RewriteAPD\Docket No. 2024-023 Cause No. 132-36 Viz Data.db'
#
# ''
# conn = sqlite3.connect(database_connect)
# cursor = conn.cursor()
#
# merged_df.to_sql('Production', conn, index=False, if_exists='append')


mainProcess()
