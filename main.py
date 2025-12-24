import streamlit as st
import pandas as pd
from pathlib import Path
import unicodedata
import io

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# =========================
# Streamlit 기본 설정
# =========================
st.set_page_config(
    page_title="극지식물 생육에 따른 최적 EC농도 분석",
    layout="wide"
)

# =========================
# 한글 폰트 (CSS)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 유틸: NFC/NFD 파일 찾기
# =========================
def find_file_by_unicode(directory: Path, target_name: str):
    target_nfc = unicodedata.normalize("NFC", target_name)
    target_nfd = unicodedata.normalize("NFD", target_name)

    for file in directory.iterdir():
        name_nfc = unicodedata.normalize("NFC", file.name)
        name_nfd = unicodedata.normalize("NFD", file.name)

        if name_nfc == target_nfc or name_nfd == target_nfd:
            return file
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_environment_data(data_dir: Path):
    env_data = {}

    for file in data_dir.iterdir():
        if file.suffix.lower() == ".csv":
            school = file.stem.replace("_환경데이터", "")
            try:
                df = pd.read_csv(file)
                env_data[school] = df
            except Exception as e:
                st.error(f"{file.name} 로딩 실패: {e}")

    return env_data


@st.cache_data
def load_growth_data(data_dir: Path):
    target_xlsx = "4개교_생육결과데이터.xlsx"
    xlsx_path = find_file_by_unicode(data_dir, target_xlsx)

    if xlsx_path is None:
        return None

    try:
        excel = pd.ExcelFile(xlsx_path)
        growth_data = {}

        for sheet in excel.sheet_names:
            df = excel.parse(sheet)
            growth_data[sheet] = df

        return growth_data
    except Exception as e:
        st.error(f"생육 데이터 로딩 실패: {e}")
        return None

# =========================
# 데이터 경로
# =========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# =========================
# 데이터 로딩
# =========================
with st.spinner("데이터를 불러오는 중입니다..."):
    env_data = load_environment_data(DATA_DIR)
    growth_data = load_growth_data(DATA_DIR)

if not env_data or growth_data is None:
    st.error("데이터를 불러올 수 없습니다. 파일 구조와 파일명을 확인하세요.")
    st.stop()

# =========================
# 제목
# =========================
st.title("🌱 극지식물 생육에 따른 최적 EC농도 분석")

# =========================
# 사이드바
# =========================
school_options = ["전체"] + list(env_data.keys())
selected_school = st.sidebar.selectbox("학교 선택", school_options)

# =========================
# 탭 구성
# =========================
tab1, tab2, tab3 = st.tabs(["연구 배경", "연구 목적", "핵심 질문"])

with tab1:
    st.markdown("""
- 극지 환경에서는 토양과 수분 조건이 극도로 제한된다  
- 양액 재배 시 **EC 농도**는 식물 생육을 좌우하는 핵심 요인이다  
- EC가 너무 낮으면 **영양 결핍**, 너무 높으면 **삼투 스트레스**가 발생한다  
    """)

with tab2:
    st.markdown("""
- EC 농도 차이에 따른 극지식물 생육 변화 분석  
- 생중량 · 잎 수 · 길이 지표를 활용한 정량 비교  
- 극지식물에 적합한 **최적 EC 농도 도출**  
    """)

with tab3:
    st.markdown("""
- EC 농도가 증가할수록 생육은 항상 좋아질까?  
- 생중량과 잎 수 · 길이는 어떤 관계가 있을까?  
- 극지식물에 가장 효율적인 EC는 얼마일까?  
    """)

# =========================
# 환경 데이터 시각화
# =========================
st.subheader("🌡️ 환경 조건 비교")

fig_env = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    subplot_titles=["온도", "습도", "pH"]
)

for school, df in env_data.items():
    if selected_school != "전체" and school != selected_school:
        continue

    fig_env.add_trace(
        go.Scatter(x=df["time"], y=df["temperature"], name=f"{school} 온도"),
        row=1, col=1
    )
    fig_env.add_trace(
        go.Scatter(x=df["time"], y=df["humidity"], name=f"{school} 습도"),
        row=2, col=1
    )
    fig_env.add_trace(
        go.Scatter(x=df["time"], y=df["ph"], name=f"{school} pH"),
        row=3, col=1
    )

fig_env.update_layout(
    height=800,
    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
)

st.plotly_chart(fig_env, use_container_width=True)

# =========================
# 생육 데이터 분석
# =========================
st.subheader("📊 EC 농도별 생육 결과 비교")

ec_map = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

growth_all = []

for school, df in growth_data.items():
    df = df.copy()
    df["학교"] = school
    df["EC"] = ec_map.get(school)
    growth_all.append(df)

growth_df = pd.concat(growth_all, ignore_index=True)

if selected_school != "전체":
    growth_df = growth_df[growth_df["학교"] == selected_school]

# =========================
# 생중량 박스플롯
# =========================
fig_weight = px.box(
    growth_df,
    x="EC",
    y="생중량(g)",
    color="학교",
    title="EC 농도별 생중량 분포"
)

fig_weight.update_layout(
    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
)

# 최적 EC 강조 (2.0)
fig_weight.add_vline(
    x=2.0,
    line_dash="dash",
    line_color="red",
    annotation_text="최적 EC (2.0)",
    annotation_position="top"
)

st.plotly_chart(fig_weight, use_container_width=True)

# =========================
# 상관 관계
# =========================
st.subheader("📈 생육 지표 간 관계")

fig_corr = px.scatter(
    growth_df,
    x="잎 수(장)",
    y="생중량(g)",
    size="지상부 길이(mm)",
    color="EC",
    title="잎 수 · 길이 · 생중량 관계"
)

fig_corr.update_layout(
    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
)

st.plotly_chart(fig_corr, use_container_width=True)

# =========================
# XLSX 다운로드
# =========================
st.subheader("⬇️ 분석 데이터 다운로드")

buffer = io.BytesIO()
growth_df.to_excel(buffer, index=False, engine="openpyxl")
buffer.seek(0)

st.download_button(
    label="생육 분석 데이터 다운로드 (Excel)",
    data=buffer,
    file_name="극지식물_EC_생육분석.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
