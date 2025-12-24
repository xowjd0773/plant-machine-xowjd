import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pathlib import Path
import unicodedata
import io

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트 CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 유틸 함수
# =========================
def normalize_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)

def find_file_by_name(directory: Path, target_name: str):
    target = normalize_name(target_name)
    for p in directory.iterdir():
        if normalize_name(p.name) == target:
            return p
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_env_data():
    data_dir = Path("data")
    result = {}

    targets = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    with st.spinner("환경 데이터 로딩 중..."):
        for t in targets:
            path = find_file_by_name(data_dir, t)
            if path is None:
                st.error(f"❌ 파일 누락: {t}")
                continue
            df = pd.read_csv(path)
            df["time"] = pd.to_datetime(df["time"])
            school = t.replace("_환경데이터.csv", "")
            result[school] = df

    return result


@st.cache_data
def load_growth_data():
    data_dir = Path("data")
    xlsx = find_file_by_name(data_dir, "4개교_생육결과데이터.xlsx")
    if xlsx is None:
        st.error("❌ 생육 결과 XLSX 파일 없음")
        return {}

    with st.spinner("생육 데이터 로딩 중..."):
        xls = pd.ExcelFile(xlsx)
        result = {}
        for sheet in xls.sheet_names:
            result[sheet] = pd.read_excel(xlsx, sheet_name=sheet)

    return result


env_data = load_env_data()
growth_data = load_growth_data()

if not env_data or not growth_data:
    st.stop()

# =========================
# 메타 정보
# =========================
ec_conditions = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# =========================
# 사이드바
# =========================
st.sidebar.title("학교 선택")
school_option = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(ec_conditions.keys())
)

# =========================
# 제목
# =========================
st.title("🌱 극지식물 최적 EC 농도 연구")

tabs = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ======================================================
# Tab 3 : 생육 결과 (오류 수정 핵심 영역)
# ======================================================
with tabs[2]:
    st.subheader("🥇 EC별 평균 생중량")

    rows = []
    for school, df in growth_data.items():
        rows.append({
            "학교": school,
            "EC": ec_conditions[school],
            "평균 생중량": df["생중량(g)"].mean(),
            "개체수": len(df)
        })

    ec_df = pd.DataFrame(rows)
    best = ec_df.loc[ec_df["평균 생중량"].idxmax()]

    col1, col2, col3 = st.columns(3)
    col1.metric("최대 평균 생중량", f"{best['평균 생중량']:.2f} g")
    col2.metric("최적 EC", best["EC"])
    col3.metric("학교", best["학교"])

    fig_bar = px.bar(
        ec_df,
        x="EC",
        y="평균 생중량",
        color="학교",
        text="평균 생중량"
    )
    fig_bar.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("상관관계 분석")

    all_df = []
    for school, df in growth_data.items():
        tmp = df.copy()
        tmp["학교"] = school
        all_df.append(tmp)

    all_df = pd.concat(all_df)

    col1, col2 = st.columns(2)

    fig1 = px.scatter(
        all_df,
        x="잎 수(장)",
        y="생중량(g)",
        color="학교"
    )
    fig1.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    col1.plotly_chart(fig1, use_container_width=True)

    fig2 = px.scatter(
        all_df,
        x="지상부 길이(mm)",
        y="생중량(g)",
        color="학교"
    )
    fig2.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    col2.plotly_chart(fig2, use_container_width=True)
