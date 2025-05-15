import os
import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from openai import OpenAI
import openai


OPENAI_API_KEY="OPENAI_API_KEY"
client = OpenAI(api_key=OPENAI_API_KEY)

def load_file(uploaded):
    if uploaded.type == "application/pdf":
        reader = PdfReader(uploaded)
        return "\n".join(p.extract_text() for p in reader.pages)
    elif uploaded.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
        if uploaded.type == "text/plain":
            return uploaded.getvalue().decode("utf-8")
        doc = Document(uploaded)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        st.error("Unsupported file type.")
        return ""

def chunk_text(text, max_tokens=1500):
    words = text.split()
    chunks, chunk = [], []
    for w in words:
        chunk.append(w)
        if len(chunk) >= max_tokens:
            chunks.append(" ".join(chunk)); chunk = []
    if chunk: chunks.append(" ".join(chunk))
    return chunks

def call_openai(prompt: str, system: str = "You are a helpful document analyzer.") -> str:
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()



st.title("📄 Document Analyzer with OpenAI")

uploaded = st.file_uploader("Upload PDF / DOCX / TXT", accept_multiple_files=False)
if uploaded:
    text = load_file(uploaded)
    chunks = chunk_text(text)

    st.sidebar.header("Analysis options")
    task = st.sidebar.selectbox("Select task", ["Summarize", "Ask a question"])
    if task == "Summarize":
        if st.sidebar.button("Run summarization"):
            with st.spinner("Summarizing..."):
                out = "\n\n".join(call_openai(c, system="Summarize this text.") for c in chunks)
            st.subheader("Summary")
            st.write(out)

    elif task == "Ask a question":
        question = st.sidebar.text_input("Your question")
        if question and st.sidebar.button("Run QA"):
            with st.spinner("Answering..."):
                context = "\n\n".join(chunks)
                out = call_openai(context + f"\n\nQ: {question}\nA:")
            st.subheader("Answer")
            st.write(out)
