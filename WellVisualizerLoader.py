import cProfile
import pstats
from io import StringIO
from collections import OrderedDict
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pyproj import Transformer
from shapely.prepared import prep
import regex as re
import rtree
from shapely.geometry import Point, Polygon
from shapely import wkt
import geopandas as gpd
import matplotlib.pyplot as plt
import urllib
import yfinance as yf
from sqlalchemy import create_engine
from pyproj import Proj, Geod
import time
import copy
from collections import defaultdict
import sqlite3
import os
import numpy as np
import pandas as pd
import pandas.errors
import pyodbc
import ModuleAgnostic as ma
import utm
import warnings
import dask_geopandas
# Suppress all future warnings
warnings.filterwarnings('ignore', category=FutureWarning)
# warnings.filterwarnings('ignore', category=SettingWithCopyWarning)
warnings.simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)
# Suppress all user warnings
warnings.filterwarnings('ignore', category=UserWarning)

# DB Location - C:\Work\RewriteAPD\Board_DB.db
def mainProcess():
    pd.set_option('display.max_columns', None)
    # Set display options
    pd.set_option('display.max_colwidth', None)  # Show full contents of each cell
    pd.set_option('display.width', None)  # Don't limit the width of the output
    pd.set_option('display.max_columns', None)  # Show all columns
    # setup()


    current_dir = os.getcwd()
    name_used = r'C:\Work\RewriteAPD\UsedBoardData.db'
    apd_data_dir_used = os.path.join(current_dir, name_used)
    conn_db_used = sqlite3.connect(apd_data_dir_used)

    name = 'Board_DB_Plss.db'
    path_db = r'C:\Work\BoardInfo'
    apd_data_dir = os.path.join(path_db, name)
    conn = sqlite3.connect(apd_data_dir)
    plss_df_adjacent = pd.read_sql('SELECT * FROM Adjacent', conn)
    plss_df_values = pd.read_sql('SELECT * FROM BaseData', conn)

    sections_file = r"C:\Work\Databases\Used_data.gdb"
    sections = gpd.read_file(sections_file, layer='PLSSSections_GCDB')
    df_own = gpd.read_file(sections_file, layer='Ownership_by_Section')
    all_df_prod_data = processAndReturnMonthlyPrices()

    string_sql = 'select * from Main'
    df_main = pd.read_sql(string_sql, conn_db_used)
    string_sql = 'select * from Apds'
    df_apd = pd.read_sql(string_sql, conn_db_used)
    string_sql = 'select * from TSR'
    df_tsr = pd.read_sql(string_sql, conn_db_used)
    all_matters = df_main['Label'].unique()
    # df_many = findDataSecondTime()

    string_sql = 'select * from Ownership'
    df_many = pd.read_sql(string_sql, conn_db_used)
    # try:
    #     df_many.to_sql('Ownership', conn_db_used, index=False, if_exists='append')
    # except (ValueError, AttributeError):
    #     pass
    errors = []
    all_years = df_main['Year'].unique()
    for year in all_years:
        monthly_data = df_main[df_main['Year'] == year]
        all_months = monthly_data['Month'].unique()
        for month in all_months:
            docket_data = monthly_data[monthly_data['Month'] == month]
            all_dockets = docket_data['Label'].unique()
            for i in all_dockets:
                main_i = docket_data[(docket_data['Label'] == i)]
                tsr_i = df_tsr[(df_tsr['Label'] == i) & (df_tsr['Month'] == month) & (df_tsr['Year'] == year)]
                tsr_data = tsr_i.drop('Label', axis=1).values

                apds = df_apd[(df_apd['Label'] == i) & (df_apd['Month'] == month) & (df_apd['Year'] == year)]['APINumber'].values

                # if i == 'Docket No. 2024-016 Cause No. 132-33':
                    # tsr_data = np.array([False, False, False])
                    # apds = [0]

                    # if month == 'October':
                doEverything(i, apds, year, month, df_many, tsr_data, plss_df_adjacent, plss_df_values, sections, df_own, all_df_prod_data)


    # for i in all_matters:
    #     main_i = df_main[(df_main['Label'] == i)]
    #     tsr_i = df_tsr[(df_tsr['Label'] == i)]
    #     tsr_data = tsr_i.drop('Label', axis=1).values
    #     year = main_i['Year'].tolist()[0]
    #     month = main_i['Month'].tolist()[0]
    #     apds = df_apd[(df_apd['Label'] == i)]['APINumber'].values
    #     # try:
    #     if i == 'Docket No. 2024-007 Cause No. 199-05':
    #
    #     # if month == 'October':
    #         doEverything(i, apds, year, month, df_many, tsr_data, plss_df_adjacent, plss_df_values)
    #     # except:
    #     #     print(i, ' error occured')
    #     errors.append(i)


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


    conn_db.execute('DROP TABLE IF EXISTS WellInfo')
    conn_db.execute('DROP TABLE IF EXISTS DX')
    conn_db.execute('DROP TABLE IF EXISTS PlatData')
    conn_db.execute('DROP TABLE IF EXISTS Production')
    conn_db.execute('DROP TABLE IF EXISTS Adjacent')
    conn_db.execute('DROP TABLE IF EXISTS BoardDataLinks')
    conn_db.execute('DROP TABLE IF EXISTS BoardData')


def doEverything(label, apds, year, month, df_many, tsr_data, plss_df_adjacent, plss_df_values, sections, df_own, all_df_prod_data):
    ma.printLineBreak()
    ma.printLineBreak()
    ma.printLineBreak()
    ma.printLineBreak()
    print(label)
    current_dir = os.getcwd()
    name = 'Board_DB.db'
    apd_data_dir = os.path.join(current_dir, name)
    print(apd_data_dir)
    conn_db = sqlite3.connect(apd_data_dir)
    cursor_db = conn_db.cursor()
    apds = list(dict.fromkeys(apds))
    apds = [int(float(str(i)[:10])) for i in apds]
    conn, cursor = sqlConnect()
    time_start = time.perf_counter()
    # ma.analyzeTime2(createDataFrame, [apds, cursor, label, conn, tsr_data, plss_df_adjacent, plss_df_values])

    df, df_dx, df_plat, df_board_data, df_links_data, df_adjacent_lst = createDataFrame(apds, cursor, label, conn,
                                                                                        tsr_data, plss_df_adjacent, plss_df_values)
    # print('createDataFrame Retrieval Time: ', time.perf_counter() - time_start)
    # ma.analyzeTime2(generateOwnershipData, [df_plat, sections, df_own])
    df_owner = generateOwnershipData(df_plat, sections, df_own)
    time_start = time.perf_counter()

    df_prod = sqlProductionDFGenerate(df['WellID'].unique().tolist(), cursor, conn, df_many, all_df_prod_data)
    # ma.analyzeTime2(sqlProductionDFGenerate, [df['WellID'].unique().tolist(), cursor, conn, df_many, all_df_prod_data])
    # print('sqlProductionDFGenerate Retrieval Time: ', time.perf_counter() - time_start)
    # print(foo)
    time_start = time.perf_counter()

    df_prod['Date'] = pd.to_datetime(df_prod['Date'], format='%Y-%m')
    df_prod = df_prod.sort_values(by=['WellID', 'Date'], ascending=[True, True])
    # print('Data Retrieval Time: ', time.perf_counter() - time_start)

    time_start = time.perf_counter()

    df['MainWell'] = df['WellID'].isin([str(i) for i in apds])
    df['Board_Docket'] = label
    df['Docket_Month'] = month
    df['Board_Year'] = year
    df_adjacent_lst['Board_Docket'] = label

    # foo = df_dx[df_dx['WellNameNumber'].str.contains('Dill', case=False)]
    # df_prod = None
    duplicate_columns = df.columns[df.columns.duplicated(keep=False)]
    # print("Duplicate columns:", duplicate_columns.tolist())
    # df = df.T.drop_duplicates().T
    df = df.loc[:, ~df.columns.duplicated(keep='first')]
    # print(foo)
    # writeToDatabase(conn_db, cursor_db, df, df_dx, df_plat, df_prod, df_links_data, df_board_data, df_adjacent_lst, df_owner)
def scrapeForLabelData(label, section, township, rng, mer):
    pattern_ns = re.compile(r'(S|N)')
    pattern_ew = re.compile(r'(E|W)')
    match_ns = pattern_ns.search(label).group(1)
    match_ew = pattern_ew.search(label).group(1)
    ns_number, ew_number, mer_val = -1, -1, -1
    if mer == '26':
        mer_val = 'S'
    elif mer == '30':
        mer_val = 'U'
    label_true = [str(int(float(section))), str(int(float(township))), match_ns, str(int(float(rng))), match_ew, mer_val]
    label_true[0] = str(label_true[0]).zfill(2)
    label_true[1] = str(label_true[1]).zfill(2)
    label_true[3] = str(label_true[3]).zfill(2)
    # output = ma.tableToConcCode(label_true)
    return output
def recreateLabel(row):
    output = f"""T{row['Township']}{row['Township Direction']} R{row['Range']}{row['Range Direction']}"""
    return output

def recreateBaselineNumber(row):
    if row['Baseline'] == 'U':
        return '30'
    else:
        return '26'
def view_polygon_details(gdf, sec_gdf, df_plat):
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
    categories = gdf['state_lgd'].unique()
    categorie_dct = {categories[i]: colors[i] for i in range(len(categories))}

    sec_gdf = sec_gdf.to_crs(epsg=4326)
    gdf = gdf.to_crs(epsg=4326)
    df_plat_all_conc = df_plat['Conc'].unique()
    df_plat['LABEL'] = df_plat.apply(recreateLabel, axis=1)
    df_plat['BASEMERIDIAN'] = df_plat.apply(recreateBaselineNumber, axis=1)
    gdf_filtered = gdf[gdf['Conc'].isin(df_plat_all_conc)]
    all_data_lst = []
    rows = gdf_filtered['FRSTDIVID'].unique()
    fig, ax = plt.subplots()

    for i in rows:
        used_gdf_rows = gdf[gdf['FRSTDIVID'] == i]

        used_data = sec_gdf[sec_gdf['FRSTDIVID'] == i]
        used_data.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=2)
        for index, row_gdf in used_gdf_rows.iterrows():
            coords = row_gdf['geometry']
            data_row = [row_gdf['objectid'], row_gdf['owner'], row_gdf['state_lgd'], row_gdf['FRSTDIVID'], row_gdf['Conc'], row_gdf['tribe'], row_gdf['county']]
            if coords.geom_type == 'Polygon':
                poly_lst = data_row + [str(coords_ex)]
                all_data_lst.append(poly_lst)
            elif coords.geom_type == 'MultiPolygon':
                # Multiple polygons
                for poly in coords.geoms:
                    poly_lst = data_row + [str(poly)]
                    all_data_lst.append(poly_lst)

    columns = ['ID', 'owner', 'state_legend', 'div_id', 'conc', 'tribe', 'county', 'geometry']
    df_test_dx = [{'ID': i[0],
                   'owner': i[1],
                   'state_legend': i[2],
                   'div_id': i[3],
                   'conc': i[4],
                   'tribe': i[5],
                   'county': i[6],
                   'geometry': i[7]} for i in all_data_lst]
    df_owner = pd.DataFrame(df_test_dx, columns=columns)
    return df_owner

def generateOwnershipData(df_plat, sections, df_own):
    used_concs = df_plat['Conc'].unique()
    # sections_file = r"C:\Work\Databases\Used_data.gdb"
    # sections = gpd.read_file(sections_file, layer='PLSSSections_GCDB')
    # df_own = gpd.read_file(sections_file, layer='Ownership_by_Section')
    # ma.analyzeTime2(view_polygon_details, [df_own, sections, df_plat])
    df_owner = view_polygon_details(df_own, sections, df_plat)
    return df_owner

    # owner_path = r"C:\Work\Databases\Board_DB_Ownership2.db"
    # df_own = gpd.read_file(owner_path)
    #
    # # conn = sqlite3.connect(owner_path)
    # # string_sql = 'select * from Ownership'
    # # df_own = pd.read_sql(string_sql, conn)

    # df_own = df_own.rename(columns={'EastingNorthing': 'geometry'})
    # df_own['Conc'] = df_own.apply(
    #     lambda x: scrapeForLabelData(x['Label'], x['Section'], x['Township'], x['Range'], x['Baseline']), axis=1)
    # df_own = df_own[df_own['Conc'].isin(used_concs)].drop_duplicates(keep='first')
    #
    # df_own['geometry'] = df_own['geometry'].apply(lambda row: wkt.loads(row))
    # gdf = gpd.GeoDataFrame(df_own, geometry='geometry')
    # gdf.set_crs(epsg=26912, inplace=True)
    # gdf = gdf.to_crs(epsg=4326)
    #
    # # used_df_own = df_own[df_own['Conc'].isin(used_concs)].drop_duplicates(keep='first')
    # # used_df_own['EastingNorthing'] = used_df_own['EastingNorthing'].apply(lambda row: wkt.loads(row))
    # colors = [
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
    # categories = df_own['Owner_Legend'].unique()
    # categorie_dct = {categories[i]: colors[i] for i in range(len(categories))}

    # fig, ax = plt.subplots()

    # for i in used_concs:
    #
    #     used_data = df_plat[df_plat['Conc'] == i]
    #     used_data = used_data.rename(columns={'EastingNorthing': 'geometry'})
    #     used_owner_rows = gdf[gdf['Conc'] == i]
    #     plat_geo = ma.geometryTransform(used_data, 'latlon')
    #     coords_plat = plat_geo['geometry'].values[0]
    #     coords = coords_plat.exterior.coords
    #     x1_p = [coord[0] for coord in coords]
    #     y1_p = [coord[1] for coord in coords]
    #     ax.plot(x1_p, y1_p, marker='o', linestyle='-', linewidth=1, c='black')
    #     label_pt = plat_geo['centroid'].values[0]
    #     label_val = plat_geo['label'].values[0]
    #     x, y = label_pt.x, label_pt.y
    #     ax.text(x, y, label_val)

    #     for index, row in used_owner_rows.iterrows():
    #         color_used = categorie_dct[row['Owner_Legend']]
    #         coords = row['geometry']
    #

    #         if coords.geom_type == 'Polygon':
    #
    #             coords = coords.exterior.coords
    #             x1 = [coord[0] for coord in coords]
    #             y1 = [coord[1] for coord in coords]
    #             ax.plot(x1, y1, marker='o', linestyle='-', linewidth=1, c='red')
    #             ax.fill(x1, y1, c=color_used, alpha=0.5)
    #
    #         elif coords.geom_type == 'MultiPolygon':
    #             # Multiple polygons
    #             for poly in coords.geoms:
    #                 coords = poly.exterior.coords
    #                 x1 = [coord[0] for coord in coords]
    #                 y1 = [coord[1] for coord in coords]
    #                 ax.plot(x1, y1, marker='o', linestyle='-', linewidth=1, c='red')
    #                 ax.fill(x1, y1, c=color_used, alpha=0.5)
    # plt.show()
    #
    # df_own.to_sql('Ownership', conn, index=False, if_exists='replace')

    # self.df_sec_fd['new_code'] = self.df_sec_fd.apply(
    #     lambda x: self.tntd(x['Section']) + self.tntd(x['Township']) + ma.translateNumberToDirection('township', x[
    #         'Township Direction']) + self.tntd(x['Range']) + ma.translateNumberToDirection('rng', x[
            #         'Range Direction']) + ma.translateNumberToDirection('baseline', x['Baseline']), axis=1)
    # for idf, row in df_own.iterrows():

        # conc = scrapeForLabelData(row['Label'], row['Section'], row['Township'], row['Range'], row['Baseline'])


        # x_coord, y_coord = record['X'], record['Y']
        # lst.append([conc, x_coord, y_coord])



def createDataFrame(apds, cursor, label, conn, tsr_data, plss_df_adjacent, plss_df_values):



    apds_original = copy.deepcopy(apds)
    time_start1 = time.perf_counter()
    if not tsr_data.any():
        apds, all_plats_lst, df_adjacent_lst = findPlatsSurrounding(cursor, apds, plss_df_adjacent)
    else:
        apds, all_plats_lst, df_adjacent_lst = findPlatsSurroundingSectionsGiven(cursor, tsr_data, plss_df_adjacent)

    time_start2 = time.perf_counter()
    df_board_data, df_links_data = retrieveBoardInformation(all_plats_lst, cursor)
    time_start3 = time.perf_counter()
    df_plat = recordPlatData(all_plats_lst, label, plss_df_values)
    time_start4 = time.perf_counter()
    output, columns = retrieveConstructDataAll(cursor, apds, apds_original)
    time_start5 = time.perf_counter()
    prod_data = sqlProdData(cursor, apds)
    prod_data = prod_data.rename(columns={'ID': 'WellID'})
    merged_df = prod_data.merge(output, on='WellID')
    time_start6 = time.perf_counter()
    result = pd.concat([
        output.iloc[:, :-2],  # All columns from output except the last two
        merged_df[['OilVolume', 'GasVolume']],  # OilVolume and GasVolume from prod_data
        output.iloc[:, 10:11],  # The 11th column from output (WCRCompletionDate)
        output.iloc[:, -2:]  # The last two columns from output
    ], axis=1)
    # Drop the 'ID' column if it was added during the merge
    result = result.drop(columns=['ID'], errors='ignore')
    result = result.drop_duplicates(keep='first')
    output_lst = result.values.tolist()
    output_nonvert = [i for i in output_lst if i[4] != 'VERTICAL']
    output_vert = [i for i in output_lst if i[4] == 'VERTICAL']
    output_nonvert_apis = [i[0] for i in output_lst]

    time_start7 = time.perf_counter()
    dx_data_all = dbDXDataAll(cursor, output_nonvert_apis)
    # retrieveOwnershipData(df_plat)
    # ma.analyzeTime2(dbSurfaceLocDrilled, [cursor, output_vert[i][0], conn, output_vert[i]])

    time_start8 = time.perf_counter()
    apis = [i[0] for i in output_vert]
    output_vert_df = pd.DataFrame(output_vert)
    dx_data = dbSurfaceLocDrilled3(conn, output_vert_df)
    #
    dx_data = dx_data.fillna(0)

    dx_data_all = dx_data.values.tolist()
    # ma.printLine(dx_data.values.tolist())
    # Combine the results
    # dx_data_all = pd.merge(dx_data, output_vert_df[[0, 1]].rename(columns={0: 'API', 1: 'Lease'}), on='API', how='left')
    # print(dx_data_all)
    # def replace_nan(value):
    #     if isinstance(value, float) and math.isnan(value):
    #         return 0
    #     return value


    # dx_data_all = []
    # for i in range(len(output_vert)):
    #     dx = dbSurfaceLocDrilled(conn, output_vert[i])
    #     dx[0][0], dx[1][0] = output_vert[i][0], output_vert[i][0]
    #     dx[0][1], dx[1][1] = output_vert[i][1], output_vert[i][1]
    #     if dx:
    #         dx[0] = [replace_nan(x) for x in dx[0]]
    #         dx[1] = [replace_nan(x) for x in dx[1]]
    #         dx_data_all.extend(dx)
    # print([i for i in dx_data_all if i[0] == '4301320352'])
    # print(foo)

    # for data_line in output_vert:
    #     api = data_line[0]
    #     dx = dbSurfaceLocDrilled(cursor, api, conn, data_line)
    #     ma.analyzeTime2(dbSurfaceLocDrilled, [cursor, api, conn, data_line])
    #     dx[0][0], dx[1][0] = api, api
    #     dx[0][1], dx[1][1] = data_line[1], data_line[1]
    #     dx_data_all.extend(dx)
    # ma.printLineBreak()
    # ma.printLine(dx_data_all)
    # ma.compareLists(dx_data_printed, dx_data_all)
    # print(foo)

    # Convert all columns to string type
    # output = output.astype(str)

    # Replace None (which will now be 'None' strings) with empty string
    # output = output.replace('None', '')

    # Strip whitespace from all elements
    # output = output.applymap(lambda x: x.strip())
    time_start9 = time.perf_counter()

    location_df = recordOutputLocation(output_lst, cursor)
    dx_columns = ['APINumber', 'WellNameNumber', 'MeasuredDepth', 'Inclination', 'Azimuth', 'TrueVerticalDepth', 'X',
                  'Y', 'CitingType']
    new_lst = []

    time_start10 = time.perf_counter()
    # for i in dx_data_all:
    #     data_line = [str(j) for j in i]
    #     new_lst.append(data_line)
    new_lst = [[str(j) for j in i] for i in dx_data_all]
    time_start11 = time.perf_counter()
    dx_data_all = new_lst
    dx_data_all = [list(i) for i in dx_data_all]
    dx_data_all = [i for i in dx_data_all if i[1] != 'None']
    df_test_dx = [{'APINumber': i[0],
                   'WellNameNumber': i[1],
                   'MeasuredDepth': i[2],
                   'Inclination': i[3],
                   'Azimuth': i[4],
                   'TrueVerticalDepth': i[5],
                   'X': i[6],
                   'Y': i[7],
                   'CitingType': i[8]} for i in dx_data_all]
    df_dx = pd.DataFrame(df_test_dx, columns=dx_columns)
    df = pd.merge(result, location_df, on='WellID')
    # print('total process ', round(time.perf_counter() - time_start1, 4))
    # print('findPlatsSurrounding', round(time_start2 - time_start1, 4))
    # print('retrieveBoardInformation', round(time_start3 - time_start2, 4))
    # print('recordPlatData', round(time_start4 - time_start3, 4))
    # print('retrieveConstructDataAll', round(time_start5 - time_start4, 4))
    # print('sqlProdData', round(time_start6 - time_start5, 4))
    # print('output_nonvert_apis', round(time_start7 - time_start6, 4))
    # print('dbDXDataAll', round(time_start8 - time_start7, 4))
    # print('dbSurfaceLocDrilled', round(time_start9 - time_start8, 4))
    # print('recordOutputLocation', round(time_start10 - time_start9, 4))
    # print('df_test_dx ', round(time_start11 - time_start10, 4))
    all_apis = set(df['WellID'].unique())
    dx_apis = set(df_dx['APINumber'].unique())
    missing_data = all_apis - dx_apis

    missing_df = df[df['WellID'].isin(missing_data)]
    if len(missing_data) > 0:
        output_df = sqlFindSHLBHL(cursor, missing_data, conn, missing_df)
        df_dx = pd.concat([df_dx, output_df])
    return df, df_dx, df_plat, df_board_data, df_links_data, df_adjacent_lst


def retrieveOwnershipData(df_plat):
    time_start = time.perf_counter()
    gdb_path = r'C:\GDB\_ags_data98DD7A7826DD45CCA34E5DA8200751E4.gdb'

    time_start = time.perf_counter()
    gdf = gpd.read_file(gdb_path)

    time_start = time.perf_counter()
    gdf = gdf.to_crs(epsg=4326)
    # Create a list to store the data
    polygon_data = []
    # Loop through each row in the GeoDataFrame

    time_start = time.perf_counter()
    for idf, row in gdf.iterrows():
        row_data = row.to_dict()
        geom = row.geometry
        coordinates = []
        if geom.geom_type == 'Polygon':
            # Single polygon
            coordinates = list(geom.exterior.coords)
        elif geom.geom_type == 'MultiPolygon':
            # Multiple polygons
            for poly in geom.geoms:
                coordinates.extend(list(poly.exterior.coords))
        row_data['coordinates'] = coordinates
        polygon_data.append(row_data)

    runOwnership(polygon_data, df_plat)


def runOwnership(polygon_data, df_coords):
    def find_containing_polygon(point, polygons, prepared_polygons, idf):
        for i in idf.intersection(point.bounds):
            if prepared_polygons[i].contains(point):
                return polygons.loc[i, 'new_code']
        return None

    def addInPoints(df_own, df_coords):
        own_polygons = df_own.groupby('Poly_ID').apply(
            lambda group: Polygon(zip(group['Easting'], group['Northing']))).reset_index()
        own_polygons.columns = ['Poly_ID', 'polygon']

        # Group df_coords by new_code and create polygons
        coords_polygons = df_coords.groupby('new_code').apply(
            lambda group: Polygon(zip(group['Easting'], group['Northing']))
        ).reset_index()
        coords_polygons.columns = ['new_code', 'polygon']

        # Create spatial index for own_polygons
        idx = rtree.index.Index()
        for i, row in own_polygons.iterrows():
            idx.insert(i, row['polygon'].bounds)

        df_own['containing_polygon'] = None
        # Convert the Easting and Northing columns to shapely Point objects
        df_own['geometry'] = df_own.apply(lambda row: Point(row['Easting'], row['Northing']), axis=1)
        # Group df_coords by new_code and create a dictionary of polygons
        polygons = df_coords.groupby('new_code').apply(
            lambda x: Polygon(zip(x['Easting'], x['Northing']))).reset_index()
        polygons.columns = ['new_code', 'geometry']
        # Create a spatial index using rtree

        idf = rtree.index.Index()
        for i, polygon in polygons.iterrows():
            idf.insert(i, polygon['geometry'].bounds)
        # Prepare the polygons for faster containment checks
        prepared_polygons = [prep(polygon) for polygon in polygons['geometry']]
        # Find the containing polygon for each point in df_own
        df_own['containing_polygon'] = df_own['geometry'].apply(
            lambda point: find_containing_polygon(point, polygons, prepared_polygons, idf))

    def checkForMatchingTSRData():
        df_coords = pd.read_csv(r'C:\GDB\All_Data_Lat_Lon.csv')
        return df_coords

    def returnUTMCoordsnp(data):
        output = utm.from_latlon(data[1], data[0])[:2]

        return output

    def returnUTMCoords(row):
        easting, northing, _, _ = utm.from_latlon(row['latitude'], row['longitude'])
        return pd.Series([easting, northing])

    # current_dir = os.getcwd()
    # name = 'Board_DB.db'
    # apd_data_dir = os.path.join(current_dir, name)
    # conn = sqlite3.connect(apd_data_dir)
    # string_sql = 'select * from Field'
    # df_tsr = pd.read_sql(string_sql, conn)
    # conn.execute('DROP TABLE IF EXISTS Ownership')
    def create_polygon_group(df):
        polygon = Polygon(zip(df['Easting'], df['Northing']))
        # Assuming other columns have the same value within each group, take the first value
        return pd.Series({
            'polygon': polygon,
            'Owner_Legend': df['Owner_Legend'].iloc[0],
            'Owner': df['Owner'].iloc[0],
            'Acreage': df['Acreage'].iloc[0]
        })

    all_data = []
    time_start = time.perf_counter()

    globalids = [data['globalid'] for data in polygon_data]
    state_lgds = [data['state_lgd'] for data in polygon_data]
    agencies = [data['agency'] for data in polygon_data]
    gis_acres = [data['gis_acres'] for data in polygon_data]

    # Extract the coordinates from polygon_data
    coordinates = np.array([coord for data in polygon_data for coord in data['coordinates']])
    time_start1 = time.perf_counter()
    df = pd.DataFrame(coordinates, columns=['longitude', 'latitude'])
    df[['easting', 'northing']] = df.apply(returnUTMCoords, axis=1)


    # Convert latitudes and longitudes to UTM coordinates
    time_start2 = time.perf_counter()
    utm_coordinates = np.apply_along_axis(returnUTMCoordsnp, 1, coordinates)

    # Convert latitudes and longitudes to UTM coordinates
    time_start3 = time.perf_counter()
    utm_coordinates = [utm.from_latlon(lat, lon)[:2] for lon, lat in coordinates]


    # Create the all_data list using list comprehension
    all_data = [[globalid, state_lgd, agency, gis_acre, coord[1], coord[0], utm_coord[0], utm_coord[1]]
                for globalid, state_lgd, agency, gis_acre, coord, utm_coord
                in zip(globalids, state_lgds, agencies, gis_acres, coordinates, utm_coordinates)]

    # for i, data in enumerate(polygon_data):
    #     for coord in data['coordinates']:
    #         test_out = list(coord)
    #         utm_out = list(utm.from_latlon(test_out[1], test_out[0])[:2])
    #         all_data.append([data['globalid'], data['state_lgd'], data['agency'], data['gis_acres'], test_out[1], test_out[0], utm_out[0], utm_out[1]])

    time_start = time.perf_counter()
    # df_coords = checkForMatchingTSRData()
    df_columns = ['Poly_ID', 'Owner_Legend', 'Owner', 'Acreage', 'Lat', 'Lon', 'Easting', 'Northing']
    df_setup = [{'Poly_ID': i[0].replace("{", "").replace("}", ""),
                 'Owner_Legend': i[1],
                 'Owner': i[2],
                 'Acreage': i[3],
                 'Lat': i[4],
                 'Lon': i[5],
                 'Easting': i[6],
                 'Northing': i[7]} for i in all_data]
    df_own = pd.DataFrame(df_setup, columns=df_columns)
    df_own = df_own.drop_duplicates(keep='first').reset_index()

    time_start = time.perf_counter()
    addInPoints(df_own, df_coords)

    #
    # try:
    #     df_own.to_sql('Ownership', conn, index=False, if_exists='append')
    # except (ValueError, AttributeError):
    #     pass


def retrieveBoardInformation(all_plats_lst, cursor):
    board_matters = sqlFindBoardMatterInformationAll(all_plats_lst, cursor)
    board_matters = ma.removeDupesListOfLists(board_matters)
    know_board_matters = set([i[1] for i in board_matters])

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

    df_links_data = pd.DataFrame(board_matters_dict,
                                 columns=['DocketNumber', 'CauseNumber', 'OrderType', 'EffectiveDate', 'EndDate',
                                          'FormationName',
                                          'Quarter', 'QuarterQuarter', 'Sec', 'Township', 'TownshipDir', 'Range',
                                          'RangeDir', 'PM', 'CountyName', 'Quip'])
    df_board_data = pd.DataFrame(links_data_dict,
                                 columns=['Cause', 'OGMDocumentName', 'Description', 'Filepath', 'DocumentDate'])
    return df_board_data, df_links_data


def rewriteDatabase():
    name = 'Board_DB_Plss.db'
    path_db = r'C:\Work\BoardInfo'
    apd_data_dir = os.path.join(path_db, name)
    conn_main = sqlite3.connect(apd_data_dir)

    name = 'Board_DB_Plss - Copy.db'
    path_db = r'C:\Work\BoardInfo'
    apd_data_dir = os.path.join(path_db, name)
    conn2 = sqlite3.connect(apd_data_dir)
    plss_df_values = pd.read_sql('SELECT * FROM BaseData', conn2)


def recordPlatData(all_plats_lst, label, plss_df_values):
    # rewriteDatabase()
    time_start1 = time.perf_counter()
    # name = 'Board_DB_Plss.db'
    # path_db = r'C:\Work\BoardInfo'
    # apd_data_dir = os.path.join(path_db, name)
    # conn = sqlite3.connect(apd_data_dir)
    # plss_df_values = pd.read_sql('SELECT * FROM BaseData', conn)

    # plss_df_values[['TOWNSHIP', 'RANGE', 'SECTION']] = (
    #     plss_df_values[['TOWNSHIP', 'RANGE', 'SECTION']].apply(
    #         lambda x: x.apply(remove_leading_zeros)))
    # plss_df_values.to_sql('BaseData', conn, index=False, if_exists='replace')

    plats_df = pd.DataFrame(all_plats_lst,
                            columns=['SECTION', 'TOWNSHIP', 'Township_D', 'RANGE', 'Range_Dir', 'Baseline'])
    time_start2 = time.perf_counter()
    # Merge plats_df with plss_df_values
    plss_df_values[['SECTION', 'TOWNSHIP', 'RANGE']] = \
        plss_df_values[['SECTION', 'TOWNSHIP', 'RANGE']].astype(
            float).astype(int)
    df_all = pd.merge(plats_df, plss_df_values,
                      on=['SECTION', 'TOWNSHIP', 'Township_D', 'RANGE', 'Range_Dir', 'Baseline'], how='left')
    time_start3 = time.perf_counter()
    # Rename columns
    column_rename = {
        'TOWNSHIP': 'Township',
        'RANGE': 'Range',
        'SECTION': 'Section',
        'Township_D': 'Township Direction',
        'Range_Dir': 'Range Direction',
        'FullConc': 'Conc',
        'X': 'Easting',
        'Y': 'Northing'
    }
    df_all = df_all.rename(columns=column_rename)

    df_all['Board_Docket'] = label
    df_all['Version'] = None
    df_all['Well'] = None
    df_all['Apd_no'] = None
    time_start4 = time.perf_counter()
    transformer = Transformer.from_crs("epsg:32612", "epsg:4326", always_xy=True)
    df_all['Lon'], df_all['Lat'] = transformer.transform(df_all['Easting'], df_all['Northing'])
    df_all = df_all[
        ['Section', 'Township', 'Township Direction', 'Range', 'Range Direction', 'Baseline', 'Lat', 'Lon', 'Well', 'Conc',
         'Version', 'Apd_no', 'Board_Docket']]
    time_start5 = time.perf_counter()

    df_all = df_all[~df_all['Conc'].str.contains('.', regex=False)]
    # test = df_all[df_all['Conc'].str.contains('.')]


    return df_all


def recordPlatData2(all_plats_lst, label):
    df = sqlConnectPlats()
    df_all = pd.DataFrame(columns=['Section', 'Township', 'Township Direction', 'Range', 'Range Direction',
                                   'Baseline', 'Lat', 'Lon', 'Well', 'Conc', 'Version', 'Apd_no', 'Board_Docket'])

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
    all_plats_lst_translated = [ma.reTranslateData(sublist) for sublist in all_plats_lst]

    #############
    conc_values = set(df['Conc'].unique())

    # Convert all_plats_lst_translated to a set
    all_plats_set = set(all_plats_lst_translated)

    # Find the values in all_plats_lst_translated that aren't in the 'Conc' column
    missing_values = all_plats_set - conc_values

    ##############

    # Filter the dataframe to include only rows where 'Conc' is in all_plats_lst_translated
    df_filtered = df[df['Conc'].isin(all_plats_lst_translated)]

    # Group the filtered dataframe by 'Conc' and apply the process_plat function
    df_processed = df_filtered.groupby('Conc').apply(process_plat)

    # Concatenate the processed dataframe with df_all
    df_all = pd.concat([df_all, df_processed], ignore_index=True)
    return df_all

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
    return df_all


def recordOutputLocation(lst, cursor):
    data_line = []
    api_lst = [i[0] for i in lst]
    all_data = dbTownshipAndRangeAndElevationAll(cursor, api_lst)

    # for i in lst:
    #     api = i[0]
    #     line = all_data[api]
    #     conc_data = list(line[2:])
    #     conc = ma.reTranslateData(conc_data)
    #     new_line = list(line[:2]) + [conc]
    #     data_line.append(new_line)
    data_line = [list(all_data[i[0]][:2]) + [ma.reTranslateData(list(all_data[i[0]][2:]))] for i in lst]
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


def remove_leading_zeros(s):
    if isinstance(s, str):
        return s.lstrip('0') or '0'
    return s


def get_adjacent_polygons(all_plats_lst, plss_df_adjacent):
    # Convert all_plats_lst to a DataFrame
    initial_plats = pd.DataFrame(all_plats_lst,
                                 columns=['src_SECTIO', 'src_TOWNSH', 'src_Town_1', 'src_RANGE', 'src_Range_',
                                          'src_Baseli'])
    initial_plats['src_SECTIO'] = initial_plats['src_SECTIO'].astype(float).astype(int)
    initial_plats['src_TOWNSH'] = initial_plats['src_TOWNSH'].astype(float).astype(int)
    initial_plats['src_RANGE'] = initial_plats['src_RANGE'].astype(float).astype(int)
    # Remove duplicates from initial_plats
    initial_plats = initial_plats.drop_duplicates()

    plss_df_adjacent[['src_TOWNSH', 'nbr_TOWNSH', 'src_RANGE', 'nbr_RANGE', 'src_SECTIO', 'nbr_SECTIO']] = \
    plss_df_adjacent[['src_TOWNSH', 'nbr_TOWNSH', 'src_RANGE', 'nbr_RANGE', 'src_SECTIO', 'nbr_SECTIO']].astype(
        float).astype(int)

    # First level of adjacency
    adjacent_1 = pd.merge(initial_plats, plss_df_adjacent,
                          on=['src_SECTIO', 'src_TOWNSH', 'src_Town_1', 'src_RANGE', 'src_Range_',
                              'src_Baseli']).drop_duplicates(keep='first')

    # Prepare the dataframe for the second level of adjacency
    adjacent_1_prep = adjacent_1[['nbr_SECTIO', 'nbr_TOWNSH', 'nbr_Town_1', 'nbr_RANGE', 'nbr_Range_', 'nbr_Baseli']]
    adjacent_1_prep.columns = [col.replace('nbr_', 'src_') for col in adjacent_1_prep.columns]

    # Second level of adjacency
    adjacent_2 = pd.merge(adjacent_1_prep, plss_df_adjacent,
                          on=['src_SECTIO', 'src_TOWNSH', 'src_Town_1', 'src_RANGE', 'src_Range_',
                              'src_Baseli']).drop_duplicates(keep='first')

    # Get unique FRSTDI codes
    init_plats_codes = plss_df_adjacent[plss_df_adjacent['src_SECTIO'].isin(initial_plats['src_SECTIO']) &
                                        plss_df_adjacent['src_TOWNSH'].isin(initial_plats['src_TOWNSH']) &
                                        plss_df_adjacent['src_Town_1'].isin(initial_plats['src_Town_1']) &
                                        plss_df_adjacent['src_RANGE'].isin(initial_plats['src_RANGE']) &
                                        plss_df_adjacent['src_Range_'].isin(initial_plats['src_Range_']) &
                                        plss_df_adjacent['src_Baseli'].isin(initial_plats['src_Baseli'])][
        'src_FRSTDI'].unique().tolist()

    adjacent_1_plats_codes = adjacent_1['nbr_FRSTDI'].unique().tolist()
    adjacent_2_plats_codes = adjacent_2['nbr_FRSTDI'].unique().tolist()
    adjacent_1_plats_codes = [i for i in adjacent_1_plats_codes if i not in init_plats_codes]
    adjacent_2_plats_codes = [i for i in adjacent_2_plats_codes if
                              i not in init_plats_codes and i not in adjacent_1_plats_codes]
    init_plats_codes = list(set(init_plats_codes))
    adjacent_1_plats_codes = list(set(adjacent_1_plats_codes))
    adjacent_2_plats_codes = list(set(adjacent_2_plats_codes))

    return adjacent_1, adjacent_2, init_plats_codes, adjacent_1_plats_codes, adjacent_2_plats_codes, initial_plats


def findPlatsSurroundingSectionsGiven(cursor2, all_plats_lst, plss_df_adjacent):
    def process_plat(plat, cursor):
        foo = sqlFindAllInSection(plat, cursor)
        return [list(j) for j in foo if str(j[0]) != 'None']



    plss_df_adjacent[['src_TOWNSH', 'nbr_TOWNSH', 'src_RANGE', 'nbr_RANGE', 'src_SECTIO', 'nbr_SECTIO']] = \
    plss_df_adjacent[['src_TOWNSH', 'nbr_TOWNSH', 'src_RANGE', 'nbr_RANGE', 'src_SECTIO', 'nbr_SECTIO']].astype(
        float).astype(int).astype(str)
    all_plats_dict = [
        {'src_SECTIO': i[0], 'src_TOWNSH': i[1], 'src_Town_1': i[2], 'src_RANGE': i[3], 'src_Range_': i[4],
         'src_Baseli': i[5]} for i in all_plats_lst]
    adjacent_1_plats, adjacent_2_plats, init_plats_codes, adjacent_1_plats_codes, adjacent_2_plats_codes, initial_plats = get_adjacent_polygons(
        all_plats_dict, plss_df_adjacent)

    init_plats_base = plss_df_adjacent[plss_df_adjacent['src_FRSTDI'].isin(init_plats_codes)]
    adjacent_1_plats_base = plss_df_adjacent[plss_df_adjacent['src_FRSTDI'].isin(adjacent_1_plats_codes)]
    adjacent_2_plats_base = plss_df_adjacent[plss_df_adjacent['src_FRSTDI'].isin(adjacent_2_plats_codes)]

    init_plats_base = init_plats_base['src_FRSTDI'].drop_duplicates(keep='first').reset_index()
    adjacent_1_plats_base = adjacent_1_plats_base['src_FRSTDI'].drop_duplicates(keep='first').reset_index()
    adjacent_2_plats_base = adjacent_2_plats_base['src_FRSTDI'].drop_duplicates(keep='first').reset_index()
    init_plats_base['Order'] = 0
    adjacent_1_plats_base['Order'] = 1
    adjacent_2_plats_base['Order'] = 2


    adjacent_lst = pd.concat([init_plats_base, adjacent_1_plats_base, adjacent_2_plats_base], ignore_index=True)

    adjacent_lst = adjacent_lst.drop('index', axis=1)

    adjacent_lst = pd.merge(adjacent_lst, plss_df_adjacent,
                            on=['src_FRSTDI'],
                            how='left')
    adjacent_lst = adjacent_lst[['src_FRSTDI', 'Order', 'src_FullCo']]
    all_codes = init_plats_codes + adjacent_1_plats_codes + adjacent_2_plats_codes
    all_codes = list(set(all_codes))

    plss_df_adjacent_to_write = plss_df_adjacent[plss_df_adjacent['src_FRSTDI'].isin(all_codes)]
    all_plats_lst = plss_df_adjacent_to_write['src_FullCo'].unique()
    new_df = plss_df_adjacent[plss_df_adjacent['src_FullCo'].isin(all_plats_lst)]
    all_plats_lst = new_df[
        ['src_SECTIO', 'src_TOWNSH', 'src_Town_1', 'src_RANGE', 'src_Range_', 'src_Baseli']].values.tolist()

    all_coords_lst = sqlFindAllInSectionAll(all_plats_lst, cursor2)
    all_apds = [int(float(i[0][:10])) for i in all_coords_lst]
    all_apds = list(set(all_apds))
    all_plats_lst = ma.removeDupesListOfLists(all_plats_lst)
    # for i, val in enumerate(all_plats_lst):
    #     val[0], val[1], val[3] = str(int(float(val[0]))), str(int(float(val[1]))), str(int(float(val[3])))
    #     val = [j.strip() for j in val]

    return all_apds, all_plats_lst, adjacent_lst


def graphPlats(df_plat, df_adjacent):
    adj1 = df_adjacent[df_adjacent['Order'] == 0]
    adj2 = df_adjacent[df_adjacent['Order'] == 1]
    adj3 = df_adjacent[df_adjacent['Order'] == 2]

    adj1_merge = df_plat[df_plat['Conc'].isin(adj1['src_FullCo'].unique())]
    adj2_merge = df_plat[df_plat['Conc'].isin(adj2['src_FullCo'].unique())]
    adj3_merge = df_plat[df_plat['Conc'].isin(adj3['src_FullCo'].unique())]

    # adj1_merg = pd.merge(adj1, df_plat, on=['src_FullCo', 'Conc'], how='left')
    plt.figure(figsize=(10, 6))  # Optional: Set the figure size
    for i in adj3_merge['Conc'].unique():
        data = adj3_merge[adj3_merge['Conc'] == i]
        plt.plot(data['Lon'], data['Lat'], c='red')

    for i in adj2_merge['Conc'].unique():
        data = adj2_merge[adj2_merge['Conc'] == i]
        plt.plot(data['Lon'], data['Lat'], c='blue')

    for i in adj1_merge['Conc'].unique():
        data = adj1_merge[adj1_merge['Conc'] == i]
        plt.plot(data['Lon'], data['Lat'], c='black')

    # plt.plot(adj1_merge['Lon'], adj1_merge['Lat'], c = 'black')
    # plt.plot(adj2_merge['Lon'], adj2_merge['Lat'], c = 'blue')
    # plt.plot(adj3_merge['Lon'], adj3_merge['Lat'], c = 'red')

    # Add labels and title
    plt.xlabel('X-axis label')
    plt.ylabel('Y-axis label')
    plt.title('Graph of Y vs X')

    # Optional: Add a grid
    plt.grid(True)

    # Display the plot
    plt.show()


def findPlatsSurrounding(cursor2, apds, plss_df_adjacent):
    time_start1 = time.perf_counter()
    data_done = dbTownshipAndRangeMany(cursor2, apds)

    all_plats_lst = data_done
    time_start2 = time.perf_counter()
    all_apds, all_plats_lst, adjacent_lst = findPlatsSurroundingSectionsGiven(cursor2, all_plats_lst, plss_df_adjacent)

    return all_apds, all_plats_lst, adjacent_lst


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
    string_sql = f"""select * from SectionDataCoordinates WHERE Township = {twsp} AND [Township Direction] = {twsp_dir} AND Range = {rng} AND [Range Direction] = {rng_dir} AND Baseline = {mer} and Section = {section}"""
    df = pd.read_sql(string_sql, conn, index_col='index')


def writeToDatabase(conn, cursor, df_info, df_dx, df_plat, df_prod, df_board_data, df_links_data, df_adjacent_lst, df_owner):
    # conn.execute('DROP TABLE IF EXISTS WellInfo')
    try:
        df_owner.to_sql('Owner', conn, index=False, if_exists='append')
    except ValueError:
        pass

    try:
        df_adjacent_lst.to_sql('Adjacent', conn, index=False, if_exists='append')
    except ValueError:
        pass
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

    ma.printLineBreak()
    string_sql = 'select * from Owner'
    df_foo = pd.read_sql(string_sql, conn)
    print('Owner', len(df_foo))

    # print("\n\nProd")
    string_sql = 'select * from Production'
    df_foo = pd.read_sql(string_sql, conn)
    print('Prod', len(df_foo))
    #
    # print("\n\nPlatData")
    # ma.printLineBreak()
    string_sql = 'select * from PlatData'
    df_foo = pd.read_sql(string_sql, conn)
    print('PlatData', len(df_foo))
    # print(df_foo)
    # print("\n\nWellInfo")
    # ma.printLineBreak()
    string_sql = 'select * from WellInfo'
    df_foo = pd.read_sql(string_sql, conn)
    print('WellInfo', len(df_foo))
    # print(df_foo['Board_Docket'].unique())
    # print(len(df_foo))
    # print("\n\nDX")
    # ma.printLineBreak()
    string_sql = 'select * from DX'
    df_foo = pd.read_sql(string_sql, conn)
    print('DX', len(df_foo))
    # print(len(df_foo))
    # print(len(df_board_data))
    # print('data written')
    string_sql = 'select * from BoardData'
    df_foo = pd.read_sql(string_sql, conn)
    print('Board', len(df_foo))

    string_sql = 'select * from BoardDataLinks'
    df_foo = pd.read_sql(string_sql, conn)
    print('BoardLinks', len(df_foo))

    string_sql = 'select * from Adjacent'
    df_foo = pd.read_sql(string_sql, conn)
    print('Adjacent', len(df_foo))


def writeToDB(df, cursor, conn, table_name):
    info_data = df.to_numpy().tolist()
    headers = df.columns.tolist()
    headers_strings = ["'" + str(i) + "'" for i in headers]
    headers_lst = ', '.join(headers_strings)
    insert_str = f'''INSERT INTO {table_name}(''' + headers_lst + ")"

    lst = ["?"] * df.shape[1]
    lst = ', '.join([f"{str(elem)}" for elem in lst])
    values_str = 'VALUES(' + lst + ");"
    for i in info_data:
        data_str = i
        data_str = [str(i) for i in data_str]
        query = insert_str + values_str
        cursor.execute(query, data_str)
        conn.commit()



def findCumProd(apis, cursor):
    query = f"""SELECT w.WellID, prodtype, SUM(PRODQUANTITY), ProdUnits
        FROM well w
        JOIN construct c on w.pkey = c.wellkey
        JOIN ProdFacilityProduction on c.PKey = ProdFacilityProduction.ConstructKey
        WHERE w.WellID IN ({apis}) and 
        ((cumulative is not null and reportdate = '1/1/1984')
        or Cumulative is null)
        GROUP BY w.WellID, prodtype, ProdUnits"""
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchall()


def retrieveConstructDataAll(cursor, well_id, apds_original):
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
			e.entityname as 'Operator',
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
			left join entity e on w.operator = e.pkey
        WHERE
            (wh.WorkType IN ('drill', 'reenter', 'deepen', 'reperf', 'recomp', 'convert', 'plug'))
            AND w.WellID IN ({apis}) and wh.WorkType != 'REPERF' ---and wh.ReportStatus NOT IN ('LA', 'RET', 'APD', 'DRL')
        """
    cursor.execute(sql_query)
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    ref_codes = fetch_ref_codes(cursor)
    new_lst = []
    api_lst = [i[0] for i in result]
    extension_lst = [i[2] for i in result]

    returned_data = get_api_depths(cursor, api_lst, extension_lst)
    # returned_data = findDepthsIfInitFailedMass(cursor, api_lst, extension_lst)
    for i in range(len(result)):
        if result[i][13] not in ['Location Abandoned - APD rescinded', 'Returned APD (Unapproved)',
                                 'Location Abandoned - APD rescinded']:
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

    result = new_lst
    result = sorted(result, key=lambda r: r[0])
    result = ma.removeDupesListOfLists(result)
    result = [list(i) for i in result]
    data1 = []

    for row in result:
        row_dict = {}
        for col_name, value in zip(columns, row):
            if isinstance(value, str):
                row_dict[col_name] = value.strip()
            else:
                row_dict[col_name] = value
        data1.append(row_dict)

    test_df = pd.DataFrame(data=data1, columns=columns)
    columns_to_map = ['CurrentWellStatus', 'CurrentWellType', 'WellStatusReport', 'WellTypeReport']

    for col in columns_to_map:
        if col in ['CurrentWellStatus', 'WellStatusReport']:
            test_df[col] = test_df[col].replace(ref_codes['WELLSTATUS'])
        elif col in ['CurrentWellType', 'WellTypeReport']:
            test_df[col] = test_df[col].replace(ref_codes['WELLTYPE'])




    return test_df, columns
    # return list(result), columns

def sqlFindSHLBHL(cursor, api_lst, connection, missing_df):
    # Function to select row based on priority
    def select_row(group):
        valid_rows = group[group['Proposed_Depth_TVD'].notna() &
                           group['Proposed_Depth_MD'].notna() &
                           (group['Proposed_Depth_TVD'] != '') &
                           (group['Proposed_Depth_TVD'] != 'Null') &
                           (group['Proposed_Depth_MD'] != '') &
                           (group['Proposed_Depth_MD'] != 'Null')]

        if not valid_rows.empty:
            return valid_rows.iloc[0]
        else:
            return group.loc[group['nan_count'].idxmin()]

    def sortFilter(df):
        df_sorted = df.sort_values(['APDNO', 'Zone_Name'])
        df_sorted['nan_count'] = df_sorted.isnull().sum(axis=1) + \
                                df_sorted.applymap(lambda x: str(x).strip() if isinstance(x, str) else x).isin(
                                    ['', 'Null']).sum(axis=1)

        df_result = df_sorted.groupby('Zone_Name', as_index=False).apply(select_row, include_groups=False).reset_index(
            drop=True)

        return df_result

    new_dataframe = []
    api_lst = [i + "0000" for i in api_lst]
    api_lst = [str(i) for i in api_lst]
    apis = ', '.join([f"'{str(elem)}'" for elem in api_lst])
    query = f"""select * from tblAPDLoc tb where tb.API IN ({apis}) and tb.Zone_Name in ('Surface Location', 'Proposed Depth')"""
    data_frame = pd.read_sql(query, connection)
    data_frame_grouped = data_frame.groupby('API')


    for val, group in data_frame_grouped:
        group = group.drop_duplicates(keep='first')

        group = sortFilter(group)

        api_val = group['API'].iloc[0][:10]
        spec_df = missing_df[missing_df['WellID'] == api_val]
        well_name = spec_df['WellName'].iloc[0]
        shl_location = [group['Wh_X'].iloc[0], group['Wh_Y'].iloc[0]]
        try:
            md, tvd = spec_df['MD'].dropna().iloc[0], spec_df['TVD'].dropna().iloc[0]
            if len(group) == 2:
                if len(group['Wh_FtNS'].unique()) == 1 and len(group['Wh_FtEW'].unique()) == 1:
                    bhl_location = shl_location
                    citing_type = 'Vertical'

                elif group['Bh_X'].isna().all():
                    bhl_location = shl_location
                    citing_type = 'Vertical'
                else:
                    bhl_location = [group['Bh_X'].iloc[0], group['Bh_Y'].iloc[0]]
                    citing_type = 'Planned'
            else:
                print(group)
            shl_data = [api_val, well_name, 0, 0, 0, 0, shl_location[0], shl_location[1], citing_type]
            bhl_data = [api_val, well_name, md, 0, 0, tvd, bhl_location[0], bhl_location[1], citing_type]
            new_dataframe.append(shl_data)
            new_dataframe.append(bhl_data)
        except IndexError:
            shl_data = [api_val, well_name, 0, 0, 0, 0, shl_location[0], shl_location[1], 'Vertical']
            new_dataframe.append(shl_data)


    columns = ['APINumber', 'WellNameNumber', 'MeasuredDepth', 'Inclination',
               'Azimuth', 'TrueVerticalDepth', 'X', 'Y', 'CitingType']
    dict_data = [{'APINumber':i[0], 'WellNameNumber':i[1], 'MeasuredDepth':i[2], 'Inclination':i[3],
               'Azimuth':i[4], 'TrueVerticalDepth':i[5], 'X':i[6], 'Y':i[7], 'CitingType':i[8]} for i in new_dataframe]
    new_df = pd.DataFrame(columns=columns, data=dict_data)
    return new_df


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
            line = list(
                cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
            if line:
                if len(line) > 1:
                    return [line[1][0], line[0][0]]
    return []


def get_api_depths(cursor, apis, extensions):
    api_depths = {api: [None, None] for api in apis}

    # Prepare all APIs at once
    apis_with_extensions = {f"{api}000{int(float(ext))}" for api, ext in zip(apis, extensions)}
    all_apis = set(apis).union(apis_with_extensions)
    all_apis_str = ', '.join(map(repr, all_apis))

    # Combined query
    query = f"""
    SELECT 
        COALESCE(t1.API, t2.APINumber, t3.WellID) AS API,
        t1.Proposed_Depth_TVD,
        t1.Proposed_Depth_MD,
        t2.TrueVerticalDepth,
        t2.MeasuredDepth,
        t3.DepthBottom,
        t3.ElevationType
    FROM 
        (SELECT API, Proposed_Depth_TVD, Proposed_Depth_MD 
         FROM tblAPDLoc 
         WHERE API IN ({all_apis_str}) AND Zone_Name = 'Proposed Depth') t1
    FULL OUTER JOIN 
        (SELECT APINumber, TrueVerticalDepth, MeasuredDepth 
         FROM [dbo].[DirectionalSurveyHeader] dsh
         JOIN [dbo].[DirectionalSurveyData] dsd ON dsd.DirectionalSurveyHeaderKey = dsh.PKey
         WHERE APINumber IN ({all_apis_str}) AND CitingType = 'Planned') t2
    ON t1.API = t2.APINumber
    FULL OUTER JOIN 
        (SELECT WellID, DepthBottom, ElevationType
         FROM Well w
         LEFT JOIN Construct c ON c.WellKey = w.PKey 
         LEFT JOIN loc l ON l.ConstructKey = c.pkey
         WHERE WellID IN ({all_apis_str}) AND ElevationType IN ('TVD', 'DTD')) t3
    ON COALESCE(t1.API, t2.APINumber) = t3.WellID
    """

    for row in cursor.execute(query):
        api = row[0][:10]  # Ensure we're using the first 10 characters of the API
        if api in api_depths:
            # First query equivalent
            if row[1] is not None and row[2] is not None:
                api_depths[api] = [row[1], row[2]]

            # Second query equivalent
            elif api_depths[api][0] is None and row[3] is not None and row[4] is not None:
                api_depths[api] = [float(row[3]), float(row[4])]

            # Third query equivalent
            elif api_depths[api][0] is None and row[5] is not None:
                if row[6] == 'TVD':
                    api_depths[api][0] = row[5]
                elif row[6] == 'DTD':
                    api_depths[api][1] = row[5]
    print(1, api_depths)

    return api_depths

    return api_depths
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
    print(2, api_depths)

    return api_depths





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

def dbSurfaceLocDrilledAll(api, conn):
    apis = [str(i) for i in api]
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    selectCommand = 'select WellID, LocType, X, Y, DepthBottom, ElevationType'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey'
    whereCommand = f""" WHERE WellID IN ({apis}) and (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD'))"""
    orderCommand = ' '
    df_foo = pd.read_sql(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand, conn)
    return df_foo


def dbSurfaceLocDrilled3(conn, df):
    # Convert the DataFrame to a list of API numbers
    api_list = df[0].tolist()

    # Construct the SQL query
    api_string = "', '".join(api_list)
    selectCommand = 'select WellID,WellName, LocType, X, Y, DepthBottom, ElevationType'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey'
    whereCommand = f""" WHERE WellID IN ('{api_string}') and (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD'))"""
    orderCommand = ' ORDER BY WellID'
    # Execute the query and get the results as a DataFrame
    df_foo = pd.read_sql(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand, conn)
    # print(df_foo)
    # Group by WellID
    grouped = df_foo.groupby('WellID')

    results = []
    for api, group in grouped:
        tvd, md = -1, -2
        df_foo_vals = group['ElevationType'].unique()
        if 'DTD' not in df_foo_vals or 'TVD' not in df_foo_vals:
            data_line = df.loc[df[0] == api].iloc[0]
            if pd.notna(data_line[24]) and pd.notna(data_line[25]):
                md, tvd = data_line[25], data_line[24]
        else:
            md = group.loc[group['ElevationType'] == 'DTD', 'DepthBottom'].values[0]
            try:
                tvd = group.loc[group['ElevationType'] == 'TVD', 'DepthBottom'].values[0]
            except IndexError:
                tvd = group.loc[group['ElevationType'] == 'DTD', 'DepthBottom'].values[0]

        surf_loc = group.loc[group['LocType'] == 'SURF', ['X', 'Y']].values[0].tolist()
        try:
            bh_loc = group.loc[group['LocType'] == 'BH', ['X', 'Y']].values[0].tolist()
        except IndexError:
            bh_loc = group.loc[group['LocType'] == 'SURF', ['X', 'Y']].values[0].tolist()

        if tvd == -1:
            if ma.equationDistance(surf_loc[0], surf_loc[1], bh_loc[0], bh_loc[1]) < 10:
                data_line = df.loc[df[0] == api].iloc[0]
                md = data_line[25] if pd.notna(data_line[25]) else 0.0
                tvd = md

        # Replace nan with 0.0


        if 'nan' in [str(i) for i in bh_loc]:
            bh_loc = surf_loc

        point1 = surf_loc + [0]
        point2 = bh_loc + [tvd]

        surf_latlon = utm.to_latlon(surf_loc[0], surf_loc[1], 12, 'T')
        bh_latlon = utm.to_latlon(bh_loc[0], bh_loc[1], 12, 'T')
        fwd_azimuth, back_azimuth, distance = Geod(ellps='WGS84').inv(surf_latlon[1], surf_latlon[0], bh_latlon[1],
                                                                      bh_latlon[0])

        if point1 == point2:
            results.extend([
                [api, group['WellName'].iloc[0], '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'],
                [api, group['WellName'].iloc[0], '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']
            ])
        elif point1 != point2:
            if point1[2] is None:
                results.extend([
                    [api, group['WellName'].iloc[0], '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'],
                    [api, group['WellName'].iloc[0], '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']
                ])
            elif point2[2] is None:
                results.extend([
                    [api, group['WellName'].iloc[0], '0', '0', '0', '0', bh_loc[0], bh_loc[1], 'Vertical'],
                    [api, group['WellName'].iloc[0], '0', '0', '0', '0', bh_loc[0], bh_loc[1], 'Vertical']
                ])
            else:
                inclination, azimuth = ma.xyzEquationIncAzi(point1, point2)
                results.extend([
                    [api, group['WellName'].iloc[0], '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'],
                    [api, group['WellName'].iloc[0], md, round(inclination, 3), round(fwd_azimuth, 3), tvd, bh_loc[0], bh_loc[1], 'Vertical']
                ])

    return pd.DataFrame(results, columns=['API', 'Lease', 'MD', 'Inclination', 'Azimuth', 'TVD', 'X', 'Y', 'Type'])

def dbSurfaceLocDrilled(conn, data_line):
    api = data_line[0]
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
    try:
        bh_loc = df_foo.loc[df_foo['LocType'] == 'BH', ['X', 'Y']].values[0].tolist()
    except IndexError:
        bh_loc = df_foo.loc[df_foo['LocType'] == 'SURF', ['X', 'Y']].values[0].tolist()
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
    fwd_azimuth, back_azimuth, distance = Geod(ellps='WGS84').inv(surf_latlon[1], surf_latlon[0], bh_latlon[1],
                                                                  bh_latlon[0])
    if point1 == point2:
        return [["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'],
                ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']]
    elif point1 != point2:
        if point1[2] is None:
            return [["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical'],
                    ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']]
        elif point2[2] is None:
            return [["", "", '0', '0', '0', '0', bh_loc[0], bh_loc[1], 'Vertical'],
                    ["", "", '0', '0', '0', '0', bh_loc[0], bh_loc[1], 'Vertical']]
        else:
            pass
    inclination, azimuth = ma.xyzEquationIncAzi(point1, point2)
    dx_asDrilled1 = ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']
    dx_asDrilled2 = ["", "", md, round(inclination, 3), round(fwd_azimuth, 3), tvd, bh_loc[0], bh_loc[1], 'Vertical']
    drilled = [dx_asDrilled1, dx_asDrilled2]

    return drilled


def dbSurfaceLocDrilled2(cursor, api, conn, data_line):
    select_command = '''
    SELECT LocType, X, Y, DepthBottom, ElevationType
    FROM Well w
    LEFT JOIN Construct c ON c.WellKey = w.PKey
    LEFT JOIN loc l ON l.ConstructKey = c.pkey
    WHERE WellID = ? AND (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD'))
    '''

    df_foo = pd.read_sql(select_command, conn, params=(api,))

    df_foo_vals = set(df_foo['ElevationType'].dropna())

    if 'DTD' not in df_foo_vals or 'TVD' not in df_foo_vals:
        md, tvd = data_line[25], data_line[24]
    else:
        md = df_foo.loc[df_foo['ElevationType'] == 'DTD', 'DepthBottom'].iloc[0]
        tvd = df_foo.loc[df_foo['ElevationType'] == 'TVD', 'DepthBottom'].iloc[0] if 'TVD' in df_foo_vals else md

    surf_loc = df_foo.loc[df_foo['LocType'] == 'SURF', ['X', 'Y']].iloc[0].tolist()
    bh_loc = df_foo.loc[df_foo['LocType'] == 'BH', ['X', 'Y']].iloc[0].tolist() if 'BH' in df_foo[
        'LocType'].values else surf_loc

    if pd.isna(tvd):
        if math.dist(surf_loc, bh_loc) < 10:
            md = data_line[25]
            tvd = md

    if any(pd.isna(coord) for coord in bh_loc):
        bh_loc = surf_loc

    point1 = surf_loc + [0]
    point2 = bh_loc + [tvd]

    surf_latlon = utm.to_latlon(surf_loc[0], surf_loc[1], 12, 'T')
    bh_latlon = utm.to_latlon(bh_loc[0], bh_loc[1], 12, 'T')
    fwd_azimuth, _, _ = Geod(ellps='WGS84').inv(surf_latlon[1], surf_latlon[0], bh_latlon[1], bh_latlon[0])

    if point1 == point2 or any(coord is None for coord in point1 + point2):
        return [["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']] * 2

    inclination, azimuth = xyzEquationIncAzi(point1, point2)

    dx_asDrilled1 = ["", "", '0', '0', '0', '0', surf_loc[0], surf_loc[1], 'Vertical']
    dx_asDrilled2 = ["", "", md, round(inclination, 3), round(fwd_azimuth, 3), tvd, bh_loc[0], bh_loc[1], 'Vertical']

    return [dx_asDrilled1, dx_asDrilled2]


def xyzEquationIncAzi(point1, point2):
    dx, dy, dz = [p2 - p1 for p1, p2 in zip(point1, point2)]
    horizontal_distance = math.hypot(dx, dy)
    inclination = abs(90 - math.degrees(math.atan2(dz, horizontal_distance)))
    azimuth = (math.degrees(math.atan2(dy, dx)) + 360) % 360
    return inclination, azimuth


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
        line = list(
            cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()[0])
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
            line2 = \
                list(
                    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())[
                    0]
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

    # result = {}
    # for api in api_lst:
    #     result[api] = [None] * 8
    result = {api: [None] * 8 for api in api_lst}
    # Query 1: Retrieve data from Well, Construct, loc, and LocExt tables
    selectCommand = 'select w.WellID, GRELEV, Sec, Township, TownshipDir, Range, RangeDir, PM'
    fromCommand = ' FROM Well w'
    joinCommand = ' left join Construct c ON c.WellKey = w.PKey left join loc l ON l.ConstructKey = c.pkey left join [LocExt] le ON le.lockey = l.Pkey'
    whereCommand = f""" WHERE WellID in ({apis}) and (ElevationType IS NULL OR ElevationType NOT IN('PBMD', 'PBTVD')) and LocType = 'SURF'"""
    orderCommand = ' '
    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand)
    rows = cursor.fetchall()
    # for row in rows:
    #     result[row[0]] = list(row)
    result.update({row[0]: list(row) for row in rows})
    # print(result)
    # Query 2: Retrieve Elevation from tblAPDLoc table
    selectCommand = 'select LEFT(al.API, 10), Elevation'
    fromCommand = ' from [dbo].[tblAPDLoc] al '
    joinCommand = ' join [dbo].[tblAPD] dsd on dsd.API_WellNo = al.API join Well w on LEFT(al.API, 10) = w.WellID '
    whereCommand = f""" where al.API in ({apis_extensions}) and Zone_Name = 'Surface Location'"""
    cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand)
    rows = cursor.fetchall()
    # for row in rows:
    #     if result[row[0]][1] is None:
    #         result[row[0]][1] = row[1]
    result.update({row[0]: [result[row[0]][0]] + [row[1] if result[row[0]][1] is None else result[row[0]][1]] + result[row[0]][2:] for row in rows if row[0] in result})
    # Query 3: Retrieve SurveySurfaceElevation from DirectionalSurveyHeader table
    selectCommand = 'select APINumber, SurveySurfaceElevation'
    fromCommand = ' from [dbo].[DirectionalSurveyHeader]'
    whereCommand = f' where APINumber in ({apis})'
    cursor.execute(selectCommand + fromCommand + whereCommand)
    rows = cursor.fetchall()
    # for row in rows:
    #     if result[row[0]][1] is None:
    #         result[row[0]][1] = row[1]
    result.update({row[0]: [result[row[0]][0]] + [row[1] if result[row[0]][1] is None else result[row[0]][1]] + result[row[0]][2:] for row in rows if row[0] in result})
    print(result)
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
    apis_strings = [str(i) + "0000" for i in api]
    apis_strings = list(dict.fromkeys(apis_strings))
    apis = ', '.join([f"'{str(elem)}'" for elem in apis_strings])

    query = f"""select [Wh_Sec], [Wh_Twpn] , [Wh_Twpd], [Wh_RngN], [Wh_RngD], [Wh_Pm]
    from [dbo].[tblAPDLoc] where API in ({apis})"""
    line = list(cursor.execute(query).fetchall())
    line = [tuple(row) for row in line]

    # Use OrderedDict to remove duplicates while preserving order
    unique_rows = list(OrderedDict.fromkeys(line))

    # output = pd.read_sql_query(query, engine_local)
    # output = output.drop_duplicates(keep="first").reset_index(drop=True)
    #
    #
    # apis = [str(i) for i in api]
    # apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    # selectCommand = 'select Wh_Sec, Wh_Twpn , Wh_Twpd, Wh_RngN, Wh_RngD, Wh_Pm'
    # fromCommand = ' from Well w'
    # joinCommand = ' inner join [dbo].[tblAPD] dsd on LEFT(dsd.API_WellNo, 10) = w.WellID inner join [dbo].[tblAPDLoc] al on al.APDNO = dsd.APDNo'
    # whereCommand = f""" where w.WellID in ({apis})"""
    # orderCommand = ' '
    # line = list(cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall())
    return unique_rows


def sqlProdData(cursor, api):
    def sqlPivtor(df):
        # Assuming your dataframe is called 'df'
        df_reshaped = df.pivot(index='API', columns='Type', values='Volume')

        # Rename the columns
        df_reshaped.columns.name = None
        df_reshaped = df_reshaped.rename(columns={'OIL': 'OilVolume', 'GAS': 'GasVolume'})

        # Reset the index to make 'API' a column again
        df_reshaped = df_reshaped.reset_index()

        # If you want to rename 'API' to 'ID'
        df_reshaped = df_reshaped.rename(columns={'API': 'ID'})

        # If you want to ensure a specific column order
        df_reshaped = df_reshaped[['ID', 'OilVolume', 'GasVolume']]
        return df_reshaped

    apis = [str(i) for i in api]
    apis = list(set(apis))
    apis = ', '.join([f"'{str(elem)}'" for elem in apis])
    # findCumProd(apis, cursor)
    query = f"""SELECT SUM(PRODQUANTITY) as 'Volume', prodtype, w.WellID
        FROM well w
        JOIN construct c on w.pkey = c.wellkey
        JOIN ProdFacilityProduction on c.PKey = ProdFacilityProduction.ConstructKey
        WHERE w.WellID IN ({apis})  and ProdType != 'WATER' and 
        ((cumulative is not null and reportdate = '1/1/1984')
        or Cumulative is null)
        GROUP BY w.WellID, prodtype, ProdUnits"""
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    # for i in range(len(result)):
    #     result[i][2] = int(float(result[i][2]))
    # lst2 = sorted(result, key=lambda x: x[2])
    selectCommand = f"""SELECT SUM(CAST(prodquantity AS FLOAT)) AS 'Volume', ProdType, w.WellID"""
    fromCommand = ' FROM Well w '
    joinCommand = ' JOIN Construct c on w.PKey = c.WellKey JOIN ProdFacilityProduction pfp on c.PKey = pfp.ConstructKey     '
    whereCommand = f""" WHERE  w.WellID IN ({apis}) and ProdType != 'WATER'"""
    orderCommand = ' GROUP BY w.WellID, ProdType, ProdUnits'
    line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()
    # for i in range(len(line)):
    #     line[i][2] = int(float(line[i][2]))
    # lst = sorted(line, key=lambda x: x[2])
    columns = ['Volume', 'Type', 'API']

    all_apis = [str(i[2]) for i in line]
    edited_lst = []
    for i in api:
        if str(i) not in all_apis:
            edited_lst.append([None, 'OIL', str(i)])
            edited_lst.append([None, 'GAS', str(i)])
    tot_lst = line + edited_lst
    tot_lst = [list(i) for i in tot_lst]
    data = [{'Volume': i[0], 'Type': i[1], 'API': i[2]} for i in tot_lst]
    df = pd.DataFrame(data=data, columns=columns)
    df = sqlPivtor(df)

    grouped_data = defaultdict(list)
    for item in tot_lst:
        grouped_data[item[2]].append(item[0])  # Append only the first element of each tuple

    # data = [values for key, values in grouped_data.items()]

    try:
        # return data
        # return grouped_data
        return df
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


def sqlGetDFData():
    name = 'Board_DB_Plss.db'
    path_db = r'C:\Work\BoardInfo'
    apd_data_dir = os.path.join(path_db, name)
    conn = sqlite3.connect(apd_data_dir)
    cursor = conn.cursor()
    # plss_df_adjacent = pd.read_sql('SELECT * FROM Adjacent', conn)
    plss_df_values = pd.read_sql('SELECT * FROM BaseData', conn)
    plss_df = pd.read_sql('SELECT * FROM PLSS1', conn)
    # plss_df_values = plss_df_values[plss_df_values['FRSTDIVID'] == 'UT300040S0100W0SN310']
    # plt.figure(figsize=(10, 6))  # Optional: Set the figure size
    # plt.scatter(plss_df_values['X'], plss_df_values['Y'])
    #
    # # Add labels and title
    # plt.xlabel('X-axis label')
    # plt.ylabel('Y-axis label')
    # plt.title('Graph of Y vs X')
    #
    # # Optional: Add a grid
    # plt.grid(True)
    #
    # # Display the plot
    # plt.show()


def sqlConnectPlats():
    sqlGetDFData()
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
    query = f"""
    SELECT ap.API_WellNo, al.APDNO, ap.Slant, Wh_X, Wh_Y
    FROM [dbo].[tblAPDLoc] al
    INNER JOIN [dbo].[tblAPD] ap ON ap.APDNo = al.APDNO
    WHERE [Wh_Twpn] = ? AND [Wh_Twpd] = ? AND [Wh_RngN] = ? 
    AND [Wh_RngD] = ? AND [Wh_Pm] = ? AND Wh_Sec = ?
    """
    params = (twsp, twsp_dir, rng, rng_dir, mer, section)
    cursor.execute(query, params)
    return cursor.fetchall()


# def sqlFindAllInSection(data, cursor):
#     section, twsp, twsp_dir, rng, rng_dir, mer = data
#     selectCommand = 'select ap.API_WellNo, al.APDNO, ap.Slant, Wh_X, Wh_Y'
#     fromCommand = ' from [dbo].[tblAPDLoc] al'
#     joinCommand = ' inner join [dbo].[tblAPD] ap on ap.APDNo = al.APDNO '
#     whereCommand = f"""    WHERE [Wh_Twpn] = '{twsp}' AND [Wh_Twpd] = '{twsp_dir}' AND [Wh_RngN] = '{rng}' AND [Wh_RngD] = '{rng_dir}' AND [Wh_Pm] = '{mer}' and Wh_Sec = '{section}'"""
#     orderCommand = ' '
#     line = cursor.execute(selectCommand + fromCommand + joinCommand + whereCommand + orderCommand).fetchall()
#     return line


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
    orderCommand = '''order by di.CauseNumber, da.PM, rc.CountyName, da.Range, da.RangeDir, da.Township, 
    da.TownshipDir, ds.Sec, ds.QuarterQuarter'''

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
    prod_line = cursor.execute(
        selectCommand + fromCommand + joinCommand + whereCommand + orderCommand + " HAVING SUM(CAST(prodquantity AS FLOAT)) > 0").fetchall()
    prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i
                 in prod_line]

    return prod_line


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

    df = df[df['Cumulative'] != 'True']
    df = df.drop('Cumulative', axis=1)

    return df


def formatSecondProd2(df, api):
    new_df = df[df['WellID'] == str(api)]
    if api == '4301330574':
        pass

    prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i
                 in new_df.values]
    return prod_line
def formatSecondProd(grouped, api):
    if api == '4301330574':
        pass
    try:
        new_df = grouped.get_group(str(api))
        return new_df[['WellID', 'Year', 'Month', 'Volume', 'ProdType', 'WellName']].to_dict('records')
    except KeyError:
        return []  # or handle the case when the API is not found


def formatSecondProdAll(df, apis):
    new_df = df[df['WellID'].isin([str(i) for i in apis])]

    prod_line = [{'WellID': i[0], 'Year': i[1], 'Month': i[2], 'Volume': i[3], 'ProdType': i[4], 'WellName': i[5]} for i
                 in new_df.values]
    return prod_line


def determineAdjacentVals(data):
    # section, township, township_dir, range_val, range_dir, meridian = int(data[:2]), int(data[2:4]), data[4], int(data[5:7]), data[7], data[8]

    section, township, township_dir, range_val, range_dir, meridian = int(data[:2]), int(data[2:4]), data[4], int(
        data[5:7]), data[7], data[8]

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
        section, township, township_dir, range_val, range_dir, meridian = str(i[0]), str(i[1]), i[2], str(i[3]), i[4], \
            i[5]
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
    df_tot = pd.read_csv(r'C:\Work\RewriteAPD\ProdData.csv', encoding="ISO-8859-1")
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


def sqlProductionDFGenerate(all_data_apis, cursor, conn, df_many, all_df):
    df_all = pd.DataFrame(columns=['WellID', 'Year', 'Month', 'Oil Volume (bbl)', 'WellName', 'Date',
                                   'Oil Price (bbl)', 'Potential Oil Profit',
                                   'Cumulative Potential Oil Production (bbl)',
                                   'Potential Cumulative Oil Profit', 'Gas Volume (mcf)',
                                   'Gas Price (mcf)', 'Potential Gas Profit',
                                   'Potential Cumulative Gas Profit',
                                   'Cumulative Potential Gas Production (mcf)'])

    # all_df = processAndReturnMonthlyPrices()

    grouped = df_many.groupby('WellID')
    for i in all_data_apis:
        # prod_output = formatSecondProd(df_many, i)
        prod_output = formatSecondProd(grouped, i)
        if prod_output:
            # temp_prod_df = pd.DataFrame(prod_output,
            #                             columns=['WellID', 'Year', 'Month', 'Volume', 'ProdType', 'WellName'])
            # temp_prod_df['Year'] = temp_prod_df['Year'].astype(int).astype(str)
            # temp_prod_df['Month'] = temp_prod_df['Month'].astype(int).astype(str).str.zfill(2)
            # temp_prod_df['Date'] = temp_prod_df['Year'].astype(int).astype(str) + '-' + temp_prod_df['Month'].astype(
            #     str)
            # merged_df = pd.merge(temp_prod_df, all_df, on=['Date', 'ProdType'], how='left')
            # merged_df['Profit'] = merged_df.apply(lambda x: x['Volume'] * x['Cost'], axis=1)
            # merged_df['Profit'] = merged_df['Profit'].astype(float)
            # df_summed = merged_df.groupby('Date')['Profit'].sum().reset_index()
            # df_summed['Cumulative Profit'] = df_summed['Profit'].cumsum()
            # df_summed['Cumulative Profit'] = df_summed['Cumulative Profit'].astype(float)
            # df_summed['Profit'] = df_summed['Profit'].astype(float)
            # merged_df_gas = merged_df[(merged_df['ProdType'] == 'GAS')]
            # merged_df_gas['Cumulative Production'] = merged_df_gas['Volume'].cumsum()
            # df_summed_gas = merged_df_gas.groupby('Date')['Profit'].sum().reset_index()
            # df_summed_gas['Cumulative Profit'] = df_summed['Profit'].cumsum()
            # merged_df_oil = merged_df[(merged_df['ProdType'] == 'OIL')]
            # merged_df_oil['Cumulative Production'] = merged_df_oil['Volume'].cumsum()
            # df_summed_oil = merged_df_oil.groupby('Date')['Profit'].sum().reset_index()
            # df_summed_oil['Cumulative Profit'] = df_summed['Profit'].cumsum()
            # df_summed_oil_new, merged_df_oil_new, df_summed_gas_new, merged_df_gas_new = copy.deepcopy(
            #     df_summed_oil), copy.deepcopy(merged_df_oil), copy.deepcopy(df_summed_gas), copy.deepcopy(
            #     merged_df_gas)
            # merged_df_oil_new['Potential Cumulative Oil Profit'] = merged_df_oil_new['Profit'].cumsum()
            # merged_df_gas_new['Potential Cumulative Gas Profit'] = merged_df_gas_new['Profit'].cumsum()
            # merged_df_oil_new = merged_df_oil_new.rename(
            #     columns={'Volume': 'Oil Volume (bbl)', 'Cost': 'Oil Price (bbl)', 'Profit': 'Potential Oil Profit',
            #              'Cumulative Production': 'Cumulative Potential Oil Production (bbl)'})
            # merged_df_oil_new = merged_df_oil_new.drop('ProdType', axis=1)
            # merged_df_gas_new = merged_df_gas_new.rename(
            #     columns={'Volume': 'Gas Volume (mcf)', 'Cost': 'Gas Price (mcf)', 'Profit': 'Potential Gas Profit',
            #              'Cumulative Production': 'Cumulative Potential Gas Production (mcf)'})
            # merged_df_gas_new_cut = merged_df_gas_new[
            #     ['Date', 'Gas Volume (mcf)', 'Gas Price (mcf)', 'Potential Gas Profit',
            #      'Potential Cumulative Gas Profit', 'Cumulative Potential Gas Production (mcf)']]
            # merged_df = pd.merge(merged_df_oil_new, merged_df_gas_new_cut, on='Date')
            # df_all = pd.concat([df_all, merged_df], ignore_index=True)  # Avoid index duplication
            # Create temp_prod_df with formatted Year, Month, and Date
            temp_prod_df = pd.DataFrame(prod_output, columns=[
                'WellID', 'Year', 'Month', 'Volume', 'ProdType', 'WellName'
            ]).assign(
                Year=lambda df: df['Year'].astype(int).astype(str),
                Month=lambda df: df['Month'].astype(int).astype(str).str.zfill(2),
                Date=lambda df: df['Year'] + '-' + df['Month']
            )

            # Merge with all_df and calculate Profit
            merged_df = pd.merge(temp_prod_df, all_df, on=['Date', 'ProdType'], how='left').assign(
                Profit=lambda df: (df['Volume'] * df['Cost']).astype(float)
            )

            # Group by Date to get summed Profit and calculate Cumulative Profit
            df_summed = merged_df.groupby('Date', as_index=False)['Profit'].sum().assign(
                Cumulative_Profit=lambda df: df['Profit'].cumsum().astype(float)
            )

            # Process GAS production
            merged_df_gas = merged_df[merged_df['ProdType'] == 'GAS'].assign(
                Cumulative_Production=lambda df: df['Volume'].cumsum()
            )
            df_summed_gas = merged_df_gas.groupby('Date', as_index=False)['Profit'].sum().assign(
                Cumulative_Profit=lambda df: df_summed['Profit'].cumsum()
            )

            # Process OIL production
            merged_df_oil = merged_df[merged_df['ProdType'] == 'OIL'].assign(
                Cumulative_Production=lambda df: df['Volume'].cumsum()
            )
            df_summed_oil = merged_df_oil.groupby('Date', as_index=False)['Profit'].sum().assign(
                Cumulative_Profit=lambda df: df_summed['Profit'].cumsum()
            )

            # Deep copy DataFrames to preserve original data
            df_summed_oil_new, merged_df_oil_new, df_summed_gas_new, merged_df_gas_new = (
                copy.deepcopy(df_summed_oil),
                copy.deepcopy(merged_df_oil),
                copy.deepcopy(df_summed_gas),
                copy.deepcopy(merged_df_gas)
            )

            # Calculate Potential Cumulative Profits
            merged_df_oil_new['Potential Cumulative Oil Profit'] = merged_df_oil_new['Profit'].cumsum()
            merged_df_gas_new['Potential Cumulative Gas Profit'] = merged_df_gas_new['Profit'].cumsum()

            # Rename columns for OIL
            merged_df_oil_new = merged_df_oil_new.rename(columns={
                'Volume': 'Oil Volume (bbl)',
                'Cost': 'Oil Price (bbl)',
                'Profit': 'Potential Oil Profit',
                'Cumulative_Production': 'Cumulative Potential Oil Production (bbl)'
            }).drop('ProdType', axis=1)

            # Rename columns for GAS
            merged_df_gas_new = merged_df_gas_new.rename(columns={
                'Volume': 'Gas Volume (mcf)',
                'Cost': 'Gas Price (mcf)',
                'Profit': 'Potential Gas Profit',
                'Cumulative_Production': 'Cumulative Potential Gas Production (mcf)'
            })

            # Select and reorder GAS columns
            merged_df_gas_new_cut = merged_df_gas_new[[
                'Date', 'Gas Volume (mcf)', 'Gas Price (mcf)', 'Potential Gas Profit',
                'Potential Cumulative Gas Profit', 'Cumulative Potential Gas Production (mcf)'
            ]]

            # Merge OIL and GAS DataFrames on Date
            merged_df_final = pd.merge(merged_df_oil_new, merged_df_gas_new_cut, on='Date')

            # Concatenate the final merged DataFrame to df_all
            df_all = pd.concat([df_all, merged_df_final], ignore_index=True)


    # # Convert dataframes to sets of tuples
    # set1 = set(df_all.itertuples(index=False, name=None))
    # set2 = set(df_all2.itertuples(index=False, name=None))
    #
    # # Find rows unique to df1
    # unique_to_df1 = set1 - set2
    #
    # # Find rows unique to df2
    # unique_to_df2 = set2 - set1
    #
    # # Convert back to dataframes
    # unshared_df1 = pd.DataFrame(list(unique_to_df1), columns=df_all.columns)
    # unshared_df2 = pd.DataFrame(list(unique_to_df2), columns=df_all2.columns)
    # print(unshared_df1)
    # print(unshared_df2)
    # print(df_all)
    # print(foo)

    return df_all


mainProcess()
