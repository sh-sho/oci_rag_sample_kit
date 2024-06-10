import os
import oracledb
from dotenv import load_dotenv, find_dotenv
import numpy as np
from langchain_community.document_loaders import UnstructuredFileLoader

import table_detail as td
import data.sample_data as sd


_ = load_dotenv(find_dotenv())
oracledb.init_oracle_client()
UN = os.environ.get("UN")
PW = os.environ.get("PW")
DSN = os.environ.get("DSN")
pdf_directory = './data/'
# pdf_directory = '/home/ubuntu/oci_script/o_sample/chunk_rag_code/data/'

def doc_loader(pdf_path: str) -> np.ndarray:
    loader = UnstructuredFileLoader(pdf_directory + pdf_path)
    doc = loader.load()
    return doc

def save_texts() -> None:
    print("Start Insert data.")
    try:
        with oracledb.connect(user=UN, password=PW, dsn=DSN) as connection:
            with connection.cursor() as cursor:

                delete_table1_sql = f"""
                    DELETE from {td.table1_name}
                """
                delete_table2_sql = f"""
                    DELETE from {td.table2_name}
                """
                delete_table3_sql = f"""
                    DELETE from {td.table3_name}
                """
                cursor.execute(delete_table1_sql)
                cursor.execute(delete_table2_sql)
                cursor.execute(delete_table3_sql)
                
                pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
                for idx, pdf_file in enumerate(pdf_files):
                    pdf_data = doc_loader(pdf_path=pdf_file)
                    
                    insert_table1_sql = f"""
                        INSERT INTO {td.table1_name} ({td.table1_index["index_id"]}, {td.table1_index["index_name"]})
                        VALUES (:sample_id, :sample_name)
                    """

                    cursor.execute(insert_table1_sql, sample_id=idx+1, sample_name=pdf_data[0].metadata['source'].replace(pdf_directory, ""))
                    print(f"Insert data {idx+1} to table1")
                
                    insert_table2_sql = f"""
                        INSERT INTO {td.table2_name} ({td.table2_index["index_id"]}, {td.table2_index["index_docs"]})
                        VALUES (:sample_id, :sample_doc)
                    """

                    cursor.execute(insert_table2_sql, sample_id=idx+1, sample_doc=pdf_data[0].page_content)
                    print(f"Insert data {idx+1} to table2")
                connection.commit()
                print("End Insert data")
    except Exception as e:
        print("Error Insert data:", e)

if __name__ == "__main__":
    save_texts()
