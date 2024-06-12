import streamlit as st
import requests
import json

from chatclass import ChatParams

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
def chat_doc_response(cparams: ChatParams) -> str:
    cparams.pdf_files = doc_search(prompt=cparams.prompt)
    chat_doc_api_params = {"input_text": {cparams.prompt}, "pdf_files": {cparams.pdf_files} }
    chat_doc_api_response = requests.get(url=chat_doc_api_url, params=chat_doc_api_params)
    return chat_doc_api_response.text


max_tokens = st.sidebar.slider('Max_tokens', 0, 1000, 100, 10)
temperature = st.sidebar.slider('Temperature', 0.0, 1.0, 0.1, 0.1)
top_k = st.sidebar.slider('Top_k', 0, 500, 1, 1)
top_p = st.sidebar.slider('Top_p', 0.01, 0.99, 0.75, 0.01)
frequency_penalty = st.sidebar.slider('Frequency_penalty', 0.0, 1.0, 0.0, 0.1)
presence_penalty = st.sidebar.slider('Presence_penalty', 0.0, 1.0, 0.0, 0.1)
cparams = ChatParams(max_tokens, temperature, top_k, top_p, frequency_penalty, presence_penalty)

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
        cparams.prompt = prompt

    with st.chat_message("assistant"):
        response = f"Response: {chat_doc_response(cparams)}"
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

