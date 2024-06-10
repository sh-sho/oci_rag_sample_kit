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
    print("Start Drop Table")
    try:
        with oracledb.connect(user=UN, password=PW, dsn=DSN) as connection:
            with connection.cursor() as cursor:

                cursor.execute(f"""
                    DROP TABLE {td.table3_name}
                """)
                print(f"Drop Table {td.table3_name}")
                
                cursor.execute(f"""
                    DROP TABLE {td.table2_name}
                """)
                print(f"Drop Table {td.table2_name}")
                
                cursor.execute(f"""
                    DROP TABLE {td.table1_name}
                """)
                print(f"Drop Table {td.table1_name}")
                connection.commit()
                print("End Drop Table")
    except Exception as e:
        print("Error Drop Table:", e)
    
