import streamlit as st
from openai import OpenAI
from docx import Document
from io import BytesIO
import requests
from datetime import datetime
import pytz
import urllib.parse
import time

# Streamlit에서 환경 변수(Secrets) 가져오기
openai_api_key = st.secrets["OPENAI_API_KEY"]
google_time_zone_api_key = st.secrets["GOOGLE_TIME_ZONE_API_KEY"]

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

if uploaded_file_sum:
    document = Document(uploaded_file_sum)
    doc_text_sum = "\n".join([para.text for para in document.paragraphs])
    st.header("문서 내용 요약")
    
    if st.button("요약 생성"):
        with st.spinner("요약을 생성하는 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",  # 모델 이름 고정
                    messages=[
                        {"role": "system", "content": "Summarize the following document."},
                        {"role": "user", "content": doc_text_sum}
                    ],
                    max_tokens=500,
                    temperature=generation_config["temperature"],
                    top_p=generation_config["top_p"]
                )
                
                st.success(response.choices[0].message.content.strip())
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")

# 4. Timezone: 사용자가 입력한 장소의 시간 확인
st.header("Timezone: 사용자가 입력한 장소의 시간 확인")
location = st.text_input("시간을 확인할 장소를 입력하세요:")

def get_timezone_info(location, retries=2):
    try:
        encoded_location = urllib.parse.quote(location)
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_location}&key={google_time_zone_api_key}"
        geocode_response = requests.get(geocode_url).json()

        if geocode_response["status"] == "OK":
            latlng = geocode_response["results"][0]["geometry"]["location"]
            timezone_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={latlng['lat']},{latlng['lng']}&timestamp={int(datetime.now().timestamp())}&key={google_time_zone_api_key}"
            timezone_response = requests.get(timezone_url).json()

            if timezone_response["status"] == "OK":
                tz_id = timezone_response["timeZoneId"]
                tz_name = timezone_response["timeZoneName"]
                local_time = datetime.now(pytz.timezone(tz_id))
                return local_time, tz_name
            else:
                st.error(f"시간대를 불러오는 데 실패했습니다. 상태 코드: {timezone_response['status']}, 메시지: {timezone_response.get('errorMessage', '없음')}")
        else:
            st.error(f"위치를 찾을 수 없습니다. 상태 코드: {geocode_response['status']}, 메시지: {geocode_response.get('error_message', '없음')}")
    except Exception as e:
        if retries > 0:
            time.sleep(1)  # 잠시 대기 후 재시도
            return get_timezone_info(location, retries - 1)
        else:
            st.error(f"시간을 확인하는 도중 에러가 발생했습니다: {str(e)}")
            return None, None

if st.button("시간 확인") and location:
    with st.spinner("시간을 확인하는 중입니다..."):
        local_time, tz_name = get_timezone_info(location)
        if local_time and tz_name:
            st.success(f"{location}의 현재 시간: {local_time.strftime('%Y-%m-%d %H:%M:%S')} ({tz_name})")
