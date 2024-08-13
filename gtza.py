import streamlit as st
from openai import OpenAI
from docx import Document
from io import BytesIO
import requests
from datetime import datetime
import pytz
import urllib.parse

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

# 사이드바에서 모델 선택
model_selection = st.sidebar.radio(
    "**사용할 모델을 선택하세요 :**", 
    ("GPT-4-turbo", "GPT-4-o-mini"),  # 모델 선택 옵션 제공
)

# 선택된 모델에 따라 사용할 모델 이름 설정
model_name = "gpt-4-turbo" if model_selection == "GPT-4-turbo" else "gpt-4-o-mini"

# 3. Doc-Sum: 문서 요약 기능
st.header("Doc-Sum: 문서 요약 기능")

# 파일 업로드 메뉴
uploaded_file_sum = st.file_uploader("요약할 문서를 업로드 해 주세요", type=["docx"], key="sum_file")

# 링크 입력 메뉴
uploaded_link_sum = st.text_input("요약할 문서의 링크를 입력해 주세요:", key="sum_link")

# 요약에 필요한 키워드 입력 메뉴
summary_keyword = st.text_input("문서 요약에 필요한 키워드를 입력해 주세요:")

# 출력할 언어 선택 메뉴
output_language_sum = st.selectbox(
    "출력할 언어를 선택하세요:",
    ("한국어", "영어", "일본어", "중국어", "러시아어", "프랑스어", "독일어", "이탈리아어", "아랍어")
)

language_prompts = {
    "한국어": "다음 문서를 한국어로 요약해 주세요.",
    "영어": "Please summarize the following document in English.",
    "일본어": "以下の文書を日本語で要約してください。",
    "중국어": "请用中文总结以下文档。",
    "러시아어": "Пожалуйста, кратко изложите следующий документ на русском языке.",
    "프랑스어": "Veuillez résumer le document suivant en français.",
    "독일어": "Bitte fassen Sie das folgende Dokument auf Deutsch zusammen.",
    "이탈리아어": "Si prega di riassumere il seguente documento in italiano.",
    "아랍어": "يرجى تلخيص المستند التالي باللغة العربية."
}

doc_text_sum = ""

# 파일이 업로드된 경우 파일 내용을 사용
if uploaded_file_sum:
    document = Document(uploaded_file_sum)
    doc_text_sum = "\n".join([para.text for para in document.paragraphs])

# 링크가 입력된 경우 링크의 텍스트를 가져옴
elif uploaded_link_sum:
    try:
        response = requests.get(uploaded_link_sum)
        if response.status_code == 200:
            doc_text_sum = response.text
        else:
            st.error("문서 링크를 불러오는 데 실패했습니다.")
    except Exception as e:
        st.error(f"문서 링크를 불러오는 도중 에러가 발생했습니다: {str(e)}")

if doc_text_sum:
    st.header("문서 내용 요약")

    if st.button("요약 생성"):
        with st.spinner("요약을 생성하는 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model=model_name,  # 선택된 모델 이름 사용
                    messages=[
                        {"role": "system", "content": language_prompts[output_language_sum]},
                        {"role": "user", "content": f"{summary_keyword}\n\n{doc_text_sum}"}
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

# 시간 확인 메뉴
location = st.text_input("시간을 확인할 장소를 입력하세요:")
if st.button("시간 확인") and location:
    with st.spinner("시간을 확인하는 중입니다..."):
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

        local_time, tz_name = get_timezone_info(location)
        if local_time and tz_name:
            st.success(f"{location}의 현재 시간: {local_time.strftime('%Y-%m-%d %H:%M:%S')} ({tz_name})")

# 생년월일 입력 메뉴
st.header("생년월일 확인")

# 생년월일 입력창
birth_date = st.date_input("생년월일을 입력하세요:", datetime(2000, 1, 1))

if st.button("생일-나이 확인"):
    def get_age_and_birthday_info(birth_date):
        today = datetime.today()
        this_year_birthday = birth_date.replace(year=today.year)

        # 나이 계산
        age = today.year - birth_date.year
        if today < this_year_birthday:
            age -= 1

        # 생일 지났는지 여부 확인
        birthday_passed = today >= this_year_birthday
        return age, birthday_passed

    age, birthday_passed = get_age_and_birthday_info(birth_date)
    if birthday_passed:
        st.info(f"생일이 지났습니다. 현재 {age}살입니다.")
    else:
        st.info(f"생일이 아직 지나지 않았습니다. 현재 {age}살입니다.")
