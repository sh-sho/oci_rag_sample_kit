import os
from typing import List

import oci
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

OCI_COMPARTMENT_ID = os.environ["OCI_COMPARTMENT_ID"]
CONFIG_PROFILE = os.environ["CONFIG_PROFILE"]
OCI_CONFIG_FILE = os.environ["OCI_CONFIG_FILE"]
config = oci.config.from_file(file_location=OCI_CONFIG_FILE, profile_name=CONFIG_PROFILE)
generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config)

def embed_documents(texts: List[str]) -> List[List[float]]:
    embed_text_response = generative_ai_inference_client.embed_text(
        embed_text_details=oci.generative_ai_inference.models.EmbedTextDetails(
            inputs=texts,
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id="cohere.embed-multilingual-v3.0"),
            compartment_id=OCI_COMPARTMENT_ID,
            input_type="SEARCH_DOCUMENT"))

    embeddings = embed_text_response.data.embeddings
    return embeddings
