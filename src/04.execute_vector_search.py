import os
import sys

import oracledb
import array
from dotenv import load_dotenv, find_dotenv

import utils
import table_detail as td

_ = load_dotenv(find_dotenv())
oracledb.init_oracle_client()
UN = os.environ.get("UN")
PW = os.environ.get("PW")
DSN = os.environ.get("DSN")



def query_text(text: str):
    embed_text = array.array('f', utils.embed_documents([text])[0])

    print(f"Start Vector Search")
    with oracledb.connect(user=UN, password=PW, dsn=DSN) as connection:
        with connection.cursor() as cursor:
            cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
            select_sql = f"""
                SELECT
                    ct.{td.table3_index["index_id"]},
                    pt.{td.table1_index["index_name"]},
                    ct.{td.table3_index["index_chunk"]},
                    VECTOR_DISTANCE({td.table3_index["index_vector"]}, :1, COSINE) as distance
                FROM
                    {td.table3_name} ct
                JOIN
                    {td.table1_name} pt ON ct.{td.table3_index["index_id"]} = pt.{td.table1_index["index_id"]}
                ORDER BY distance
                FETCH FIRST 5 ROWS ONLY
            """
            cursor.execute(select_sql, [embed_text])

            print(f"============検索結果============")
            index = 1
            for row in cursor:
                print(f"{index}: {row}")
                index += 1
            print(f"================================")
        connection.commit()
    print(f"End Vector Search")


if __name__ == "__main__":
    args = sys.argv
    query = args[1]
    print(f"検索テキスト：{query}")
    query_text(query)
