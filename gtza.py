import streamlit as st
from openai import OpenAI
from docx import Document
from io import BytesIO
import requests
from datetime import datetime
import pytz
import urllib.parse
import tiktoken  # 토큰 계산을 위한 라이브러리

# Streamlit에서 환경 변수(Secrets) 가져오기
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Streamlit 페이지 설정
st.set_page_config(
    page_title="Doc-Sum + Timezone",
    page_icon="📝",
)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=openai_api_key)

generation_config = {
    "temperature": 0.4,
    "top_p": 0.95,
}

st.title("Doc-Sum + Timezone")
st.caption("By Phoenix AI")

# 3. Doc-Sum: 문서 요약 기능
st.header("Doc-Sum: 문서 요약 기능")
uploaded_file_sum = st.file_uploader("요약할 문서를 업로드 해 주세요", type=["docx"], key="sum_file")

def calculate_tokens(text):
    tokenizer = tiktoken.encoding_for_model("gpt-4")
    tokens = tokenizer.encode(text)
    return len(tokens)

def split_text_by_tokens(text, max_tokens=2000):
    tokenizer = tiktoken.encoding_for_model("gpt-4")
    tokens = tokenizer.encode(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for token in tokens:
        current_chunk.append(token)
        current_length += 1
        if current_length >= max_tokens:
            chunks.append(tokenizer.decode(current_chunk))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append(tokenizer.decode(current_chunk))
    
    return chunks

if uploaded_file_sum:
    document = Document(uploaded_file_sum)
    doc_text_sum = "\n".join([para.text for para in document.paragraphs])
    st.header("문서 내용 요약")
    
    # 문서의 토큰 길이 계산
    total_tokens = calculate_tokens(doc_text_sum)
    
    if total_tokens > 8192:
        st.error(f"문서가 너무 깁니다. 문서의 총 토큰 수: {total_tokens}. 문서를 분할하여 요약합니다.")
        chunks = split_text_by_tokens(doc_text_sum)
    else:
        chunks = [doc_text_sum]

    # 요약 요청 처리
    for i, chunk in enumerate(chunks):
        st.subheader(f"문서 요약 {i+1}/{len(chunks)}")
        if st.button(f"요약 생성 {i+1}"):
            with st.spinner("요약을 생성하는 중입니다..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",  # 모델 이름 고정
                        messages=[
                            {"role": "system", "content": "Summarize the following document."},
                            {"role": "user", "content": chunk}
                        ],
                        max_tokens=500,
                        temperature=generation_config["temperature"],
                        top_p=generation_config["top_p"]
                    )
                    st.success(response.choices[0].message.content.strip())
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
