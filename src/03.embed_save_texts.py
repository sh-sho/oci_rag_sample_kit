import os
import oci
import sys
import oracledb
from dotenv import load_dotenv, find_dotenv
import multiprocessing as mp
import time
import csv
import gc
from functools import wraps
import shutil
from typing import Any, Callable, TypeVar
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import glob
import warnings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import utils
import table_detail as td

warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('ignore', FutureWarning)

F = TypeVar('F', bound=Callable[..., Any])
_ = load_dotenv(find_dotenv())
oracledb.init_oracle_client()
UN = os.environ.get("UN")
PW = os.environ.get("PW")
DSN = os.environ.get("DSN")
OCI_COMPARTMENT_ID = os.environ["OCI_COMPARTMENT_ID"]
CSV_DIRECTORY_PATH = os.environ["CSV_DIRECTORY_PATH"]

NO_OF_PROCESSORS = mp.cpu_count()
BATCH_SIZE = 96
CHUNK_SIZE = 400
CHUNK_OVERLAP = 10
    
pool = oracledb.create_pool(user=UN, password=PW, dsn=DSN, min=NO_OF_PROCESSORS, max=NO_OF_PROCESSORS)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = CHUNK_SIZE,
    chunk_overlap = CHUNK_OVERLAP,
    length_function=len, 
    add_start_index=True, 
    strip_whitespace=True,
    is_separator_regex=False
    )

def timer(func: F) -> None:
    """Any functions wrapper for calculate execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start
        print(f"{func.__name__} took a {elapsed_time}s")
        return result
    return wrapper

def auth_check():
    config = oci.config.from_file(file_location=os.environ["OCI_CONFIG_FILE"])
    compute_client = oci.core.ComputeClient(config)
    auth_response = compute_client.list_instances(OCI_COMPARTMENT_ID)
    if auth_response.status != 200:
        print(f"Auth Failed\n Error Status:{auth_response.status}")
        sys.exit
    else:
        print(f"Auth Success\n Status:{auth_response.status}")

def csv_dir_check():
    if os.path.exists(CSV_DIRECTORY_PATH):
        try:
            delete_csv_files(CSV_DIRECTORY_PATH)
            print("success delete csv")
        except FileNotFoundError:
            print("no target csv")
        except Exception as e:
            print("Error delete csv", e)
    else:
        try:
            os.makedirs(CSV_DIRECTORY_PATH, exist_ok=True)
        except Exception as e:
            print("Error make dirctory ", e)

def delete_csv_files(csv_directory):
    files = os.listdir(csv_directory)
    try:
        for file in files:
            if file.endswith(".csv"):
                os.remove(os.path.join(csv_directory, file))
    except FileNotFoundError:
        print("no target csv")
    except Exception as e:
        print("Error delete csv", e)

def delete_dir():
    if os.path.exists(CSV_DIRECTORY_PATH):
        try:
            shutil.rmtree(CSV_DIRECTORY_PATH)
            print("success delete csv directory")
        except Exception as e:
            print("Error delete directory", e)

@timer
def embed_text(texts):
    text_vector = utils.embed_documents(texts)
    return text_vector

def fetch_data_from_db(connection, table_name, table_index):
    engine = create_engine("oracle+oracledb://", creator=lambda: connection)
    select_sql = f"""
        SELECT {table_index["index_id"]}, {table_index["index_docs"]}
        FROM {table_name}
        ORDER BY {table_index["index_id"]} DESC
    """
    fetch_data = pd.read_sql(select_sql, engine)
    return fetch_data

def split_text_to_chunks(df, table_index, chunk_columns):
    all_chunks = []
    for _, row in df.iterrows():
        chunks = text_splitter.split_text(row[table_index["index_docs"].lower()])
        for i, chunk in enumerate(chunks):
            all_chunks.append([row[table_index["index_id"].lower()], i + 1, chunk])
    df_chunks = pd.DataFrame(data=all_chunks, columns=chunk_columns)
    return df_chunks

@timer
def fetch_batches() -> np.ndarray:
    with pool.acquire() as connection:
        df_select = fetch_data_from_db(connection, td.table2_name, td.table2_index)
        
        if df_select.empty:
            print(f"{td.table2_name} doesn't contain any data.")
            exit(1)

        chunk_columns = [td.table3_index["index_id"], td.table3_index["index_chunkid"], td.table3_index["index_chunk"]]
        
        try:
            df_chunks = split_text_to_chunks(df_select, td.table2_index, chunk_columns)
        except Exception as e:
            print("Error chunk loop:", e)
            exit(1)

        df_chunks.reset_index(inplace=True, drop=True)
        batches = np.array_split(df_chunks, len(df_chunks) // BATCH_SIZE + 1)
        print(f"Fetched all data: {len(df_chunks)}")
        return batches


@timer
def handle_chunk(batch):
    print(f"handle_chunk {batch}")

    try:
        chunks_id = batch[td.table3_index["index_chunkid"]].tolist()
        texts = batch[td.table3_index["index_chunk"]].tolist()
    except Exception as e:
        print("Error batch loop:", e)
        return

    embed_data = embed_text(texts)
    data_df = pd.DataFrame({
        td.table3_index["index_id"]: batch[td.table2_index["index_id"]],
        td.table3_index["index_chunkid"]: chunks_id,
        td.table3_index["index_chunk"]: texts,
        td.table3_index["index_vector"]: embed_data
    })
    print(data_df)
    del texts
    gc.collect()

    to_csv(batch=data_df)
    del data_df
    gc.collect()

@timer
def to_csv(batch: np.ndarray) -> None:
    """Dump data to CSV"""
    pd.DataFrame(batch).to_csv(f"{CSV_DIRECTORY_PATH}/insert-data-{time.time()}.csv", header=False, index=False)

@timer
def finalizer(exception: Exception, cursor: oracledb.Cursor, connection: oracledb.Connection) -> None:
    """Close some resources(cursor, connection) and exit this task."""
    print(exception)
    print(f"Finalize these resources. cursor: {cursor}, connection: {connection}")
    cursor.close()
    connection.close()
    exit(1)

@timer
def insert_columns(chunk, table_name):
    with pool.acquire() as connection:
        connection.autocommit = True
        with connection.cursor():
            engine = create_engine("oracle+oracledb://", creator=lambda: connection)
            print(chunk)
            try:
                chunk.to_sql(table_name, con=engine,  index=False, if_exists='append')
            except Exception as e:
                print("Error insert_columns:", e)

@timer
def flush(data: list) -> None:
    """Flush the on-memory data"""
    with pool.acquire() as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
            
            insert_sql = f"""
                INSERT INTO {td.table3_name} ({td.table3_index["index_id"]}, {td.table3_index["index_chunkid"]}, {td.table3_index["index_chunk"]}, {td.table3_index["index_vector"]}) 
                VALUES(:1, :2, :3, :4)
                """
            try:
                cursor.executemany(statement=insert_sql, parameters=data, batcherrors=True, arraydmlrowcounts=True)
                print(f"Insert rows: {len(cursor.getarraydmlrowcounts())}")
            except oracledb.DatabaseError as e:
                finalizer(exception=e, cursor=cursor, connection=connection)
            except KeyboardInterrupt as e:
                finalizer(exception=e, cursor=cursor, connection=connection)

@timer
def bulk_insert() -> None:
    """Bulk insert to sink table"""
    files = glob.glob(f"{CSV_DIRECTORY_PATH}/*.csv")
    insert_data = []
    for file in files:
        with open(file, "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for line in csv_reader:
                insert_data.append(tuple(line))
                if (len(insert_data)) >= 10_000:
                    flush(data=insert_data)
                    insert_data = []
    if insert_data:
        flush(data=insert_data)
        
def data_checks() -> None:
    """Check Embedded data"""
    with oracledb.connect(user=UN, password=PW, dsn=DSN) as conn:
        with conn.cursor() as cursor:
            check_sql = f"""
                SELECT {td.table3_index["index_id"]}, {td.table3_index["index_vector"]}
                FROM {td.table3_name}
                WHERE ROWNUM <= 2
                ORDER BY {td.table3_index["index_id"]} DESC
            """
            try:
                cursor.execute(check_sql)
                print(f"check data {cursor.fetchall()}")
            except Exception as e:
                print("Error connect db checksql", e)
        conn.close()

if __name__ == "__main__":
    start_time = time.time()
    auth_check()
    csv_dir_check()
    
    batches = fetch_batches()
    print(f"batches {batches}")
    
    with mp.Pool(NO_OF_PROCESSORS) as mappool:
        mappool.starmap(handle_chunk, zip(batches))
    
    del batches
    gc.collect()
    bulk_insert()
    data_checks()
    end_time = time.time()
    execution_time = end_time - start_time
    print("Total Run Time ", execution_time)
    delete_dir()
    pool.close()
