table1_name = "SOURCE_TABLE"
table2_name = "DOCUMENT_TABLE"
table3_name = "CHUNK_TABLE"

table1_index = dict(
    index_id="ID",
    index_name="NAME"
)

table2_index = dict(
    index_id="ID",
    index_docs="DOCUMENT",
)

table3_index = dict(
    index_id="ID",
    index_chunkid="CHUNK_ID",
    index_chunk="CHUNK",
    index_vector="CHUNK_VECTOR"
)

