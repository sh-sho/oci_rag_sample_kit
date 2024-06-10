import os
import oracledb
from dotenv import load_dotenv, find_dotenv
import table_detail as td

_ = load_dotenv(find_dotenv())
oracledb.init_oracle_client()

UN = os.environ.get("UN")
PW = os.environ.get("PW")
DSN = os.environ.get("DSN")

if __name__ == "__main__":
    print("Start Creating Table.")

    try:
        with oracledb.connect(user=UN, password=PW, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                create_table1_sql = f"""
                    CREATE TABLE {td.table1_name}
                    (
                        {td.table1_index["index_id"]} NUMBER(9,0),
                        {td.table1_index["index_name"]} VARCHAR2(100 BYTE)
                    )
                """
                
                create_table2_sql = f"""
                    CREATE TABLE {td.table2_name}
                    (
                        {td.table2_index["index_id"]} NUMBER(9,0),
                        {td.table2_index["index_docs"]} CLOB
                    )
                """
                
                create_table3_sql = f"""
                    CREATE TABLE {td.table3_name}
                    (
                        {td.table3_index["index_id"]} NUMBER(9,0),
                        {td.table3_index["index_chunkid"]} NUMBER,
                        {td.table3_index["index_chunk"]} VARCHAR2(2000 BYTE),
                        {td.table3_index["index_vector"]} VECTOR
                    )
                """

                cursor.execute(create_table1_sql)
                cursor.execute(create_table2_sql)
                cursor.execute(create_table3_sql)
            connection.commit()
    except Exception as e:
        print("Error create_table:", e)

    print("End Creating Table.")
