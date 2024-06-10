import os
import oracledb
import array
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
import uvicorn
import numpy as np
from langchain_community.document_loaders import UnstructuredFileLoader
import oci.config
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import ChatDetails, CohereChatRequest, OnDemandServingMode, CohereTool, CohereParameterDefinition, CohereUserMessage, CohereChatBotMessage

import utils
import table_detail as td

_ = load_dotenv(find_dotenv())
oracledb.init_oracle_client()
UN = os.environ.get("UN")
PW = os.environ.get("PW")
DSN = os.environ.get("DSN")
OCI_CONFIG_FILE = os.environ["OCI_CONFIG_FILE"]
OCI_CONFIG_PROFILE = os.environ["CONFIG_PROFILE"]
OCI_COMPARTMENT_ID = os.environ["OCI_COMPARTMENT_ID"]


config = oci.config.from_file(file_location="~/.oci/config", profile_name=OCI_CONFIG_PROFILE)
generative_ai_inference_client = GenerativeAiInferenceClient(config)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/vector_search/")
async def vector_search(
    input_text: str = 'Hello'
):
    embed_text = array.array('f', utils.embed_documents([input_text])[0])
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
                FETCH FIRST 1 ROWS ONLY
            """
            cursor.execute(select_sql, [embed_text])
            results = cursor.fetchall()
    return {"result": results}

@app.get("/chat/")
async def chat_command_r(
    input_text: str = 'Hello'
):
    chat_detail = ChatDetails(
        chat_request=CohereChatRequest(
            message=input_text,
            max_tokens=500
            ),
        compartment_id=OCI_COMPARTMENT_ID,
        serving_mode=OnDemandServingMode(
            model_id="cohere.command-r-16k"
        ))
    chat_response = generative_ai_inference_client.chat(chat_detail)
    return chat_response.data.chat_response.text


pdf_directory = './data/'
def doc_loader(pdf_path: str) -> np.ndarray:
    loader = UnstructuredFileLoader(pdf_directory + pdf_path.strip("'"))
    doc = loader.load()
    return doc

def create_documents(pdf_files: np.ndarray) -> np.ndarray:
    documents=[]
    for idx, pdf_file in enumerate(pdf_files):
        pdf_data = doc_loader(pdf_path=pdf_file)
        documents.append(
            { "title": pdf_data[0].metadata['source'].replace(pdf_directory, "").replace('.pdf', ""), "text": pdf_data[0].page_content })
    return documents

@app.get('/chat_doc/')
async def chat_command_r_documents(
    input_text: str = 'Hello', 
    pdf_files: str = None
    ):
    documents = create_documents(pdf_files=[pdf_files])
    chat_detail = ChatDetails(
        chat_request=CohereChatRequest(
            documents=documents,
            message=input_text,
            max_tokens=500
            ),
        compartment_id=OCI_COMPARTMENT_ID,
        serving_mode=OnDemandServingMode(
            model_id="cohere.command-r-16k"
        ))
    chat_response = generative_ai_inference_client.chat(chat_detail)
    # return chat_response.data.chat_response.citations[0].document_ids[0]
    return chat_response.data.chat_response.text

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
