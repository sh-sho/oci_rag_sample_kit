import streamlit as st
import requests
import json

chat_api_url = "http://localhost:8000/chat"
def chat_response(prompt: str) -> str:
    chat_api_params = {"input_text": {prompt} }
    chat_api_response = requests.get(url=chat_api_url, params=chat_api_params)
    return chat_api_response.text


doc_search_api_url = "http://localhost:8000/vector_search/"
def doc_search(prompt: str) -> str:
    doc_search_api_params = {"input_text": {prompt}}
    doc_search_api_response = requests.get(url=doc_search_api_url, params=doc_search_api_params)
    result = json.loads(doc_search_api_response.text)['result'][0][1]
    return result

chat_doc_api_url = "http://localhost:8000/chat_doc/"
def chat_doc_response(prompt: str) -> str:
    doc = doc_search(prompt=prompt)
    chat_doc_api_params = {"input_text": {prompt}, "pdf_files": {doc} }
    chat_doc_api_response = requests.get(url=chat_doc_api_url, params=chat_doc_api_params)
    return chat_doc_api_response.text

st.title("OCI Chat Bot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = f"Response: {chat_doc_response(prompt)}"
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

