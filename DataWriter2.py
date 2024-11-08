import pandas as pd
from sqlalchemy import create_engine, types, Table, MetaData
import sqlite3
from geoalchemy2 import Geometry
import uuid
import numpy as np
import pyodbc
import time
from sqlalchemy.ext.declarative import declarative_base
# Assume you have a DataFrame called 'df'
# df = pd.DataFrame({'column1': [1, 2, 3], 'column2': ['a', 'b', 'c']})
def get_pandas_dtype(sql_type):
    sql_to_pandas = {
        'int': 'int64',
        'varchar': 'object',
        'char': 'object',
        'datetime': 'datetime64[ns]',
        'smalldatetime': 'datetime64[ns]',
        'tinyint': 'int8',
        'smallint': 'int16',
        'decimal': 'float64',
        'real': 'float32',
        'float': 'float64',
        'bit': 'bool',
        'text': 'object',
        'nvarchar': 'object',
        'geometry': 'object',
        'uniqueidentifier': 'object'
    }
    return sql_to_pandas.get(sql_type.lower(), 'object')

def get_sqlalchemy_type(sql_type):
    sql_to_sqlalchemy = {
        'int': types.INTEGER(),
        'varchar': types.VARCHAR(length=255),  # Adjust length as needed
        'char': types.CHAR(length=255),  # Adjust length as needed
        'datetime': types.DATETIME(),
        'smalldatetime': types.DATETIME(),
        'tinyint': types.SMALLINT(),  # SQLAlchemy doesn't have TINYINT, using SMALLINT
        'smallint': types.SMALLINT(),
        'decimal': types.DECIMAL(precision=10, scale=2),  # Adjust precision and scale as needed
        'real': types.FLOAT(),
        'float': types.FLOAT(),
        'bit': types.BINARY(),
        'text': types.TEXT(),
        'nvarchar': types.NVARCHAR(length=255),  # Adjust length as needed
        'geometry': Geometry(geometry_type='GEOMETRY', srid=4326),  # Adjust SRID as needed
        'uniqueidentifier': types.CHAR(36)  # UUIDs are 36 characters long
    }
    return sql_to_sqlalchemy.get(sql_type.lower(), types.VARCHAR())


def convert_column(df, column, sql_type):
    pandas_type = get_pandas_dtype(sql_type)

    if pandas_type == 'datetime64[ns]':
        df[column] = pd.to_datetime(df[column], errors='coerce')
    elif sql_type.lower() == 'uniqueidentifier':
        df[column] = df[column].apply(lambda x: str(uuid.UUID(x)) if x and pd.notna(x) else None)
    elif sql_type.lower() == 'geometry':
        # Assuming geometry is stored as WKT (Well-Known Text)
        pass  # Keep as object type
    elif pandas_type.startswith('int'):
        # For integer types, we need to handle NaN and inf values
        if df[column].dtype == 'object':
            df[column] = pd.to_numeric(df[column], errors='coerce')
        df[column] = df[column].fillna(0)  # Replace NaN with 0
        df[column] = df[column].replace([np.inf, -np.inf], 0)  # Replace inf with 0
        df[column] = df[column].astype(pandas_type)
    elif pandas_type.startswith('float'):
        if df[column].dtype == 'object':
            df[column] = pd.to_numeric(df[column], errors='coerce')
        df[column] = df[column].fillna(0.0)  # Replace NaN with 0.0
        df[column] = df[column].replace([np.inf, -np.inf], 0.0)  # Replace inf with 0.0
        df[column] = df[column].astype(pandas_type)
    else:
        df[column] = df[column].astype(pandas_type)

    return df


def drop_table_func(engine, table_name, schema='dbo'):
    metadata = MetaData()
    table = Table(table_name, metadata, schema=schema, autoload_with=engine)

    try:
        table.drop(engine)
        print(f"Table '{schema}.{table_name}' has been dropped successfully.")
    except Exception as e:
        print(f"Error dropping table '{schema}.{table_name}': {str(e)}")

def categorize(value):
    if pd.isna(value) or value == '':
        return 'empty'
    return value

cnxn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=CGDESKTOP\SQLEXPRESS;"
    "Database=UTRBDMSNET;"
    "Trusted_Connection = yes;")
cxrsor = cnxn.cursor()
    # return cnxn, cursor
pd.set_option('display.max_columns', None)
params = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=CGDESKTOP\SQLEXPRESS;"
    "Database=UTRBDMSNET;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;")
engine_local = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

db_file = r'C:\Work\your_database.db'  # Replace with your .db file path
conn = sqlite3.connect(db_file)

# Create a cursor object
cursor = conn.cursor()

# Create a SQLAlchemy engine
# For SQLite:
# engine_db = create_engine('sqlite:///your_database.db')

# For MySQL:
# engine = create_engine('mysql://username:password@localhost/dbname')

# For PostgreSQL:
# engine = create_engine('postgresql://username:password@localhost/dbname')

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Fetch all results
tables = cursor.fetchall()

# Print the table names
print("Tables in the database:")
all_tables = [table[0] for table in tables]
# print(all_tables)
# print(foo)
# used_tables_here = ['vw_DON_WH_SPUDdates', 'vw_DON_WH_SPUDdates_DataTypes', 'vw_DON_WH_APDNO', 'vw_DON_WH_APDNO_DataTypes', 'vw_DON_WH_SLANT',
#  'vw_DON_WH_SLANT_DataTypes', 'vw_DON_WH_FirstProdDate', 'vw_DON_WH_FirstProdDate_DataTypes', 'WellHistory', 'WellHistory_DataTypes',
#  'tblAPDWellCement', 'tblAPDWellCement_DataTypes', 'vw_DON_WH_ProdTest', 'vw_DON_WH_ProdTest_DataTypes', 'tblAPDWellCementCls',
#  'tblAPDWellCementCls_DataTypes', 'tblAPD', 'tblAPD_DataTypes', 'vw_DON_WH_Surveys', 'vw_DON_WH_Surveys_DataTypes', 'Construct',
#  'Construct_DataTypes', 'tblAPDWellStringPipe', 'tblAPDWellStringPipe_DataTypes', 'vw_DON_WH_Depths', 'vw_DON_WH_Depths_DataTypes',
#  'ConstructAPD', 'ConstructAPD_DataTypes', 'tblAPDWellStrings', 'tblAPDWellStrings_DataTypes', 'tblAPDBOPE', 'tblAPDBOPE_DataTypes',
#  'WellDate', 'WellDate_DataTypes', 'FACT_vwWellInformation', 'FACT_vwWellInformation_DataTypes', 'ConstructCasing', 'ConstructCasing_DataTypes',
#  'ConstructDate', 'ConstructDate_DataTypes', 'RefFormation', 'RefFormation_DataTypes', 'RefFields', 'RefFields_DataTypes',
#  'ShutInAbandonedSuspendedWellsRpt', 'ShutInAbandonedSuspendedWellsRpt_DataTypes', 'Lease', 'Lease_DataTypes', 'tblAPDWCRWellInfo',
#  'tblAPDWCRWellInfo_DataTypes', 'Loc', 'Loc_DataTypes', 'Well', 'Well_DataTypes', 'LocExt', 'LocExt_DataTypes', 'DocketItemArea',
#  'DocketItemArea_DataTypes', 'tblAPDLoc', 'tblAPDLoc_DataTypes', 'DocketItemAreaSection', 'DocketItemAreaSection_DataTypes',
#  'RefCounty', 'RefCounty_DataTypes', 'DirectionalSurveyHeader', 'DirectionalSurveyHeader_DataTypes', 'DirectionalSurveyData',
#   'DirectionalSurveyData_DataTypes']#, 'RefCodes', 'RefCodes_DataTypes', 'ConstructPerforation', 'ConstructPerforation_DataTypes', 'Entity', 'Entity_DataTypes']
for table in tables:


    table_val = table[0]
    # if 'DataTypes' not in table_val:# and table_val not in used_tables_here:
    # if 'DataTypes' not in table_val and table_val =='DirectionalSurveyHeader':
    if 'DataTypes' not in table_val and table_val != 'ProdFacilityProduction':
        time_start = time.perf_counter()

        print("\n\n\n\n\n", table_val)
        loaded_df = pd.read_sql_query(f"""Select * from {table_val}""", conn)
        loaded_df_data = pd.read_sql_query(f"""Select * from {table_val}_DataTypes""", conn)
        cut_columns = ['Comment', 'DirectionalLineFeature', 'DirectionalPointFeature', 'Description', 'ProdComment']
        # if table_val == 'DirectionalSurveyData':
        #     used = loaded_df[loaded_df['MeasuredDepth'] == 20551]
        #     print(used)
        # if table_val == 'DirectionalSurveyHeader':
        #     used = loaded_df[loaded_df['APINumber'] == '4301354305']
        #     # print(used)
        #     df2 = pd.read_sql_query(f"""Select * from DirectionalSurveyHeader where ConstructKey = '{40099}'""", conn)
        #     # print(df2)
        for i in cut_columns:
            try:
                loaded_df = loaded_df.drop(columns=[i])
                loaded_df_data = loaded_df_data.drop(columns=[i])
            except KeyError:
                pass
        for column, sql_type in loaded_df_data.iloc[0].items():
            loaded_df = convert_column(loaded_df, column, sql_type)
            # date_series = pd.to_datetime(loaded_df[column], errors='coerce')
            non_empty_df = loaded_df[loaded_df[column].notna() & (loaded_df[column] != '')]
            # Now convert to datetime
            date_series = pd.to_datetime(non_empty_df[column],format='%m/%d/%Y',  errors='coerce')
            valid_dates = date_series.notnull().sum()
            total_non_empty_rows = len(non_empty_df)
            if valid_dates == total_non_empty_rows:
                loaded_df[column] = loaded_df[column].astype('datetime64[ns]')
        # print('data types load', time.perf_counter() - time_start)
        time_start = time.perf_counter()
        dtype_dict = {column: get_sqlalchemy_type(sql_type) for column, sql_type in loaded_df_data.iloc[0].items()}
        # print(dtype_dict)
        # print('dict write', time.perf_counter() - time_start)
        time_start = time.perf_counter()
        columns = loaded_df.columns
        local_df = pd.read_sql_query(f"""Select * from {table_val}""", engine_local)
        # print(local_df)
        loaded_df = loaded_df.replace({pd.NaT: None})
        loaded_df = loaded_df.reset_index(drop=True)
        # print(len(local_df), len(loaded_df))
        # print(tester)
        # A. Check for rows in local_df that aren't in loaded_df and append them
        # rows_to_append = local_df[~local_df.index.isin(loaded_df.index)]
        # print(local_df.head(1).values.tolist()[0])
        # print(loaded_df.head(1).values.tolist()[0])

        rows_to_append = loaded_df[~loaded_df.index.isin(local_df.index)]
        # used = loaded_df[loaded_df['APINumber'] == '4301354305']
        # used2 = local_df[local_df['APINumber'] == '4301354305']
        # rows_only_in_df1 = loaded_df[~loaded_df.isin(local_df).all(axis=1)]
        # print(used, used2)
        # print(len(rows_to_append), len(rows_only_in_df1))
        #
        # print(rows_to_append)
        # print(local_df.iloc[4006])
        # print(loaded_df.iloc[4006])


        # Only concatenate if there are actually rows to append
        # if not rows_to_append.empty:
        #     # Ensure dtypes match before concatenation
        #     for col in rows_to_append.columns:
        #         if col in loaded_df.columns:
        #             rows_to_append[col] = rows_to_append[col].astype(loaded_df[col].dtype)
        #
        #     loaded_df = pd.concat([loaded_df, rows_to_append], axis=0)
        #
        # # B. Compare rows with identical indexes and update local_df if different
        # # common_indexes = local_df.index.intersection(loaded_df.index)
        # #
        # # for idx in common_indexes:
        # #     if not local_df.loc[idx].equals(loaded_df.loc[idx]):
        # #         local_df.loc[idx] = loaded_df.loc[idx]
        # print(len(local_df), 'rows already exist')
        # print(len(loaded_df), 'rows to be written')
        # print(loaded_df)
        loaded_df.to_sql(table_val, engine_local, if_exists='replace', index=False, dtype=dtype_dict)


        # if not rows_to_append.empty:
        #     print(len(loaded_df), 'rows found')
        #     print(len(local_df), 'rows in database')
        #     print(len(rows_to_append), 'rows to be written')
        #     rows_to_append.to_sql(table_val, engine_local, if_exists='replace', index=False, dtype=dtype_dict)

        print('\nwriteData', time.perf_counter() - time_start)
